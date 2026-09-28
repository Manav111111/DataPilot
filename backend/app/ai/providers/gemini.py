import json
import logging
import asyncio
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=FutureWarning)
    import google.generativeai as genai
from app.ai.providers.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL or "gemini-1.5-flash"
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def get_provider_name(self) -> str:
        return "gemini"

    def get_model_name(self) -> str:
        return self.model_name

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        system_msg = (
            (system_instruction or "")
            + f"\n\nYou MUST return ONLY a valid JSON object strictly matching this schema:\n{schema_json}"
        )

        generation_config = {
            "temperature": temperature,
            "response_mime_type": "application/json",
        }

        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_msg,
            generation_config=generation_config,
        )

        retries = settings.AI_PLANNING_MAX_RETRIES
        last_err = None

        for attempt in range(retries + 1):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(model.generate_content, prompt),
                    timeout=settings.AI_PLANNING_TIMEOUT_SECONDS,
                )

                if not response.text:
                    raise ValueError("Empty response received from Gemini API.")

                data = json.loads(response.text)
                return response_schema.model_validate(data)
            except Exception as e:
                last_err = e
                logger.warning(
                    f"Gemini generation attempt {attempt + 1}/{retries + 1} failed: {e}"
                )
                if attempt < retries:
                    await asyncio.sleep(1.5 * (attempt + 1))

        raise RuntimeError(f"Gemini structured generation failed after retries: {last_err}")
