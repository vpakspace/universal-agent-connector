# Universal Agent Connector - Project Memory

AI Agent Infrastructure with Semantic Validation (OntoGuard Integration)

**Создан**: 2026-01-28
**GitHub**: https://github.com/vpakspace/universal-agent-connector

---

## Обзор проекта

Universal Agent Connector - MCP инфраструктура для AI-агентов с интегрированной семантической валидацией на основе OWL онтологий (OntoGuard).

### Ключевые возможности

- **Agent Registry** - регистрация и управление AI-агентами
- **Database Connectors** - PostgreSQL, SQLite подключения
- **OntoGuard Integration** - семантическая валидация действий
- **Resource Permissions** - двухуровневая система прав
- **GraphQL API** - альтернативный интерфейс
- **Audit Logging** - логирование всех операций

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
    ...
}
```

---

## Тестирование

### E2E Query Validation Tests (21/21 passed)

**Двухуровневая защита**: OntoGuard (semantic RBAC) + Resource Permissions

#### Round 1 (11/11)

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

#### Round 2 (10/10)

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
# Запуск сервера
cd ~/universal-agent-connector
python main_simple.py

# Проверка статуса
curl http://localhost:5000/api/ontoguard/status

# Регистрация агента
curl -X POST http://localhost:5000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "my-agent", "name": "My Agent", "role": "Doctor"}'

# Выполнение запроса
curl -X POST http://localhost:5000/api/agents/my-agent/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <agent_api_key>" \
  -H "X-User-Role: Doctor" \
  -d '{"query": "SELECT * FROM patients"}'
```

---

## Commits (2026-01-28)

| Commit | Описание |
|--------|----------|
| `1fb9d14` | feat: OntoGuard + Universal Agent Connector Integration (7 фаз) |
| `2950716` | feat: Add OntoGuard validation to query endpoints |
| `03ccff7` | feat: Add SQL table to OWL entity type mapping |

---

## Связанные проекты

- **OntoGuard AI**: `~/ontoguard-ai/` - Semantic Firewall (OWL validator)
- **Hospital OWL**: `ontologies/hospital.owl` - Medical domain ontology

---

## TODO

- [ ] Добавить PostgreSQL для production
- [ ] Natural Language Query с LLM
- [ ] GraphQL mutations для OntoGuard
- [ ] WebSocket для real-time validation
- [ ] Docker Compose setup

---

**Последнее обновление**: 2026-01-28
