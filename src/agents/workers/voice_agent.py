from typing import Any, Dict, List, Optional
from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class VoiceAgent(BaseAgent):
    """Voice worker agent with Twilio/Vapi integration for calls."""

    def __init__(self, voice_tool=None, llm=None):
        super().__init__(
            name="Voice Agent",
            description="Makes and manages voice calls via Twilio/Vapi",
            tools=[voice_tool] if voice_tool else [],
            llm=llm,
        )
        self.voice_tool = voice_tool

    def run(self, task: Task):
        task.set_status("running")
        try:
            if not self.voice_tool:
                raise RuntimeError("Voice tool is not configured")

            action = task.metadata.get("action", "plan")
            phone = task.metadata.get("phone", "")
            objective = task.description

            if action == "plan":
                result = self.voice_tool.create_call_plan(phone=phone, objective=objective)
            elif action == "call":
                result = self.voice_tool.make_call(
                    phone=phone,
                    objective=objective,
                    script=task.metadata.get("script"),
                    voice_id=task.metadata.get("voice_id"),
                )
            elif action == "schedule":
                result = self.voice_tool.schedule_call(
                    phone=phone,
                    objective=objective,
                    schedule_time=task.metadata.get("schedule_time"),
                    script=task.metadata.get("script"),
                )
            elif action == "list":
                result = self.voice_tool.list_calls()
            elif action == "get_recording":
                result = self.voice_tool.get_recording(task.metadata.get("call_sid"))
            elif action == "transcribe":
                result = self.voice_tool.transcribe_call(task.metadata.get("call_sid"))
            else:
                result = {
                    "status": "needs_input",
                    "message": "Provide metadata.action (plan/call/schedule/list/get_recording/transcribe) with required parameters.",
                }

            task.set_result({"agent": self.name, "result": result})
        except Exception as exc:
            task.set_error(str(exc))
        return task.result