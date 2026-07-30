from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
import uuid


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """Represents one unit of work in the agent system."""

    description: str
    agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    subtasks: List["Task"] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def set_status(self, status: str) -> None:
        self.status = status
        self.updated_at = time.time()

    def set_result(self, result: Any) -> None:
        self.result = result
        self.error = None
        self.set_status(TaskStatus.COMPLETED)

    def set_error(self, error: str) -> None:
        self.error = error
        self.result = {"error": error}
        self.set_status(TaskStatus.FAILED)

    def add_subtask(self, task: "Task") -> None:
        self.subtasks.append(task)
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "agent": self.agent,
            "metadata": self.metadata,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "subtasks": [task.to_dict() for task in self.subtasks],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        task = cls(
            description=data["description"],
            agent=data.get("agent"),
            metadata=data.get("metadata") or {},
            id=data.get("id") or str(uuid.uuid4()),
        )
        task.status = data.get("status", TaskStatus.PENDING)
        task.result = data.get("result")
        task.error = data.get("error")
        for subtask in data.get("subtasks", []):
            task.add_subtask(cls.from_dict(subtask))
        return task
