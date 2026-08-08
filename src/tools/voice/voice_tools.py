import os
from typing import Any, Dict, List, Optional


class VoiceTool:
    """Voice tool with Twilio and Vapi integration for making and managing calls."""

    def __init__(self):
        self.provider = os.getenv("VOICE_PROVIDER", "twilio").lower()
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from = os.getenv("TWILIO_FROM_NUMBER")
        self.vapi_key = os.getenv("VAPI_API_KEY")
        self.vapi_assistant_id = os.getenv("VAPI_ASSISTANT_ID")

    def _check_twilio(self) -> bool:
        return bool(self.twilio_sid and self.twilio_token and self.twilio_from)

    def _check_vapi(self) -> bool:
        return bool(self.vapi_key)

    def create_call_plan(self, phone: str, objective: str) -> Dict[str, Any]:
        return {
            "phone": phone,
            "objective": objective,
            "status": "planned",
            "provider": self.provider,
            "configured": self._check_twilio() or self._check_vapi(),
        }

    def make_call(
        self,
        phone: str,
        objective: str,
        script: Optional[str] = None,
        voice_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self.provider == "twilio":
            return self._make_twilio_call(phone, objective, script)
        elif self.provider == "vapi":
            return self._make_vapi_call(phone, objective, script, voice_id)
        return {"status": "error", "message": f"Unknown provider: {self.provider}"}

    def _make_twilio_call(
        self,
        phone: str,
        objective: str,
        script: Optional[str],
    ) -> Dict[str, Any]:
        if not self._check_twilio():
            return {"status": "error", "message": "Twilio not configured"}

        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)

            twiml = f"""
            <Response>
                <Say voice="alice">{script or objective}</Say>
                <Pause length="1"/>
            </Response>
            """

            call = client.calls.create(
                to=phone,
                from_=self.twilio_from,
                twiml=twiml.strip(),
            )
            return {
                "status": "initiated",
                "call_sid": call.sid,
                "phone": phone,
                "provider": "twilio",
            }
        except ImportError:
            return {"status": "error", "message": "twilio package not installed"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def _make_vapi_call(
        self,
        phone: str,
        objective: str,
        script: Optional[str],
        voice_id: Optional[str],
    ) -> Dict[str, Any]:
        if not self._check_vapi():
            return {"status": "error", "message": "Vapi not configured"}

        try:
            import requests
            headers = {
                "Authorization": f"Bearer {self.vapi_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "assistantId": self.vapi_assistant_id,
                "phoneNumber": phone,
            }
            if script:
                payload["assistantOverrides"] = {
                    "firstMessage": script,
                }
            if voice_id:
                payload.setdefault("assistantOverrides", {})["voice"] = {"voiceId": voice_id}

            response = requests.post(
                "https://api.vapi.ai/call",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "status": "initiated",
                "call_id": data.get("id"),
                "phone": phone,
                "provider": "vapi",
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def schedule_call(
        self,
        phone: str,
        objective: str,
        schedule_time: str,
        script: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "status": "scheduled",
            "phone": phone,
            "objective": objective,
            "schedule_time": schedule_time,
            "script": script,
            "provider": self.provider,
            "note": "Scheduling requires external cron/queue system",
        }

    def list_calls(self) -> Dict[str, Any]:
        if self.provider == "twilio" and self._check_twilio():
            try:
                from twilio.rest import Client
                client = Client(self.twilio_sid, self.twilio_token)
                calls = client.calls.list(limit=50)
                return {
                    "status": "success",
                    "provider": "twilio",
                    "calls": [
                        {
                            "sid": c.sid,
                            "to": c.to,
                            "from": c.from_,
                            "status": c.status,
                            "duration": c.duration,
                            "start_time": str(c.start_time) if c.start_time else None,
                        }
                        for c in calls
                    ],
                }
            except Exception as exc:
                return {"status": "error", "message": str(exc)}
        elif self.provider == "vapi" and self._check_vapi():
            try:
                import requests
                headers = {"Authorization": f"Bearer {self.vapi_key}"}
                response = requests.get("https://api.vapi.ai/call", headers=headers, timeout=30)
                response.raise_for_status()
                return {"status": "success", "provider": "vapi", "calls": response.json()}
            except Exception as exc:
                return {"status": "error", "message": str(exc)}
        return {"status": "error", "message": f"{self.provider} not configured"}

    def get_recording(self, call_sid: str) -> Dict[str, Any]:
        if not call_sid:
            return {"status": "error", "message": "call_sid required"}
        if self.provider == "twilio" and self._check_twilio():
            try:
                from twilio.rest import Client
                client = Client(self.twilio_sid, self.twilio_token)
                recordings = client.recordings.list(call_sid=call_sid)
                return {
                    "status": "success",
                    "recordings": [
                        {
                            "sid": r.sid,
                            "url": f"https://api.twilio.com{r.uri.replace('.json', '.mp3')}",
                            "duration": r.duration,
                            "date_created": str(r.date_created),
                        }
                        for r in recordings
                    ],
                }
            except Exception as exc:
                return {"status": "error", "message": str(exc)}
        return {"status": "error", "message": "Recordings not supported for current provider"}

    def transcribe_call(self, call_sid: str) -> Dict[str, Any]:
        if not call_sid:
            return {"status": "error", "message": "call_sid required"}
        return {
            "status": "not_implemented",
            "message": "Transcription requires additional setup (Twilio Transcribe or AssemblyAI)",
            "call_sid": call_sid,
        }