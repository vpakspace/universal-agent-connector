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
- **Audit Trail** - persistent logging (file/SQLite backends, rotation, export)
- **Alerting Integration** - Slack/PagerDuty/webhook alerts при CRITICAL events
- **Schema Drift Detection** - обнаружение изменений схемы БД (missing/new columns, type changes, renames)
- **Validation Caching** - LRU кэш с TTL для OntoGuard валидаций (опционально Redis)
- **Rate Limiting** - Ограничение запросов per agent (sliding window)
- **OpenAPI/Swagger Docs** - Автогенерация API документации (flasgger)
- **JWT Authentication** - JWT токены с access/refresh и revocation
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

## Rate Limiting

Ограничение запросов per agent с sliding window алгоритмом.

### Features

- **Sliding window**: точный подсчёт запросов за время
- **Multi-window**: лимиты per minute/hour/day
- **Per-agent config**: индивидуальные лимиты для каждого агента
- **Default limits**: 60/min, 1000/hour, 10000/day
- **Usage stats**: текущее использование и remaining
- **Auto-setup**: лимиты устанавливаются при регистрации агента

### REST API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/api/rate-limits` | GET | Список всех лимитов |
| `/api/rate-limits/default` | GET | Default лимиты |
| `/api/rate-limits/<agent_id>` | GET | Лимиты агента + usage |
| `/api/rate-limits/<agent_id>` | PUT | Установить лимиты |
| `/api/rate-limits/<agent_id>` | DELETE | Удалить лимиты |
| `/api/rate-limits/<agent_id>/reset` | POST | Сбросить счётчики |

### Использование

```bash
# Получить лимиты агента
curl http://localhost:5000/api/rate-limits/doctor-1

# Установить custom лимиты
curl -X PUT http://localhost:5000/api/rate-limits/doctor-1 \
  -H "Content-Type: application/json" \
  -d '{"queries_per_minute": 30, "queries_per_hour": 500}'

# Сбросить счётчики
curl -X POST http://localhost:5000/api/rate-limits/doctor-1/reset
```

### Регистрация агента с лимитами

```bash
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "doctor-1",
    "agent_info": {"name": "Dr. Smith"},
    "rate_limits": {
      "queries_per_minute": 30,
      "queries_per_hour": 500,
      "queries_per_day": 5000
    }
  }'
```

### HTTP 429 Response

При превышении лимита:
```json
{
  "error": "Rate limit exceeded",
  "message": "Rate limit exceeded: 60 queries per minute",
  "retry_after": 60
}
```

---

## JWT Authentication

JWT токены с expiration для безопасной аутентификации API.

### Features

- **Access tokens** — короткоживущие (30 мин по умолчанию)
- **Refresh tokens** — долгоживущие (7 дней по умолчанию)
- **Token revocation** — отзыв токенов через in-memory blacklist
- **Role embedding** — роль пользователя включена в токен
- **Dual auth support** — JWT или API Key (совместимость)

### REST API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/api/auth/token` | POST | Получить JWT токены (требует X-API-Key) |
| `/api/auth/refresh` | POST | Обновить access token через refresh token |
| `/api/auth/verify` | POST | Проверить валидность токена |
| `/api/auth/revoke` | POST | Отозвать токен |
| `/api/auth/config` | GET | Получить конфигурацию JWT |

### Использование

```bash
# 1. Получить токены (требует API Key)
curl -X POST http://localhost:5000/api/auth/token \
  -H "X-API-Key: <agent-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"role": "Doctor"}'

# Response:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "Bearer",
#   "expires_in": 1800
# }

# 2. Использовать access token для запросов
curl http://localhost:5000/api/agents/doctor-1/query \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM patients"}'

# 3. Обновить access token
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'

# 4. Проверить токен
curl -X POST http://localhost:5000/api/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "<token>", "type": "access"}'

# 5. Отозвать токен
curl -X POST http://localhost:5000/api/auth/revoke \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"token": "<token_to_revoke>"}'
```

### Конфигурация

Переменные окружения:
- `JWT_SECRET_KEY` — секретный ключ для подписи (auto-generated если не задан)

Программная конфигурация:
```python
from ai_agent_connector.app.security.jwt_auth import init_jwt_manager, JWTConfig

config = JWTConfig(
    secret_key="your-secret-key",
    access_token_expire_minutes=15,  # default: 30
    refresh_token_expire_days=30,     # default: 7
)
init_jwt_manager(config)
```

### Dual Authentication

Endpoints поддерживают оба метода аутентификации:
- `Authorization: Bearer <jwt_token>` — JWT
- `X-API-Key: <api_key>` — API Key

---

## Audit Trail

Persistent logging для отслеживания операций системы.

### Backends

| Backend | Описание | Use case |
|---------|----------|----------|
| `memory` | In-memory buffer (FIFO) | Тестирование, отладка |
| `file` | JSON Lines файлы с ротацией | Production (default) |
| `sqlite` | SQLite БД с индексами | Structured queries |

### Features

- **File rotation**: по размеру (100MB default) и количеству файлов (10 default)
- **Date filtering**: start_date, end_date (ISO format)
- **Export**: JSONL или JSON формат
- **Statistics**: by action_type, by status, by day

### REST API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/api/audit/logs` | GET | Получить логи с фильтрацией |
| `/api/audit/logs/{id}` | GET | Получить лог по ID |
| `/api/audit/statistics` | GET | Статистика (by_action_type, by_status, by_day) |
| `/api/audit/export` | POST | Экспорт логов в файл |
| `/api/audit/config` | GET | Конфигурация logger |
| `/api/audit/config` | POST | Переинициализация logger |

### Использование

```bash
# Получить логи с фильтрацией
curl "http://localhost:5000/api/audit/logs?agent_id=doctor-1&status=success&limit=50"

# Логи за период
curl "http://localhost:5000/api/audit/logs?start_date=2026-02-01&end_date=2026-02-03"

# Статистика за 7 дней
curl "http://localhost:5000/api/audit/statistics?days=7"

# Экспорт логов
curl -X POST http://localhost:5000/api/audit/export \
  -H "Content-Type: application/json" \
  -d '{"output_path": "logs/export.jsonl", "format": "jsonl"}'

# Переключить на SQLite backend
curl -X POST http://localhost:5000/api/audit/config \
  -H "Content-Type: application/json" \
  -d '{"backend": "sqlite", "db_path": "logs/audit.db"}'
```

### Конфигурация

Environment variable:
- `AUDIT_BACKEND` — backend type (`memory`, `file`, `sqlite`), default: `file`

Программная конфигурация:
```python
from ai_agent_connector.app.utils.audit_logger import init_audit_logger

init_audit_logger(
    backend='file',
    log_dir='logs/audit',
    max_file_size_mb=100,
    max_files=10
)
```

---

## Alerting Integration

Интеграция с внешними системами оповещений: Slack, PagerDuty, generic webhooks.

### Каналы оповещений

| Канал | Описание | Min Severity |
|-------|----------|--------------|
| **Slack** | Webhook интеграция | WARNING |
| **PagerDuty** | Events API v2 | ERROR |
| **Webhook** | Generic HTTP POST | WARNING |

### Features

- **Deduplication**: предотвращение дублей (5 мин по умолчанию)
- **Severity filtering**: отправка только >= min_severity
- **Async dispatch**: неблокирующая отправка через threading
- **Alert history**: история отправленных оповещений
- **Statistics**: статистика по severity, type, channel

### REST API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/api/alerts/channels` | GET | Список каналов |
| `/api/alerts/channels/slack` | POST | Добавить Slack |
| `/api/alerts/channels/pagerduty` | POST | Добавить PagerDuty |
| `/api/alerts/channels/webhook` | POST | Добавить webhook |
| `/api/alerts/channels/{name}` | DELETE | Удалить канал |
| `/api/alerts/test` | POST | Тестовое оповещение |
| `/api/alerts/send` | POST | Отправить alert |
| `/api/alerts/history` | GET | История оповещений |
| `/api/alerts/statistics` | GET | Статистика |
| `/api/alerts/config` | GET | Конфигурация |

### Alert Types

| Type | Описание |
|------|----------|
| `QUERY_SLOW` | Медленный запрос |
| `ONTOGUARD_DENIED` | OntoGuard отказ |
| `SCHEMA_DRIFT_CRITICAL` | Критический drift |
| `RATE_LIMIT_EXCEEDED` | Превышение лимита |
| `AGENT_ERROR` | Ошибка агента |
| `CUSTOM` | Пользовательский |

### Использование

```bash
# Добавить Slack канал
curl -X POST http://localhost:5000/api/alerts/channels/slack \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://hooks.slack.com/services/...", "min_severity": "WARNING"}'

# Добавить PagerDuty канал
curl -X POST http://localhost:5000/api/alerts/channels/pagerduty \
  -H "Content-Type: application/json" \
  -d '{"routing_key": "...", "min_severity": "ERROR"}'

# Отправить тестовый alert
curl -X POST http://localhost:5000/api/alerts/test

# Отправить custom alert
curl -X POST http://localhost:5000/api/alerts/send \
  -H "Content-Type: application/json" \
  -d '{"alert_type": "CUSTOM", "title": "Test", "severity": "WARNING", "message": "Test message"}'

# Статистика
curl http://localhost:5000/api/alerts/statistics?days=7
```

### Программная интеграция

```python
from ai_agent_connector.app.utils.alerting import (
    get_notification_manager, init_notification_manager,
    NotificationAlert, AlertType, AlertSeverity,
    SlackChannel, PagerDutyChannel, WebhookChannel,
)

# Инициализация с каналами
init_notification_manager(channels=[
    SlackChannel(webhook_url="https://hooks.slack.com/...", min_severity=AlertSeverity.WARNING),
    PagerDutyChannel(routing_key="...", min_severity=AlertSeverity.ERROR),
])

# Отправка alert
manager = get_notification_manager()
manager.send_alert(NotificationAlert(
    alert_type=AlertType.CUSTOM,
    title="Schema Drift Detected",
    severity=AlertSeverity.CRITICAL,
    message="Missing column 'email' in patients table",
    details={"entity": "PatientRecord", "column": "email"}
))
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
| `app/security/jwt_auth.py` | JWT Authentication (tokens, refresh, revoke) |
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

### Unit Tests (282 passed) ✅

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
| `test_rate_limit_api.py` | 15 | Rate limit API (list, get, set, remove, reset, integration) |
| `test_jwt_auth.py` | 27 | JWT authentication (config, tokens, refresh, revoke, API endpoints) |
| `test_audit_logger.py` | 28 | Audit trail (backends, persistence, export, statistics, API endpoints) |
| `test_alerting.py` | 42 | Alerting (channels, manager, deduplication, history, API endpoints) |
| **Итого** | **324** | +9 skipped (optional deps) |

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
│       ├── security/           # OntoGuard adapter, JWT auth, schema drift, exceptions
│       ├── mcp/tools/          # MCP tools for AI agents
│       ├── utils/nl_to_sql.py  # NL→SQL converter (OpenAI)
│       └── db/connectors.py    # PostgreSQL/MySQL/SQLite connectors
├── ontologies/
│   └── hospital.owl            # Medical domain OWL ontology
├── config/
│   ├── ontoguard.yaml          # OntoGuard configuration
│   ├── hospital_ontoguard.yaml # Hospital-specific config
│   ├── schema_bindings.yaml    # Schema drift bindings (hospital+finance)
│   └── openapi.yaml            # OpenAPI 3.0.3 specification (Swagger)
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
- [x] ~~Validation Caching~~ (done: LRU cache, TTL, Redis optional, 17 tests)
- [x] ~~Rate Limiting~~ (done: sliding window, per-agent config, 15 tests)
- [x] ~~OpenAPI/Swagger documentation~~ (done: flasgger, /apidocs/, openapi.yaml)
- [x] ~~JWT Authentication~~ (done: access/refresh tokens, revocation, dual auth, 27 tests)

---

## Roadmap (Planned Improvements)

### 🔥 Высокий приоритет
| # | Улучшение | Описание | Статус |
|---|-----------|----------|--------|
| 1 | **Caching Layer** | LRU кэш с TTL для OntoGuard валидаций | ✅ done |
| 2 | **Rate Limiting** | Ограничение запросов per agent (sliding window) | ✅ done |
| 3 | **OpenAPI/Swagger Docs** | Автогенерация API документации (flasgger) | ✅ done |
| 4 | **JWT Authentication** | JWT tokens с expiration вместо API Key | ✅ done |

### ⚡ Средний приоритет
| # | Улучшение | Описание | Статус |
|---|-----------|----------|--------|
| 5 | **Audit Trail** | Persistent logging (file/SQLite, rotation, export) | ✅ done |
| 6 | **Alerting Integration** | Slack/PagerDuty alerts при CRITICAL events | ✅ done |
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
| `c70d22c` | 2026-02-03 | feat: Add persistent Audit Trail with file/SQLite backends |
| `4dc86b3` | 2026-02-03 | feat: Add JWT Authentication with access and refresh tokens |
| `d883896` | 2026-02-03 | feat: Add OpenAPI/Swagger documentation with flasgger |
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

**Последнее обновление**: 2026-02-03 (Alerting Integration + Audit Trail + JWT Authentication)
