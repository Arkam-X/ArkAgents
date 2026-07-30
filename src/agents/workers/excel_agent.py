from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class ExcelAgent(BaseAgent):
    """Spreadsheet worker agent."""

    def __init__(self, excel_tool=None, llm=None):
        super().__init__(
            name="Excel Agent",
            description="Reads, writes, and summarizes spreadsheet data",
            tools=[excel_tool] if excel_tool else [],
            llm=llm,
        )
        self.excel_tool = excel_tool

    def run(self, task: Task):
        task.set_status("running")
        try:
            if not self.excel_tool:
                raise RuntimeError("Excel tool is not configured")

            path = task.metadata.get("path")
            rows = task.metadata.get("rows")
            output_path = task.metadata.get("output_path")

            if rows is not None and output_path:
                result = self.excel_tool.write_rows(output_path, rows)
            elif path:
                read_rows = self.excel_tool.read_rows(path, limit=task.metadata.get("limit", 100))
                result = {
                    "summary": self.excel_tool.summarize_rows(read_rows),
                    "rows": read_rows,
                }
            else:
                result = {
                    "status": "needs_input",
                    "message": "Provide metadata.path to read or metadata.rows plus metadata.output_path to write.",
                }

            task.set_result({"agent": self.name, "result": result})
        except Exception as exc:
            task.set_error(str(exc))
        return task.result
