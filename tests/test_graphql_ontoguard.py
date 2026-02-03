"""
Unit tests for GraphQL OntoGuard mutations and queries.
Tests GraphQL schema types, inputs, and mutations.

Note: These tests require graphene package. They will be skipped if graphene is not installed.
"""

import pytest
from unittest.mock import patch, MagicMock

# Check if graphene is available
try:
    import graphene
    GRAPHENE_AVAILABLE = True
except ImportError:
    GRAPHENE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not GRAPHENE_AVAILABLE,
    reason="graphene not installed"
)


@pytest.mark.skipif(not GRAPHENE_AVAILABLE, reason="graphene not installed")
class TestOntoGuardGraphQLTypes:
    """Test OntoGuard GraphQL type definitions"""

    def test_import_schema(self):
        """Test that schema imports correctly"""
        from ai_agent_connector.app.graphql.schema import schema
        assert schema is not None

    def test_ontoguard_types_exist(self):
        """Test that OntoGuard types are defined"""
        from ai_agent_connector.app.graphql.schema import (
            OntoGuardValidationResultType,
            OntoGuardStatusType,
            AllowedActionType,
            RuleExplanationType,
        )
        assert OntoGuardValidationResultType is not None
        assert OntoGuardStatusType is not None
        assert AllowedActionType is not None
        assert RuleExplanationType is not None

    def test_ontoguard_input_types_exist(self):
        """Test that OntoGuard input types are defined"""
        from ai_agent_connector.app.graphql.schema import (
            ValidateActionInput,
            CheckPermissionsInput,
            ExplainRuleInput,
        )
        assert ValidateActionInput is not None
        assert CheckPermissionsInput is not None
        assert ExplainRuleInput is not None


@pytest.mark.skipif(not GRAPHENE_AVAILABLE, reason="graphene not installed")
class TestOntoGuardGraphQLMutations:
    """Test OntoGuard GraphQL mutations"""

    def test_mutations_registered(self):
        """Test that OntoGuard mutations are registered in Mutation class"""
        from ai_agent_connector.app.graphql.schema import Mutation
        # Check mutation fields exist
        assert hasattr(Mutation, 'validate_ontoguard_action')
        assert hasattr(Mutation, 'check_ontoguard_permissions')
        assert hasattr(Mutation, 'explain_ontoguard_rule')

    def test_validate_mutation_class_exists(self):
        """Test ValidateOntoGuardAction mutation class"""
        from ai_agent_connector.app.graphql.schema import ValidateOntoGuardAction
        assert ValidateOntoGuardAction is not None
        assert hasattr(ValidateOntoGuardAction, 'Arguments')
        assert hasattr(ValidateOntoGuardAction, 'mutate')

    def test_check_permissions_mutation_class_exists(self):
        """Test CheckOntoGuardPermissions mutation class"""
        from ai_agent_connector.app.graphql.schema import CheckOntoGuardPermissions
        assert CheckOntoGuardPermissions is not None
        assert hasattr(CheckOntoGuardPermissions, 'Arguments')
        assert hasattr(CheckOntoGuardPermissions, 'mutate')

    def test_explain_rule_mutation_class_exists(self):
        """Test ExplainOntoGuardRule mutation class"""
        from ai_agent_connector.app.graphql.schema import ExplainOntoGuardRule
        assert ExplainOntoGuardRule is not None
        assert hasattr(ExplainOntoGuardRule, 'Arguments')
        assert hasattr(ExplainOntoGuardRule, 'mutate')


@pytest.mark.skipif(not GRAPHENE_AVAILABLE, reason="graphene not installed")
class TestOntoGuardGraphQLQueries:
    """Test OntoGuard GraphQL queries"""

    def test_queries_registered(self):
        """Test that OntoGuard queries are registered in Query class"""
        from ai_agent_connector.app.graphql.schema import Query
        # Check query fields exist
        assert hasattr(Query, 'ontoguard_status')
        assert hasattr(Query, 'ontoguard_validate')
        assert hasattr(Query, 'ontoguard_allowed_actions')
        assert hasattr(Query, 'ontoguard_explain_rule')

    def test_resolver_methods_exist(self):
        """Test that resolver methods exist"""
        from ai_agent_connector.app.graphql.schema import Query
        assert hasattr(Query, 'resolve_ontoguard_status')
        assert hasattr(Query, 'resolve_ontoguard_validate')
        assert hasattr(Query, 'resolve_ontoguard_allowed_actions')
        assert hasattr(Query, 'resolve_ontoguard_explain_rule')
