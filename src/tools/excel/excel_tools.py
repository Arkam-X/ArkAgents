import csv
from pathlib import Path
from typing import Any, Dict, List


class ExcelTool:
    """Reads and writes spreadsheet-like files."""

    def read_rows(self, path: str, limit: int = 100) -> List[Dict[str, Any]]:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(path)

        if file_path.suffix.lower() == ".csv":
            with file_path.open(newline="", encoding="utf-8") as handle:
                return list(csv.DictReader(handle))[:limit]

        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Install pandas and openpyxl to read Excel files") from exc

        frame = pd.read_excel(file_path)
        return frame.head(limit).to_dict(orient="records")

    def write_rows(self, path: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.suffix.lower() == ".csv":
            fieldnames = sorted({key for row in rows for key in row.keys()})
            with file_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            return {"status": "success", "path": str(file_path), "rows": len(rows)}

        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Install pandas and openpyxl to write Excel files") from exc

        pd.DataFrame(rows).to_excel(file_path, index=False)
        return {"status": "success", "path": str(file_path), "rows": len(rows)}

    def summarize_rows(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        columns = sorted({key for row in rows for key in row.keys()})
        return {"rows": len(rows), "columns": columns}
