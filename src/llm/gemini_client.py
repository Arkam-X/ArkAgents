import os
from typing import Optional


class GeminiClient:
    """Gemini client using google-genai when installed and configured."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", model)
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _load_client(self):
        if self._client is not None:
            return self._client
        if not self.available:
            raise EnvironmentError("GEMINI_API_KEY is not configured")
        from google import genai

        self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str) -> str:
        if not self.available:
            raise EnvironmentError("GEMINI_API_KEY is not configured")
        if not prompt:
            raise ValueError("Prompt must not be empty")

        client = self._load_client()
        response = client.models.generate_content(model=self.model, contents=prompt)
        return getattr(response, "text", "") or ""
