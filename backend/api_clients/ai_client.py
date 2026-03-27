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
#import logging
import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

#logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-3-12b-it:free"

DEFAULT_MAX_TOKENS = 512      # Judge responses are short — no need for more
DEFAULT_TEMPERATURE = 0.0     # Zero temperature = deterministic, consistent verdicts
DEFAULT_TIMEOUT = 30          # Seconds before giving up on a request
MAX_RETRIES = 3               # Retry on transient failures (rate limits, timeouts)
RETRY_DELAY = 2               # Seconds to wait between retries


# ---------------------------------------------------------------------------
# OpenRouterClient
# ---------------------------------------------------------------------------

class AiClient:
    """
    Sends a message to OpenRouter and returns the raw text response.

    Usage:
        client = OpenRouterClient()
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
        Send a system prompt + user message to OpenRouter

        Args:
            system_prompt : Instructions that control the model's behaviour (the judge rules)
            user_message  : The actual content to evaluate (description + question + answer)

        Returns:
            Raw text string from the model. Parsing is llm_judge.py's responsibility.

        Raises:
            RuntimeError if all retries are exhausted.
        """
        payload = self._build_payload(system_prompt, user_message)
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                #logger.debug(f"OpenRouter API call attempt {attempt}/{MAX_RETRIES}")

                response = requests.post(
                    url=OPENROUTER_URL,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                )
                response.raise_for_status()

                return self._extract_text(response.json())

            except requests.exceptions.Timeout:
                #logger.warning(f"OpenRouter request timed out (attempt {attempt})")
                print("timed out")

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
                if status == 429:
                    # Rate limited, wait longer before retrying
                    #logger.warning(f"Rate limited by OpenRouter (attempt {attempt}). Waiting...")
                    time.sleep(RETRY_DELAY * attempt)
                    continue
                #elif status == 400:
                    # Bad request , retrying won't help
                    #logger.error(f"OpenRouter rejected the request (400): {e.response.text}")
                    #raise
                #else:
                    #logger.warning(f"OpenRouter HTTP error {status} (attempt {attempt}): {e}")

            #except requests.exceptions.RequestException as e:
                #logger.warning(f"OpenRouter request failed (attempt {attempt}): {e}")

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

        raise RuntimeError(
            f"OpenRouter API call failed after {MAX_RETRIES} attempts. "
            "Check your API key, network connection, and rate limits."
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_payload(self, system_prompt: str, user_message: str) -> dict:
        """
        Build the OpenRouter request body.

        The system prompt goes in as a "system" role message, which is the
        standard OpenAI-compatible format that OpenRouter follows.
        """
        return {
            "model": MODEL,
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
        """
        Pull the text content out of OpenRouter's response structure.

        OpenRouter follows the OpenAI response format:
        {
            "choices": [
                {
                    "message": {
                        "content": "..."
                    }
                }
            ]
        }
        """
        try:
            return response_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            #logger.error(f"Unexpected OpenRouter response structure: {response_json}")
            raise RuntimeError(f"Could not extract text from OpenRouter response: {e}")