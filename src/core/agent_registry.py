from typing import Dict, List, Optional

from src.agents.base.base_agent import BaseAgent


class AgentRegistry:
    """Stores and manages available agents."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, name: str, agent: BaseAgent) -> None:
        self._agents[name] = agent

    def get(self, name: Optional[str]) -> Optional[BaseAgent]:
        if not name:
            return None
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())

    def describe_agents(self) -> Dict[str, str]:
        return {name: agent.description for name, agent in self._agents.items()}

    def get_all(self) -> Dict[str, BaseAgent]:
        return self._agents
