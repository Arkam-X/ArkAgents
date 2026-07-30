from typing import List

from src.core.agent_registry import AgentRegistry
from src.core.task import Task


class TaskPlanner:
    """Creates bounded subtask plans for the manager agent."""

    def __init__(self, registry: AgentRegistry, llm=None, max_subtasks: int = 5):
        self.registry = registry
        self.llm = llm
        self.max_subtasks = max_subtasks

    def plan(self, task: Task) -> List[Task]:
        if task.agent:
            return [task]

        llm_plan = self._llm_plan(task)
        if llm_plan:
            return llm_plan[: self.max_subtasks]

        agent = self._rule_based_agent(task.description)
        return [Task(description=task.description, agent=agent, metadata=task.metadata)]

    def _llm_plan(self, task: Task) -> List[Task]:
        if not self.llm:
            return []

        prompt = f"""
You are the manager planner for a business automation system.
Return only a JSON array. Each item must have: agent, task, metadata.
Use only these agents:
{self.registry.describe_agents()}
Keep the plan under {self.max_subtasks} subtasks.

User request:
{task.description}
Metadata:
{task.metadata}
"""
        data = self.llm.generate_json(prompt, task_type="reasoning", default=[])
        if not isinstance(data, list):
            return []

        tasks = []
        available_agents = set(self.registry.list_agents())
        for item in data:
            if not isinstance(item, dict):
                continue
            agent = item.get("agent")
            description = item.get("task") or item.get("description")
            if agent in available_agents and description:
                metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
                tasks.append(Task(description=description, agent=agent, metadata=metadata))
        return tasks

    def _rule_based_agent(self, description: str) -> str:
        text = description.lower()
        candidates = [
            ("voice", ["call", "phone", "voice"]),
            ("email", ["email", "mail", "proposal", "reply"]),
            ("excel", ["excel", "spreadsheet", "xlsx", "csv"]),
            ("lead", ["lead", "prospect", "contact", "businesses"]),
            ("report", ["report", "summary", "summarize", "analytics"]),
            ("db", ["database", "db", "sql", "customer", "booking", "table", "users"]),
        ]

        available = set(self.registry.list_agents())
        for agent, keywords in candidates:
            if agent in available and any(keyword in text for keyword in keywords):
                return agent
        if "db" in available:
            return "db"
        agents = self.registry.list_agents()
        if not agents:
            raise RuntimeError("No agents registered")
        return agents[0]
