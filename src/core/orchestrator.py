from typing import Optional
from src.core.task import Task
from src.utils.logger import setup_logger


class Orchestrator:
    """
    Orchestrator Engine

    Responsible for:
    - Task execution
    - Workflow orchestration
    - Multi-agent coordination
    """

    def __init__(self, manager):
        self.manager = manager
        self.logger = setup_logger("Orchestrator")

    def run(self, task: Task):
        """
        Execute task using manager
        """

        self.logger.info("Starting orchestration")

        task.set_status("running")

        try:
            result = self.manager.run(task)
            task.set_result(result)
            self.logger.info("Orchestration completed")
            return task

        except Exception as e:
            task.set_status("failed")
            task.set_result({"error": str(e)})
            self.logger.error(f"Error: {str(e)}")
            return task

    def run_async(self, task: Task):
        """
        Future async support
        """

        # Placeholder for async execution
        return self.run(task)