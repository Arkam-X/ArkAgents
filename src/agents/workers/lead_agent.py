from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class LeadAgent(BaseAgent):
    """Lead extraction worker agent."""

    def __init__(self, lead_tool=None, llm=None):
        super().__init__(
            name="Lead Agent",
            description="Extracts lead contact data from supplied text",
            tools=[lead_tool] if lead_tool else [],
            llm=llm,
        )
        self.lead_tool = lead_tool

    def run(self, task: Task):
        task.set_status("running")
        try:
            if not self.lead_tool:
                raise RuntimeError("Lead tool is not configured")
            text = task.metadata.get("text") or task.description
            source = task.metadata.get("source", "manual")
            leads = self.lead_tool.extract_contacts(text, source=source)
            task.set_result({"agent": self.name, "result": {"leads": leads, "count": len(leads)}})
        except Exception as exc:
            task.set_error(str(exc))
        return task.result
