"""
Single place to control which AI backend is active.

To switch backends, comment/uncomment ONE line below.
llm_judge.py and question_generator.py both import AiClient from here,
so they never need to change.

Usage in llm_judge.py /question_generator.py:
    from api_clients.client_factory import AiClient
"""

#Toggle here 

from api_clients.ai_client import AiClient          # OpenRouter free models
# from api_clients.gemini_client import GeminiClient as AiClient   # Gemini model

