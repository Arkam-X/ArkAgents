from typing import Any, Dict, Iterable, List


class ReportTool:
    """Builds compact structured reports from agent results."""

    def summarize(self, items: Iterable[Any]) -> Dict[str, Any]:
        rows: List[Any] = list(items)
        completed = sum(1 for item in rows if self._status(item) == "completed")
        failed = sum(1 for item in rows if self._status(item) == "failed")
        return {
            "total": len(rows),
            "completed": completed,
            "failed": failed,
            "items": rows,
        }

    def _status(self, item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("status", "unknown"))
        return str(getattr(item, "status", "unknown"))
