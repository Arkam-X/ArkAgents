from typing import Optional
from src.llm.openrouter_client import OpenRouterClient
from src.llm.gemini_client import GeminiClient


class LLMRouter:
    """
    LLM Router

    Routes requests to different LLM providers
    """

    def __init__(self):
        self.openrouter = OpenRouterClient()
        self.gemini = GeminiClient()

    def generate(
        self,
        prompt: str,
        task_type: Optional[str] = "reasoning"
    ):
        """
        Route request based on task type
        """

        # Reasoning tasks
        if task_type == "reasoning":
            try:
                return self.openrouter.generate(prompt)
            except Exception:
                return self.gemini.generate(prompt)

        # Cheap / fast tasks
        elif task_type == "fast":
            try:
                return self.gemini.generate(prompt)
            except Exception:
                return self.openrouter.generate(prompt)

        # Default fallback
        try:
            return self.openrouter.generate(prompt)
        except Exception:
            return self.gemini.generate(prompt)
