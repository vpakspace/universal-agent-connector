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
- **Schema Drift Detection** - обнаружение изменений схемы БД (missing/new columns, type changes, renames)
- **Validation Caching** - LRU кэш с TTL для OntoGuard валидаций (опционально Redis)
- **E2E Testing** - PostgreSQL + OntoGuard тесты

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (Flask)                        │
│  /api/agents/* │ /api/ontoguard/* │ /api/schema/* │ /graphql │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                 Security Layer                               │
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │ Agent Auth      │  │ OntoGuard Adapter               │   │
│  │ (X-API-Key)     │  │ - OWL Ontology Validation       │   │
│  └─────────────────┘  │ - Role-based Access Control     │   │
│  ┌─────────────────┐  │ - Semantic Action Mapping       │   │
│  │ Schema Drift    │  └─────────────────────────────────┘   │
│  │ Detector        │                                        │
│  └─────────────────┘                                        │
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
| **Schema Drift** | Мониторинг drift через live DB connection |
| **Real-Time WebSocket** | WebSocket валидация (single, batch, get actions) |

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

## Prometheus Metrics

Метрики для мониторинга через Prometheus.

### Endpoint

```
GET /metrics
```

### Доступные метрики

| Метрика | Тип | Описание |
|---------|-----|----------|
| `uac_http_requests_total` | Counter | HTTP запросы (method, endpoint, status) |
| `uac_http_request_duration_seconds` | Histogram | Latency HTTP запросов |
| `uac_ontoguard_validations_total` | Counter | OntoGuard валидации (action, entity, result, role) |
| `uac_ontoguard_validation_duration_seconds` | Histogram | Latency валидаций |
| `uac_websocket_connections` | Gauge | Текущие WebSocket соединения |
| `uac_websocket_events_total` | Counter | WebSocket события |
| `uac_schema_drift_checks_total` | Counter | Schema drift проверки (domain, severity) |
| `uac_db_queries_total` | Counter | Database запросы (type, status, agent) |
| `uac_db_query_duration_seconds` | Histogram | Latency DB запросов |
| `uac_agent_operations_total` | Counter | Операции с агентами |
| `uac_agents_registered` | Gauge | Количество зарегистрированных агентов |
| `uac_build_info` | Info | Информация о версии |

### Prometheus scrape config

```yaml
scrape_configs:
  - job_name: 'uac'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
```

### Grafana Dashboard (пример PromQL)

```promql
# Request rate
rate(uac_http_requests_total[5m])

# OntoGuard denied rate
rate(uac_ontoguard_validations_total{result="denied"}[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(uac_http_request_duration_seconds_bucket[5m]))
```

---

## Validation Caching

LRU кэш для OntoGuard валидаций с поддержкой TTL и опциональным Redis backend.

### Компоненты

| Файл | Описание |
|------|----------|
| `app/cache/__init__.py` | Экспорт API кэша |
| `app/cache/validation_cache.py` | ValidationCache, CacheEntry, CacheStats |

### Features

- **LRU eviction**: автоматическое удаление старых записей при переполнении
- **TTL support**: time-to-live для каждой записи (default: 5 минут)
- **Thread-safe**: потокобезопасные операции через Lock
- **Optional Redis**: распределённый кэш для multi-instance deployment
- **Statistics**: hits, misses, hit_rate, evictions, expired
- **Domain-aware**: раздельный кэш для разных доменов/ролей

### REST API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/api/cache/stats` | GET | Статистика кэша (hits, misses, hit_rate) |
| `/api/cache/config` | GET | Конфигурация (max_size, ttl, redis) |
| `/api/cache/invalidate` | POST | Инвалидация (всего или по фильтру) |
| `/api/cache/cleanup` | POST | Очистка expired записей |

### Использование

```python
from ai_agent_connector.app.cache import (
    get_validation_cache,
    cache_validation_result,
    get_cached_validation,
    invalidate_cache,
    get_cache_stats,
)

# Кэширование результата валидации
cache_validation_result(
    action='read',
    entity_type='PatientRecord',
    result={'allowed': True, 'reason': 'Doctor can read'},
    role='Doctor',
    domain='hospital',
)

# Получение из кэша
cached = get_cached_validation('read', 'PatientRecord', role='Doctor', domain='hospital')

# Инвалидация
invalidate_cache()  # Очистить всё
invalidate_cache(domain='hospital')  # Только hospital

# Статистика
stats = get_cache_stats()
print(f"Hit rate: {stats['hit_rate']}%")
```

### Интеграция с OntoGuard Adapter

Кэширование автоматически интегрировано в `OntoGuardAdapter.validate_action()`:
- Первый вызов → валидация через OWL → результат кэшируется
- Повторные вызовы → результат из кэша (hit)
- `use_cache=False` → отключить кэширование для конкретного вызова

### REST API

```bash
# Статистика кэша
curl http://localhost:5000/api/cache/stats

# Конфигурация
curl http://localhost:5000/api/cache/config

# Инвалидация всего кэша
curl -X POST http://localhost:5000/api/cache/invalidate

# Инвалидация по фильтру
curl -X POST http://localhost:5000/api/cache/invalidate \
  -H "Content-Type: application/json" \
  -d '{"domain": "hospital", "role": "Doctor"}'

# Очистка expired
curl -X POST http://localhost:5000/api/cache/cleanup
```

---

## WebSocket Real-Time Validation

WebSocket endpoints для real-time OntoGuard валидации с поддержкой доменов.

### Поддержка доменов

WebSocket поддерживает **multi-domain** валидацию:
- **Table-to-Entity auto-mapping**: `patients` → `PatientRecord`, `accounts` → `Account`
- **Domain-specific role validation**: проверка ролей по домену (hospital/finance)
- **Auto ontology switching**: автоматическое переключение OWL онтологии при смене домена

### Подключение

```javascript
const socket = io('http://localhost:5000');

socket.on('connected', (data) => {
    console.log('Connected:', data.session_id);
});
```

### События (Client → Server)

| Event | Описание | Payload |
|-------|----------|---------|
| `validate_action` | Валидация действия | `{action, entity_type OR table, domain?, context: {role, domain?}, request_id?}` |
| `check_permissions` | Проверка разрешений | `{role, action, entity_type OR table, domain?, request_id?}` |
| `get_allowed_actions` | Список разрешённых действий | `{role, entity_type OR table, domain?, request_id?}` |
| `explain_rule` | Объяснение правила | `{action, entity_type OR table, domain?, context, request_id?}` |
| `validate_batch` | Batch валидация | `{domain?, validations: [{action, entity_type OR table, context}], request_id?}` |
| `subscribe_validation` | Подписка на события агента | `{agent_id}` |
| `unsubscribe_validation` | Отписка от событий | `{agent_id}` |
| `get_status` | Статус OntoGuard | `{request_id?}` |

### События (Server → Client)

| Event | Описание |
|-------|----------|
| `validation_result` | Результат валидации (+ domain, role, entity_type) |
| `permission_result` | Результат проверки разрешений (+ domain) |
| `allowed_actions_result` | Список разрешённых действий (+ domain) |
| `rule_explanation` | Объяснение правила (+ domain, role) |
| `batch_result` | Результаты batch валидации (+ default_domain) |
| `validation_event` | Real-time событие (для подписчиков) |
| `error` | Сообщение об ошибке (INVALID_ROLE, DOMAIN_SWITCH_FAILED) |

### Пример использования

```javascript
// Валидация с table-to-entity mapping
socket.emit('validate_action', {
    action: 'read',
    table: 'patients',  // auto-mapped to PatientRecord
    domain: 'hospital',
    context: { role: 'Doctor' },
    request_id: 'req-001'
});

socket.on('validation_result', (result) => {
    console.log('Allowed:', result.allowed);
    console.log('Entity:', result.entity_type);  // PatientRecord
    console.log('Domain:', result.domain);       // hospital
});

// Batch валидация с разными доменами
socket.emit('validate_batch', {
    domain: 'hospital',  // default domain
    validations: [
        { action: 'read', table: 'patients', context: { role: 'Doctor' } },
        { action: 'read', entity_type: 'Account', context: { role: 'Analyst', domain: 'finance' } }
    ]
});

// Подписка на события агента
socket.emit('subscribe_validation', { agent_id: 'doctor-1' });

socket.on('validation_event', (event) => {
    console.log('Agent event:', event);
});
```

### Ошибки доменной валидации

| Код ошибки | Описание |
|------------|----------|
| `INVALID_ROLE` | Роль не существует в указанном домене |
| `DOMAIN_SWITCH_FAILED` | Не удалось переключить онтологию |
| `INVALID_REQUEST` | Отсутствуют обязательные поля |

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

## Schema Drift Detection

Обнаружение изменений схемы БД между ожидаемыми bindings и actual schema.

### Компоненты

| Файл | Описание |
|------|----------|
| `app/security/schema_drift.py` | SchemaDriftDetector, SchemaBinding, DriftReport, Fix |
| `config/schema_bindings.yaml` | YAML конфигурация bindings (hospital: 6, finance: 5 entities) |
| `policy_engine.py` | ExtendedPolicyEngine с `_check_schema_drift()` |
| `tests/test_schema_drift.py` | 31 unit тест |
| `tests/test_schema_drift_live.py` | 9 unit тестов (live drift via information_schema) |

### REST API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/api/schema/drift-check` | GET | Список bindings (фильтр по entity/domain) |
| `/api/schema/drift-check` | POST | Проверка drift с actual schema |
| `/api/schema/drift-check/live` | POST | Auto-detect drift через live DB (information_schema) |
| `/api/schema/bindings` | GET | Список всех bindings |
| `/api/schema/bindings` | POST | Создать/обновить binding |

### Severity Levels

| Severity | Trigger | Action |
|----------|---------|--------|
| **CRITICAL** | Missing columns | Запрос блокируется |
| **WARNING** | Type changes, renames | Логирование, запрос проходит |
| **INFO** | New columns / no drift | Без действий |

### Features

- **Type normalization**: `varchar(255)` == `text`, `int` == `integer`, `bool` == `boolean`
- **Rename detection**: эвристика на containment + character similarity (>70%)
- **Fix suggestions**: verify_column, update_mapping, add_column
- **Multi-domain**: hospital (6 entities) + finance (5 entities)
- **Policy Engine integration**: CRITICAL drift блокирует запрос в ExtendedPolicyEngine
- **Live DB auto-detect**: `fetch_live_schema()` + `check_live()` через `information_schema.columns`

### Использование

```bash
# Проверить bindings
curl http://localhost:5000/api/schema/bindings

# Проверить drift с actual schema
curl -X POST http://localhost:5000/api/schema/drift-check \
  -H "Content-Type: application/json" \
  -d '{"schemas": {"PatientRecord": {"id": "integer", "first_name": "text"}}}'

# Добавить binding
curl -X POST http://localhost:5000/api/schema/bindings \
  -H "Content-Type: application/json" \
  -d '{"entity": "NewEntity", "table": "new_table", "domain": "hospital", "columns": {"id": "integer"}}'
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

### Unit Tests (212 passed) ✅

```bash
pytest tests/ -v
# 172 passed, 9 skipped in 0.50s
```

| Файл | Тестов | Модуль |
|------|--------|--------|
| `test_sql_parser_unit.py` | 16 | sql_parser (extract_tables, get_query_type, permissions) |
| `test_rate_limiter_unit.py` | 11 | rate_limiter (config, sliding window, reset) |
| `test_retry_policy_unit.py` | 16 | retry_policy (delays, strategies, executor) |
| `test_ontoguard_adapter_unit.py` | 20 | ontoguard_adapter + exceptions (pass-through, mock validator, 6 exception classes) |
| `test_helpers_unit.py` | 10 | helpers (format_response, validate_json, timestamps, json parsing) |
| `test_smoke.py` | 3 | import smoke tests |
| `test_schema_drift.py` | 31 | schema drift (detect, fixes, bindings, type normalization, renames) |
| `test_schema_drift_live.py` | 9 | live drift (fetch_live_schema, check_live, mock connector) |
| `test_graphql_ontoguard.py` | 9 | GraphQL OntoGuard (types, inputs, mutations, queries) — skipped без graphene |
| `test_websocket_ontoguard.py` | 30 | WebSocket (connect, validate, permissions, batch, subscribe, domain support) |
| `test_prometheus_metrics.py` | 23 | Prometheus metrics (tracking, endpoint, normalization) |
| `test_validation_cache.py` | 17 | Validation cache (LRU, TTL, stats, domain isolation) |
| `test_cache_api.py` | 8 | Cache API endpoints (stats, config, invalidate, cleanup) |
| **Итого** | **212** | +9 skipped (optional deps) |

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
├── requirements.txt            # Production dependencies (UTF-8)
├── requirements-dev.txt        # Dev dependencies (-r requirements.txt)
├── requirements_streamlit.txt  # Streamlit dependencies
├── pyproject.toml              # black, isort, pytest, mypy config
├── Dockerfile                  # Python 3.11-slim, non-root user
├── .dockerignore               # venv, .git, .env, tests excluded
├── docker-compose.yml          # PostgreSQL container (port 5433)
├── init_db.sql                 # Test data (hospital)
├── e2e_postgres_tests.py       # E2E test script (15 tests)
├── .github/
│   ├── workflows/ci.yml        # GitHub Actions CI (pytest+lint+bandit)
│   └── dependabot.yml          # Auto dependency updates
├── ai_agent_connector/
│   └── app/
│       ├── api/routes.py       # REST API endpoints
│       ├── security/           # OntoGuard adapter, schema drift, exceptions
│       ├── mcp/tools/          # MCP tools for AI agents
│       ├── utils/nl_to_sql.py  # NL→SQL converter (OpenAI)
│       └── db/connectors.py    # PostgreSQL/MySQL/SQLite connectors
├── ontologies/
│   └── hospital.owl            # Medical domain OWL ontology
├── config/
│   ├── ontoguard.yaml          # OntoGuard configuration
│   ├── hospital_ontoguard.yaml # Hospital-specific config
│   └── schema_bindings.yaml    # Schema drift bindings (hospital+finance)
└── tests/
    ├── test_smoke.py               # Import smoke tests (3)
    ├── test_sql_parser_unit.py     # SQL parser tests (16)
    ├── test_rate_limiter_unit.py   # Rate limiter tests (11)
    ├── test_retry_policy_unit.py   # Retry policy tests (16)
    ├── test_ontoguard_adapter_unit.py # OntoGuard adapter + exceptions (20)
    ├── test_helpers_unit.py        # Helper utilities tests (10)
    ├── test_schema_drift.py        # Schema drift detection tests (31)
    ├── test_schema_drift_live.py   # Live drift detection tests (9)
    └── test_ontoguard_*.py         # Legacy unit tests
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
- [x] ~~Выбор онтологии через UI~~ (done: Hospital/Finance domains, auto-switch ontology)
- [x] ~~Настройка БД через UI~~ (done: hospital_db/finance_db auto-switch)
- [x] ~~Agent re-registration fix~~ (done: re-register instead of 400 error)
- [x] ~~Schema Drift Detection~~ (done: detector, YAML bindings, REST endpoints, 31 tests, policy engine integration)
- [x] ~~GraphQL mutations для OntoGuard~~ (done: 3 mutations, 4 queries, 4 types, 3 inputs)
- [x] ~~CI/CD pipeline~~ (done: GitHub Actions — pytest, black, isort, bandit, dependabot)
- [x] ~~Code audit (Kimi K2)~~ (done: SECRET_KEY, .dockerignore, requirements split, src/ cleanup)
- [x] ~~Unit tests для core modules~~ (done: 125 passed, CI green — lint + test 3.10/3.11/3.12)
- [x] ~~Schema drift: auto-detect from live DB connection~~ (done: fetch_live_schema, check_live, POST /api/schema/drift-check/live, 9 tests)
- [x] ~~Schema drift: Streamlit UI tab for drift monitoring~~ (done: 4th tab with live drift check, severity colors, fix suggestions)
- [x] ~~WebSocket для real-time validation~~ (done: flask-socketio, 8 events, 15 tests)
- [x] ~~Prometheus metrics~~ (done: prometheus-client, 9 metrics, /metrics endpoint, 23 tests)
- [x] ~~WebSocket domain support~~ (done: table-to-entity mapping, role validation, ontology switching, 30 tests)
- [x] ~~WebSocket client в Streamlit UI~~ (done: 5th tab, single/batch/get_actions modes, python-socketio)

---

## Roadmap (Planned Improvements)

### 🔥 Высокий приоритет
| # | Улучшение | Описание | Статус |
|---|-----------|----------|--------|
| 1 | **Caching Layer** | LRU кэш с TTL для OntoGuard валидаций | ✅ done |
| 2 | **Rate Limiting** | Ограничение запросов per agent (защита от abuse) | pending |
| 3 | **OpenAPI/Swagger Docs** | Автогенерация API документации (flask-apispec) | pending |
| 4 | **JWT Authentication** | JWT tokens с expiration вместо API Key | pending |

### ⚡ Средний приоритет
| # | Улучшение | Описание | Статус |
|---|-----------|----------|--------|
| 5 | **Audit Trail** | Логирование операций в отдельную таблицу/файл | planned |
| 6 | **Alerting Integration** | Slack/PagerDuty alerts при CRITICAL events | planned |
| 7 | **Load Testing** | Locust/k6 нагрузочное тестирование | planned |
| 8 | **Kubernetes Deployment** | Helm charts, manifests, HPA | planned |

### 📦 Низкий приоритет
| # | Улучшение | Описание | Статус |
|---|-----------|----------|--------|
| 9 | **Admin Dashboard** | UI для управления agents, ontologies, permissions | backlog |
| 10 | **Multi-tenancy** | Поддержка нескольких организаций | backlog |
| 11 | **Async Query Execution** | Celery для долгих запросов | backlog |
| 12 | **Test Coverage Report** | pytest-cov с 80%+ coverage | backlog |

---

## Commits

| Commit | Дата | Описание |
|--------|------|----------|
| `fb58c2b` | 2026-02-03 | feat: Add Prometheus metrics for monitoring |
| `ac64002` | 2026-02-03 | feat: Add WebSocket support for real-time OntoGuard validation |
| `cea11d3` | 2026-02-03 | feat: Add GraphQL mutations for OntoGuard semantic validation |
| `ba42ed8` | 2026-02-02 | feat: Add Schema Drift Monitor tab to Streamlit UI |
| `3122c45` | 2026-02-02 | feat: Add live schema drift detection via information_schema |
| `aabb756` | 2026-02-02 | feat: Add schema drift detection module (31 tests, REST endpoints) |
| `3747ed0` | 2026-02-01 | fix: Allow agent re-registration and fix Streamlit auth flow |
| `50bb79c` | 2026-01-30 | test: Add unit tests for core modules (94 tests, no external deps) |
| `026ab44` | 2026-01-30 | ci: GitHub Actions CI/CD, dependabot, pyproject.toml |
| `95d871d` | 2026-01-30 | fix: SECRET_KEY, .dockerignore, healthcheck, requirements split |
| `06e6564` | 2026-01-30 | refactor: remove unused experimental src/ (4753 lines) |
| `9ebbea8` | 2026-01-28 | feat: Add Streamlit UI for Natural Language queries |
| `3129e82` | 2026-01-28 | feat: Add PostgreSQL E2E testing with OntoGuard validation |
| `25f509a` | 2026-01-28 | docs: Update project memory with Round 2 test results |
| `03ccff7` | 2026-01-28 | feat: Add SQL table to OWL entity type mapping |
| `2950716` | 2026-01-28 | feat: Add OntoGuard validation to query endpoints |
| `1fb9d14` | 2026-01-28 | feat: OntoGuard + Universal Agent Connector Integration |

---

**Последнее обновление**: 2026-02-03 (WebSocket client в Streamlit UI)
