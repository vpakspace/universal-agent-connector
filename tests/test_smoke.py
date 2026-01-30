"""Minimal smoke tests to verify basic imports work."""


def test_import_connector():
    """Verify ai_agent_connector package is importable."""
    import ai_agent_connector  # noqa: F401


def test_import_db_connectors():
    """Verify database connectors module is importable."""
    from ai_agent_connector.app.db import connectors  # noqa: F401


def test_import_security():
    """Verify security module is importable."""
    from ai_agent_connector.app.security import ontoguard_adapter  # noqa: F401
