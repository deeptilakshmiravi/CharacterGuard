"""
Single place to control which AI backend is active.

To switch backends, comment/uncomment ONE line below.
llm_judge.py and question_generator.py both import AiClient from here,
so they never need to change.

Usage in llm_judge.py /question_generator.py:
    from api_clients.client_factory import AiClient
"""

from api_clients.ai_client import AiClient          # OpenRouter free models
from api_clients.gemini_client import GeminiClient as AiClient   # Gemini model

class AiClient:
    """
    Tries GeminiClient first. Falls back to OpenRouterClient on 503 or RuntimeError
    """
    def __init__(self):
        self._openrouter = OpenRouterClient()
        self._gemini = GeminiClient()

    def call(self, system_prompt: str, user_message: str) -> str:
        try:
            return self._gemini.call(system_prompt, user_message)
        except RuntimeError as e:
            print(f"Gemini failed ({e}), falling back to OpenRouter...")
            return self._openrouter.call(system_prompt, user_message)