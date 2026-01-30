"""
Universal Agent Connector - Streamlit UI
Простой интерфейс для работы с OntoGuard и базой данных
"""

import os
import streamlit as st
import requests
from typing import Optional, Dict, Any
import pandas as pd

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
        "tables": ["patients", "medical_records", "lab_results", "appointments", "billing", "staff"]
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
        "tables": ["accounts", "transactions", "loans", "cards", "customer_profiles", "reports", "audit_log"]
    },
}

DEFAULT_CONFIG = DOMAIN_CONFIGS["Hospital (Госпиталь)"]


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
            # Агент уже существует — переиспользуем
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
                        st.session_state.api_key = st.session_state.get("api_key")
                    else:
                        st.session_state.api_key = result.get("api_key")
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
    tab1, tab2, tab3 = st.tabs(["💬 Запросы", "🔍 OntoGuard Валидация", "📊 История"])

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

            question = st.text_area(
                "Ваш вопрос",
                placeholder="Например: Покажи всех пациентов с диабетом",
                height=100
            )

            # Примеры вопросов
            st.markdown("**Примеры:**")
            example_questions = [
                "Покажи всех пациентов",
                "Сколько записей в medical_records?",
                "Покажи результаты анализов для пациента John Doe",
                "Покажи все назначенные приёмы",
                "Какие сотрудники работают в больнице?"
            ]

            cols = st.columns(3)
            for i, q in enumerate(example_questions):
                with cols[i % 3]:
                    if st.button(q, key=f"example_{i}"):
                        question = q

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

            sql_query = st.text_area(
                "SQL запрос",
                placeholder="SELECT * FROM patients LIMIT 10",
                height=150
            )

            # Примеры SQL
            example_sqls = [
                "SELECT * FROM patients",
                "SELECT * FROM staff WHERE role = 'Doctor'",
                "SELECT p.name, m.diagnosis FROM patients p JOIN medical_records m ON p.id = m.patient_id",
                "DELETE FROM patients WHERE id = 999"
            ]

            st.markdown("**Примеры:**")
            cols = st.columns(2)
            for i, q in enumerate(example_sqls):
                with cols[i % 2]:
                    if st.button(q[:40] + "...", key=f"sql_example_{i}"):
                        sql_query = q

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
            entity_types = [
                "PatientRecord", "MedicalRecord", "LabResult", "Prescription",
                "Billing", "Appointment", "Staff", "User", "Order", "Product"
            ]
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
        st.subheader("📋 Матрица прав (Hospital Ontology)")

        permissions_matrix = {
            "Роль": ["Admin", "Doctor", "Nurse", "LabTech", "Receptionist"],
            "PatientRecord": ["CRUD", "R", "R", "-", "CR"],
            "MedicalRecord": ["CRUD", "RU", "-", "-", "-"],
            "LabResult": ["CRUD", "R", "-", "RU", "-"],
            "Appointment": ["CRUD", "R", "R", "-", "CR"],
            "Billing": ["CRUD", "-", "-", "-", "-"],
            "Staff": ["CRUD", "-", "-", "-", "-"],
        }

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


if __name__ == "__main__":
    main()
