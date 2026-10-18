# AI Project Structure Guidelines (Python)

This is the standard structure for every AI project we build in Python. It keeps code clean, layered and easy to track, so anyone on the team can open any project and know where everything is.

Give this file to your coding agent as well (save it as `CLAUDE.md` or `ARCHITECTURE.md` in the repo root) so it follows these rules from the first line of code.

---

## 1. Request Flow

Every request follows one path, top to bottom:

```
main.py → middlewares → routers → services → orchestrators → agents → clients (LLM, search, external APIs)
                                     ↓
                               repositories → db
```

Command-line scripts in `scripts/` are entry points like `main.py`. They call services only:

```
scripts → services → repositories → db
```

MCP servers in `mcp_servers/` are entry points for AI clients, like routers are for HTTP. Each tool calls one service only:

```
mcp_servers → services → orchestrators / repositories
```

---

## 2. Folder Structure

```
project-root/
  app/
    main.py              # App setup, middleware and router registration
    core/                # Config, DI, logging, clock, custom exceptions, prompt loader
    middlewares/         # Request ID, logging, security headers, rate limit, global error handler
    routers/             # Endpoints only, no logic
    mcp_servers/         # MCP servers that expose app features as tools for AI clients
    schemas/             # Request/response DTOs (Pydantic)
    services/            # Business logic
    orchestrators/       # Runs the flow between agents
    agents/              # base_agent.py + one class per agent
    prompts/             # Prompts as .md files
    clients/             # LLM, search and external API clients
    repositories/        # Data access
    models/              # DB entities (SQLAlchemy)
    db/                  # DB session and setup
  tests/
    unit/                # Mirrors app/ folder by folder
    integration/         # End-to-end flows
    fakes/               # Fake clients for tests (no real LLM or API calls)
  web/                   # Frontend (if any)
  data/                  # Sample/demo data
  docs/
    screenshots/         # App screenshots for README and portfolio
  scripts/               # One-off CLI utilities (create_user.py)
  .env.example           # All env vars with dummy values
  .gitignore
  pyproject.toml
  README.md
```

Every folder inside `app/` has an `__init__.py`. `scripts/` has one too, so scripts run as `python -m scripts.<name>`.

---

## 3. Layer Responsibilities

| Layer | Does | Never does |
|---|---|---|
| `main.py` | Creates the app, registers middlewares and routers | Business logic |
| `middlewares/` | Cross-cutting work on every request: logging, request ID, security headers, rate limiting, error handling | Call services or agents |
| `routers/` | Receive request, validate with schema, call one service, return response | Logic, DB calls, LLM calls |
| `mcp_servers/` | Expose features as MCP tools, validate tool input, call one service per tool, act as the configured MCP user | Logic, DB calls, LLM calls, skipping role checks |
| `services/` | Business rules, decide what happens, call orchestrators and repositories | Talk to HTTP or LLM APIs directly |
| `orchestrators/` | Decide which agent runs, in what order, and pass data between them | DB calls, direct LLM calls |
| `agents/` | One focused AI task each (plan, research, write, review) | Touch the DB, call other agents directly |
| `clients/` | The only place that talks to outside APIs (LLM, search, email, etc.) | Business logic |
| `repositories/` | All reads and writes to DB or files | Business logic |
| `models/` | DB table definitions | Logic |
| `schemas/` | Input/output shapes and validation | Logic |
| `prompts/` | Prompt text, one file per prompt | Code |
| `core/` | Settings, DI setup, logger, clock, exception classes, prompt loader | Feature logic |
| `scripts/` | One-off admin tasks (create users, seed data) by calling services | Business logic, direct DB access |
| `docs/` | Documentation assets such as screenshots | Code |

---

## 4. Dependency Rules

1. Calls only go **downward** in the flow. A lower layer never imports a higher one.
2. **No skipping layers.** A router or MCP tool never calls a repository or an agent directly.
3. Agents never call each other. The orchestrator connects them.
4. Only `clients/` talk to the outside world. Only `repositories/` touch data.
5. Depend on base classes or Protocols, not on concrete classes. Inject the real one through DI.
6. No circular imports. If two modules need each other, the design is wrong.

---

## 5. Naming Conventions

**Golden rule:** one main class per file, and the file name is the class name in snake_case.
`planner_agent.py` holds only `PlannerAgent`.

| Thing | Convention | Example |
|---|---|---|
| Files / folders | snake_case | `research_service.py` |
| Classes | PascalCase + layer suffix | `ResearchService`, `PlannerAgent` |
| Functions / methods | snake_case, verb first | `create_report()`, `get_by_id()` |
| Variables | snake_case | `report_id` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| Private members | `_` prefix | `_llm_client` |
| Abstract base classes | `Base` prefix | `BaseAgent`, `BaseRepository` |
| Interfaces | Plain name as Protocol (no `I` prefix) | `LlmClient`, `SearchClient` |
| Implementations | Provider prefix | `GroqLlmClient`, `TavilySearchClient` |
| Request DTOs | `Request` suffix | `CreateResearchRequest` |
| Response DTOs | `Response` suffix | `ResearchReportResponse` |
| Agent input/output | `Input` / `Output` suffix | `PlannerInput`, `PlannerOutput` |
| DB entities | Singular noun | `ResearchJob` |
| Router files | `<feature>_router.py` | `research_router.py` |
| MCP server files | `<feature>_mcp_server.py` | `claims_mcp_server.py` |
| MCP tool names | snake_case, verb first | `search_policies`, `get_claim` |
| URLs | Versioned, plural, kebab-case | `/api/v1/research-jobs` |
| Prompt files | `<agent>_<purpose>.md` | `planner_system.md` |
| Script files | `<verb>_<thing>.py` | `create_user.py` |
| Screenshot files | `<number>-<short-name>.png` | `01-api-docs.png` |
| Test files | `test_<file>.py` | `test_planner_agent.py` |
| Test functions | `test_<what>_when_<condition>_<expected>` | `test_run_when_no_sources_raises_error` |
| Env vars | UPPER_SNAKE | `LLM_PROVIDER`, `GROQ_API_KEY` |

**Suffix list:** `Service`, `Orchestrator`, `Agent`, `Client`, `Repository`, `Request`, `Response`, `Input`, `Output`, `Middleware`, `McpServer`, `Error`.

---

## 6. Agent Rules

Every agent inherits `BaseAgent` and exposes one public method.

```python
# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from pydantic import BaseModel

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)

class BaseAgent(ABC, Generic[TInput, TOutput]):
    name: str

    def __init__(self, llm_client: "LlmClient", prompt_loader: "PromptLoader") -> None:
        self._llm_client = llm_client
        self._prompt_loader = prompt_loader

    @abstractmethod
    async def run(self, input: TInput) -> TOutput: ...
```

- Input and output are always Pydantic models.
- Prompts are loaded from `prompts/`, never written inside Python files.
- One agent = one job. If you describe it with "and", split it.
- Agents return data. They do not save, send or log business events.

---

## 7. Config and Dependency Injection

- All settings live in `core/config.py` using `pydantic-settings`, read from `.env`.
- No hardcoded keys, URLs or model names in code.
- `.env.example` lists every variable with a dummy value.
- Wire dependencies in `core/dependencies.py` and inject with FastAPI `Depends`.
- Switching LLM provider (Groq, Gemini, etc.) must only need a `.env` change.

---

## 8. Code Quality

- Type hints on every function and method.
- Use `async` for anything that does I/O.
- Raise custom exceptions from `core/exceptions.py`. The global error middleware turns them into proper HTTP responses.
- Use the shared logger from `core/logging.py`. No `print()`.
- Tools: `ruff` (lint + format), `mypy` (types), `pre-commit` (runs both before every commit).
- Keep files small. If a file passes ~300 lines, split it.

---

## 9. Testing

- `tests/unit/` mirrors `app/` folder by folder.
- Unit tests never call a real LLM or API. Use fake clients.
- `tests/integration/` covers full request flows.
- Every agent and service has at least one test.
- Shared test fakes (like `FakeLlmClient`) live in `tests/fakes/`.

---

## 10. Git Hygiene

`.gitignore` must include at least:

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.env
```

Never commit API keys, `.venv` or cache folders.

---

## 11. Adding Anything New

When you need something that does not fit an existing folder, follow these steps before writing code:

1. **Check first.** Re-read section 3. Most new things belong to an existing layer.
2. **Define its one job.** Write one sentence for what it does and what it never does.
3. **Place it in the flow.** Decide who calls it and what it calls. It must fit the top-to-bottom flow in section 1 without breaking the dependency rules.
4. **Create a folder** under `app/` with a plural snake_case name and an `__init__.py`.
5. **Pick a suffix** for its classes and use it on every class in that folder.
6. **Add a base class or Protocol** if it will have more than one implementation.
7. **Mirror it** in `tests/unit/`.
8. **Update this file:** add a row to the tables in sections 1, 2, 3 and 5, so the next developer knows where it lives.

If you are not sure where something goes, ask before building it. A wrong placement is cheap to fix on day one and expensive later.