import unittest
import uuid
from pathlib import Path

from src.core.app import build_orchestrator
from src.core.task import Task
from src.tools.database import DBTool
from src.tools.lead import LeadTool


class ArkAgentsCoreTests(unittest.TestCase):
    def db_path(self) -> str:
        root = Path.cwd() / ".test_tmp"
        root.mkdir(exist_ok=True)
        return str(root / f"{uuid.uuid4()}.db")

    def test_database_tool_blocks_writes_by_default(self):
        db_path = self.db_path()
        writable = DBTool(db_path, allow_writes=True)
        writable.seed_demo_data()

        readonly = DBTool(db_path)
        with self.assertRaises(PermissionError):
            readonly.insert(
                "INSERT INTO customer (booking_id, agent_id, travel_date, destination, total_price) "
                "VALUES (99, 1, '2024-01-01', 'Dubai', 1.0)"
            )

    def test_orchestrator_runs_db_task_without_llm_keys(self):
        db_path = self.db_path()
        DBTool(db_path, allow_writes=True).seed_demo_data()
        orchestrator = build_orchestrator(db_path=db_path)

        result = orchestrator.run(Task(description="Get all customers from database"))
        payload = result.to_dict()

        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["result"]["failed"], 0)
        rows = payload["result"]["results"][0]["result"]["result"]
        self.assertGreaterEqual(len(rows), 1)

    def test_lead_tool_extracts_contacts(self):
        leads = LeadTool().extract_contacts(
            "Contact sales@example.com or +1 212 555 0100",
            source="unit-test",
        )
        self.assertEqual(len(leads), 2)


if __name__ == "__main__":
    unittest.main()
