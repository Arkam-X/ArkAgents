from typing import Any, Dict, List, Optional
from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class ReportAgent(BaseAgent):
    """Reporting worker agent with charts, PDF export, and scheduling."""

    def __init__(self, report_tool=None, llm=None):
        super().__init__(
            name="Reporting Agent",
            description="Generates comprehensive reports with charts, exports, and scheduling",
            tools=[report_tool] if report_tool else [],
            llm=llm,
        )
        self.report_tool = report_tool

    def run(self, task: Task):
        task.set_status("running")
        try:
            if not self.report_tool:
                raise RuntimeError("Report tool is not configured")

            action = task.metadata.get("action", "summarize")
            items = task.metadata.get("items", [])
            if not items and task.subtasks:
                items = [subtask.to_dict() for subtask in task.subtasks]

            if action == "summarize":
                result = self.report_tool.summarize(items)
            elif action == "detailed":
                result = self.report_tool.detailed_report(items, task.metadata)
            elif action == "export":
                result = self.report_tool.export_report(
                    items,
                    task.metadata.get("format", "json"),
                    task.metadata.get("output_path", "report.json"),
                )
            elif action == "performance":
                result = self.report_tool.performance_report(items)
            elif action == "agent_performance":
                result = self.report_tool.agent_performance_report(items)
            elif action == "trend":
                result = self.report_tool.trend_report(items, task.metadata)
            else:
                result = {
                    "status": "needs_input",
                    "message": "Provide metadata.action (summarize/detailed/export/performance/agent_performance/trend) with required parameters.",
                }

            task.set_result({"agent": self.name, "result": result})
        except Exception as exc:
            task.set_error(str(exc))
        return task.result