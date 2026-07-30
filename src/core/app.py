from src.agents.manager.manager_agent import ManagerAgent
from src.agents.workers import (
    DBAgent,
    EmailAgent,
    ExcelAgent,
    LeadAgent,
    ReportAgent,
    VoiceAgent,
)
from src.config import settings
from src.core.agent_registry import AgentRegistry
from src.core.orchestrator import Orchestrator
from src.llm.router import LLMRouter
from src.tools.database.db_tools import DBTool
from src.tools.email import EmailTool
from src.tools.excel import ExcelTool
from src.tools.lead import LeadTool
from src.tools.reporting import ReportTool
from src.tools.voice import VoiceTool


def build_orchestrator(
    db_path: str | None = None,
    allow_db_writes: bool = False,
    use_llm: bool | None = None,
):
    llm_router = LLMRouter(enabled=settings.ENABLE_LLM if use_llm is None else use_llm)
    registry = AgentRegistry()

    registry.register("db", DBAgent(DBTool(db_path or settings.DB_PATH, allow_writes=allow_db_writes), llm_router))
    registry.register("excel", ExcelAgent(ExcelTool(), llm_router))
    registry.register("email", EmailAgent(EmailTool(), llm_router))
    registry.register("lead", LeadAgent(LeadTool(), llm_router))
    registry.register("voice", VoiceAgent(VoiceTool(), llm_router))
    registry.register("report", ReportAgent(ReportTool(), llm_router))

    manager = ManagerAgent(registry=registry, llm=llm_router)
    return Orchestrator(manager)
