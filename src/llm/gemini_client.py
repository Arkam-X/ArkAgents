import os
from google import genai


class GeminiClient:
    """
    Gemini Client
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("GEMINI_API_KEY is required")

        try:
            self.model = genai.GenerativeModel("gemini-2.5-flash")
        except Exception:
            self.model = None

    def generate(self, prompt: str):
        if not prompt:
            raise ValueError("Prompt must not be empty")

        if self.model is None:
            return "[Gemini fallback] Model unavailable"

        try:
            response = self.model.generate_content(prompt)

            if hasattr(response, "text"):
                return response.text

            if isinstance(response, dict):
                return response.get("text", "")

            return "[Gemini fallback] unexpected response"
        except Exception as e:
            return f"[Gemini fallback] {str(e)}"

