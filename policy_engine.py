"""
Policy Engine for MCP Governance
Validates tool execution requests against security policies

This module provides the PolicyEngine class for validating tool execution
requests against various security policies including rate limits, RLS,
complexity limits, PII access, and OntoGuard semantic validation.
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of policy validation"""
    is_allowed: bool
    reason: str
    suggestions: List[str]
    failed_policy: Optional[str] = None  # Which policy failed (rate_limit, rls, complexity, pii_access)
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PolicyEngine:
    """
    Policy engine that validates tool execution requests.
    Checks: rate limits, RLS, complexity, PII access permissions.
    """
    
    def __init__(
        self,
        max_calls_per_hour: int = 100,
        max_complexity_score: int = 100
    ):
        """
        Initialize policy engine
        
        Args:
            max_calls_per_hour: Maximum tool calls per hour per user
            max_complexity_score: Maximum allowed query complexity score
        """
        self.max_calls_per_hour = max_calls_per_hour
        self.max_complexity_score = max_complexity_score
        
        # Rate limiting: user_id -> list of timestamps
        self._rate_limit_timestamps: Dict[str, List[datetime]] = defaultdict(list)
        
        # RLS mapping: user_id -> list of allowed tenant_ids
        self._user_tenants: Dict[str, List[str]] = {
            # Example: "user1" can access ["tenant1", "tenant2"]
        }
        
        # PII permissions: user_id -> bool (has PII_READ permission)
        self._pii_permissions: Dict[str, bool] = {
            # Example: "user1" -> True (has PII_READ)
        }
        
        # Validation result cache: cache_key -> (result, expiry_time)
        self._cache: Dict[str, tuple[ValidationResult, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def validate(
        self,
        user_id: str,
        tenant_id: Optional[str],
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate tool execution request against policies
        
        Args:
            user_id: User ID making the request
            tenant_id: Tenant ID (for RLS check)
            tool_name: Name of the tool being called
            arguments: Arguments passed to the tool
        
        Returns:
            ValidationResult indicating if request is allowed
        """
        # Check cache first
        cache_key = self._get_cache_key(user_id, tenant_id, tool_name, arguments)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        # Run validation checks in order
        validation_result = await self._run_validation_checks(
            user_id, tenant_id, tool_name, arguments
        )
        
        # Cache result
        self._cache_result(cache_key, validation_result)
        
        return validation_result
    
    async def _run_validation_checks(
        self,
        user_id: str,
        tenant_id: Optional[str],
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ValidationResult:
        """Run all validation checks in order"""
        
        # 1. Rate limit check
        rate_limit_result = self._check_rate_limit(user_id)
        if not rate_limit_result.is_allowed:
            return rate_limit_result
        
        # 2. RLS check (if tenant_id provided)
        if tenant_id:
            rls_result = self._check_rls(user_id, tenant_id)
            if not rls_result.is_allowed:
                return rls_result
        
        # 3. Complexity check
        complexity_result = self._check_complexity(tool_name, arguments)
        if not complexity_result.is_allowed:
            return complexity_result
        
        # 4. PII access check (if tool accesses PII)
        if self._tool_accesses_pii(tool_name, arguments):
            pii_result = self._check_pii_access(user_id)
            if not pii_result.is_allowed:
                return pii_result
        
        # All checks passed
        return ValidationResult(
            is_allowed=True,
            reason="All policy checks passed",
            suggestions=[],
            metadata={
                "checks_passed": ["rate_limit", "rls", "complexity", "pii_access"]
            }
        )
    
    def _check_rate_limit(self, user_id: str) -> ValidationResult:
        """
        Check rate limit: max 100 calls/hour per user
        
        Returns:
            ValidationResult
        """
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old timestamps
        user_timestamps = self._rate_limit_timestamps[user_id]
        user_timestamps[:] = [ts for ts in user_timestamps if ts > hour_ago]
        
        # Check limit
        call_count = len(user_timestamps)
        if call_count >= self.max_calls_per_hour:
            return ValidationResult(
                is_allowed=False,
                reason=f"Rate limit exceeded: {call_count}/{self.max_calls_per_hour} calls per hour",
                suggestions=[
                    f"Wait until {(user_timestamps[0] + timedelta(hours=1)).isoformat()} to retry",
                    "Contact administrator to request higher rate limit"
                ],
                failed_policy="rate_limit",
                metadata={"call_count": call_count, "limit": self.max_calls_per_hour}
            )
        
        # Record this call
        user_timestamps.append(now)
        
        return ValidationResult(
            is_allowed=True,
            reason="Rate limit check passed",
            suggestions=[],
            metadata={"call_count": call_count + 1, "limit": self.max_calls_per_hour}
        )
    
    def _check_rls(self, user_id: str, tenant_id: str) -> ValidationResult:
        """
        Check RLS: user can access requested tenant data
        
        Returns:
            ValidationResult
        """
        allowed_tenants = self._user_tenants.get(user_id, [])
        
        if tenant_id not in allowed_tenants:
            return ValidationResult(
                is_allowed=False,
                reason=f"RLS check failed: User '{user_id}' cannot access tenant '{tenant_id}'",
                suggestions=[
                    f"Request access to tenant '{tenant_id}' from administrator",
                    f"Use one of your allowed tenants: {', '.join(allowed_tenants) if allowed_tenants else 'none'}"
                ],
                failed_policy="rls",
                metadata={
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "allowed_tenants": allowed_tenants
                }
            )
        
        return ValidationResult(
            is_allowed=True,
            reason="RLS check passed",
            suggestions=[],
            metadata={"user_id": user_id, "tenant_id": tenant_id}
        )
    
    def _check_complexity(self, tool_name: str, arguments: Dict[str, Any]) -> ValidationResult:
        """
        Check complexity: query complexity score < 100
        
        Returns:
            ValidationResult
        """
        complexity_score = self._calculate_complexity_score(tool_name, arguments)
        
        if complexity_score > self.max_complexity_score:
            return ValidationResult(
                is_allowed=False,
                reason=f"Complexity check failed: Score {complexity_score} exceeds maximum {self.max_complexity_score}",
                suggestions=[
                    "Simplify the query by reducing number of joins",
                    "Add filters to limit result set size",
                    "Split complex query into multiple simpler queries",
                    "Contact administrator to request higher complexity limit"
                ],
                failed_policy="complexity",
                metadata={"complexity_score": complexity_score, "max_score": self.max_complexity_score}
            )
        
        return ValidationResult(
            is_allowed=True,
            reason="Complexity check passed",
            suggestions=[],
            metadata={"complexity_score": complexity_score}
        )
    
    def _check_pii_access(self, user_id: str) -> ValidationResult:
        """
        Check PII access: user has PII_READ permission
        
        Returns:
            ValidationResult
        """
        has_pii_permission = self._pii_permissions.get(user_id, False)
        
        if not has_pii_permission:
            return ValidationResult(
                is_allowed=False,
                reason="PII access check failed: User does not have PII_READ permission",
                suggestions=[
                    "Request PII_READ permission from administrator",
                    "Use a tool that does not access PII data"
                ],
                failed_policy="pii_access",
                metadata={"user_id": user_id, "has_pii_permission": False}
            )
        
        return ValidationResult(
            is_allowed=True,
            reason="PII access check passed",
            suggestions=[],
            metadata={"user_id": user_id, "has_pii_permission": True}
        )
    
    def _calculate_complexity_score(self, tool_name: str, arguments: Dict[str, Any]) -> int:
        """
        Calculate complexity score for a tool call
        
        Simple scoring:
        - Base score: 10
        - Query length: +1 per 100 characters
        - Number of arguments: +5 per argument
        - Nested structures: +10 per level
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
        
        Returns:
            Complexity score
        """
        score = 10  # Base score
        
        # Query length (if query argument exists)
        if "query" in arguments:
            query = str(arguments["query"])
            score += len(query) // 100
        
        # Number of arguments
        score += len(arguments) * 5
        
        # Nested structures
        def count_nesting(obj, depth=0):
            if isinstance(obj, dict):
                return max([count_nesting(v, depth + 1) for v in obj.values()], default=depth)
            elif isinstance(obj, list):
                return max([count_nesting(item, depth + 1) for item in obj], default=depth)
            return depth
        
        max_depth = count_nesting(arguments)
        score += max_depth * 10
        
        return score
    
    def _tool_accesses_pii(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """
        Determine if a tool accesses PII data
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
        
        Returns:
            True if tool accesses PII
        """
        # Check tool name for PII indicators
        tool_lower = tool_name.lower()
        pii_indicators = ["customer", "user", "personal", "pii", "email", "phone", "ssn", "credit"]
        if any(indicator in tool_lower for indicator in pii_indicators):
            return True
        
        # Check arguments for PII indicators
        args_str = json.dumps(arguments).lower()
        if any(indicator in args_str for indicator in pii_indicators):
            return True
        
        return False
    
    def _get_cache_key(self, user_id: str, tenant_id: Optional[str], tool_name: str, arguments: Dict[str, Any]) -> str:
        """Generate cache key for validation result"""
        # Create deterministic key from inputs
        key_data = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "tool_name": tool_name,
            "arguments": json.dumps(arguments, sort_keys=True)
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[ValidationResult]:
        """Get cached validation result if still valid"""
        if cache_key in self._cache:
            result, expiry = self._cache[cache_key]
            if datetime.utcnow() < expiry:
                return result
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: ValidationResult) -> None:
        """Cache validation result"""
        expiry = datetime.utcnow() + self._cache_ttl
        self._cache[cache_key] = (result, expiry)
    
    # Configuration methods for setting permissions (for testing/admin use)
    def grant_tenant_access(self, user_id: str, tenant_id: str) -> None:
        """Grant user access to a tenant"""
        if user_id not in self._user_tenants:
            self._user_tenants[user_id] = []
        if tenant_id not in self._user_tenants[user_id]:
            self._user_tenants[user_id].append(tenant_id)
    
    def revoke_tenant_access(self, user_id: str, tenant_id: str) -> None:
        """Revoke user access to a tenant"""
        if user_id in self._user_tenants:
            self._user_tenants[user_id] = [t for t in self._user_tenants[user_id] if t != tenant_id]
    
    def grant_pii_permission(self, user_id: str) -> None:
        """Grant PII_READ permission to user"""
        self._pii_permissions[user_id] = True
    
    def revoke_pii_permission(self, user_id: str) -> None:
        """Revoke PII_READ permission from user"""
        self._pii_permissions[user_id] = False

    def enable_ontoguard(self, ontology_paths: Optional[List[str]] = None) -> bool:
        """
        Enable OntoGuard semantic validation in the policy engine.

        Args:
            ontology_paths: List of paths to OWL ontology files

        Returns:
            True if OntoGuard was successfully enabled
        """
        try:
            from ai_agent_connector.app.security import (
                get_ontoguard_adapter,
                initialize_ontoguard
            )

            config = {}
            if ontology_paths:
                config['ontology_paths'] = ontology_paths

            return initialize_ontoguard(config)

        except ImportError:
            # OntoGuard module not available
            return False
        except Exception:
            return False


class OntoGuardValidator:
    """
    Policy validator using OntoGuard semantic rules.

    This validator integrates OntoGuard ontology-based validation
    into the existing policy engine infrastructure.
    """

    def __init__(self, adapter=None):
        """
        Initialize the OntoGuard validator.

        Args:
            adapter: Optional OntoGuardAdapter instance. If None, uses singleton.
        """
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    @property
    def adapter(self):
        """Get the OntoGuard adapter (lazy initialization)."""
        if self._adapter is None:
            try:
                from ai_agent_connector.app.security import get_ontoguard_adapter
                self._adapter = get_ontoguard_adapter()
            except ImportError:
                self._logger.warning("OntoGuard module not available")
                return None
        return self._adapter

    def validate(
        self,
        action: str,
        entity_type: str,
        context: Dict[str, Any],
        policy: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate using OntoGuard ontology rules.

        Args:
            action: The action being performed
            entity_type: The entity type being acted upon
            context: Request context (role, user_id, etc.)
            policy: Policy configuration

        Returns:
            ValidationResult indicating if the action is allowed
        """
        # Check if OntoGuard validation is enabled in policy
        if not policy.get('ontoguard_enabled', True):
            return ValidationResult(
                is_allowed=True,
                reason="OntoGuard disabled in policy",
                suggestions=[],
                metadata={"ontoguard_enabled": False}
            )

        adapter = self.adapter
        if adapter is None or not adapter.is_active:
            return ValidationResult(
                is_allowed=True,
                reason="OntoGuard not active (pass-through)",
                suggestions=[],
                metadata={"ontoguard_active": False}
            )

        # Get role from context
        role = context.get('role', 'anonymous')
        user_id = context.get('user_id', 'unknown')

        # Validate action using OntoGuard
        result = adapter.validate_action(action, entity_type, context)

        # Log validation
        self._logger.info(
            f"OntoGuard validation: {action} on {entity_type} "
            f"by {role} (user: {user_id}) = {result.allowed}"
        )

        # Convert to policy engine ValidationResult
        return ValidationResult(
            is_allowed=result.allowed,
            reason=result.reason,
            suggestions=result.suggestions,
            failed_policy="ontoguard" if not result.allowed else None,
            metadata={
                "ontoguard_constraints": result.constraints,
                "ontoguard_metadata": result.metadata
            }
        )


class ExtendedPolicyEngine(PolicyEngine):
    """
    Extended policy engine with OntoGuard integration and schema drift detection.

    This class extends the base PolicyEngine to include OntoGuard
    semantic validation and schema drift checks as additional policy checks.
    """

    def __init__(
        self,
        max_calls_per_hour: int = 100,
        max_complexity_score: int = 100,
        enable_ontoguard: bool = True,
        schema_bindings_path: Optional[str] = None
    ):
        """
        Initialize the extended policy engine.

        Args:
            max_calls_per_hour: Maximum tool calls per hour per user
            max_complexity_score: Maximum allowed query complexity score
            enable_ontoguard: Whether to enable OntoGuard validation
            schema_bindings_path: Path to schema_bindings.yaml (None to disable drift checks)
        """
        super().__init__(max_calls_per_hour, max_complexity_score)
        self._ontoguard_enabled = enable_ontoguard
        self._ontoguard_validator = OntoGuardValidator() if enable_ontoguard else None
        self._schema_drift_detector = None
        self._schema_bindings_path = schema_bindings_path

        if schema_bindings_path:
            self._init_schema_drift(schema_bindings_path)

    async def validate(
        self,
        user_id: str,
        tenant_id: Optional[str],
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate tool execution request against policies including OntoGuard.

        Args:
            user_id: User ID making the request
            tenant_id: Tenant ID (for RLS check)
            tool_name: Name of the tool being called
            arguments: Arguments passed to the tool

        Returns:
            ValidationResult indicating if request is allowed
        """
        # First, run base policy checks
        base_result = await super().validate(user_id, tenant_id, tool_name, arguments)

        if not base_result.is_allowed:
            return base_result

        # Schema drift check (if detector configured and query has schema info)
        if self._schema_drift_detector:
            drift_result = self._check_schema_drift(arguments)
            if drift_result and not drift_result.is_allowed:
                return drift_result

        # Then, run OntoGuard validation if enabled
        if self._ontoguard_enabled and self._ontoguard_validator:
            # Extract action and entity from tool_name and arguments
            action = self._extract_action(tool_name)
            entity_type = self._extract_entity_type(arguments)

            context = {
                'role': arguments.get('role', 'anonymous'),
                'user_id': user_id,
                'tenant_id': tenant_id
            }

            policy = {
                'ontoguard_enabled': self._ontoguard_enabled
            }

            ontoguard_result = self._ontoguard_validator.validate(
                action, entity_type, context, policy
            )

            if not ontoguard_result.is_allowed:
                return ontoguard_result

        return base_result

    def _init_schema_drift(self, config_path: str) -> None:
        """Initialize schema drift detector from config."""
        try:
            from ai_agent_connector.app.security.schema_drift import SchemaDriftDetector
            self._schema_drift_detector = SchemaDriftDetector()
            count = self._schema_drift_detector.load_bindings(config_path)
            logger.info("Schema drift detector initialized with %d bindings", count)
        except Exception as e:
            logger.warning("Failed to initialize schema drift detector: %s", e)
            self._schema_drift_detector = None

    def _check_schema_drift(self, arguments: Dict[str, Any]) -> Optional[ValidationResult]:
        """
        Check schema drift for entities referenced in the query.

        Only blocks on CRITICAL severity (missing columns).
        WARNING severity is logged but allowed.
        CRITICAL severity triggers an alert via the alerting system.
        """
        entity_type = self._extract_entity_type(arguments)
        current_schema = arguments.get("current_schema")

        if not current_schema or not entity_type:
            return None

        report = self._schema_drift_detector.detect_drift(entity_type, current_schema)

        if report.severity == "CRITICAL":
            fixes = self._schema_drift_detector.suggest_fixes(report)

            # Send alert for CRITICAL schema drift (the $4.6M mistake prevention)
            self._send_schema_drift_alert(report, fixes)

            return ValidationResult(
                is_allowed=False,
                reason=f"Schema drift detected: {report.message}",
                suggestions=[f.description for f in fixes],
                failed_policy="schema_drift",
                metadata=report.to_dict(),
            )

        if report.severity == "WARNING":
            logger.warning("Schema drift warning for %s: %s", entity_type, report.message)

        return None

    def _send_schema_drift_alert(self, report, fixes: List) -> None:
        """Send alert via alerting system and WebSocket for CRITICAL schema drift."""
        # Send WebSocket real-time event
        try:
            from ai_agent_connector.app.websocket.ontoguard_ws import emit_schema_drift_event
            emit_schema_drift_event(report.to_dict(), [f.to_dict() for f in fixes])
        except ImportError:
            logger.debug("WebSocket module not available, skipping real-time event")
        except Exception as e:
            logger.debug("Failed to emit WebSocket schema drift event: %s", e)

        # Send alert via notification manager (Slack/PagerDuty/webhook)
        try:
            from ai_agent_connector.app.utils.alerting import (
                get_notification_manager,
                NotificationAlert,
                AlertType,
                AlertSeverity,
            )

            manager = get_notification_manager()
            if manager is None:
                logger.debug("Notification manager not initialized, skipping alert")
                return

            alert = NotificationAlert(
                alert_type=AlertType.SCHEMA_DRIFT_CRITICAL,
                title=f"CRITICAL Schema Drift: {report.entity}",
                severity=AlertSeverity.CRITICAL,
                message=report.message,
                details={
                    "entity": report.entity,
                    "table": report.table,
                    "missing_columns": report.missing_columns,
                    "type_changes": report.type_changes,
                    "renamed_columns": report.renamed_columns,
                    "suggested_fixes": [f.description for f in fixes],
                }
            )
            manager.send(alert)
            logger.info("Schema drift alert sent for entity '%s'", report.entity)

        except ImportError:
            logger.debug("Alerting module not available, skipping schema drift alert")
        except Exception as e:
            logger.warning("Failed to send schema drift alert: %s", e)

    @property
    def schema_drift_detector(self):
        """Access the schema drift detector (for REST endpoints)."""
        return self._schema_drift_detector

    def _extract_action(self, tool_name: str) -> str:
        """Extract action from tool name."""
        # Map common tool names to actions
        action_mapping = {
            'query': 'read',
            'select': 'read',
            'insert': 'create',
            'create': 'create',
            'update': 'update',
            'modify': 'update',
            'delete': 'delete',
            'remove': 'delete',
            'execute': 'execute'
        }

        tool_lower = tool_name.lower()
        for keyword, action in action_mapping.items():
            if keyword in tool_lower:
                return action

        return 'execute'  # Default action

    def _extract_entity_type(self, arguments: Dict[str, Any]) -> str:
        """Extract entity type from arguments."""
        # Try to find entity type in arguments
        entity_keys = ['entity_type', 'entity', 'table', 'resource', 'type']

        for key in entity_keys:
            if key in arguments:
                return str(arguments[key])

        # Try to extract from query
        if 'query' in arguments:
            query = str(arguments['query']).lower()
            # Simple extraction from SQL
            if 'from' in query:
                parts = query.split('from')
                if len(parts) > 1:
                    table_part = parts[1].strip().split()[0]
                    return table_part.strip()

        return 'Resource'  # Default entity type


# Global instances
policy_engine = PolicyEngine()
extended_policy_engine = ExtendedPolicyEngine()

