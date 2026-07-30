from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class EmailAgent(BaseAgent):
    """Email worker agent."""

    def __init__(self, email_tool=None, llm=None):
        super().__init__(
            name="Email Agent",
            description="Drafts and sends business emails",
            tools=[email_tool] if email_tool else [],
            llm=llm,
        )
        self.email_tool = email_tool

    def run(self, task: Task):
        task.set_status("running")
        try:
            if not self.email_tool:
                raise RuntimeError("Email tool is not configured")

            to_email = task.metadata.get("to", "")
            subject = task.metadata.get("subject", "Business update")
            body = task.metadata.get("body") or task.description
            dry_run = bool(task.metadata.get("dry_run", True))

            if not to_email:
                result = self.email_tool.draft("", subject, body)
                result["message"] = "No recipient provided; draft only."
            else:
                result = self.email_tool.send(to_email, subject, body, dry_run=dry_run)

            task.set_result({"agent": self.name, "result": result})
        except Exception as exc:
            task.set_error(str(exc))
        return task.result
