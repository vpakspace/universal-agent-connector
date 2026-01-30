"""
Test configuration - skip tests that require unavailable optional dependencies.
"""

# Tests requiring graphene (incompatible graphene 3.3 + flask-graphql 2.0.1)
# Tests requiring 'src' module (legacy tests from different project structure)
# Tests requiring external services (locust, etc.)
_skip_tests = [
    # graphene-dependent
    "test_admin_database_endpoints.py",
    "test_admin_database_stories_api.py",
    "test_analytics_automation_stories.py",
    "test_api_routes.py",
    "test_compliance_privacy_stories.py",
    "test_cost_tracking.py",
    "test_custom_ai_providers.py",
    "test_graphql.py",
    "test_admin_ai_agent_stories.py",
    "test_ai_agent_api_endpoints.py",
    "test_error_handling_failover_stories.py",
    "test_governance_middleware.py",
    "test_integration.py",
    "test_mcp_semantic_router.py",
    "test_monitoring_observability_stories.py",
    "test_nl_resource_resolver.py",
    "test_plugin_marketplace_ui.py",
    "test_plugin_sdk.py",
    "test_plugin_validation_automation.py",
    "test_query_enhancement_stories.py",
    "test_security_compliance_stories.py",
    "test_teams_collaboration_stories.py",
    "test_tenant_mcp_manager.py",
    "test_user_experience_stories.py",
    "test_e2e.py",
    # 'src' module (legacy structure)
    "test_jaguar_problem.py",
    "test_jaguar_standalone.py",
    "test_mine_metrics.py",
    "test_mine_standalone.py",
    "test_ontology_compliance.py",
    "test_ontology_compliance_standalone.py",
    "test_spectral_metrics.py",
    "test_spectral_metrics_standalone.py",
    "test_universal_ontology.py",
    # external services
    "test_load_testing.py",
    "test_locust_config.py",
]

collect_ignore = _skip_tests
