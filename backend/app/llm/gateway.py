import json
import logging
import hashlib
from typing import Any, Dict, List, Optional, Union
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from PIL import Image
import redis
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)

# Configure the Gemini API client
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


class LLMGateway:
    def __init__(self):
        # Lazy initialization of Redis client
        self._redis_client = None

    @property
    def redis(self):
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception as e:
                logger.error(f"Failed to connect to Redis cache: {e}")
        return self._redis_client

    def _get_cache_key(self, system: str, user: str, model: str, schema_name: Optional[str]) -> str:
        """Generate a stable MD5 hash key for Redis caching."""
        hasher = hashlib.md5()
        hasher.update(system.encode("utf-8"))
        hasher.update(user.encode("utf-8"))
        hasher.update(model.encode("utf-8"))
        if schema_name:
            hasher.update(schema_name.encode("utf-8"))
        return f"llm_cache:{hasher.hexdigest()}"

    async def generate(
        self,
        system: str,
        user: str,
        *,
        model: Optional[str] = None,
        response_schema: Optional[type[BaseModel]] = None,
        images: Optional[List[Image.Image]] = None,
        temperature: float = 0.1
    ) -> Any:
        """
        Generate content from Gemini.
        Supports text, images (multimodal), JSON schema output, Redis caching,
        and fallback from heavy (pro) to primary (flash) on failure.
        """
        selected_model = model or settings.LLM_PRIMARY
        schema_name = response_schema.__name__ if response_schema else None
        
        # Check cache if no images are present (images are hard to serialize for keys)
        cache_key = None
        if not images and self.redis:
            cache_key = self._get_cache_key(system, user, selected_model, schema_name)
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    logger.info("LLM Cache Hit")
                    parsed = json.loads(cached)
                    if response_schema:
                        return response_schema.model_validate(parsed)
                    return parsed["text"]
            except Exception as e:
                logger.warning(f"Error reading from LLM cache: {e}")

        # Prepare generation config
        gen_config_kwargs = {"temperature": temperature}
        if response_schema:
            gen_config_kwargs["response_mime_type"] = "application/json"
            gen_config_kwargs["response_schema"] = response_schema
            
        generation_config = GenerationConfig(**gen_config_kwargs)

        try:
            result_text = await self._call_gemini(selected_model, system, user, generation_config, images)
        except Exception as e:
            logger.warning(f"Primary model {selected_model} failed: {e}. Falling back to flash...")
            # Fallback to flash
            if selected_model != "gemini-2.0-flash":
                try:
                    result_text = await self._call_gemini("gemini-2.0-flash", system, user, generation_config, images)
                except Exception as fallback_err:
                    logger.error(f"Fallback model also failed: {fallback_err}")
                    raise fallback_err
            else:
                raise e

        # Validate response schema if required
        if response_schema:
            try:
                # Strip potential markdown formatting wraps from JSON
                clean_json = result_text.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()
                
                validated = response_schema.model_validate_json(clean_json)
                
                # Cache validated response
                if cache_key and self.redis:
                    try:
                        self.redis.setex(cache_key, 3600, clean_json) # 1 hour TTL
                    except Exception as ce:
                        logger.warning(f"Failed to save to LLM cache: {ce}")
                        
                return validated
            except Exception as schema_err:
                logger.error(f"JSON schema validation failed: {schema_err}. Raw output: {result_text}")
                raise schema_err

        # Cache text response
        if cache_key and self.redis:
            try:
                self.redis.setex(cache_key, 3600, json.dumps({"text": result_text}))
            except Exception as ce:
                logger.warning(f"Failed to save to LLM cache: {ce}")

        return result_text

    async def _call_gemini(
        self,
        model_name: str,
        system_instruction: str,
        user_prompt: str,
        generation_config: GenerationConfig,
        images: Optional[List[Image.Image]]
    ) -> str:
        """Actual call wrapper to google-generativeai client."""
        # Use primary or heavy models. Ensure name matches API expectation.
        # Translates generic settings names to actual API models if needed
        api_model_name = model_name
        if model_name == "gemini-2.0-flash":
            api_model_name = "gemini-2.0-flash"
        elif model_name == "gemini-2.0-pro":
            api_model_name = "gemini-2.0-pro-exp-02-05" # or the current stable pro version

        model = genai.GenerativeModel(
            model_name=api_model_name,
            system_instruction=system_instruction
        )
        
        contents = []
        if images:
            contents.extend(images)
        contents.append(user_prompt)
        
        # Async call is supported using generate_content_async
        response = await model.generate_content_async(
            contents,
            generation_config=generation_config
        )
        return response.text


llm_gateway = LLMGateway()
