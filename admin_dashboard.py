"""
Universal Agent Connector - Admin Dashboard
Административный интерфейс для управления системой
"""

import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

# Конфигурация
API_URL = os.getenv("UAC_API_URL", "http://localhost:5000")

# Page config
st.set_page_config(
    page_title="UAC Admin Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
    }
    .status-ok { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-error { color: #dc3545; }
    .agent-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)


# ============== Helper Functions ==============

def api_get(endpoint: str) -> Optional[Dict]:
    """GET request to API."""
    try:
        resp = requests.get(f"{API_URL}{endpoint}", timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def api_post(endpoint: str, data: Dict) -> Optional[Dict]:
    """POST request to API."""
    try:
        resp = requests.post(f"{API_URL}{endpoint}", json=data, timeout=10)
        return resp.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def api_delete(endpoint: str) -> bool:
    """DELETE request to API."""
    try:
        resp = requests.delete(f"{API_URL}{endpoint}", timeout=10)
        return resp.status_code == 200
    except Exception as e:
        st.error(f"API Error: {e}")
        return False


def api_put(endpoint: str, data: Dict) -> Optional[Dict]:
    """PUT request to API."""
    try:
        resp = requests.put(f"{API_URL}{endpoint}", json=data, timeout=10)
        return resp.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


# ============== Sidebar ==============

st.sidebar.title("⚙️ UAC Admin")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Навигация",
    ["📊 Dashboard", "👥 Agents", "🛡️ OntoGuard", "📈 Monitoring",
     "🔔 Alerts", "📋 Audit", "⚡ Cache & Rate Limits", "🔧 Settings"]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**API URL:** `{API_URL}`")

# Health check
health = api_get("/health")
if health:
    st.sidebar.success("✅ API Online")
else:
    st.sidebar.error("❌ API Offline")


# ============== Dashboard Page ==============

if page == "📊 Dashboard":
    st.title("📊 System Dashboard")

    # System metrics row
    col1, col2, col3, col4 = st.columns(4)

    # Agents count
    agents_data = api_get("/api/agents")
    with col1:
        count = agents_data.get("count", 0) if agents_data else 0
        st.metric("Registered Agents", count)

    # OntoGuard status
    ontoguard = api_get("/api/ontoguard/status")
    with col2:
        status = ontoguard.get("status", "unknown") if ontoguard else "offline"
        st.metric("OntoGuard Status", status.upper())

    # Cache stats
    cache = api_get("/api/cache/stats")
    with col3:
        if cache and "cache" in cache:
            hit_rate = cache["cache"].get("hit_rate", 0)
            st.metric("Cache Hit Rate", f"{hit_rate:.1f}%")
        else:
            st.metric("Cache Hit Rate", "N/A")

    # Alert channels
    alerts = api_get("/api/alerts/channels")
    with col4:
        channels = len(alerts.get("channels", [])) if alerts else 0
        st.metric("Alert Channels", channels)

    st.markdown("---")

    # Two columns for more details
    left, right = st.columns(2)

    with left:
        st.subheader("📋 Recent Audit Logs")
        audit = api_get("/api/audit/logs?limit=10")
        if audit and "logs" in audit:
            logs = audit["logs"]
            if logs:
                df = pd.DataFrame(logs)
                display_cols = ["timestamp", "action_type", "agent_id", "status"]
                available_cols = [c for c in display_cols if c in df.columns]
                if available_cols:
                    st.dataframe(df[available_cols], use_container_width=True, height=300)
            else:
                st.info("No audit logs yet")
        else:
            st.warning("Could not load audit logs")

    with right:
        st.subheader("📈 Audit Statistics")
        stats = api_get("/api/audit/statistics?days=7")
        if stats:
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Total Actions (7 days)", stats.get("total_actions", 0))
            with col_b:
                st.metric("Period", f"{stats.get('period_days', 7)} days")

            # By status
            by_status = stats.get("by_status", {})
            if by_status:
                st.markdown("**By Status:**")
                status_df = pd.DataFrame([
                    {"Status": k, "Count": v} for k, v in by_status.items()
                ])
                st.bar_chart(status_df.set_index("Status"))
        else:
            st.warning("Could not load statistics")


# ============== Agents Page ==============

elif page == "👥 Agents":
    st.title("👥 Agent Management")

    tab1, tab2, tab3 = st.tabs(["📋 List Agents", "➕ Register Agent", "🗑️ Delete Agent"])

    with tab1:
        st.subheader("Registered Agents")
        agents = api_get("/api/agents")

        if agents and "agents" in agents:
            agent_list = agents["agents"]
            if agent_list:
                for agent in agent_list:
                    with st.expander(f"🤖 {agent.get('agent_id', 'Unknown')}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.json(agent.get("agent_info", {}))
                        with col2:
                            # Get rate limits
                            agent_id = agent.get("agent_id")
                            limits = api_get(f"/api/rate-limits/{agent_id}")
                            if limits:
                                st.markdown("**Rate Limits:**")
                                st.json(limits.get("limits", {}))

                            # Get permissions
                            perms = api_get(f"/api/agents/{agent_id}/permissions")
                            if perms:
                                st.markdown("**Permissions:**")
                                st.json(perms.get("permissions", {}))
            else:
                st.info("No agents registered")
        else:
            st.warning("Could not load agents")

    with tab2:
        st.subheader("Register New Agent")

        with st.form("register_agent"):
            agent_id = st.text_input("Agent ID", placeholder="e.g., doctor-1")

            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name", placeholder="e.g., Dr. Smith")
                role = st.selectbox("Role", ["Admin", "Doctor", "Nurse", "LabTech", "Receptionist", "Manager", "Analyst"])
            with col2:
                department = st.text_input("Department", placeholder="e.g., Cardiology")

            st.markdown("**Rate Limits:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                qpm = st.number_input("Queries/Minute", value=60, min_value=1)
            with col2:
                qph = st.number_input("Queries/Hour", value=1000, min_value=1)
            with col3:
                qpd = st.number_input("Queries/Day", value=10000, min_value=1)

            submitted = st.form_submit_button("Register Agent", type="primary")

            if submitted and agent_id:
                data = {
                    "agent_id": agent_id,
                    "agent_info": {
                        "name": name,
                        "role": role,
                        "department": department
                    },
                    "rate_limits": {
                        "queries_per_minute": qpm,
                        "queries_per_hour": qph,
                        "queries_per_day": qpd
                    }
                }
                result = api_post("/api/agents/register", data)
                if result and "api_key" in result:
                    st.success(f"✅ Agent registered! API Key: `{result['api_key']}`")
                else:
                    st.error(f"Registration failed: {result}")

    with tab3:
        st.subheader("Delete Agent")

        agents = api_get("/api/agents")
        if agents and agents.get("agents"):
            agent_ids = [a.get("agent_id") for a in agents["agents"]]
            selected = st.selectbox("Select Agent to Delete", agent_ids)

            if st.button("🗑️ Delete Agent", type="secondary"):
                if api_delete(f"/api/agents/{selected}"):
                    st.success(f"✅ Agent {selected} deleted")
                    st.rerun()
                else:
                    st.error("Failed to delete agent")
        else:
            st.info("No agents to delete")


# ============== OntoGuard Page ==============

elif page == "🛡️ OntoGuard":
    st.title("🛡️ OntoGuard Management")

    tab1, tab2, tab3 = st.tabs(["📊 Status", "✅ Validate Action", "📋 Schema Drift"])

    with tab1:
        st.subheader("OntoGuard Status")

        status = api_get("/api/ontoguard/status")
        if status:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status", status.get("status", "unknown").upper())
                st.metric("Ontologies Loaded", status.get("ontologies_loaded", 0))
            with col2:
                st.json(status)
        else:
            st.error("Could not get OntoGuard status")

    with tab2:
        st.subheader("Validate Action")

        col1, col2 = st.columns(2)
        with col1:
            action = st.selectbox("Action", ["read", "create", "update", "delete"])
            entity_type = st.selectbox("Entity Type", [
                "PatientRecord", "MedicalRecord", "LabResult",
                "Appointment", "Billing", "Staff",
                "Account", "Transaction", "Loan", "Card"
            ])
        with col2:
            role = st.selectbox("Role", [
                "Admin", "Doctor", "Nurse", "LabTech", "Receptionist",
                "Manager", "Teller", "Analyst", "Auditor"
            ])
            domain = st.selectbox("Domain", ["hospital", "finance"])

        if st.button("🔍 Validate", type="primary"):
            result = api_post("/api/ontoguard/validate", {
                "action": action,
                "entity_type": entity_type,
                "context": {"role": role, "domain": domain}
            })
            if result:
                if result.get("allowed"):
                    st.success(f"✅ Action ALLOWED: {result.get('reason', '')}")
                else:
                    st.error(f"❌ Action DENIED: {result.get('reason', '')}")
                    if result.get("constraints"):
                        st.warning(f"Constraints: {result['constraints']}")
                    if result.get("suggestions"):
                        st.info(f"Suggestions: {result['suggestions']}")
            else:
                st.error("Validation failed")

    with tab3:
        st.subheader("Schema Drift Detection")

        # Get bindings
        bindings = api_get("/api/schema/bindings")
        if bindings and "bindings" in bindings:
            st.markdown("**Current Schema Bindings:**")
            st.json(bindings["bindings"])

        # Check drift
        if st.button("🔄 Check Drift (Live)"):
            st.info("Live drift check requires an authenticated agent with database connection")


# ============== Monitoring Page ==============

elif page == "📈 Monitoring":
    st.title("📈 System Monitoring")

    tab1, tab2 = st.tabs(["📊 Metrics", "🔗 Prometheus"])

    with tab1:
        st.subheader("System Metrics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Cache Statistics")
            cache = api_get("/api/cache/stats")
            if cache and "cache" in cache:
                c = cache["cache"]
                st.metric("Hits", c.get("hits", 0))
                st.metric("Misses", c.get("misses", 0))
                st.metric("Hit Rate", f"{c.get('hit_rate', 0):.2f}%")
                st.metric("Size", c.get("size", 0))
                st.metric("Evictions", c.get("evictions", 0))

        with col2:
            st.markdown("### Rate Limits Overview")
            limits = api_get("/api/rate-limits")
            if limits and "rate_limits" in limits:
                st.json(limits["rate_limits"])

    with tab2:
        st.subheader("Prometheus Metrics")
        st.markdown(f"**Metrics Endpoint:** `{API_URL}/metrics`")

        st.code("""
# Prometheus scrape config
scrape_configs:
  - job_name: 'uac'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
""", language="yaml")

        st.markdown("**Available Metrics:**")
        metrics_list = [
            "uac_http_requests_total",
            "uac_http_request_duration_seconds",
            "uac_ontoguard_validations_total",
            "uac_db_queries_total",
            "uac_agents_registered"
        ]
        for m in metrics_list:
            st.markdown(f"- `{m}`")


# ============== Alerts Page ==============

elif page == "🔔 Alerts":
    st.title("🔔 Alerting Configuration")

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Channels", "➕ Add Channel", "📊 History", "📈 Statistics"])

    with tab1:
        st.subheader("Configured Channels")

        channels = api_get("/api/alerts/channels")
        if channels and "channels" in channels:
            ch_list = channels["channels"]
            if ch_list:
                for ch in ch_list:
                    icon = "🔔" if ch.get("type") == "slack" else "📟" if ch.get("type") == "pagerduty" else "🌐"
                    st.markdown(f"{icon} **{ch.get('name', 'Unknown')}** ({ch.get('type', 'unknown')})")
            else:
                st.info("No channels configured")
        else:
            st.warning("Could not load channels")

    with tab2:
        st.subheader("Add Alert Channel")

        channel_type = st.selectbox("Channel Type", ["slack", "pagerduty", "webhook"])

        if channel_type == "slack":
            with st.form("add_slack"):
                webhook_url = st.text_input("Webhook URL", placeholder="https://hooks.slack.com/services/...")
                channel_name = st.text_input("Channel (optional)", placeholder="#alerts")
                min_severity = st.selectbox("Min Severity", ["INFO", "WARNING", "ERROR", "CRITICAL"])

                if st.form_submit_button("Add Slack Channel"):
                    result = api_post("/api/alerts/channels/slack", {
                        "webhook_url": webhook_url,
                        "channel": channel_name,
                        "min_severity": min_severity
                    })
                    if result and result.get("status") == "ok":
                        st.success("✅ Slack channel added")
                    else:
                        st.error(f"Failed: {result}")

        elif channel_type == "pagerduty":
            with st.form("add_pagerduty"):
                routing_key = st.text_input("Routing Key")
                min_severity = st.selectbox("Min Severity", ["ERROR", "CRITICAL"])

                if st.form_submit_button("Add PagerDuty Channel"):
                    result = api_post("/api/alerts/channels/pagerduty", {
                        "routing_key": routing_key,
                        "min_severity": min_severity
                    })
                    if result and result.get("status") == "ok":
                        st.success("✅ PagerDuty channel added")
                    else:
                        st.error(f"Failed: {result}")

        else:  # webhook
            with st.form("add_webhook"):
                url = st.text_input("Webhook URL")
                min_severity = st.selectbox("Min Severity", ["INFO", "WARNING", "ERROR", "CRITICAL"])

                if st.form_submit_button("Add Webhook Channel"):
                    result = api_post("/api/alerts/channels/webhook", {
                        "url": url,
                        "min_severity": min_severity
                    })
                    if result and result.get("status") == "ok":
                        st.success("✅ Webhook channel added")
                    else:
                        st.error(f"Failed: {result}")

    with tab3:
        st.subheader("Alert History")

        limit = st.slider("Limit", 10, 200, 50)
        history = api_get(f"/api/alerts/history?limit={limit}")

        if history and "alerts" in history:
            alerts = history["alerts"]
            if alerts:
                df = pd.DataFrame(alerts)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No alerts in history")
        else:
            st.warning("Could not load history")

    with tab4:
        st.subheader("Alert Statistics")

        days = st.selectbox("Period", [1, 7, 30], index=1)
        stats = api_get(f"/api/alerts/statistics?days={days}")

        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Alerts", stats.get("total_alerts", 0))
            with col2:
                st.json(stats.get("by_severity", {}))


# ============== Audit Page ==============

elif page == "📋 Audit":
    st.title("📋 Audit Trail")

    tab1, tab2, tab3 = st.tabs(["📋 Logs", "📊 Statistics", "💾 Export"])

    with tab1:
        st.subheader("Audit Logs")

        col1, col2, col3 = st.columns(3)
        with col1:
            filter_agent = st.text_input("Filter by Agent ID")
        with col2:
            filter_status = st.selectbox("Filter by Status", ["", "success", "error", "denied"])
        with col3:
            limit = st.number_input("Limit", value=100, min_value=10, max_value=1000)

        # Build query
        query = f"/api/audit/logs?limit={limit}"
        if filter_agent:
            query += f"&agent_id={filter_agent}"
        if filter_status:
            query += f"&status={filter_status}"

        logs = api_get(query)
        if logs and "logs" in logs:
            log_list = logs["logs"]
            if log_list:
                df = pd.DataFrame(log_list)
                st.dataframe(df, use_container_width=True, height=400)
                st.caption(f"Total: {logs.get('total', len(log_list))} | Backend: {logs.get('backend', 'unknown')}")
            else:
                st.info("No logs found")
        else:
            st.warning("Could not load logs")

    with tab2:
        st.subheader("Audit Statistics")

        days = st.selectbox("Period (days)", [1, 7, 30, 90], index=1)
        stats = api_get(f"/api/audit/statistics?days={days}")

        if stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Actions", stats.get("total_actions", 0))
            with col2:
                st.metric("Period", f"{stats.get('period_days', days)} days")
            with col3:
                st.metric("Backend", stats.get("backend", "unknown"))

            st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**By Action Type:**")
                by_type = stats.get("by_action_type", {})
                if by_type:
                    df = pd.DataFrame([{"Type": k, "Count": v} for k, v in by_type.items()])
                    st.bar_chart(df.set_index("Type"))

            with col2:
                st.markdown("**By Status:**")
                by_status = stats.get("by_status", {})
                if by_status:
                    df = pd.DataFrame([{"Status": k, "Count": v} for k, v in by_status.items()])
                    st.bar_chart(df.set_index("Status"))

    with tab3:
        st.subheader("Export Logs")

        with st.form("export_logs"):
            output_path = st.text_input("Output Path", value="logs/audit_export.jsonl")
            export_format = st.selectbox("Format", ["jsonl", "json"])

            if st.form_submit_button("📥 Export"):
                result = api_post("/api/audit/export", {
                    "output_path": output_path,
                    "format": export_format
                })
                if result and result.get("status") == "ok":
                    st.success(f"✅ Exported {result.get('count', 0)} logs to {output_path}")
                else:
                    st.error(f"Export failed: {result}")


# ============== Cache & Rate Limits Page ==============

elif page == "⚡ Cache & Rate Limits":
    st.title("⚡ Cache & Rate Limits")

    tab1, tab2 = st.tabs(["🗄️ Cache", "⏱️ Rate Limits"])

    with tab1:
        st.subheader("Validation Cache")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Statistics")
            stats = api_get("/api/cache/stats")
            if stats and "cache" in stats:
                c = stats["cache"]
                metrics = {
                    "Hits": c.get("hits", 0),
                    "Misses": c.get("misses", 0),
                    "Hit Rate": f"{c.get('hit_rate', 0):.2f}%",
                    "Size": c.get("size", 0),
                    "Evictions": c.get("evictions", 0),
                    "Expired": c.get("expired", 0)
                }
                for k, v in metrics.items():
                    st.metric(k, v)

        with col2:
            st.markdown("### Configuration")
            config = api_get("/api/cache/config")
            if config:
                st.json(config)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Invalidate All Cache"):
                result = api_post("/api/cache/invalidate", {})
                if result and result.get("status") == "ok":
                    st.success("✅ Cache invalidated")
                else:
                    st.error("Failed to invalidate cache")

        with col2:
            if st.button("🧹 Cleanup Expired"):
                result = api_post("/api/cache/cleanup", {})
                if result and result.get("status") == "ok":
                    st.success(f"✅ Cleaned up {result.get('removed', 0)} entries")
                else:
                    st.error("Cleanup failed")

    with tab2:
        st.subheader("Rate Limits")

        # Default limits
        st.markdown("### Default Limits")
        defaults = api_get("/api/rate-limits/default")
        if defaults:
            st.json(defaults)

        st.markdown("---")

        # Per-agent limits
        st.markdown("### Per-Agent Limits")
        all_limits = api_get("/api/rate-limits")
        if all_limits and "rate_limits" in all_limits:
            st.json(all_limits["rate_limits"])

        st.markdown("---")

        # Update limits
        st.markdown("### Update Agent Limits")
        agents = api_get("/api/agents")
        if agents and agents.get("agents"):
            agent_ids = [a.get("agent_id") for a in agents["agents"]]
            selected = st.selectbox("Select Agent", agent_ids)

            col1, col2, col3 = st.columns(3)
            with col1:
                new_qpm = st.number_input("Queries/Minute", value=60, min_value=1)
            with col2:
                new_qph = st.number_input("Queries/Hour", value=1000, min_value=1)
            with col3:
                new_qpd = st.number_input("Queries/Day", value=10000, min_value=1)

            if st.button("💾 Update Limits"):
                result = api_put(f"/api/rate-limits/{selected}", {
                    "queries_per_minute": new_qpm,
                    "queries_per_hour": new_qph,
                    "queries_per_day": new_qpd
                })
                if result:
                    st.success("✅ Limits updated")
                else:
                    st.error("Failed to update limits")


# ============== Settings Page ==============

elif page == "🔧 Settings":
    st.title("🔧 System Settings")

    tab1, tab2, tab3 = st.tabs(["⚙️ General", "🔐 JWT", "📝 Audit Config"])

    with tab1:
        st.subheader("General Settings")

        st.markdown("### API Information")
        st.code(f"API URL: {API_URL}", language="text")

        health = api_get("/health")
        if health:
            st.json(health)

    with tab2:
        st.subheader("JWT Configuration")

        jwt_config = api_get("/api/auth/config")
        if jwt_config and "config" in jwt_config:
            config = jwt_config["config"]

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Algorithm", config.get("algorithm", "N/A"))
                st.metric("Access Token Expire", f"{config.get('access_token_expire_minutes', 30)} min")
            with col2:
                st.metric("Refresh Token Expire", f"{config.get('refresh_token_expire_days', 7)} days")
                st.metric("Issuer", config.get("issuer", "N/A"))

    with tab3:
        st.subheader("Audit Logger Configuration")

        audit_config = api_get("/api/audit/config")
        if audit_config:
            st.json(audit_config)

        st.markdown("---")

        st.markdown("### Update Configuration")
        with st.form("update_audit_config"):
            backend = st.selectbox("Backend", ["memory", "file", "sqlite"])
            log_dir = st.text_input("Log Directory", value="logs/audit")
            max_logs = st.number_input("Max Logs (memory)", value=10000, min_value=100)

            if st.form_submit_button("💾 Update Config"):
                result = api_post("/api/audit/config", {
                    "backend": backend,
                    "log_dir": log_dir,
                    "max_logs": max_logs
                })
                if result and result.get("status") == "ok":
                    st.success("✅ Configuration updated")
                else:
                    st.error(f"Failed: {result}")


# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Universal Agent Connector**")
st.sidebar.markdown("Admin Dashboard v1.0")
