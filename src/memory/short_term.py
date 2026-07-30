from collections import deque
from typing import Any, Deque, Dict, List


class ShortTermMemory:
    """In-memory rolling context store."""

    def __init__(self, max_items: int = 20):
        self.max_items = max_items
        self._items: Deque[Dict[str, Any]] = deque(maxlen=max_items)

    def add(self, item: Dict[str, Any]) -> None:
        self._items.append(item)

    def list(self) -> List[Dict[str, Any]]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
