from abc import ABC, abstractmethod
from typing import Any, List

from src.core.task import Task
from src.utils.logger import setup_logger


class BaseAgent(ABC):
    """Base class for every worker and manager agent."""

    def __init__(
        self,
        name: str,
        description: str,
        tools: List[Any] | None = None,
        llm: Any = None,
        max_iterations: int = 3,
    ):
        self.name = name
        self.description = description
        self.tools = tools or []
        self.llm = llm
        self.max_iterations = max_iterations
        self.logger = setup_logger(self.name)

    def log(self, message: str) -> None:
        self.logger.info(message)

    def add_tool(self, tool: Any) -> None:
        self.tools.append(tool)

    def get_tools(self) -> List[Any]:
        return self.tools

    def call_llm(self, prompt: str, task_type: str = "reasoning") -> str:
        if not self.llm:
            raise ValueError("LLM not configured for agent")
        return self.llm.generate(prompt, task_type=task_type)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    @abstractmethod
    def run(self, task: Task) -> Any:
        """Execute a task and return a structured result."""
        pass
