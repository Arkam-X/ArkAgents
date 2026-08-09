# TRACK.md - ArkAgents Change Log

## Project Overview
ArkAgents - Multi-Agent AI Business Manager with hierarchical agent architecture (Manager → Workers)

---

## Session Changes (2026-08-09)

### Backend - Core Architecture

#### `src/core/app.py`
- **Purpose**: Application bootstrap, builds orchestrator with all agents
- **Changes**: Updated imports for enhanced agents, added all 6 workers to registry
- **Functions**: `build_orchestrator(db_path, allow_db_writes, use_llm)` - creates LLMRouter, AgentRegistry, registers all agents, returns Orchestrator

#### `src/core/orchestrator.py`
- **Purpose**: Executes tasks through manager agent
- **Functions**: `run(task)` - sets task running, calls manager.run(), handles errors; `run_async(task)` - alias for run

#### `src/core/agent_registry.py`
- **Purpose**: Stores and manages available agents
- **Functions**: `register(name, agent)`, `get(name)`, `list_agents()`, `describe_agents()`, `get_all()`

#### `src/core/task.py`
- **Purpose**: Task data model with status tracking
- **Classes**: `TaskStatus` (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED), `Task` dataclass
- **Functions**: `set_status()`, `set_result()`, `set_error()`, `add_subtask()`, `to_dict()`, `from_dict()`

---

### Backend - Base Agent

#### `src/agents/base/base_agent.py`
- **Purpose**: Abstract base class for all agents
- **Functions**: `__init__(name, description, tools, llm, max_iterations)`, `log()`, `add_tool()`, `get_tools()`, `call_llm(prompt, task_type)`, `info/warning/error()`, abstract `run(task)`

---

### Backend - Manager Agent

#### `src/agents/manager/manager_agent.py`
- **Purpose**: Plans work, delegates to workers, aggregates results
- **Functions**: `__init__(registry, llm, planner)`, `think(task)` → List[Task], `assign(tasks)` → List[Task], `run(task)` → summary dict

#### `src/workflows/task_planner.py`
- **Purpose**: Creates bounded subtask plans (LLM + rule-based fallback)
- **Functions**: `plan(task)` → List[Task], `_llm_plan(task)`, `_rule_based_agent(description)` → agent_name

#### `src/workflows/workflow_engine.py`
- **Purpose**: Sequential workflow runner
- **Functions**: `run(tasks)` → List[Task], `run_single(task)`

---

### Backend - Worker Agents (ALL ENHANCED)

#### `src/agents/workers/db_agent.py` **✨ ENHANCED**
- **Purpose**: Database operations with smart SQL generation
- **New Functions**: 
  - `_fallback_sql()` - handles count, sum, avg, min, max, group by, recent, top N
  - `export_to_csv(rows, path)`, `export_to_json(rows, path)`
  - `run(task)` - supports `export` metadata (csv/json), param binding
- **Operations**: query, insert, update, delete, schema, export

#### `src/agents/workers/email_agent.py` **✨ ENHANCED**
- **Purpose**: Business emails with templates & attachments
- **Templates**: proposal, follow_up, meeting_request, invoice, welcome
- **New Functions**:
  - `list_templates()` → Dict
  - `render_template(name, variables)` → {subject, body} with safe defaults
  - `generate_email_with_llm(task)` → {subject, body, to}
  - `run(task)` - supports template, variables (flat or nested), LLM, CC/BCC, attachments, dry_run

#### `src/agents/workers/excel_agent.py` **✨ ENHANCED**
- **Purpose**: Spreadsheet read/write/analyze/visualize
- **Actions**: read, write, analyze, pivot, chart, filter, merge
- **New Functions**:
  - `_handle_read/analyze/pivot/chart/filter/merge()`
  - `run(task)` - routes by `action` metadata

#### `src/agents/workers/lead_agent.py` **✨ ENHANCED**
- **Purpose**: Lead extraction, enrichment, validation, scoring
- **Pipeline**: extract → enrich → validate → score → deduplicate → export
- **New Functions**:
  - `_handle_extract/enrich/validate/score/deduplicate/export()`
  - `run(task)` - routes by `action` metadata

#### `src/agents/workers/report_agent.py` **✨ ENHANCED**
- **Purpose**: Comprehensive reporting with exports
- **Actions**: summarize, detailed, export, performance, agent_performance, trend
- **New Functions**: `run(task)` - routes by `action` metadata

#### `src/agents/workers/voice_agent.py` **✨ ENHANCED**
- **Purpose**: Voice calls via Twilio/Vapi
- **Actions**: plan, call, schedule, list, get_recording, transcribe
- **New Functions**: `run(task)` - routes by `action` metadata

---

### Backend - Tools (ALL ENHANCED)

#### `src/tools/database/db_tools.py`
- **Purpose**: SQLite tool with schema discovery & write protection
- **Functions**: `connect()`, `get_tables()`, `get_columns()`, `describe_schema()`, `execute()`, `query()`, `insert()`, `update()`, `delete()`, `seed_demo_data()`

#### `src/tools/email/email_tools.py` **✨ ENHANCED**
- **Purpose**: SMTP email with drafts, attachments, CC/BCC
- **Functions**: `draft(to, subject, body, cc, bcc, attachments)`, `send(to, subject, body, from, dry_run, cc, bcc, attachments)`

#### `src/tools/excel/excel_tools.py` **✨ ENHANCED**
- **Purpose**: Pandas-backed Excel/CSV operations
- **New Functions**: `analyze()`, `pivot_table()`, `create_chart()`, `filter_rows()`, `_basic_analyze/filter()`

#### `src/tools/lead/lead_tools.py` **✨ ENHANCED**
- **Purpose**: Lead processing pipeline
- **New Functions**: `enrich_leads()`, `validate_leads()`, `score_leads()`, `deduplicate_leads()`, `export_leads()`, helper: `_classify_email_provider()`, `_detect_country_code()`, `_format_phone()`, `_get_tier()`

#### `src/tools/reporting/report_tools.py` **✨ ENHANCED**
- **Purpose**: Report generation & export
- **New Functions**: `detailed_report()`, `performance_report()`, `agent_performance_report()`, `trend_report()`, `export_report(json/csv/markdown)`, `_to_markdown()`

#### `src/tools/voice/voice_tools.py` **✨ ENHANCED**
- **Purpose**: Twilio & Vapi voice integration
- **New Functions**: `make_call()`, `_make_twilio_call()`, `_make_vapi_call()`, `schedule_call()`, `list_calls()`, `get_recording()`, `transcribe_call()`, `_check_twilio()`, `_check_vapi()`

---

### Backend - LLM Layer

#### `src/llm/router.py`
- **Purpose**: Routes prompts across providers with fallback
- **Functions**: `generate(prompt, task_type)`, `generate_json(prompt, task_type, default)`, `status()`, `_route(task_type)` - cheap→gemini, reasoning→openai

#### `src/llm/openai_client.py`, `gemini_client.py`, `openrouter_client.py`
- **Purpose**: Provider-specific clients
- **Functions**: `generate(prompt)` - returns text response

---

### Backend - Memory

#### `src/memory/short_term.py`
- **Purpose**: In-memory rolling context (deque, max 20)
- **Functions**: `add(item)`, `list()`, `clear()`

#### `src/memory/long_term.py`
- **Purpose**: JSONL-backed persistent memory
- **Functions**: `add(item)`, `list(limit=100)`

---

### Backend - Config

#### `src/config/settings.py` **✨ UPDATED**
- **Purpose**: Environment variable loading
- **New Vars**: `VOICE_PROVIDER`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `VAPI_API_KEY`, `VAPI_ASSISTANT_ID`

---

### Frontend - Web UI **✨ MAJOR ENHANCEMENT**

#### `src/web/server.py` **✨ ENHANCED**
- **Purpose**: Lightweight local HTTP server, JSON API, static UI hosting
- **Current Endpoints**:
  - `GET /api/health` - server and LLM default status
  - `GET /api/agents` - registered agent descriptions
  - `GET /api/schema?db_path=...` - database schema inspection
  - `GET /api/history` - in-memory task history
  - `POST /api/seed-db` - seed demo database data
  - `POST /api/run` - execute a task through the orchestrator
  - `POST /api/templates` - list email templates
- **History**: `add_to_history()` stores the last 100 local tasks

#### `web/index.html` **✨ ENHANCED**
- **New Features**:
  - Y2K Operations Dashboard layout
  - History panel with task log
  - Email Templates modal
  - Agent roster, schema view, terminal-style command console
  - Direct HTTP API calls only

#### `web/app.js` **✨ ENHANCED**
- **New Features**:
  - Direct API calls with no login flow
  - Local task history rendering
  - History rendering
  - Templates modal with "Use Template" buttons
  - Table/JSON/timeline result tabs

#### `web/styles.css` **✨ ENHANCED**
- **New Styles**: Login screen, history items, status badges, modal, template cards, user info, responsive tweaks

---

### Configuration Files

#### `requirements.txt` **✨ UPDATED**
- Added: `matplotlib`, `twilio`

#### `.env.example` **✨ UPDATED**
- Added voice provider credentials

---

## Test Results
```
tests/test_core.py::test_database_tool_blocks_writes_by_default PASSED
tests/test_core.py::test_orchestrator_runs_db_task_without_llm_keys PASSED
tests/test_core.py::test_lead_tool_extracts_contacts PASSED
```

---

## CLI Verification
```bash
python main.py agents                    # Lists all 6 agents
python main.py run "Get customer count"  # DB agent works
python main.py run "Send email" --agent email --meta template=proposal ...  # Email agent works
python main.py ui                        # Starts web server on :8000
```

---

## Agent Capabilities Summary

| Agent | Key Features |
|-------|--------------|
| **DB** | Query, insert, update, delete, schema, aggregations, export CSV/JSON |
| **Email** | 5 templates, LLM generation, attachments, CC/BCC, dry-run |
| **Excel** | Read/write, analyze, pivot tables, charts (matplotlib), filter, merge |
| **Lead** | Extract, enrich (domain/phone), validate, score (0-100), deduplicate, export |
| **Report** | Summarize, detailed, performance, trends, export JSON/CSV/MD |
| **Voice** | Twilio/Vapi calls, schedule, recordings, list calls |

---

## Architecture Flow
```
User Request (CLI/UI)
    ↓
Orchestrator.run(Task)
    ↓
ManagerAgent.run(Task)
    ↓
TaskPlanner.plan() → Subtasks
    ↓
AgentRegistry.get(agent) → WorkerAgent.run(Task)
    ↓
Tool.execute() → Result
    ↓
Manager aggregates → Task.result
    ↓
Orchestrator returns Task
    ↓
UI updates from direct HTTP task responses
```

---

## Next Steps (Future Phases)
- [ ] Phase 2: Multi-agent coordination, task routing
- [ ] Phase 3: Email/Excel agent production hardening
- [ ] Phase 4: Lead generation with web scraping
- [ ] Phase 5: Voice agents with real Twilio/Vapi credentials
- [ ] Dashboard UI, multi-user, SaaS platform
