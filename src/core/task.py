from typing import Any, Dict, List, Optional
import uuid


class Task:
    """
    Task Model

    Represents a unit of work in the agent system
    """

    def __init__(
        self,
        description: str,
        agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.description = description
        self.agent = agent
        self.metadata = metadata or {}

        self.status = "pending"
        self.result = None
        self.subtasks: List["Task"] = []

    def set_status(self, status: str):
        """Update task status"""
        self.status = status

    def set_result(self, result: Any):
        """Set task result"""
        self.result = result
        self.status = "completed"

    def add_subtask(self, task: "Task"):
        """Add subtask"""
        self.subtasks.append(task)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "description": self.description,
            "agent": self.agent,
            "status": self.status,
            "result": self.result,
            "subtasks": [task.to_dict() for task in self.subtasks]
        }