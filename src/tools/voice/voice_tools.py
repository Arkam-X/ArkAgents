from typing import Dict


class VoiceTool:
    """Placeholder voice tool for future Twilio/Vapi integrations."""

    def create_call_plan(self, phone: str, objective: str) -> Dict[str, str]:
        return {
            "phone": phone,
            "objective": objective,
            "status": "planned",
            "provider": "not_configured",
        }
