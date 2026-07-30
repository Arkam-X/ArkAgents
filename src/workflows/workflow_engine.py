from typing import Iterable, List

from src.core.task import Task
from src.utils.logger import setup_logger


class WorkflowEngine:
    """Sequential workflow runner."""

    def __init__(self, manager):
        self.manager = manager
        self.logger = setup_logger("WorkflowEngine")

    def run(self, tasks: Iterable[Task] | Task) -> List[Task]:
        self.logger.info("Starting workflow")
        if isinstance(tasks, Task):
            tasks = [tasks]
        results = []

        for task in tasks:
            self.logger.info(f"Running task: {task.description}")
            try:
                result = self.manager.run(task)
                if task.status != "failed":
                    task.set_result(result)
                results.append(task)

            except Exception as exc:
                task.set_error(str(exc))
                results.append(task)
                self.logger.error(f"Task failed: {task.description} | {exc}")
                break

        self.logger.info("Workflow completed")
        return results

    def run_single(self, task: Task) -> List[Task]:
        return self.run([task])
