from typing import Any, Dict, List, Optional
import json
import csv
from pathlib import Path

from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class DBAgent(BaseAgent):
    """Database worker agent. SQL execution is delegated to DBTool."""

    def __init__(self, db_tool=None, llm=None):
        super().__init__(
            name="Database Agent",
            description="Handles database operations intelligently",
            tools=[db_tool] if db_tool else [],
            llm=llm
        )
        self.db_tool = db_tool

    def discover_schema(self) -> Dict[str, Any]:
        return self.db_tool.describe_schema()

    def generate_sql(self, task: Task, schema: Dict[str, Any]) -> Dict[str, str]:
        if task.metadata.get("sql"):
            sql = task.metadata["sql"]
            return {"sql": sql, "operation": sql.strip().split()[0].lower()}

        prompt = f"""
You are a database tool planner.
Return only JSON with keys: sql, operation, params (optional).
Only produce one SQLite statement.
Use SELECT unless the user explicitly asks to write data.

Schema:
{schema}

User request:
{task.description}
"""
        decision = None
        if self.llm:
            decision = self.llm.generate_json(prompt, task_type="reasoning", default=None)
        if isinstance(decision, dict) and decision.get("sql"):
            return {
                "sql": str(decision["sql"]),
                "operation": str(decision.get("operation", "query")).lower(),
                "params": decision.get("params", []),
            }
        return self._fallback_sql(task, schema)

    def _fallback_sql(self, task: Task, schema: Dict[str, Any]) -> Dict[str, str]:
        description = task.description.lower()
        tables = list(schema.keys())
        table = "customer" if "customer" in tables else tables[0] if tables else ""
        if not table:
            return {"sql": "", "operation": "query"}

        if "count" in description or "how many" in description:
            return {"sql": f"SELECT COUNT(*) AS count FROM {table}", "operation": "query"}
        if "schema" in description or "tables" in description:
            return {"sql": "", "operation": "schema"}
        if "total" in description and "price" in description:
            return {
                "sql": f"SELECT SUM(total_price) AS total_price FROM {table}",
                "operation": "query",
            }
        if "average" in description or "avg" in description:
            if "price" in description:
                return {
                    "sql": f"SELECT AVG(total_price) AS avg_price FROM {table}",
                    "operation": "query",
                }
        if "max" in description or "highest" in description:
            if "price" in description:
                return {
                    "sql": f"SELECT MAX(total_price) AS max_price FROM {table}",
                    "operation": "query",
                }
        if "min" in description or "lowest" in description:
            if "price" in description:
                return {
                    "sql": f"SELECT MIN(total_price) AS min_price FROM {table}",
                    "operation": "query",
                }
        if "group by" in description or "per " in description:
            if "destination" in description:
                return {
                    "sql": f"SELECT destination, COUNT(*) AS count, SUM(total_price) AS total FROM {table} GROUP BY destination",
                    "operation": "query",
                }
            if "agent" in description:
                return {
                    "sql": f"SELECT agent_id, COUNT(*) AS count, SUM(total_price) AS total FROM {table} GROUP BY agent_id",
                    "operation": "query",
                }
        if "recent" in description or "latest" in description:
            return {
                "sql": f"SELECT * FROM {table} ORDER BY booking_date DESC LIMIT 10",
                "operation": "query",
            }
        if "top" in description and ("customer" in description or "booking" in description):
            return {
                "sql": f"SELECT * FROM {table} ORDER BY total_price DESC LIMIT 10",
                "operation": "query",
            }
        return {"sql": f"SELECT * FROM {table} LIMIT 50", "operation": "query"}

    def export_to_csv(self, rows: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        if not rows:
            return {"status": "error", "message": "No data to export"}
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(rows[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return {"status": "success", "path": output_path, "rows": len(rows)}

    def export_to_json(self, rows: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, default=str)
        return {"status": "success", "path": output_path, "rows": len(rows)}

    def run(self, task: Task):
        self.info("DB Agent started")
        task.set_status("running")

        if not self.db_tool:
            task.set_error("DB tool is not configured")
            return task.result

        try:
            schema = self.discover_schema()
            decision = self.generate_sql(task, schema)
            operation = decision.get("operation", "query")
            sql = decision.get("sql", "")
            params = decision.get("params", [])

            if operation == "schema":
                result = schema
            elif operation in {"query", "select"}:
                result = self.db_tool.query(sql, tuple(params) if params else None)
            elif operation == "insert":
                result = self.db_tool.insert(sql, tuple(params) if params else None)
            elif operation == "update":
                result = self.db_tool.update(sql, tuple(params) if params else None)
            elif operation == "delete":
                result = self.db_tool.delete(sql, tuple(params) if params else None)
            else:
                raise ValueError(f"Unknown database operation: {operation}")

            export_format = task.metadata.get("export")
            export_path = task.metadata.get("export_path")
            if export_format and export_path and isinstance(result, list):
                if export_format == "csv":
                    export_result = self.export_to_csv(result, export_path)
                elif export_format == "json":
                    export_result = self.export_to_json(result, export_path)
                else:
                    export_result = {"status": "error", "message": f"Unknown export format: {export_format}"}
                result = {"data": result, "export": export_result}

            task.set_result({"agent": self.name, "sql": sql, "result": result})
            self.info("DB Agent finished")
        except Exception as exc:
            self.error(str(exc))
            task.set_error(str(exc))
        return task.result