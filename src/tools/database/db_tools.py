import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class DBTool:
    """SQLite database tool with schema discovery and write safeguards."""

    def __init__(self, db_path: str = "arkagents.db", allow_writes: bool = False):
        self.db_path = db_path
        self.allow_writes = allow_writes

    def connect(self):
        db_parent = Path(self.db_path).expanduser().resolve().parent
        db_parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _safe_identifier(name: str) -> str:
        if not name or not name.replace("_", "").isalnum():
            raise ValueError("Invalid table or column name")
        return name

    def get_tables(self) -> List[str]:
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [row[0] for row in cursor.fetchall()]

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        table_name = self._safe_identifier(table_name)
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            return [
                {
                    "cid": row[0],
                    "name": row[1],
                    "type": row[2],
                    "notnull": bool(row[3]),
                    "dflt_value": row[4],
                    "pk": bool(row[5])
                }
                for row in cursor.fetchall()
            ]

    def describe_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        return {table: self.get_columns(table) for table in self.get_tables()}

    def _operation(self, query: str) -> str:
        statement = query.strip().lower()
        if not statement:
            raise ValueError("Query must not be empty")
        if ";" in statement.rstrip(";"):
            raise ValueError("Only one SQL statement is allowed")
        return statement.split()[0]

    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        operation = self._operation(query)
        if operation not in {"select", "insert", "update", "delete"}:
            raise ValueError(f"Unsupported SQL operation: {operation}")
        if operation != "select" and not self.allow_writes:
            raise PermissionError("Database writes are disabled for this DBTool")

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if operation == "select":
                return [dict(row) for row in cursor.fetchall()]
            conn.commit()
            return {"status": "success", "rowcount": cursor.rowcount}

    def query(self, query: str, params: Optional[tuple] = None) -> Any:
        if self._operation(query) != "select":
            raise ValueError("query() only accepts SELECT statements")
        return self.execute(query, params)

    def insert(self, query: str, params: Optional[tuple] = None) -> Any:
        if self._operation(query) != "insert":
            raise ValueError("insert() only accepts INSERT statements")
        return self.execute(query, params)

    def update(self, query: str, params: Optional[tuple] = None) -> Any:
        if self._operation(query) != "update":
            raise ValueError("update() only accepts UPDATE statements")
        return self.execute(query, params)

    def delete(self, query: str, params: Optional[tuple] = None) -> Any:
        if self._operation(query) != "delete":
            raise ValueError("delete() only accepts DELETE statements")
        return self.execute(query, params)

    def seed_demo_data(self) -> Dict[str, Any]:
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS customer (
                    booking_id INTEGER PRIMARY KEY,
                    agent_id INTEGER NOT NULL,
                    no_of_pax INTEGER,
                    booking_date TEXT,
                    travel_date TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    total_price REAL NOT NULL
                )
                """
            )
            rows = [
                (1, 101, 2, "2024-01-01", "2024-02-01", "Dubai", 1200.50),
                (2, 102, 4, "2024-01-02", "2024-02-10", "Singapore", 2400.00),
                (3, 103, 1, "2024-01-03", "2024-02-15", "Bali", 900.75),
                (4, 101, 3, "2024-01-04", "2024-02-18", "Thailand", 1800.20),
                (5, 104, 5, "2024-01-05", "2024-02-20", "Maldives", 4500.00),
            ]
            cursor.executemany(
                """
                INSERT OR IGNORE INTO customer (
                    booking_id, agent_id, no_of_pax, booking_date,
                    travel_date, destination, total_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
            return {"status": "success", "rows_available": len(rows)}
