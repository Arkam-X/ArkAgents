from typing import List
from src.core.task import Task
from src.utils.logger import setup_logger


class WorkflowEngine:
    """
    Workflow Engine

    Handles:
    - Sequential workflows
    - Multi-step execution
    - Task dependencies
    """

    def __init__(self, manager):
        self.manager = manager
        self.logger = setup_logger("WorkflowEngine")

    def run(self, tasks: List[Task]):
        """
        Run tasks sequentially
        """

        self.logger.info("Starting workflow")

        results = []

        for task in tasks:

            self.logger.info(f"Running task: {task.description}")

            try:
                result = self.manager.run(task)

                task.set_result(result)

                results.append(task)

            except Exception as e:

                task.set_status("failed")

                self.logger.error(
                    f"Task failed: {task.description} | {str(e)}"
                )

                break

        self.logger.info("Workflow completed")

        return results

    def run_single(self, task: Task):
        """
        Run single task workflow
        """

        return self.run([task])