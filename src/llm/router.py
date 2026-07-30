import json
import re
from typing import Any, Dict, Optional

from src.llm.openai_client import OpenAIClient
from src.llm.openrouter_client import OpenRouterClient
from src.llm.gemini_client import GeminiClient


class LLMRouter:
    """Routes prompts across configured LLM providers with local fallback."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.openai = OpenAIClient()
        self.openrouter = OpenRouterClient()
        self.gemini = GeminiClient()
        self.last_error: Optional[str] = None

    def generate(
        self,
        prompt: str,
        task_type: Optional[str] = "reasoning"
    ) -> str:
        if not self.enabled:
            self.last_error = "LLM routing is disabled"
            return ""

        clients = self._route(task_type or "reasoning")
        errors = []

        for client in clients:
            if not getattr(client, "available", False):
                continue
            try:
                return client.generate(prompt)
            except Exception as exc:
                errors.append(f"{client.__class__.__name__}: {exc}")

        self.last_error = "; ".join(errors) or "No LLM provider configured"
        return ""

    def generate_json(
        self,
        prompt: str,
        task_type: Optional[str] = "reasoning",
        default: Any = None,
    ) -> Any:
        content = self.generate(prompt, task_type=task_type)
        if not content:
            return default
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    return default
            match = re.search(r"(\{.*\}|\[.*\])", content, re.DOTALL)
            if not match:
                return default
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return default

    def status(self) -> Dict[str, bool]:
        return {
            "enabled": self.enabled,
            "openai": self.openai.available,
            "openrouter": self.openrouter.available,
            "gemini": self.gemini.available,
        }

    def _route(self, task_type: str):
        if task_type in {"cheap", "fast"}:
            return [self.gemini, self.openrouter, self.openai]
        if task_type in {"coding", "reasoning"}:
            return [self.openai, self.openrouter, self.gemini]
        return [self.openrouter, self.openai, self.gemini]
