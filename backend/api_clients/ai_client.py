"""
Thin wrapper around the OpenRouter API.

Responsibility:
    - Send a system prompt + user message to OpenRouter
    - Return the raw text response as a string
    - Nothing else

This class has zero knowledge of safety evaluation, scoring, or parsing.
All of that lives in llm_judge.py.

"""

import json
import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

#pick a few free models in case 1 failed
MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-4b-it:free",
    "openrouter/free",
]

#Judge responses are short, no need for more
DEFAULT_MAX_TOKENS = 512      
#Zero temperature = deterministic, consistent verdicts
DEFAULT_TEMPERATURE = 0.0    
#Seconds before giving up on a request 
DEFAULT_TIMEOUT = 30       
#Retry on transient failures (rate limits, timeouts)   
MAX_RETRIES = 3     
#Seconds to wait between retries          
RETRY_DELAY = 2        


class AiClient:
    """
    Sends a message to OpenRouter and returns the raw text response.
    Falls back through MODELS list if a model is rate limited.

    Usage:
        client = AiClient()
        response = client.call(
            system_prompt="You are a strict safety evaluator...",
            user_message="CHARACTER DESCRIPTION: ..."
        )
        print(response)  # raw string from the model (expected to be JSON)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key or os.environ.get("API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not found. "
                "Set API_KEY in your .env file or pass it directly."
            )

        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

    def call(self, system_prompt: str, user_message: str) -> str:
        """
        Send a system prompt + user message to OpenRouter.
        Tries each model in MODELS in order, falling back on rate limits.

        Args:
            system_prompt : Instructions that control the model's behaviour (the judge rules)
            user_message  : The actual content to evaluate (description + question + answer)

        Returns:
            Raw text string from the model. Parsing is llm_judge.py's responsibility.

        Raises:
            RuntimeError if all models and retries are exhausted.
        """
        last_error = None

        for model in MODELS:
            result = self._try_model(model, system_prompt, user_message)
            if result is not None:
                return result
            print(f"Model {model} unavailable, trying next fallback...")

        raise RuntimeError(
            f"All models exhausted after retries. Last error: {last_error}\n"
            "Check your API key, network connection, and rate limits."
        )

    #Private helpers
    def _try_model(self, model: str, system_prompt: str, user_message: str) -> Optional[str]:
        """
        Attempt to call a specific model with retries.
        Returns the response text on success, or None if rate limited / failed.
        """
        payload = self._build_payload(model, system_prompt, user_message)
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.post(
                    url=OPENROUTER_URL,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return self._extract_text(response.json())

            except requests.exceptions.Timeout:
                print(f"[{model}] Timed out (attempt {attempt})")

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
                if status == 429:
                    if attempt == MAX_RETRIES:
                        print(f"[{model}] Rate limited on all retries, falling back.")
                        return None
                    print(f"[{model}] Rate limited (attempt {attempt}), waiting...")
                    time.sleep(RETRY_DELAY * attempt)
                    continue
                else:
                    print(f"[{model}] HTTP error {status} (attempt {attempt})")

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        return None 

    def _build_payload(self, model: str, system_prompt: str, user_message: str) -> dict:
        return {
            "model": model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message,
                        }
                    ],
                }
            ],
        }

    def _extract_text(self, response_json: dict) -> str:
        try:
            return response_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Could not extract text from OpenRouter response: {e}")