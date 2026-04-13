from typing import Dict, Any
import json

from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class DBAgent(BaseAgent):
    """
    Agentic Database Agent
    """

    def __init__(self, db_tool=None, llm=None):
        super().__init__(
            name="Database Agent",
            description="Handles database operations intelligently",
            tools=[db_tool] if db_tool else [],
            llm=llm
        )

        self.db_tool = db_tool

    def discover_schema(self):
        """
        Discover database schema dynamically
        """

        tables = self.db_tool.get_tables()

        if isinstance(tables, dict) and "error" in tables:
            raise RuntimeError(f"Failed to discover schema: {tables['error']}")

        schema = {}

        for table in tables:
            table_name = table[0] if isinstance(table, (list, tuple)) else table
            columns = self.db_tool.get_columns(table_name)
            schema[table_name] = columns

        return schema

    def generate_sql(self, task: Task, schema):
        """
        Generate SQL using AI
        """

        prompt = f"""
You are a database expert.

Database Schema:
{schema}

Generate SQL query for the following request.

Return JSON:

{{
    "sql": "SQL query",
    "operation": "query/insert/update/delete"
}}

User Request:
{task.description}
"""

        response = self.call_llm(prompt)

        try:
            decision = json.loads(response)
        except Exception:
            decision = {
                "sql": "",
                "operation": "query"
            }

        return decision

    def run(self, task: Task):
        """
        Main Execution
        """

        self.info("DB Agent started")

        task.set_status("running")

        if not self.db_tool:
            error_msg = "DB tool is not configured"
            self.error(error_msg)
            task.set_status("failed")
            task.set_result({"error": error_msg})
            return task.result

        # Step 1: Discover schema
        schema = self.discover_schema()

        self.info("Schema discovered")

        # Step 2: Generate SQL
        decision = self.generate_sql(task, schema)

        sql = decision.get("sql")
        operation = decision.get("operation")

        self.info(f"Generated SQL: {sql}")

        # Step 3: Execute SQL
        if operation == "query":
            result = self.db_tool.query(sql)

        elif operation == "insert":
            result = self.db_tool.insert(sql)

        elif operation == "update":
            result = self.db_tool.update(sql)

        elif operation == "delete":
            result = self.db_tool.delete(sql)

        else:
            result = {"error": "Unknown operation"}

        task.set_result({
            "agent": self.name,
            "sql": sql,
            "result": result
        })

        self.info("DB Agent finished")

        return task.result