import json
from pathlib import Path
from typing import Any, Dict, List


class LongTermMemory:
    """Simple JSONL-backed memory store."""

    def __init__(self, path: str = "memory.jsonl"):
        self.path = Path(path)

    def add(self, item: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    def list(self, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows[-limit:]
