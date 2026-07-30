from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class ReportAgent(BaseAgent):
    """Reporting worker agent."""

    def __init__(self, report_tool=None, llm=None):
        super().__init__(
            name="Reporting Agent",
            description="Summarizes task outputs and workflow performance",
            tools=[report_tool] if report_tool else [],
            llm=llm,
        )
        self.report_tool = report_tool

    def run(self, task: Task):
        task.set_status("running")
        try:
            if not self.report_tool:
                raise RuntimeError("Report tool is not configured")
            items = task.metadata.get("items", [])
            if not items and task.subtasks:
                items = [subtask.to_dict() for subtask in task.subtasks]
            task.set_result({"agent": self.name, "result": self.report_tool.summarize(items)})
        except Exception as exc:
            task.set_error(str(exc))
        return task.result
