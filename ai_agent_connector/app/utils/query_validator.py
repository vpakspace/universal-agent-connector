"""
Query complexity and safety validator
Restricts dangerous operations and limits query complexity
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from ..utils.sql_parser import QueryType, get_query_type, extract_tables_from_query


class RiskLevel(Enum):
    """Query risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplexityLimits:
    """Query complexity limits"""
    max_join_depth: int = 3  # Maximum number of JOINs
    max_tables: int = 5  # Maximum number of tables in query
    max_subquery_depth: int = 2  # Maximum nested subquery depth
    max_union_queries: int = 3  # Maximum UNION queries
    max_query_length: int = 10000  # Maximum query length in characters
    allow_delete: bool = False  # Allow DELETE operations
    allow_drop: bool = False  # Allow DROP operations
    allow_truncate: bool = False  # Allow TRUNCATE operations
    allow_alter: bool = False  # Allow ALTER operations
    allow_create: bool = False  # Allow CREATE operations
    allow_grant: bool = False  # Allow GRANT operations
    allow_revoke: bool = False  # Allow REVOKE operations
    allow_execute: bool = False  # Allow EXECUTE/EXEC operations
    max_result_rows: Optional[int] = None  # Maximum rows to return (None = unlimited)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'max_join_depth': self.max_join_depth,
            'max_tables': self.max_tables,
            'max_subquery_depth': self.max_subquery_depth,
            'max_union_queries': self.max_union_queries,
            'max_query_length': self.max_query_length,
            'allow_delete': self.allow_delete,
            'allow_drop': self.allow_drop,
            'allow_truncate': self.allow_truncate,
            'allow_alter': self.allow_alter,
            'allow_create': self.allow_create,
            'allow_grant': self.allow_grant,
            'allow_revoke': self.allow_revoke,
            'allow_execute': self.allow_execute,
            'max_result_rows': self.max_result_rows
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplexityLimits':
        """Create from dictionary"""
        return cls(
            max_join_depth=data.get('max_join_depth', 3),
            max_tables=data.get('max_tables', 5),
            max_subquery_depth=data.get('max_subquery_depth', 2),
            max_union_queries=data.get('max_union_queries', 3),
            max_query_length=data.get('max_query_length', 10000),
            allow_delete=data.get('allow_delete', False),
            allow_drop=data.get('allow_drop', False),
            allow_truncate=data.get('allow_truncate', False),
            allow_alter=data.get('allow_alter', False),
            allow_create=data.get('allow_create', False),
            allow_grant=data.get('allow_grant', False),
            allow_revoke=data.get('allow_revoke', False),
            allow_execute=data.get('allow_execute', False),
            max_result_rows=data.get('max_result_rows')
        )


@dataclass
class ValidationResult:
    """Query validation result"""
    is_valid: bool
    risk_level: RiskLevel
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    requires_approval: bool = False
    complexity_score: int = 0  # 0-100, higher = more complex
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'is_valid': self.is_valid,
            'risk_level': self.risk_level.value,
            'errors': self.errors,
            'warnings': self.warnings,
            'requires_approval': self.requires_approval,
            'complexity_score': self.complexity_score
        }


class QueryValidator:
    """
    Query complexity and safety validator.
    Validates queries against complexity limits and dangerous operations.
    """
    
    def __init__(self):
        """Initialize query validator"""
        # agent_id -> ComplexityLimits
        self._limits: Dict[str, ComplexityLimits] = {}
        # Default limits
        self._default_limits = ComplexityLimits()
    
    def set_limits(self, agent_id: str, limits: ComplexityLimits) -> None:
        """
        Set complexity limits for an agent.
        
        Args:
            agent_id: Agent ID
            limits: Complexity limits
        """
        self._limits[agent_id] = limits
    
    def get_limits(self, agent_id: str) -> ComplexityLimits:
        """
        Get complexity limits for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            ComplexityLimits: Limits for the agent (or default if not set)
        """
        return self._limits.get(agent_id, self._default_limits)
    
    def validate_query(
        self,
        agent_id: str,
        query: str,
        query_type: Optional[QueryType] = None
    ) -> ValidationResult:
        """
        Validate a query against complexity limits and safety rules.
        
        Args:
            agent_id: Agent ID executing the query
            query: SQL query to validate
            query_type: Optional query type (will be detected if not provided)
            
        Returns:
            ValidationResult: Validation result
        """
        if not query or not isinstance(query, str):
            return ValidationResult(
                is_valid=False,
                risk_level=RiskLevel.CRITICAL,
                errors=["Query is empty or invalid"]
            )
        
        limits = self.get_limits(agent_id)
        result = ValidationResult(is_valid=True, risk_level=RiskLevel.LOW)
        
        # Detect query type
        if query_type is None:
            query_type = get_query_type(query)
        
        # Check query length
        if len(query) > limits.max_query_length:
            result.is_valid = False
            result.errors.append(
                f"Query length ({len(query)}) exceeds maximum ({limits.max_query_length})"
            )
            result.risk_level = RiskLevel.HIGH
        
        # Check for dangerous operations
        dangerous_ops = self._check_dangerous_operations(query, limits, query_type)
        result.errors.extend(dangerous_ops['errors'])
        result.warnings.extend(dangerous_ops['warnings'])
        
        if dangerous_ops['errors']:
            result.is_valid = False
            result.risk_level = RiskLevel.CRITICAL
        
        # Check complexity
        complexity = self._analyze_complexity(query, limits)
        result.complexity_score = complexity['score']
        result.errors.extend(complexity['errors'])
        result.warnings.extend(complexity['warnings'])
        
        if complexity['errors']:
            result.is_valid = False
            if result.risk_level == RiskLevel.LOW:
                result.risk_level = RiskLevel.MEDIUM
        
        # Determine if approval is required
        result.requires_approval = (
            result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] or
            result.complexity_score > 70 or
            query_type in [QueryType.DELETE, QueryType.UPDATE] or
            'DROP' in query.upper() or
            'TRUNCATE' in query.upper()
        )
        
        # Update risk level based on complexity
        if result.complexity_score > 80:
            result.risk_level = RiskLevel.HIGH
        elif result.complexity_score > 50:
            if result.risk_level == RiskLevel.LOW:
                result.risk_level = RiskLevel.MEDIUM
        
        return result
    
    def _check_dangerous_operations(
        self,
        query: str,
        limits: ComplexityLimits,
        query_type: QueryType
    ) -> Dict[str, List[str]]:
        """Check for dangerous operations"""
        errors = []
        warnings = []
        query_upper = query.upper()
        
        # Check DELETE
        if not limits.allow_delete and query_type == QueryType.DELETE:
            errors.append("DELETE operations are not allowed")
        
        # Check DROP
        if not limits.allow_drop and 'DROP' in query_upper:
            errors.append("DROP operations are not allowed")
        
        # Check TRUNCATE
        if not limits.allow_truncate and 'TRUNCATE' in query_upper:
            errors.append("TRUNCATE operations are not allowed")
        
        # Check ALTER
        if not limits.allow_alter and 'ALTER' in query_upper:
            errors.append("ALTER operations are not allowed")
        
        # Check CREATE
        if not limits.allow_create and 'CREATE' in query_upper:
            errors.append("CREATE operations are not allowed")
        
        # Check GRANT
        if not limits.allow_grant and 'GRANT' in query_upper:
            errors.append("GRANT operations are not allowed")
        
        # Check REVOKE
        if not limits.allow_revoke and 'REVOKE' in query_upper:
            errors.append("REVOKE operations are not allowed")
        
        # Check EXECUTE/EXEC
        if not limits.allow_execute and ('EXECUTE' in query_upper or 'EXEC' in query_upper):
            errors.append("EXECUTE operations are not allowed")
        
        # Warnings for UPDATE without WHERE
        if query_type == QueryType.UPDATE and 'WHERE' not in query_upper:
            warnings.append("UPDATE without WHERE clause may affect all rows")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _analyze_complexity(
        self,
        query: str,
        limits: ComplexityLimits
    ) -> Dict[str, Any]:
        """Analyze query complexity"""
        errors = []
        warnings = []
        score = 0
        
        query_upper = query.upper()
        normalized = re.sub(r'\s+', ' ', query.strip())
        
        # Count JOINs
        join_count = len(re.findall(r'\bJOIN\b', query_upper, re.IGNORECASE))
        if join_count > limits.max_join_depth:
            errors.append(
                f"Query has {join_count} JOINs, exceeds maximum of {limits.max_join_depth}"
            )
        score += join_count * 10
        
        # Count tables
        tables = extract_tables_from_query(query)
        table_count = len(tables)
        if table_count > limits.max_tables:
            errors.append(
                f"Query references {table_count} tables, exceeds maximum of {limits.max_tables}"
            )
        score += table_count * 5
        
        # Count UNION queries
        union_count = len(re.findall(r'\bUNION\b', query_upper, re.IGNORECASE))
        if union_count > limits.max_union_queries:
            errors.append(
                f"Query has {union_count} UNIONs, exceeds maximum of {limits.max_union_queries}"
            )
        score += union_count * 8
        
        # Estimate subquery depth (simple heuristic)
        subquery_depth = self._estimate_subquery_depth(query)
        if subquery_depth > limits.max_subquery_depth:
            errors.append(
                f"Query has subquery depth of {subquery_depth}, exceeds maximum of {limits.max_subquery_depth}"
            )
        score += subquery_depth * 15
        
        # Check for complex functions
        if 'WINDOW' in query_upper or 'OVER(' in query_upper:
            score += 10
            warnings.append("Query contains window functions (may be complex)")
        
        if 'CASE' in query_upper:
            case_count = len(re.findall(r'\bCASE\b', query_upper, re.IGNORECASE))
            score += case_count * 3
        
        # Check for CTEs (Common Table Expressions)
        if 'WITH' in query_upper:
            score += 5
            warnings.append("Query contains CTEs (may be complex)")
        
        # Cap score at 100
        score = min(score, 100)
        
        return {
            'score': score,
            'errors': errors,
            'warnings': warnings
        }
    
    def _estimate_subquery_depth(self, query: str) -> int:
        """Estimate maximum subquery nesting depth"""
        # Simple heuristic: count opening parentheses after SELECT
        depth = 0
        max_depth = 0
        in_select = False
        
        query_upper = query.upper()
        i = 0
        while i < len(query_upper):
            if query_upper[i:i+6] == 'SELECT':
                in_select = True
                i += 6
            elif query_upper[i] == '(':
                if in_select:
                    depth += 1
                    max_depth = max(max_depth, depth)
                i += 1
            elif query_upper[i] == ')':
                if in_select:
                    depth = max(0, depth - 1)
                i += 1
            else:
                i += 1
        
        return max_depth
    
    def remove_agent_limits(self, agent_id: str) -> None:
        """Remove limits for an agent"""
        self._limits.pop(agent_id, None)

