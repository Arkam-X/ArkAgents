from typing import Dict
from src.agents.base.base_agent import BaseAgent


class AgentRegistry:
    """
    Agent Registry

    Stores and manages all agents
    """

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, name: str, agent: BaseAgent):
        """
        Register new agent
        """

        self._agents[name] = agent

    def get(self, name: str):
        """
        Get agent by name
        """

        return self._agents.get(name)

    def list_agents(self):
        """
        List all agents
        """

        return list(self._agents.keys())

    def get_all(self):
        """
        Get all agents
        """

        return self._agents