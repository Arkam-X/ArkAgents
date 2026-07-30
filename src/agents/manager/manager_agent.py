from typing import List

from src.agents.base.base_agent import BaseAgent
from src.core.task import Task, TaskStatus
from src.workflows.task_planner import TaskPlanner


class ManagerAgent(BaseAgent):
    """Plans work, assigns subtasks, and aggregates results."""

    def __init__(self, registry, llm=None, planner=None):
        super().__init__(
            name="Manager Agent",
            description="Plans and delegates business automation tasks",
            tools=[],
            llm=llm
        )
        self.registry = registry
        self.planner = planner or TaskPlanner(registry=registry, llm=llm)

    def think(self, task: Task) -> List[Task]:
        return self.planner.plan(task)

    def assign(self, tasks: List[Task]) -> List[Task]:
        results = []
        for task in tasks:
            agent = self.registry.get(task.agent)
            if agent is None:
                task.set_error(f"Agent not found: {task.agent}")
                results.append(task)
                continue

            self.info(f"Assigning task to {task.agent}")
            try:
                agent.run(task)
            except Exception as exc:
                task.set_error(str(exc))
            results.append(task)
        return results

    def run(self, task: Task):
        self.info("Manager started")
        task.set_status(TaskStatus.RUNNING)

        subtasks = self.think(task)
        for subtask in subtasks:
            if subtask.id != task.id:
                task.add_subtask(subtask)
        results = self.assign(subtasks)

        failed = [item for item in results if item.status == TaskStatus.FAILED]
        summary = {
            "total": len(results),
            "completed": len(results) - len(failed),
            "failed": len(failed),
            "results": [item.to_dict() for item in results],
        }
        if failed:
            task.set_error("One or more subtasks failed")
            task.result = summary
        else:
            task.set_result(summary)
        self.info("Manager finished")
        return summary
