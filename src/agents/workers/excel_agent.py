from typing import Any, Dict, List, Optional
from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class ExcelAgent(BaseAgent):
    """Spreadsheet worker agent with formulas, charts, and pivot tables."""

    def __init__(self, excel_tool=None, llm=None):
        super().__init__(
            name="Excel Agent",
            description="Reads, writes, analyzes, and visualizes spreadsheet data",
            tools=[excel_tool] if excel_tool else [],
            llm=llm,
        )
        self.excel_tool = excel_tool

    def run(self, task: Task):
        task.set_status("running")
        try:
            if not self.excel_tool:
                raise RuntimeError("Excel tool is not configured")

            action = task.metadata.get("action", "auto")
            path = task.metadata.get("path")
            rows = task.metadata.get("rows")
            output_path = task.metadata.get("output_path")

            if action == "read" or (path and not rows and not output_path):
                result = self._handle_read(task, path)
            elif action == "write" or (rows is not None and output_path):
                result = self._handle_write(task, rows, output_path)
            elif action == "analyze" or (path and task.metadata.get("analysis")):
                result = self._handle_analyze(task, path)
            elif action == "pivot" or (path and task.metadata.get("pivot")):
                result = self._handle_pivot(task, path)
            elif action == "chart" or (path and task.metadata.get("chart")):
                result = self._handle_chart(task, path)
            elif action == "filter" or (path and task.metadata.get("filter")):
                result = self._handle_filter(task, path)
            elif action == "merge" or (task.metadata.get("merge_files")):
                result = self._handle_merge(task)
            else:
                result = {
                    "status": "needs_input",
                    "message": "Provide metadata.action (read/write/analyze/pivot/chart/filter/merge) with required parameters.",
                }

            task.set_result({"agent": self.name, "result": result})
        except Exception as exc:
            task.set_error(str(exc))
        return task.result

    def _handle_read(self, task: Task, path: str) -> Dict[str, Any]:
        limit = task.metadata.get("limit", 100)
        read_rows = self.excel_tool.read_rows(path, limit=limit)
        return {
            "summary": self.excel_tool.summarize_rows(read_rows),
            "rows": read_rows,
            "row_count": len(read_rows),
        }

    def _handle_write(self, task: Task, rows: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        return self.excel_tool.write_rows(output_path, rows)

    def _handle_analyze(self, task: Task, path: str) -> Dict[str, Any]:
        read_rows = self.excel_tool.read_rows(path, limit=task.metadata.get("limit", 1000))
        analysis_type = task.metadata.get("analysis", "summary")
        return self.excel_tool.analyze(read_rows, analysis_type)

    def _handle_pivot(self, task: Task, path: str) -> Dict[str, Any]:
        read_rows = self.excel_tool.read_rows(path, limit=task.metadata.get("limit", 5000))
        pivot_config = task.metadata.get("pivot", {})
        return self.excel_tool.pivot_table(read_rows, pivot_config)

    def _handle_chart(self, task: Task, path: str) -> Dict[str, Any]:
        read_rows = self.excel_tool.read_rows(path, limit=task.metadata.get("limit", 5000))
        chart_config = task.metadata.get("chart", {})
        return self.excel_tool.create_chart(read_rows, chart_config, task.metadata.get("output_path"))

    def _handle_filter(self, task: Task, path: str) -> Dict[str, Any]:
        read_rows = self.excel_tool.read_rows(path, limit=task.metadata.get("limit", 5000))
        filter_config = task.metadata.get("filter", {})
        filtered = self.excel_tool.filter_rows(read_rows, filter_config)
        if task.metadata.get("output_path"):
            write_result = self.excel_tool.write_rows(task.metadata["output_path"], filtered)
            return {"filtered_rows": filtered, "write_result": write_result}
        return {"filtered_rows": filtered, "count": len(filtered)}

    def _handle_merge(self, task: Task) -> Dict[str, Any]:
        merge_files = task.metadata.get("merge_files", [])
        if not merge_files:
            return {"status": "error", "message": "No files to merge"}
        all_rows = []
        for file_path in merge_files:
            rows = self.excel_tool.read_rows(file_path, limit=10000)
            all_rows.extend(rows)
        output_path = task.metadata.get("output_path", "merged_output.xlsx")
        write_result = self.excel_tool.write_rows(output_path, all_rows)
        return {"merged_rows": len(all_rows), "write_result": write_result}