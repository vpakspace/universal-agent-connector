"""
OntoGuard integration exceptions.

This module defines custom exceptions for the OntoGuard integration,
providing clear error types for different failure scenarios.
"""

from typing import Optional, List, Dict, Any


class OntoGuardError(Exception):
    """
    Base exception for all OntoGuard-related errors.

    Attributes:
        message: Human-readable error description
        details: Additional error details (optional)
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ValidationDeniedError(OntoGuardError):
    """
    Raised when an action is denied by OntoGuard validation.

    Attributes:
        action: The action that was denied
        entity_type: The entity type involved
        reason: The reason for denial
        suggestions: List of suggested alternative actions
    """

    def __init__(
        self,
        action: str,
        entity_type: str,
        reason: str,
        suggestions: Optional[List[str]] = None
    ):
        self.action = action
        self.entity_type = entity_type
        self.reason = reason
        self.suggestions = suggestions or []

        message = f"Action '{action}' on '{entity_type}' denied: {reason}"
        details = {
            "action": action,
            "entity_type": entity_type,
            "suggestions": self.suggestions
        }

        super().__init__(message, details)


class OntologyLoadError(OntoGuardError):
    """
    Raised when an ontology file fails to load.

    Attributes:
        path: Path to the ontology file that failed to load
        error: The underlying error message
    """

    def __init__(self, path: str, error: str):
        self.path = path
        self.error = error

        message = f"Failed to load ontology '{path}': {error}"
        details = {
            "path": path,
            "underlying_error": error
        }

        super().__init__(message, details)


class OntologyParseError(OntoGuardError):
    """
    Raised when an ontology file cannot be parsed.

    Attributes:
        path: Path to the ontology file
        line: Line number where parsing failed (if available)
        error: The parsing error message
    """

    def __init__(self, path: str, error: str, line: Optional[int] = None):
        self.path = path
        self.line = line
        self.error = error

        message = f"Failed to parse ontology '{path}'"
        if line:
            message += f" at line {line}"
        message += f": {error}"

        details = {
            "path": path,
            "line": line,
            "underlying_error": error
        }

        super().__init__(message, details)


class ConfigurationError(OntoGuardError):
    """
    Raised when there is an invalid OntoGuard configuration.

    Attributes:
        config_path: Path to the configuration file (if applicable)
        field: The configuration field that is invalid
        error: Description of the configuration error
    """

    def __init__(
        self,
        error: str,
        config_path: Optional[str] = None,
        field: Optional[str] = None
    ):
        self.config_path = config_path
        self.field = field
        self.error = error

        message = "Invalid OntoGuard configuration"
        if config_path:
            message += f" in '{config_path}'"
        if field:
            message += f" (field: {field})"
        message += f": {error}"

        details = {
            "config_path": config_path,
            "field": field,
            "underlying_error": error
        }

        super().__init__(message, details)


class PermissionDeniedError(OntoGuardError):
    """
    Raised when a role lacks permission for an action.

    Attributes:
        role: The role that was denied
        action: The action that was attempted
        entity_type: The entity type involved
        required_role: The role that would have permission
    """

    def __init__(
        self,
        role: str,
        action: str,
        entity_type: str,
        required_role: Optional[str] = None
    ):
        self.role = role
        self.action = action
        self.entity_type = entity_type
        self.required_role = required_role

        message = f"Role '{role}' does not have permission to '{action}' on '{entity_type}'"
        if required_role:
            message += f" (requires role: {required_role})"

        details = {
            "role": role,
            "action": action,
            "entity_type": entity_type,
            "required_role": required_role
        }

        super().__init__(message, details)


class ApprovalRequiredError(OntoGuardError):
    """
    Raised when an action requires approval that hasn't been granted.

    Attributes:
        action: The action that requires approval
        entity_type: The entity type involved
        approver_role: The role that must approve the action
    """

    def __init__(self, action: str, entity_type: str, approver_role: str):
        self.action = action
        self.entity_type = entity_type
        self.approver_role = approver_role

        message = f"Action '{action}' on '{entity_type}' requires approval from '{approver_role}'"
        details = {
            "action": action,
            "entity_type": entity_type,
            "approver_role": approver_role
        }

        super().__init__(message, details)
