import sqlite3
from typing import Any, Dict, List, Optional


class DBTool:
    """
    Database Tool

    Handles:
    - Query
    - Insert
    - Update
    - Delete
    """

    def __init__(self, db_path: str = "arkagents.db"):
        self.db_path = db_path

    def connect(self):
        """Create DB connection"""
        return sqlite3.connect(self.db_path)

    @staticmethod
    def _safe_identifier(name: str) -> str:
        if not name or not name.replace("_", "").isalnum():
            raise ValueError("Invalid table or column name")
        return name

    def get_tables(self) -> List[str]:
        """Get all tables"""

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            return tables

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get columns of table"""

        table_name = self._safe_identifier(table_name)

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            return [
                {
                    "cid": row[0],
                    "name": row[1],
                    "type": row[2],
                    "notnull": bool(row[3]),
                    "dflt_value": row[4],
                    "pk": bool(row[5])
                }
                for row in columns
            ]

    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Run a SQL command"""

        if not query:
            raise ValueError("Query must not be empty")

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if query.strip().lower().startswith("select"):
                return cursor.fetchall()
            conn.commit()
            return {"status": "success"}

    def query(self, query: str, params: Optional[tuple] = None) -> Any:
        return self.execute(query, params)

    def insert(self, query: str, params: Optional[tuple] = None) -> Any:
        return self.execute(query, params)

    def update(self, query: str, params: Optional[tuple] = None) -> Any:
        return self.execute(query, params)

    def delete(self, query: str, params: Optional[tuple] = None) -> Any:
        return self.execute(query, params)

    # def query(self, query: str):
    #     """Query database"""

    #     conn = self.connect()
    #     cursor = conn.cursor()

    #     try:
    #         cursor.execute(query)
    #         result = cursor.fetchall()

    #         conn.close()

    #         return result

    #     except Exception as e:
    #         conn.close()
    #         return {"error": str(e)}

    # def insert(self, query: str):
    #     """Insert data"""

    #     conn = self.connect()
    #     cursor = conn.cursor()

    #     try:
    #         cursor.execute(query)
    #         conn.commit()

    #         conn.close()

    #         return {"status": "success"}

    #     except Exception as e:
    #         conn.close()
    #         return {"error": str(e)}

    # def update(self, query: str):
    #     """Update data"""

    #     conn = self.connect()
    #     cursor = conn.cursor()

    #     try:
    #         cursor.execute(query)
    #         conn.commit()

    #         conn.close()

    #         return {"status": "success"}

    #     except Exception as e:
    #         conn.close()
    #         return {"error": str(e)}

    # def delete(self, query: str):
    #     """Delete data"""

    #     conn = self.connect()
    #     cursor = conn.cursor()

    #     try:
    #         cursor.execute(query)
    #         conn.commit()

    #         conn.close()

    #         return {"status": "success"}

    #     except Exception as e:
    #         conn.close()
    #         return {"error": str(e)}