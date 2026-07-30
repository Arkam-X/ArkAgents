from typing import Any, Dict

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
Return only JSON with keys: sql, operation.
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
        return {"sql": f"SELECT * FROM {table} LIMIT 50", "operation": "query"}

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

            if operation == "schema":
                result = schema
            elif operation in {"query", "select"}:
                result = self.db_tool.query(sql)
            elif operation == "insert":
                result = self.db_tool.insert(sql)
            elif operation == "update":
                result = self.db_tool.update(sql)
            elif operation == "delete":
                result = self.db_tool.delete(sql)
            else:
                raise ValueError(f"Unknown database operation: {operation}")

            task.set_result({"agent": self.name, "sql": sql, "result": result})
            self.info("DB Agent finished")
        except Exception as exc:
            self.error(str(exc))
            task.set_error(str(exc))
        return task.result
