import os
import requests


class OpenRouterClient:
    """
    OpenRouter LLM Client
    """

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            raise EnvironmentError("OPENROUTER_API_KEY is required")

    def generate(self, prompt: str):
        if not prompt:
            raise ValueError("Prompt must not be empty")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()

            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")

        except Exception as e:
            # Fallback text if API call fails (for offline/test mode)
            return f"[OpenRouter fallback] {str(e)}"

