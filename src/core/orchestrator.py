from src.core.task import Task
from src.utils.logger import setup_logger


class Orchestrator:
    """Executes tasks through the manager."""

    def __init__(self, manager):
        self.manager = manager
        self.logger = setup_logger("Orchestrator")

    def run(self, task: Task):
        self.logger.info("Starting orchestration")
        task.set_status("running")

        try:
            result = self.manager.run(task)
            if task.status != "failed":
                task.set_result(result)
            self.logger.info("Orchestration completed")
            return task

        except Exception as exc:
            task.set_error(str(exc))
            self.logger.error(f"Error: {exc}")
            return task

    def run_async(self, task: Task):
        return self.run(task)
