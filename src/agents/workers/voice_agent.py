from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class VoiceAgent(BaseAgent):
    """Future voice worker agent."""

    def __init__(self, voice_tool=None, llm=None):
        super().__init__(
            name="Voice Agent",
            description="Plans future customer calls and voice workflows",
            tools=[voice_tool] if voice_tool else [],
            llm=llm,
        )
        self.voice_tool = voice_tool

    def run(self, task: Task):
        task.set_status("running")
        try:
            if not self.voice_tool:
                raise RuntimeError("Voice tool is not configured")
            phone = task.metadata.get("phone", "")
            result = self.voice_tool.create_call_plan(phone=phone, objective=task.description)
            task.set_result({"agent": self.name, "result": result})
        except Exception as exc:
            task.set_error(str(exc))
        return task.result
