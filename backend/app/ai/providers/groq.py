import json
import logging
import asyncio
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from groq import AsyncGroq
from app.ai.providers.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model_name = model_name or settings.GROQ_MODEL or "llama-3.3-70b-versatile"
        self.client = AsyncGroq(api_key=self.api_key) if self.api_key else None

    def get_provider_name(self) -> str:
        return "groq"

    def get_model_name(self) -> str:
        return self.model_name

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        if not self.client:
            raise ValueError("GROQ_API_KEY is not configured.")

        # Construct JSON schema prompt instructions
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        system_msg = (
            (system_instruction or "")
            + f"\n\nYou MUST respond ONLY with a valid JSON object matching this JSON Schema:\n{schema_json}"
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ]

        retries = settings.AI_PLANNING_MAX_RETRIES
        last_err = None

        for attempt in range(retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=temperature,
                        response_format={"type": "json_object"},
                    ),
                    timeout=settings.AI_PLANNING_TIMEOUT_SECONDS,
                )

                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response received from Groq API.")

                data = json.loads(content)
                return response_schema.model_validate(data)
            except Exception as e:
                last_err = e
                logger.warning(
                    f"Groq generation attempt {attempt + 1}/{retries + 1} failed: {e}"
                )
                if attempt < retries:
                    await asyncio.sleep(1.5 * (attempt + 1))

        raise RuntimeError(f"Groq structured generation failed after retries: {last_err}")
