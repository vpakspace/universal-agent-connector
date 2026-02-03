"""
Universal Agent Connector - Streamlit UI
Простой интерфейс для работы с OntoGuard и базой данных
"""

import os
import streamlit as st
import requests
from typing import Optional, Dict, Any, List
import pandas as pd
import threading
import queue
import time

# WebSocket client (optional)
try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False

# Конфигурация
API_BASE_URL = "http://localhost:5000"

# Конфигурации доменов
DOMAIN_CONFIGS = {
    "Hospital (Госпиталь)": {
        "ontology": "ontologies/hospital.owl",
        "database": {
            "type": "postgresql",
            "host": "localhost",
            "port": 5433,
            "database": "hospital_db",
            "user": "uac_user",
            "password": "uac_password"
        },
        "roles": ["Admin", "Doctor", "Nurse", "LabTech", "Receptionist", "Patient", "InsuranceAgent"],
        "tables": ["patients", "medical_records", "lab_results", "appointments", "billing", "staff"],
        "entity_types": ["PatientRecord", "MedicalRecord", "LabResult", "Prescription", "Billing", "Appointment", "Staff"],
        "permissions_matrix": {
            "Роль": ["Admin", "Doctor", "Nurse", "LabTech", "Receptionist"],
            "PatientRecord": ["CRUD", "R", "R", "-", "CR"],
            "MedicalRecord": ["CRUD", "RU", "-", "-", "-"],
            "LabResult": ["CRUD", "R", "-", "RU", "-"],
            "Appointment": ["CRUD", "R", "R", "-", "CR"],
            "Billing": ["CRUD", "-", "-", "-", "-"],
            "Staff": ["CRUD", "-", "-", "-", "-"],
        },
        "nl_examples": [
            "Покажи всех пациентов",
            "Сколько записей в medical_records?",
            "Покажи результаты анализов для пациента John Doe",
            "Покажи все назначенные приёмы",
            "Какие сотрудники работают в больнице?"
        ],
        "sql_examples": [
            "SELECT * FROM patients",
            "SELECT * FROM staff WHERE role = 'Doctor'",
            "SELECT p.name, m.diagnosis FROM patients p JOIN medical_records m ON p.id = m.patient_id",
            "DELETE FROM patients WHERE id = 999"
        ]
    },
    "Finance (Финансы)": {
        "ontology": "ontologies/finance.owl",
        "database": {
            "type": "postgresql",
            "host": "localhost",
            "port": 5433,
            "database": "finance_db",
            "user": "uac_user",
            "password": "uac_password"
        },
        "roles": ["Admin", "Manager", "Teller", "Analyst", "Auditor", "ComplianceOfficer",
                   "IndividualCustomer", "CorporateCustomer"],
        "tables": ["accounts", "transactions", "loans", "cards", "customer_profiles", "reports", "audit_log"],
        "entity_types": ["Account", "Transaction", "Loan", "Card", "CustomerProfile", "Report", "AuditLog"],
        "permissions_matrix": {
            "Роль": ["Admin", "Manager", "Teller", "Analyst", "Auditor", "ComplianceOfficer"],
            "Account": ["CRUD", "CRUD", "RU", "R", "R", "R"],
            "Transaction": ["CRUD", "RU", "CR", "R", "R", "R"],
            "Loan": ["CRUD", "CRUD", "R", "R", "R", "-"],
            "Card": ["CRUD", "CRU", "RU", "-", "R", "-"],
            "CustomerProfile": ["CRUD", "RU", "R", "R", "R", "R"],
            "Report": ["CRUD", "CR", "-", "CR", "R", "R"],
            "AuditLog": ["CRUD", "-", "-", "-", "R", "R"],
        },
        "nl_examples": [
            "Покажи все счета",
            "Сколько транзакций за последний месяц?",
            "Покажи все активные кредиты",
            "Какие карты выпущены?",
            "Покажи профили клиентов"
        ],
        "sql_examples": [
            "SELECT * FROM accounts",
            "SELECT * FROM transactions WHERE amount > 1000",
            "SELECT a.id, a.balance, c.name FROM accounts a JOIN customer_profiles c ON a.customer_id = c.id",
            "DELETE FROM transactions WHERE id = 999"
        ]
    },
}

DEFAULT_CONFIG = DOMAIN_CONFIGS["Hospital (Госпиталь)"]


# =============================================================================
# WebSocket Client Manager
# =============================================================================

class WebSocketManager:
    """Manager for WebSocket connection to OntoGuard server."""

    def __init__(self, server_url: str = "http://localhost:5000"):
        self.server_url = server_url
        self.sio = None
        self.connected = False
        self.results_queue = queue.Queue()
        self.last_result = None
        self.session_id = None

    def connect(self) -> bool:
        """Establish WebSocket connection."""
        if not SOCKETIO_AVAILABLE:
            return False

        if self.connected and self.sio:
            return True

        try:
            self.sio = socketio.Client()

            @self.sio.on('connected')
            def on_connected(data):
                self.connected = True
                self.session_id = data.get('session_id')
                self.results_queue.put({'event': 'connected', 'data': data})

            @self.sio.on('validation_result')
            def on_validation_result(data):
                self.last_result = data
                self.results_queue.put({'event': 'validation_result', 'data': data})

            @self.sio.on('permission_result')
            def on_permission_result(data):
                self.last_result = data
                self.results_queue.put({'event': 'permission_result', 'data': data})

            @self.sio.on('allowed_actions_result')
            def on_allowed_actions_result(data):
                self.last_result = data
                self.results_queue.put({'event': 'allowed_actions_result', 'data': data})

            @self.sio.on('batch_result')
            def on_batch_result(data):
                self.last_result = data
                self.results_queue.put({'event': 'batch_result', 'data': data})

            @self.sio.on('error')
            def on_error(data):
                self.last_result = {'error': data}
                self.results_queue.put({'event': 'error', 'data': data})

            @self.sio.on('disconnect')
            def on_disconnect():
                self.connected = False
                self.results_queue.put({'event': 'disconnected', 'data': {}})

            self.sio.connect(self.server_url)
            return True

        except Exception as e:
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from server."""
        if self.sio and self.connected:
            try:
                self.sio.disconnect()
            except:
                pass
        self.connected = False
        self.sio = None

    def validate_action(self, action: str, entity_type: str = None, table: str = None,
                        domain: str = None, role: str = None, request_id: str = None) -> Optional[Dict]:
        """Validate action via WebSocket."""
        if not self.connected:
            return None

        payload = {'action': action}
        if entity_type:
            payload['entity_type'] = entity_type
        if table:
            payload['table'] = table
        if domain:
            payload['domain'] = domain
        if role:
            payload['context'] = {'role': role, 'domain': domain}
        if request_id:
            payload['request_id'] = request_id

        self.sio.emit('validate_action', payload)
        return self._wait_for_result(timeout=5.0)

    def check_permissions(self, role: str, action: str, entity_type: str = None,
                         table: str = None, domain: str = None) -> Optional[Dict]:
        """Check permissions via WebSocket."""
        if not self.connected:
            return None

        payload = {'role': role, 'action': action}
        if entity_type:
            payload['entity_type'] = entity_type
        if table:
            payload['table'] = table
        if domain:
            payload['domain'] = domain

        self.sio.emit('check_permissions', payload)
        return self._wait_for_result(timeout=5.0)

    def get_allowed_actions(self, role: str, entity_type: str = None,
                           table: str = None, domain: str = None) -> Optional[Dict]:
        """Get allowed actions via WebSocket."""
        if not self.connected:
            return None

        payload = {'role': role}
        if entity_type:
            payload['entity_type'] = entity_type
        if table:
            payload['table'] = table
        if domain:
            payload['domain'] = domain

        self.sio.emit('get_allowed_actions', payload)
        return self._wait_for_result(timeout=5.0)

    def validate_batch(self, validations: List[Dict], domain: str = None) -> Optional[Dict]:
        """Validate batch of actions via WebSocket."""
        if not self.connected:
            return None

        payload = {'validations': validations}
        if domain:
            payload['domain'] = domain

        self.sio.emit('validate_batch', payload)
        return self._wait_for_result(timeout=10.0)

    def _wait_for_result(self, timeout: float = 5.0) -> Optional[Dict]:
        """Wait for result from queue."""
        try:
            result = self.results_queue.get(timeout=timeout)
            if result['event'] == 'error':
                return {'error': result['data']}
            return result['data']
        except queue.Empty:
            return {'error': 'Timeout waiting for response'}


def get_ws_manager() -> WebSocketManager:
    """Get or create WebSocket manager in session state."""
    if 'ws_manager' not in st.session_state:
        st.session_state.ws_manager = WebSocketManager(API_BASE_URL)
    return st.session_state.ws_manager


# =============================================================================
# Session State & API Functions
# =============================================================================

def init_session_state():
    """Инициализация session state"""
    if "agent_registered" not in st.session_state:
        st.session_state.agent_registered = False
    if "agent_id" not in st.session_state:
        st.session_state.agent_id = None
    if "api_key" not in st.session_state:
        st.session_state.api_key = None
    if "query_history" not in st.session_state:
        st.session_state.query_history = []


def check_api_health() -> bool:
    """Проверка доступности API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_ontoguard_status() -> Dict[str, Any]:
    """Получение статуса OntoGuard"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/ontoguard/status", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"enabled": False, "active": False}


def reload_ontology(ontology_path: str) -> bool:
    """Перезагрузка онтологии на сервере"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/ontoguard/reload",
            json={"ontology_path": ontology_path},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False


def register_agent(agent_id: str, role: str, db_config: Dict) -> Optional[Dict]:
    """Регистрация агента"""
    payload = {
        "agent_id": agent_id,
        "agent_info": {
            "name": f"Streamlit UI Agent ({role})",
            "role": role
        },
        "agent_credentials": {
            "api_key": f"streamlit-{agent_id}-key",
            "api_secret": f"streamlit-{agent_id}-secret"
        },
        "database": db_config
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/agents/register",
            json=payload,
            timeout=10
        )
        if response.status_code in [200, 201]:
            data = response.json()
            # Сервер возвращает сгенерированный api_key
            return data
        elif response.status_code == 400:
            # Агент уже существует — удаляем и перерегистрируем
            requests.delete(f"{API_BASE_URL}/api/agents/{agent_id}", timeout=5)
            retry = requests.post(
                f"{API_BASE_URL}/api/agents/register",
                json=payload,
                timeout=10
            )
            if retry.status_code in [200, 201]:
                return retry.json()
            return {"agent_id": agent_id, "already_exists": True}
        else:
            st.error(f"Ошибка сервера: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Ошибка регистрации: {e}")
    return None


def add_resource_permissions(agent_id: str, tables: list = None) -> bool:
    """Добавление прав доступа к таблицам"""
    if tables is None:
        tables = ["patients", "medical_records", "lab_results", "appointments", "billing", "staff"]
    success = True
    for table in tables:
        try:
            response = requests.put(
                f"{API_BASE_URL}/api/agents/{agent_id}/permissions/resources",
                json={
                    "resource_id": table,
                    "resource_type": "table",
                    "permissions": ["read", "write", "delete"]
                },
                timeout=5
            )
            if response.status_code not in [200, 201]:
                success = False
        except Exception:
            success = False
    return success


def execute_sql_query(agent_id: str, api_key: str, role: str, query: str) -> Dict:
    """Выполнение SQL запроса"""
    headers = {
        "X-API-Key": api_key,
        "X-User-Role": role,
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "as_dict": True
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/agents/{agent_id}/query",
            json=payload,
            headers=headers,
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def execute_natural_query(agent_id: str, api_key: str, role: str, question: str) -> Dict:
    """Выполнение Natural Language запроса"""
    headers = {
        "X-API-Key": api_key,
        "X-User-Role": role,
        "Content-Type": "application/json"
    }

    payload = {
        "query": question,
        "as_dict": True
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/agents/{agent_id}/query/natural",
            json=payload,
            headers=headers,
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def check_live_drift(agent_id: str, api_key: str, entities: list = None) -> dict:
    """Проверка schema drift через live DB connection"""
    payload = {"agent_id": agent_id}
    if entities:
        payload["entities"] = entities
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/schema/drift-check/live",
            json=payload,
            headers={"X-API-Key": api_key},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_schema_bindings() -> dict:
    """Получение списка schema bindings"""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/schema/bindings", timeout=5)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def call_validate_action(role: str, action: str, entity_type: str) -> Dict:
    """Валидация действия через OntoGuard"""
    payload = {
        "action": action,
        "entity_type": entity_type,
        "context": {"role": role}
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/ontoguard/validate",
            json=payload,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def main():
    st.set_page_config(
        page_title="Universal Agent Connector",
        page_icon="🔐",
        layout="wide"
    )

    init_session_state()

    # Header
    st.title("🔐 Universal Agent Connector")
    st.markdown("**AI Agent Infrastructure с OntoGuard Semantic Validation**")

    # Sidebar - Настройки
    with st.sidebar:
        st.header("⚙️ Настройки")

        # Статус API
        api_healthy = check_api_health()
        if api_healthy:
            st.success("✅ API доступен")
        else:
            st.error("❌ API недоступен")
            st.info("Запустите: `python main_simple.py`")
            return

        # Статус OntoGuard
        ontoguard_status = get_ontoguard_status()
        if ontoguard_status.get("active"):
            st.success("✅ OntoGuard активен")
        else:
            st.warning("⚠️ OntoGuard в pass-through режиме")

        st.divider()

        # Выбор домена
        st.subheader("🌐 Домен")
        domain_names = list(DOMAIN_CONFIGS.keys())
        selected_domain = st.selectbox(
            "Выберите домен",
            domain_names,
            index=0,
            help="Домен определяет онтологию, БД и доступные роли"
        )
        domain_config = DOMAIN_CONFIGS[selected_domain]
        st.caption(f"Онтология: {domain_config['ontology'].split('/')[-1]}")

        st.divider()

        # База данных (автозаполнение из домена)
        st.subheader("🗄️ База данных")
        db_defaults = domain_config["database"]
        db_type = st.selectbox("Тип БД", ["PostgreSQL", "SQLite"], index=0)

        if db_type == "PostgreSQL":
            col1, col2 = st.columns(2)
            with col1:
                db_host = st.text_input("Host", value=db_defaults.get("host", "localhost"))
                db_port = st.number_input("Port", value=db_defaults.get("port", 5433), min_value=1, max_value=65535)
            with col2:
                db_name = st.text_input("Database", value=db_defaults.get("database", "hospital_db"))
                db_user = st.text_input("User", value=db_defaults.get("user", "uac_user"))
            db_password = st.text_input("Password", value=db_defaults.get("password", "uac_password"), type="password")

            db_config = {
                "type": "postgresql",
                "host": db_host,
                "port": int(db_port),
                "database": db_name,
                "user": db_user,
                "password": db_password
            }
        else:
            db_path = st.text_input("SQLite путь", value="data/hospital.db")
            db_config = {
                "type": "sqlite",
                "path": db_path
            }

        st.divider()

        # Роль пользователя (из домена)
        st.subheader("👤 Роль пользователя")
        selected_role = st.selectbox(
            "Выберите роль",
            domain_config["roles"],
            index=0,
            help="Роль определяет доступные действия согласно OWL онтологии"
        )

        st.divider()

        # Регистрация агента (уникальный ID = домен + роль)
        domain_key = selected_domain.split(" ")[0].lower()
        agent_id = f"st-{domain_key}-{selected_role.lower()}"

        if st.button("🔗 Подключиться", type="primary", use_container_width=True):
            with st.spinner("Подключение..."):
                # Reload ontology for selected domain
                ontology_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), domain_config["ontology"])
                if reload_ontology(ontology_path):
                    st.success(f"✅ Онтология загружена: {domain_config['ontology'].split('/')[-1]}")
                else:
                    st.warning("⚠️ Не удалось переключить онтологию")

                result = register_agent(agent_id, selected_role, db_config)
                if result:
                    st.session_state.agent_registered = True
                    st.session_state.agent_id = agent_id
                    if result.get("already_exists"):
                        st.info(f"ℹ️ Агент уже существует: {agent_id}")
                        st.session_state.api_key = result.get("api_key", f"streamlit-{agent_id}-key")
                    else:
                        st.session_state.api_key = result.get("api_key", f"streamlit-{agent_id}-key")
                        st.success(f"✅ Агент зарегистрирован: {agent_id}")
                    # Добавляем права доступа к таблицам
                    tables = domain_config.get("tables")
                    if add_resource_permissions(agent_id, tables):
                        st.success("✅ Права доступа к таблицам добавлены")
                    else:
                        st.warning("⚠️ Не удалось добавить все права доступа")
                else:
                    st.error("Ошибка регистрации агента")

        if st.session_state.agent_registered:
            st.info(f"**Агент:** {st.session_state.agent_id}")

    # Главная область
    if not st.session_state.agent_registered:
        st.info("👈 Настройте подключение в боковой панели и нажмите 'Подключиться'")

        # Показать информацию о системе
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            ### 🏥 Hospital Demo Data

            **Таблицы:**
            - `patients` - 5 записей
            - `medical_records` - 7 записей
            - `lab_results` - 8 записей
            - `appointments` - 7 записей
            - `billing` - 7 записей
            - `staff` - 7 записей
            """)

        with col2:
            st.markdown("""
            ### 👥 Роли и права (OWL)

            | Роль | Права |
            |------|-------|
            | **Admin** | Полный доступ |
            | **Doctor** | read: PatientRecord, MedicalRecord, LabResult |
            | **Nurse** | read: PatientRecord |
            | **LabTech** | read/update: LabResult |
            | **Receptionist** | create: Appointment, PatientRecord |
            """)
        return

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Запросы",
        "🔍 OntoGuard Валидация",
        "📊 История",
        "🔄 Schema Drift",
        "🔌 Real-Time WebSocket"
    ])

    with tab1:
        st.header("💬 Задать вопрос к базе данных")

        # Выбор режима
        query_mode = st.radio(
            "Режим запроса",
            ["Natural Language (AI)", "SQL"],
            horizontal=True
        )

        if query_mode == "Natural Language (AI)":
            st.markdown("Задайте вопрос на естественном языке, AI преобразует его в SQL.")

            # Примеры заполняют через отдельный ключ, text_area читает из него
            if "nl_prefill" not in st.session_state:
                st.session_state.nl_prefill = ""

            question = st.text_area(
                "Ваш вопрос",
                value=st.session_state.nl_prefill,
                placeholder=f"Например: {domain_config.get('nl_examples', ['Покажи все записи'])[0]}",
                height=100
            )

            # Примеры вопросов (из конфига домена)
            st.markdown("**Примеры:**")
            example_questions = domain_config.get("nl_examples", [
                "Покажи все записи",
                "Сколько записей в таблице?",
            ])

            cols = st.columns(3)
            for i, q in enumerate(example_questions):
                with cols[i % 3]:
                    if st.button(q, key=f"example_{i}"):
                        st.session_state.nl_prefill = q
                        st.rerun()

            if st.button("🚀 Выполнить", type="primary") and question:
                with st.spinner("Обработка запроса..."):
                    result = execute_natural_query(
                        st.session_state.agent_id,
                        st.session_state.api_key,
                        selected_role,
                        question
                    )

                    # Сохранить в историю
                    st.session_state.query_history.append({
                        "type": "natural",
                        "question": question,
                        "role": selected_role,
                        "result": result
                    })

                    if result.get("error"):
                        st.error(f"❌ Ошибка: {result.get('error')}")
                        if result.get("reason"):
                            st.warning(f"**Причина:** {result.get('reason')}")
                        if result.get("suggestions"):
                            st.info(f"**Рекомендации:** {', '.join(result.get('suggestions', []))}")
                    else:
                        st.success("✅ Запрос выполнен успешно")

                        if result.get("generated_sql"):
                            with st.expander("📝 Сгенерированный SQL"):
                                st.code(result["generated_sql"], language="sql")

                        # Результаты
                        if result.get("result"):
                            df = pd.DataFrame(result["result"])
                            st.dataframe(df, use_container_width=True)
                            st.caption(f"Найдено записей: {result.get('row_count', len(df))}")
                        else:
                            st.info("Запрос выполнен, но результатов нет")

        else:  # SQL режим
            st.markdown("Введите SQL запрос напрямую.")

            if "sql_prefill" not in st.session_state:
                st.session_state.sql_prefill = ""

            sql_query = st.text_area(
                "SQL запрос",
                value=st.session_state.sql_prefill,
                placeholder="SELECT * FROM patients LIMIT 10",
                height=150
            )

            # Примеры SQL (из конфига домена)
            example_sqls = domain_config.get("sql_examples", [
                "SELECT * FROM " + (domain_config.get("tables", ["data"])[0]),
            ])

            st.markdown("**Примеры:**")
            cols = st.columns(2)
            for i, q in enumerate(example_sqls):
                with cols[i % 2]:
                    if st.button(q[:40] + "...", key=f"sql_example_{i}"):
                        st.session_state.sql_prefill = q
                        st.rerun()

            if st.button("🚀 Выполнить SQL", type="primary") and sql_query:
                with st.spinner("Выполнение запроса..."):
                    result = execute_sql_query(
                        st.session_state.agent_id,
                        st.session_state.api_key,
                        selected_role,
                        sql_query
                    )

                    # Сохранить в историю
                    st.session_state.query_history.append({
                        "type": "sql",
                        "query": sql_query,
                        "role": selected_role,
                        "result": result
                    })

                    if result.get("error"):
                        st.error(f"❌ {result.get('error')}")
                        if result.get("reason"):
                            st.warning(f"**OntoGuard:** {result.get('reason')}")
                        if result.get("constraints"):
                            st.info(f"**Ограничения:** {result.get('constraints')}")
                        if result.get("suggestions"):
                            st.info(f"**Рекомендации:** {', '.join(result.get('suggestions', []))}")
                    else:
                        st.success("✅ Запрос выполнен")

                        if result.get("result"):
                            df = pd.DataFrame(result["result"])
                            st.dataframe(df, use_container_width=True)
                            st.caption(f"Записей: {result.get('row_count', len(df))}")
                        else:
                            st.info(f"Запрос выполнен. Тип: {result.get('query_type', 'unknown')}")

    with tab2:
        st.header("🔍 OntoGuard Валидация")
        st.markdown("Проверьте, разрешено ли действие согласно OWL онтологии.")

        col1, col2 = st.columns(2)

        with col1:
            validate_role = st.selectbox(
                "Роль",
                domain_config["roles"],
                index=domain_config["roles"].index(selected_role),
                key="validate_role"
            )

            validate_action = st.selectbox(
                "Действие",
                ["read", "create", "update", "delete"],
                key="validate_action"
            )

        with col2:
            entity_types = domain_config.get("entity_types", ["PatientRecord", "MedicalRecord", "LabResult"])
            validate_entity = st.selectbox(
                "Тип сущности",
                entity_types,
                key="validate_entity"
            )

        if st.button("🔐 Проверить разрешение"):
            with st.spinner("Валидация..."):
                result = call_validate_action(validate_role, validate_action, validate_entity)

                if result.get("allowed"):
                    st.success(f"✅ **РАЗРЕШЕНО**: {validate_role} может выполнить {validate_action} на {validate_entity}")
                else:
                    st.error(f"❌ **ЗАПРЕЩЕНО**: {validate_role} НЕ может выполнить {validate_action} на {validate_entity}")
                    if result.get("reason"):
                        st.warning(f"**Причина:** {result.get('reason')}")
                    if result.get("constraints"):
                        st.info(f"**Ограничения:** {result.get('constraints')}")

        # Матрица прав
        st.divider()
        domain_label = selected_domain.split(" ")[0]
        st.subheader(f"📋 Матрица прав ({domain_label} Ontology)")

        permissions_matrix = domain_config.get("permissions_matrix")
        if permissions_matrix:
            df_matrix = pd.DataFrame(permissions_matrix)
            st.dataframe(df_matrix, use_container_width=True, hide_index=True)
            st.caption("C=Create, R=Read, U=Update, D=Delete")

    with tab3:
        st.header("📊 История запросов")

        if not st.session_state.query_history:
            st.info("История пуста. Выполните запросы во вкладке 'Запросы'.")
        else:
            for i, item in enumerate(reversed(st.session_state.query_history[-20:])):
                with st.expander(f"#{len(st.session_state.query_history) - i}: {item['type'].upper()} ({item['role']})"):
                    if item["type"] == "natural":
                        st.markdown(f"**Вопрос:** {item['question']}")
                    else:
                        st.code(item.get("query", ""), language="sql")

                    result = item["result"]
                    if result.get("error"):
                        st.error(f"Ошибка: {result['error']}")
                    else:
                        st.success(f"Успешно. Записей: {result.get('row_count', 0)}")

            if st.button("🗑️ Очистить историю"):
                st.session_state.query_history = []
                st.rerun()

    with tab4:
        st.header("🔄 Schema Drift Monitor")
        st.markdown("Проверка соответствия схемы БД ожидаемым bindings через live DB connection.")

        # Фильтр по entity types
        available_entities = domain_config.get("entity_types", [])
        selected_entities = st.multiselect(
            "Фильтр по entity types (пусто = все)",
            available_entities,
            default=[],
            key="drift_entities"
        )

        if st.button("🔍 Проверить drift", type="primary"):
            with st.spinner("Проверка schema drift..."):
                result = check_live_drift(
                    st.session_state.agent_id,
                    st.session_state.api_key,
                    selected_entities if selected_entities else None
                )

                if result.get("error"):
                    st.error(f"Ошибка: {result['error']}")
                else:
                    reports = result.get("reports", [])
                    if not reports:
                        st.success("✅ Drift не обнаружен — схема соответствует bindings.")
                    else:
                        for report in reports:
                            entity = report.get("entity", "Unknown")
                            severity = report.get("max_severity", "INFO")
                            diffs = report.get("diffs", [])

                            if severity == "CRITICAL":
                                st.error(f"🔴 **{entity}** — CRITICAL drift ({len(diffs)} проблем)")
                            elif severity == "WARNING":
                                st.warning(f"🟡 **{entity}** — WARNING drift ({len(diffs)} проблем)")
                            else:
                                st.success(f"🟢 **{entity}** — OK")

                            if diffs:
                                with st.expander(f"Детали drift: {entity}"):
                                    for d in diffs:
                                        st.markdown(f"- **{d.get('type', '')}**: `{d.get('column', '')}` — {d.get('detail', '')}")

                            fixes = report.get("fixes", [])
                            if fixes:
                                with st.expander(f"Рекомендации: {entity}"):
                                    for f in fixes:
                                        st.markdown(f"- **{f.get('action', '')}**: `{f.get('column', '')}` — {f.get('detail', '')}")

        # Текущие bindings
        st.divider()
        with st.expander("📋 Текущие Schema Bindings"):
            bindings = get_schema_bindings()
            if bindings.get("error"):
                st.error(f"Ошибка: {bindings['error']}")
            elif bindings.get("bindings"):
                for b in bindings["bindings"]:
                    st.markdown(f"**{b.get('entity', '')}** → `{b.get('table', '')}` ({b.get('domain', '')})")
                    cols = b.get("columns", {})
                    if cols:
                        st.code(", ".join(f"{k}: {v}" for k, v in cols.items()), language="text")
            else:
                st.info("Bindings не настроены.")

    with tab5:
        st.header("🔌 Real-Time WebSocket Validation")

        if not SOCKETIO_AVAILABLE:
            st.warning("⚠️ WebSocket client не установлен. Установите: `pip install python-socketio[client]`")
            st.code("pip install python-socketio[client]", language="bash")
        else:
            st.markdown("""
            Real-time валидация через WebSocket соединение.
            **Преимущества**: мгновенный ответ, поддержка batch операций, domain switching.
            """)

            # WebSocket connection status
            ws_manager = get_ws_manager()

            col1, col2 = st.columns([1, 3])
            with col1:
                if ws_manager.connected:
                    st.success("🟢 Connected")
                    if st.button("🔌 Отключиться"):
                        ws_manager.disconnect()
                        st.rerun()
                else:
                    st.error("🔴 Disconnected")
                    if st.button("🔌 Подключиться", type="primary"):
                        with st.spinner("Подключение..."):
                            if ws_manager.connect():
                                time.sleep(0.5)  # Wait for connection
                                st.success("✅ Подключено!")
                                st.rerun()
                            else:
                                st.error("❌ Не удалось подключиться")

            with col2:
                if ws_manager.connected and ws_manager.session_id:
                    st.caption(f"Session ID: `{ws_manager.session_id}`")

            st.divider()

            if ws_manager.connected:
                # Domain selection for WebSocket
                domain_key = selected_domain.split(" ")[0].lower()

                # Validation mode selection
                ws_mode = st.radio(
                    "Режим валидации",
                    ["Single Action", "Batch Validation", "Get Allowed Actions"],
                    horizontal=True,
                    key="ws_mode"
                )

                if ws_mode == "Single Action":
                    st.subheader("🔍 Single Action Validation")

                    col1, col2 = st.columns(2)
                    with col1:
                        ws_role = st.selectbox(
                            "Роль",
                            domain_config["roles"],
                            index=0,
                            key="ws_role"
                        )
                        ws_action = st.selectbox(
                            "Действие",
                            ["read", "create", "update", "delete"],
                            key="ws_action"
                        )

                    with col2:
                        # Choice: entity_type or table
                        ws_input_type = st.radio(
                            "Тип ввода",
                            ["Entity Type", "SQL Table"],
                            horizontal=True,
                            key="ws_input_type"
                        )

                        if ws_input_type == "Entity Type":
                            ws_entity = st.selectbox(
                                "Entity Type",
                                domain_config.get("entity_types", []),
                                key="ws_entity"
                            )
                            ws_table = None
                        else:
                            ws_table = st.selectbox(
                                "SQL Table",
                                domain_config.get("tables", []),
                                key="ws_table"
                            )
                            ws_entity = None

                    if st.button("🚀 Validate via WebSocket", type="primary"):
                        with st.spinner("Validating..."):
                            result = ws_manager.validate_action(
                                action=ws_action,
                                entity_type=ws_entity,
                                table=ws_table,
                                domain=domain_key,
                                role=ws_role,
                                request_id=f"st-{int(time.time())}"
                            )

                            if result:
                                if result.get("error"):
                                    st.error(f"❌ Ошибка: {result.get('error')}")
                                elif result.get("allowed"):
                                    st.success(f"✅ **РАЗРЕШЕНО**: {ws_role} может {ws_action} на {result.get('entity_type', ws_entity or ws_table)}")
                                    st.json(result)
                                else:
                                    st.error(f"❌ **ЗАПРЕЩЕНО**: {ws_role} НЕ может {ws_action}")
                                    if result.get("reason"):
                                        st.warning(f"**Причина:** {result.get('reason')}")
                                    st.json(result)
                            else:
                                st.error("❌ Нет ответа от сервера")

                elif ws_mode == "Batch Validation":
                    st.subheader("📦 Batch Validation")
                    st.markdown("Проверка нескольких действий за один запрос.")

                    # Quick batch test
                    if st.button("🧪 Тест: batch validation (3 действия)"):
                        with st.spinner("Batch validation..."):
                            validations = [
                                {"action": "read", "table": domain_config["tables"][0], "context": {"role": domain_config["roles"][0]}},
                                {"action": "delete", "table": domain_config["tables"][0], "context": {"role": domain_config["roles"][-1]}},
                                {"action": "create", "table": domain_config["tables"][0], "context": {"role": domain_config["roles"][1] if len(domain_config["roles"]) > 1 else domain_config["roles"][0]}},
                            ]

                            result = ws_manager.validate_batch(validations, domain=domain_key)

                            if result:
                                if result.get("error"):
                                    st.error(f"❌ Ошибка: {result.get('error')}")
                                else:
                                    st.success(f"✅ Batch completed: {result.get('total', 0)} validations")
                                    st.metric("Allowed", result.get("allowed_count", 0))
                                    st.metric("Denied", result.get("denied_count", 0))

                                    with st.expander("📋 Детали"):
                                        st.json(result)
                            else:
                                st.error("❌ Нет ответа от сервера")

                else:  # Get Allowed Actions
                    st.subheader("📋 Get Allowed Actions")

                    col1, col2 = st.columns(2)
                    with col1:
                        ws_role_actions = st.selectbox(
                            "Роль",
                            domain_config["roles"],
                            index=0,
                            key="ws_role_actions"
                        )
                    with col2:
                        ws_entity_actions = st.selectbox(
                            "Entity Type",
                            domain_config.get("entity_types", []),
                            key="ws_entity_actions"
                        )

                    if st.button("📋 Get Actions via WebSocket", type="primary"):
                        with st.spinner("Getting allowed actions..."):
                            result = ws_manager.get_allowed_actions(
                                role=ws_role_actions,
                                entity_type=ws_entity_actions,
                                domain=domain_key
                            )

                            if result:
                                if result.get("error"):
                                    st.error(f"❌ Ошибка: {result.get('error')}")
                                else:
                                    actions = result.get("allowed_actions", [])
                                    if actions:
                                        st.success(f"✅ {ws_role_actions} может выполнить на {ws_entity_actions}:")
                                        for action in actions:
                                            st.markdown(f"- `{action}`")
                                    else:
                                        st.warning(f"⚠️ {ws_role_actions} не имеет разрешённых действий на {ws_entity_actions}")
                                    st.json(result)
                            else:
                                st.error("❌ Нет ответа от сервера")

            else:
                st.info("👆 Нажмите 'Подключиться' для установки WebSocket соединения")


if __name__ == "__main__":
    main()
