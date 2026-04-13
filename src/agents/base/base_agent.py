from abc import ABC, abstractmethod
from typing import Any, Dict, List
from src.utils.logger import setup_logger

class BaseAgent(ABC):
    """Base Agent -- Every agent will inherit from this class"""

    def __init__(self, name, description, tools: List[Any] = None, llm = None):
        self.name = name
        self.description = description
        self.tools = tools or []
        self.llm = llm


        self.logger = setup_logger(self.name)

    def log(self, message: str):
        """Basic Logging via configured logger"""
        self.logger.info(message)

    def add_tool(self, tool):
        """Add tools to the Agent"""
        self.tools.append(tool)

    def get_tools(self):
        """Returns available tools"""
        return self.tools

    def call_llm(self, prompt, task_type="reasoning"):
        """Call LLM via router"""

        if not self.llm:
            raise ValueError("LLM not configured for agent")

        return self.llm.generate(prompt, task_type=task_type)
    
    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    @abstractmethod
    def run(self, task: Dict[str, Any]):
        """Main agent execution method, Must be implemented by all the agents"""
        pass