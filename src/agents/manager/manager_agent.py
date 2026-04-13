from typing import List
import json

from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class ManagerAgent(BaseAgent):
    """
    Agentic Manager Agent
    """

    def __init__(self, registry, llm=None):
        super().__init__(
            name="Manager Agent",
            description="AI Manager Agent",
            tools=[],
            llm=llm
        )

        self.registry = registry

    def think(self, task: Task) -> List[Task]:
        """
        AI Task Planning
        """

        agent_list = self.registry.list_agents()

        prompt = f"""
You are a Manager Agent.

Available agents:
{agent_list}

Break the task into subtasks.

Return JSON:

[
    {{
        "agent": "agent_name",
        "task": "subtask"
    }}
]

Task:
{task.description}
"""

        response = self.call_llm(prompt)

        try:
            plan = json.loads(response)
        except ValueError:
            plan = [{"agent": "db", "task": task.description}]

        subtasks = []

        for item in plan:
            subtask = Task(
                description=item["task"],
                agent=item["agent"]
            )

            subtasks.append(subtask)

        return subtasks

    def assign(self, tasks: List[Task]):
        """
        Assign tasks to agents
        """

        results = []

        for task in tasks:
            agent_name = task.agent

            agent = self.registry.get(agent_name)

            if agent is None:
                self.error(f"Agent not found: {agent_name}")
                task.set_status("failed")
                task.set_result({"error": f"Agent not found: {agent_name}"})
                continue

            self.info(f"Assigning to {agent_name}")
            task.set_status("running")
            result = agent.run(task)
            task.set_result(result)
            results.append(task)

        return results

    def run(self, task: Task):
        """
        Main Manager Execution
        """

        self.info("Manager started")

        # Step 1: Plan
        subtasks = self.think(task)

        for subtask in subtasks:
            task.add_subtask(subtask)

        # Step 2: Assign
        results = self.assign(subtasks)

        # Step 3: Aggregate
        task.set_result([r.to_dict() for r in results])

        self.info("Manager finished")

        return task.to_dict()