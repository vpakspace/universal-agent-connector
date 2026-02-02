"""
Schema Drift Detection Module.

Detects changes between expected schema bindings and actual database schemas.
Adapted from powerbi-ontology-extractor's SchemaMapper.

Key concepts:
- SchemaBinding: maps logical entity -> physical table/columns
- DriftReport: result of drift check (missing/new columns, type changes, renames)
- SchemaDriftDetector: main detection class
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SchemaBinding:
    """Maps a logical entity to its physical table and expected columns."""
    entity: str
    table: str
    columns: Dict[str, str]  # column_name -> expected_type
    domain: str = "default"


@dataclass
class DriftReport:
    """Result of schema drift detection."""
    entity: str
    table: str
    missing_columns: List[str] = field(default_factory=list)
    new_columns: List[str] = field(default_factory=list)
    type_changes: Dict[str, str] = field(default_factory=dict)  # col -> "old -> new"
    renamed_columns: Dict[str, str] = field(default_factory=dict)  # old -> new
    severity: str = "INFO"  # INFO, WARNING, CRITICAL
    message: str = ""

    @property
    def has_drift(self) -> bool:
        return bool(
            self.missing_columns
            or self.type_changes
            or self.renamed_columns
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity,
            "table": self.table,
            "missing_columns": self.missing_columns,
            "new_columns": self.new_columns,
            "type_changes": self.type_changes,
            "renamed_columns": self.renamed_columns,
            "severity": self.severity,
            "message": self.message,
            "has_drift": self.has_drift,
        }


@dataclass
class Fix:
    """Suggested fix for a drift issue."""
    type: str  # update_mapping, add_column, verify_column
    description: str
    action: str
    entity: str
    column: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "description": self.description,
            "action": self.action,
            "entity": self.entity,
            "column": self.column,
        }


class SchemaDriftDetector:
    """
    Detects schema drift between expected bindings and actual DB schemas.

    Usage:
        detector = SchemaDriftDetector()
        detector.load_bindings("config/schema_bindings.yaml")
        report = detector.detect_drift("PatientRecord", {"id": "integer", "name": "text"})
    """

    def __init__(self):
        self._bindings: Dict[str, SchemaBinding] = {}  # entity -> binding

    def load_bindings(self, config_path: str) -> int:
        """
        Load schema bindings from YAML config.

        Returns:
            Number of bindings loaded.
        """
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}

        count = 0
        for domain_name, domain_data in data.get("domains", {}).items():
            for entity_name, entity_data in domain_data.get("entities", {}).items():
                binding = SchemaBinding(
                    entity=entity_name,
                    table=entity_data["table"],
                    columns=entity_data.get("columns", {}),
                    domain=domain_name,
                )
                self._bindings[entity_name] = binding
                count += 1

        logger.info("Loaded %d schema bindings from %s", count, config_path)
        return count

    def add_binding(self, binding: SchemaBinding) -> None:
        """Add or update a single binding."""
        self._bindings[binding.entity] = binding

    def get_binding(self, entity: str) -> Optional[SchemaBinding]:
        """Get binding for an entity."""
        return self._bindings.get(entity)

    @property
    def bindings(self) -> Dict[str, SchemaBinding]:
        return dict(self._bindings)

    def detect_drift(
        self, entity: str, current_schema: Dict[str, str]
    ) -> DriftReport:
        """
        Detect schema drift for an entity.

        Args:
            entity: Logical entity name (e.g. "PatientRecord")
            current_schema: Current DB schema as {column_name: data_type}

        Returns:
            DriftReport with detected issues.
        """
        binding = self._bindings.get(entity)
        if not binding:
            return DriftReport(
                entity=entity,
                table="unknown",
                severity="INFO",
                message=f"No binding found for entity '{entity}'",
            )

        expected_cols = set(binding.columns.keys())
        actual_cols = set(current_schema.keys())

        missing = list(expected_cols - actual_cols)
        new = list(actual_cols - expected_cols)

        # Type changes (for columns that exist in both)
        type_changes = {}
        for col in expected_cols & actual_cols:
            expected_type = _normalize_type(binding.columns[col])
            actual_type = _normalize_type(current_schema[col])
            if expected_type != actual_type:
                type_changes[col] = f"{binding.columns[col]} -> {current_schema[col]}"

        # Rename detection heuristic
        renamed = {}
        if missing and new:
            remaining_missing = list(missing)
            remaining_new = list(new)
            for m_col in list(remaining_missing):
                for n_col in list(remaining_new):
                    if _similar_names(m_col, n_col):
                        renamed[m_col] = n_col
                        remaining_missing.remove(m_col)
                        remaining_new.remove(n_col)
                        break
            missing = remaining_missing
            new = remaining_new

        # Determine severity
        if missing:
            severity = "CRITICAL"
            message = f"Missing columns in '{binding.table}': {missing}"
        elif type_changes or renamed:
            severity = "WARNING"
            parts = []
            if type_changes:
                parts.append(f"type changes: {type_changes}")
            if renamed:
                parts.append(f"renamed: {renamed}")
            message = f"Schema changes in '{binding.table}': {'; '.join(parts)}"
        else:
            severity = "INFO"
            message = f"No drift detected for '{binding.table}'"
            if new:
                message += f" (new columns: {new})"

        return DriftReport(
            entity=entity,
            table=binding.table,
            missing_columns=missing,
            new_columns=new,
            type_changes=type_changes,
            renamed_columns=renamed,
            severity=severity,
            message=message,
        )

    def suggest_fixes(self, report: DriftReport) -> List[Fix]:
        """Generate fix suggestions for a drift report."""
        fixes = []

        for old_name, new_name in report.renamed_columns.items():
            fixes.append(Fix(
                type="update_mapping",
                description=f"Column '{old_name}' appears renamed to '{new_name}'",
                action=f"UPDATE binding: {old_name} -> {new_name}",
                entity=report.entity,
                column=old_name,
            ))

        for col in report.missing_columns:
            fixes.append(Fix(
                type="verify_column",
                description=f"Column '{col}' missing from table '{report.table}'",
                action=f"SELECT * FROM {report.table} WHERE 1=0  -- verify column exists",
                entity=report.entity,
                column=col,
            ))

        for col in report.new_columns:
            fixes.append(Fix(
                type="add_column",
                description=f"New column '{col}' found in table '{report.table}'",
                action=f"Add '{col}' to entity '{report.entity}' binding",
                entity=report.entity,
                column=col,
            ))

        return fixes

    def check_all(self, current_schemas: Dict[str, Dict[str, str]]) -> List[DriftReport]:
        """
        Check drift for all bindings.

        Args:
            current_schemas: {entity_name: {col: type}} for each entity

        Returns:
            List of DriftReports (only those with drift or missing schemas).
        """
        reports = []
        for entity, binding in self._bindings.items():
            schema = current_schemas.get(entity)
            if schema is None:
                reports.append(DriftReport(
                    entity=entity,
                    table=binding.table,
                    severity="CRITICAL",
                    message=f"No current schema provided for entity '{entity}' (table: {binding.table})",
                    missing_columns=list(binding.columns.keys()),
                ))
            else:
                report = self.detect_drift(entity, schema)
                reports.append(report)
        return reports


def _normalize_type(t: str) -> str:
    """Normalize SQL type for comparison."""
    t = t.lower().strip()
    # Common aliases
    aliases = {
        "int": "integer",
        "int4": "integer",
        "int8": "bigint",
        "serial": "integer",
        "bigserial": "bigint",
        "bool": "boolean",
        "varchar": "text",
        "character varying": "text",
        "char": "text",
        "timestamp without time zone": "timestamp",
        "timestamp with time zone": "timestamptz",
        "double precision": "float",
        "real": "float",
        "float4": "float",
        "float8": "float",
        "numeric": "decimal",
    }
    # Strip length specifiers: varchar(255) -> varchar
    base = t.split("(")[0].strip()
    return aliases.get(base, base)


def _similar_names(a: str, b: str) -> bool:
    """
    Heuristic check if two column names are similar (possible rename).

    Checks:
    1. One contains the other (ignoring underscores/hyphens)
    2. Levenshtein-like similarity > 70%
    """
    a_clean = a.replace("_", "").replace("-", "").lower()
    b_clean = b.replace("_", "").replace("-", "").lower()

    if not a_clean or not b_clean:
        return False

    # Containment check
    if a_clean in b_clean or b_clean in a_clean:
        return True

    # Simple similarity (character overlap ratio)
    common = sum(1 for c in a_clean if c in b_clean)
    ratio = (2 * common) / (len(a_clean) + len(b_clean))
    return ratio > 0.7
