"""
OntoGuard Adapter - Integration of semantic validation into Universal Agent Connector.

This module provides an adapter layer between the OntoGuard semantic firewall
and the UAC infrastructure, enabling OWL ontology-based validation for AI agent actions.

Features:
- OWL ontology-based RBAC validation
- LRU caching with TTL for performance
- Pass-through mode when OntoGuard not available
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Optional cache import (graceful degradation)
try:
    from ai_agent_connector.app.cache import (
        cache_validation_result,
        get_cached_validation,
    )
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    cache_validation_result = None  # type: ignore
    get_cached_validation = None  # type: ignore
    logger.warning("Cache module not available, caching disabled")


@dataclass
class ValidationResult:
    """
    Result of an OntoGuard validation operation.

    Attributes:
        allowed: Whether the action is permitted according to the ontology
        reason: Human-readable explanation of the validation result
        constraints: List of constraints that were checked
        suggestions: List of alternative actions that might be allowed
        metadata: Additional metadata about the validation
    """
    allowed: bool
    reason: str
    constraints: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "constraints": self.constraints,
            "suggestions": self.suggestions,
            "metadata": self.metadata
        }


class OntoGuardAdapter:
    """
    Adapter for integrating OntoGuard semantic validation into UAC.

    This class provides a unified interface for validating AI agent actions
    against OWL ontologies using the OntoGuard library. It supports graceful
    degradation when OntoGuard is not available.

    Attributes:
        validator: The OntoGuard OntologyValidator instance (if loaded)
        config_path: Path to the configuration file (optional)
        ontology_paths: List of loaded ontology file paths
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the OntoGuard adapter.

        Args:
            config_path: Optional path to a YAML configuration file
        """
        self.validator = None
        self.config_path = config_path
        self.ontology_paths: List[str] = []
        self._initialized = False
        self._pass_through_mode = False

        logger.info("OntoGuard adapter initialized")

    def initialize(self, ontology_paths: Optional[List[str]] = None) -> bool:
        """
        Initialize the adapter with OWL ontologies.

        Args:
            ontology_paths: List of paths to OWL ontology files.
                           If None, tries to load from config.

        Returns:
            True if initialization was successful, False otherwise
        """
        # Resolve ontology paths
        if ontology_paths is None:
            ontology_paths = self._load_paths_from_config()

        if not ontology_paths:
            logger.warning("No ontology paths provided, using pass-through mode")
            self._pass_through_mode = True
            self._initialized = True
            return True

        # Try to import and initialize OntoGuard
        try:
            from ontoguard.validator import OntologyValidator

            # Load the first ontology (OntoGuard currently supports single ontology)
            # In future, we could extend to merge multiple ontologies
            primary_ontology = ontology_paths[0]

            if not Path(primary_ontology).exists():
                logger.error(f"Ontology file not found: {primary_ontology}")
                self._pass_through_mode = True
                self._initialized = True
                return False

            self.validator = OntologyValidator(primary_ontology)
            self.ontology_paths = ontology_paths
            self._initialized = True
            self._pass_through_mode = False

            logger.info(f"OntoGuard initialized with {len(ontology_paths)} ontology(ies)")
            return True

        except ImportError:
            logger.warning(
                "OntoGuard not installed. Using pass-through mode. "
                "Install with: pip install ontoguard"
            )
            self._pass_through_mode = True
            self._initialized = True
            return False

        except Exception as e:
            logger.error(f"OntoGuard initialization failed: {e}")
            self._pass_through_mode = True
            self._initialized = True
            return False

    def _load_paths_from_config(self) -> List[str]:
        """
        Load ontology paths from configuration file.

        Returns:
            List of ontology file paths
        """
        if not self.config_path:
            return []

        try:
            import yaml

            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return []

            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            ontoguard_config = config.get('ontoguard', {})
            ontologies = ontoguard_config.get('ontologies', [])

            paths = []
            for ont in ontologies:
                path = ont.get('path')
                if path:
                    # Resolve relative paths
                    if not Path(path).is_absolute():
                        path = str(config_file.parent / path)
                    paths.append(path)

            return paths

        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return []

    def validate_action(
        self,
        action: str,
        entity_type: str,
        context: Dict[str, Any],
        use_cache: bool = True
    ) -> ValidationResult:
        """
        Validate an action against the ontology.

        Args:
            action: The action to validate (e.g., "create", "read", "update", "delete")
            entity_type: The entity type being acted upon (e.g., "User", "Order")
            context: Additional context including:
                - role: User's role (e.g., "Admin", "Customer")
                - user_id: User identifier
                - ip: Request IP address
                - timestamp: Request timestamp
                - approved_by: Approver role (if applicable)
                - domain: Domain name for multi-domain support
            use_cache: Whether to use caching (default True)

        Returns:
            ValidationResult indicating whether the action is allowed
        """
        if not self._initialized:
            return ValidationResult(
                allowed=True,
                reason="OntoGuard not initialized (pass-through)",
                constraints=[],
                suggestions=[],
                metadata={"mode": "uninitialized"}
            )

        if self._pass_through_mode or self.validator is None:
            return ValidationResult(
                allowed=True,
                reason="OntoGuard in pass-through mode",
                constraints=[],
                suggestions=[],
                metadata={"mode": "pass_through"}
            )

        # Extract cache key parameters
        role = context.get('role')
        domain = context.get('domain')

        # Check cache first
        if use_cache and CACHE_AVAILABLE:
            cached = get_cached_validation(action, entity_type, role, domain)
            if cached is not None:
                logger.debug(f"Cache HIT: {action}:{entity_type}:{role}:{domain}")
                return ValidationResult(
                    allowed=cached['allowed'],
                    reason=cached.get('reason', 'Cached result'),
                    constraints=cached.get('constraints', []),
                    suggestions=cached.get('suggestions', []),
                    metadata={**cached.get('metadata', {}), 'cached': True}
                )

        try:
            # Extract entity_id from context or generate a placeholder
            entity_id = context.get('entity_id', context.get('user_id', 'unknown'))

            # Call OntoGuard validator
            result = self.validator.validate(
                action=action,
                entity=entity_type,
                entity_id=str(entity_id),
                context=context
            )

            # Convert OntoGuard result to our ValidationResult
            validation_result = ValidationResult(
                allowed=result.allowed,
                reason=result.reason,
                constraints=self._extract_constraints(result),
                suggestions=result.suggested_actions,
                metadata=result.metadata
            )

            # Cache the result
            if use_cache:
                cache_validation_result(
                    action=action,
                    entity_type=entity_type,
                    result=validation_result.to_dict(),
                    role=role,
                    domain=domain
                )
                logger.debug(f"Cache SET: {action}:{entity_type}:{role}:{domain}")

            return validation_result

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                allowed=False,
                reason=f"Validation error: {str(e)}",
                constraints=[],
                suggestions=["Check OntoGuard configuration", "Verify ontology file"],
                metadata={"error": str(e)}
            )

    def _extract_constraints(self, result) -> List[str]:
        """Extract constraint information from validation result."""
        constraints = []
        metadata = result.metadata or {}

        constraint_type = metadata.get('constraint_type')
        if constraint_type:
            constraints.append(f"constraint_type: {constraint_type}")

        if 'required_role' in metadata:
            constraints.append(f"required_role: {metadata['required_role']}")

        if 'applies_to' in metadata:
            constraints.append(f"applies_to: {metadata['applies_to']}")

        return constraints

    def check_permissions(
        self,
        role: str,
        action: str,
        entity_type: str
    ) -> bool:
        """
        Check if a role has permission for a specific action on an entity type.

        Args:
            role: User role (e.g., "Admin", "Manager", "Customer")
            action: The action to check
            entity_type: The entity type

        Returns:
            True if the action is permitted, False otherwise
        """
        if not self._initialized or self._pass_through_mode or self.validator is None:
            return True

        try:
            # Create a minimal context with the role
            context = {"role": role}

            # Use validation to check permissions
            result = self.validate_action(action, entity_type, context)
            return result.allowed

        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False

    def get_allowed_actions(
        self,
        role: str,
        entity_type: str
    ) -> List[str]:
        """
        Get list of allowed actions for a role on a specific entity type.

        Args:
            role: User role
            entity_type: The entity type to query

        Returns:
            List of allowed action names
        """
        if not self._initialized or self._pass_through_mode or self.validator is None:
            return ["*"]  # All actions allowed in pass-through mode

        try:
            # Create context with role
            context = {"role": role}

            # Get allowed actions from OntoGuard
            actions = self.validator.get_allowed_actions(entity_type, context)
            return actions

        except Exception as e:
            logger.error(f"Get allowed actions error: {e}")
            return []

    def explain_rule(
        self,
        action: str,
        entity_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Get a detailed explanation of why an action was allowed or denied.

        Args:
            action: The action to explain
            entity_type: The entity type
            context: Additional context

        Returns:
            Human-readable explanation
        """
        if not self._initialized or self._pass_through_mode or self.validator is None:
            return "OntoGuard not active - all actions are allowed by default."

        try:
            return self.validator.explain_denial(action, entity_type, context)
        except Exception as e:
            return f"Error generating explanation: {e}"

    @property
    def is_active(self) -> bool:
        """Check if OntoGuard is actively validating (not in pass-through mode)."""
        return self._initialized and not self._pass_through_mode and self.validator is not None


# Singleton instance
_adapter_instance: Optional[OntoGuardAdapter] = None


def get_ontoguard_adapter() -> OntoGuardAdapter:
    """
    Get or create the OntoGuard adapter singleton.

    Returns:
        The global OntoGuardAdapter instance
    """
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = OntoGuardAdapter()
    return _adapter_instance


def initialize_ontoguard(config: Dict[str, Any]) -> bool:
    """
    Initialize OntoGuard from a configuration dictionary.

    Args:
        config: Configuration dictionary containing:
            - ontology_paths: List of paths to OWL ontology files
            - config_path: Optional path to YAML config file

    Returns:
        True if initialization was successful, False otherwise
    """
    adapter = get_ontoguard_adapter()

    # Set config path if provided
    config_path = config.get('config_path')
    if config_path:
        adapter.config_path = config_path

    # Get ontology paths
    ontology_paths = config.get('ontology_paths', [])

    return adapter.initialize(ontology_paths)


def reset_ontoguard_adapter() -> None:
    """
    Reset the OntoGuard adapter singleton.

    Useful for testing or reinitializing with different configuration.
    """
    global _adapter_instance
    _adapter_instance = None
