# Universal Agent Connector - Project Memory

AI Agent Infrastructure with Semantic Validation (OntoGuard Integration)

**Создан**: 2026-01-28
**GitHub**: https://github.com/vpakspace/universal-agent-connector

---

## Обзор проекта

Universal Agent Connector - MCP инфраструктура для AI-агентов с интегрированной семантической валидацией на основе OWL онтологий (OntoGuard).

### Ключевые возможности

- **Streamlit UI** - веб-интерфейс для Natural Language запросов
- **Natural Language Query** - NL→SQL через OpenAI API (русский/английский)
- **Agent Registry** - регистрация и управление AI-агентами
- **Database Connectors** - PostgreSQL, SQLite подключения
- **OntoGuard Integration** - семантическая валидация действий
- **Resource Permissions** - двухуровневая система прав
- **GraphQL API** - альтернативный интерфейс
- **Audit Logging** - логирование всех операций
- **E2E Testing** - PostgreSQL + OntoGuard тесты

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (Flask)                        │
│  /api/agents/* │ /api/ontoguard/* │ /graphql               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                 Security Layer                               │
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │ Agent Auth      │  │ OntoGuard Adapter               │   │
│  │ (X-API-Key)     │  │ - OWL Ontology Validation       │   │
│  └─────────────────┘  │ - Role-based Access Control     │   │
│                       │ - Semantic Action Mapping       │   │
│                       └─────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│               Permission Layer                               │
│  Resource Permissions (table-level read/write/delete/admin) │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│               Database Layer                                 │
│  PostgreSQL / SQLite Connectors                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Streamlit UI

Веб-интерфейс для работы с системой.

### Запуск

```bash
# Терминал 1: Flask API
export OPENAI_API_KEY="your-key"
python main_simple.py

# Терминал 2: Streamlit
streamlit run streamlit_app.py
```

**URLs:**
- Flask API: http://localhost:5000
- Streamlit UI: http://localhost:8501

### Функционал

| Вкладка | Описание |
|---------|----------|
| **Вопросы (NL)** | Natural Language запросы на русском/английском |
| **SQL запросы** | Прямые SQL запросы к БД |
| **OntoGuard** | Проверка разрешений по OWL онтологии |
| **История** | Лог выполненных запросов |

### Natural Language Query

```
Вопрос: "Покажи всех пациентов"
SQL: SELECT * FROM patients;
Результат: 5 записей
```

**Поддерживаемые языки**: русский, английский

**Требования**: `OPENAI_API_KEY` для NL→SQL конверсии

### Файлы

| Файл | Описание |
|------|----------|
| `streamlit_app.py` | Главное приложение (~500 строк) |
| `run_streamlit.sh` | Скрипт запуска |
| `requirements_streamlit.txt` | Зависимости (streamlit, pandas, requests) |

---

## OntoGuard Integration

### Компоненты

| Файл | Описание |
|------|----------|
| `app/security/ontoguard_adapter.py` | Адаптер для OntoGuard валидации |
| `app/security/exceptions.py` | Custom exceptions |
| `app/mcp/tools/ontoguard_tools.py` | 5 MCP tools для AI агентов |
| `config/ontoguard.yaml` | Конфигурация OntoGuard |
| `ontologies/hospital.owl` | OWL онтология (RBAC правила) |

### REST API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/api/ontoguard/status` | GET | Статус OntoGuard |
| `/api/ontoguard/validate` | POST | Валидация действия |
| `/api/ontoguard/permissions` | POST | Проверка разрешений |
| `/api/ontoguard/allowed-actions` | GET | Список разрешённых действий |
| `/api/ontoguard/explain` | POST | Объяснение правил |

### SQL → OWL Mapping

```python
# SQL operations → semantic actions
action_map = {
    SELECT: 'read',
    INSERT: 'create',
    UPDATE: 'update',
    DELETE: 'delete'
}

# SQL tables → OWL entity types
table_entity_map = {
    'patients': 'PatientRecord',
    'medical_records': 'MedicalRecord',
    'lab_results': 'LabResult',
    'appointments': 'Appointment',
    'billing': 'Billing',
    'staff': 'Staff'
}
```

---

## E2E PostgreSQL Testing

### Конфигурация

```bash
# Запуск PostgreSQL контейнера
docker-compose up -d

# PostgreSQL на порту 5433
# Database: hospital_db
# User: uac_user
```

### Тестовые данные (init_db.sql)

| Таблица | Записей | Описание |
|---------|---------|----------|
| patients | 5 | John Doe, Jane Smith, Bob Wilson, Alice Brown, Charlie Davis |
| medical_records | 7 | Диагнозы, рецепты, осмотры |
| lab_results | 8 | Анализы крови, МРТ, HbA1c |
| appointments | 7 | 5 scheduled, 2 completed |
| billing | 7 | 4 paid, 3 pending |
| staff | 7 | 2 Doctor, 2 Nurse, 1 LabTech, 1 Receptionist, 1 Admin |

### E2E PostgreSQL Tests (15/15 passed) ✅

```bash
python e2e_postgres_tests.py
```

**ALLOWED (9/9)** - реальные SQL запросы в PostgreSQL:

| # | Тест | Роль | Результат |
|---|------|------|-----------|
| E2E-01 | SELECT patients | Doctor | 5 rows |
| E2E-02 | SELECT staff | Admin | 7 rows |
| E2E-03 | SELECT lab_results | LabTech | 8 rows |
| E2E-04 | SELECT appointments | Receptionist | 5 rows |
| E2E-05 | SELECT patients | Nurse | 5 rows |
| E2E-06 | DELETE staff (id=999) | Admin | 0 rows |
| E2E-11 | SELECT with JOIN | Doctor | 2 rows |
| E2E-12 | SELECT billing | Admin | 3 rows |
| E2E-13 | INSERT appointment | Receptionist | 0 rows |

**DENIED (6/6)** - OntoGuard блокирует по OWL правилам:

| # | Тест | Роль | Причина отказа |
|---|------|------|----------------|
| E2E-07 | DELETE patients | Nurse | requires Admin |
| E2E-08 | DELETE medical_records | Receptionist | no delete permission |
| E2E-09 | DELETE lab_results | LabTech | no rule found |
| E2E-10 | UPDATE patients | Doctor | requires Patient/Receptionist/Admin |
| E2E-14 | INSERT patients | Nurse | requires Admin/Receptionist |
| E2E-15 | UPDATE billing | Admin | can only update PatientRecord |

---

## Semantic Validation Tests (21/21 passed)

**Двухуровневая защита**: OntoGuard (semantic RBAC) + Resource Permissions

### Round 1 (11/11)

**ALLOWED (5/5)**:
- ✅ Doctor SELECT patients
- ✅ Admin DELETE patients
- ✅ LabTech SELECT lab_results
- ✅ Receptionist INSERT appointments
- ✅ Nurse SELECT patients

**DENIED by OntoGuard (6/6)**:
- ✅ Nurse DELETE patients
- ✅ Receptionist DELETE medical_records
- ✅ LabTech DELETE lab_results
- ✅ Receptionist UPDATE medical_records
- ✅ Nurse UPDATE patients
- ✅ Doctor UPDATE patients (OWL: only Patient/Receptionist/Admin)

### Round 2 (10/10)

**ALLOWED (3/3)**:
- ✅ Admin INSERT lab_results
- ✅ Doctor SELECT lab_results
- ✅ LabTech UPDATE lab_results

**DENIED by OWL rules (7/7)**:
- ✅ Admin UPDATE billing (OWL: Admin can update only PatientRecord)
- ✅ Nurse INSERT patients (OWL: Nurse has no create permission)
- ✅ Receptionist SELECT billing (OWL: only Patient/Insurance can read Billing)
- ✅ Receptionist DELETE appointments (OWL: no delete permission)
- ✅ Nurse UPDATE medical_records (OWL: no update permission)
- ✅ Admin DELETE appointments (OWL: Admin can delete only Staff/PatientRecord)
- ✅ Doctor DELETE lab_results (OWL: no delete permission)

### Unit Tests

```bash
pytest tests/ -v
# 27 tests (22 passed, 5 skipped)
```

---

## Запуск

```bash
# 1. Запуск PostgreSQL
docker-compose up -d

# 2. Запуск сервера
python main_simple.py

# 3. Проверка статуса
curl http://localhost:5000/api/ontoguard/status

# 4. Регистрация агента с PostgreSQL
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "doctor-1",
    "agent_info": {"name": "Dr. Smith", "role": "Doctor"},
    "agent_credentials": {"api_key": "doc-key", "api_secret": "doc-secret"},
    "database": {
      "type": "postgresql",
      "host": "localhost",
      "port": 5433,
      "database": "hospital_db",
      "user": "uac_user",
      "password": "uac_password"
    }
  }'

# 5. Выполнение запроса
curl -X POST http://localhost:5000/api/agents/doctor-1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <api_key>" \
  -H "X-User-Role: Doctor" \
  -d '{"query": "SELECT * FROM patients"}'

# 6. E2E тесты
python e2e_postgres_tests.py
```

---

## Файлы проекта

```
universal-agent-connector/
├── main_simple.py              # Flask entry point
├── streamlit_app.py            # Streamlit UI (~500 строк)
├── run_streamlit.sh            # Скрипт запуска Streamlit
├── requirements_streamlit.txt  # Streamlit dependencies
├── docker-compose.yml          # PostgreSQL container (port 5433)
├── init_db.sql                 # Test data (hospital)
├── e2e_postgres_tests.py       # E2E test script (15 tests)
├── ai_agent_connector/
│   └── app/
│       ├── api/routes.py       # REST API endpoints
│       ├── security/           # OntoGuard adapter, exceptions
│       ├── mcp/tools/          # MCP tools for AI agents
│       ├── utils/nl_to_sql.py  # NL→SQL converter (OpenAI)
│       └── db/connectors.py    # PostgreSQL/MySQL/SQLite connectors
├── ontologies/
│   └── hospital.owl            # Medical domain OWL ontology
├── config/
│   ├── ontoguard.yaml          # OntoGuard configuration
│   └── hospital_ontoguard.yaml # Hospital-specific config
└── tests/
    └── test_ontoguard_*.py     # Unit tests
```

---

## Связанные проекты

- **OntoGuard AI**: `~/ontoguard-ai/` - Semantic Firewall (OWL validator)
- **Hospital OWL**: `ontologies/hospital.owl` - Medical domain ontology (478 triples)

---

## TODO

- [x] ~~Docker Compose setup~~ (done: port 5433)
- [x] ~~PostgreSQL E2E тесты~~ (done: 15/15 passed)
- [x] ~~Natural Language Query с LLM~~ (done: OpenAI API, русский/английский)
- [x] ~~Streamlit UI~~ (done: NL queries, SQL, OntoGuard validation)
- [ ] Выбор онтологии через UI (сейчас hardcoded hospital.owl)
- [ ] Настройка БД через UI (сейчас hardcoded hospital_db)
- [ ] GraphQL mutations для OntoGuard
- [ ] WebSocket для real-time validation
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Prometheus metrics

---

## Commits

| Commit | Дата | Описание |
|--------|------|----------|
| `9ebbea8` | 2026-01-28 | feat: Add Streamlit UI for Natural Language queries |
| `3129e82` | 2026-01-28 | feat: Add PostgreSQL E2E testing with OntoGuard validation |
| `25f509a` | 2026-01-28 | docs: Update project memory with Round 2 test results |
| `03ccff7` | 2026-01-28 | feat: Add SQL table to OWL entity type mapping |
| `2950716` | 2026-01-28 | feat: Add OntoGuard validation to query endpoints |
| `1fb9d14` | 2026-01-28 | feat: OntoGuard + Universal Agent Connector Integration |

---

**Последнее обновление**: 2026-01-28
