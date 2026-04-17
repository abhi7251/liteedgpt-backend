"""
LLM Service for LiteEdGPT - Supports provider routing per request.
"""
import base64
import io
import os
from typing import Optional

from src.config import config


class GeminiService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model_name = config.GEMINI_MODEL
        self.vision_model_name = config.GEMINI_VISION_MODEL
        self.model = None
        self.vision_model = None

        if self.api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.vision_model = genai.GenerativeModel(self.vision_model_name)
                print(f"[LiteEdGPT] Gemini Service initialized with {self.model_name} (vision: {self.vision_model_name})")
            except Exception as e:
                print(f"[LiteEdGPT] Gemini init error: {e}")
        else:
            print("[LiteEdGPT] Gemini Service: No API key")

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        if not self.model:
            return "Error: Please add your Gemini API key in Settings"

        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"[Gemini] Error: {e}")
            return f"Error: {str(e)}"

    async def generate_with_image(
        self, prompt: str, image_data: bytes, system_prompt: str = None
    ) -> str:
        if not self.vision_model:
            return "Error: Please add your Gemini API key in Settings"

        try:
            from PIL import Image

            image = Image.open(io.BytesIO(image_data))
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self.vision_model.generate_content([full_prompt, image])
            return response.text
        except Exception as e:
            print(f"[Gemini] Vision error: {e}")
            return f"Error: {str(e)}"


class OpenAIService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model_name = config.OPENAI_MODEL
        self.vision_model_name = config.OPENAI_VISION_MODEL
        self.client = None

        if self.api_key:
            try:
                from openai import AsyncOpenAI

                self.client = AsyncOpenAI(api_key=self.api_key)
                print(f"[LiteEdGPT] OpenAI Service initialized with {self.model_name}")
            except Exception as e:
                print(f"[LiteEdGPT] OpenAI init error: {e}")
        else:
            print("[LiteEdGPT] OpenAI Service: No API key")

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        if not self.client:
            return "Error: Please add your OpenAI API key in Settings"

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"[OpenAI] Error: {e}")
            return f"Error: {str(e)}"

    async def generate_with_image(
        self, prompt: str, image_data: bytes, system_prompt: str = None
    ) -> str:
        if not self.client:
            return "Error: Please add your OpenAI API key in Settings"

        try:
            image_b64 = base64.b64encode(image_data).decode("utf-8")
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                }
            )

            response = await self.client.chat.completions.create(
                model=self.vision_model_name,
                messages=messages,
                max_tokens=2000,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"[OpenAI] Vision error: {e}")
            return f"Error: {str(e)}"


class LocalModelService:
    """Placeholder service for self-hosted models using Ollama-compatible API."""

    def __init__(self, base_url: str = None, model_name: str = None):
        self.base_url = (base_url or config.LOCAL_MODEL_URL).rstrip("/")
        self.model_name = model_name or config.LOCAL_MODEL_NAME
        print(f"[LiteEdGPT] Local Model Service initialized: {self.base_url} ({self.model_name})")

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        try:
            import aiohttp

            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload, timeout=120) as resp:
                    if resp.status >= 400:
                        body = await resp.text()
                        return f"Error: Local model request failed ({resp.status}) {body}"
                    data = await resp.json()
                    return data.get("response", "")
        except Exception as e:
            print(f"[LocalModel] Error: {e}")
            return f"Error: {str(e)}"

    async def generate_with_image(
        self, prompt: str, image_data: bytes, system_prompt: str = None
    ) -> str:
        try:
            import aiohttp

            image_b64 = base64.b64encode(image_data).decode("utf-8")
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "images": [image_b64],
                "stream": False,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload, timeout=120) as resp:
                    if resp.status >= 400:
                        body = await resp.text()
                        return f"Error: Local model image request failed ({resp.status}) {body}"
                    data = await resp.json()
                    return data.get("response", "")
        except Exception as e:
            print(f"[LocalModel] Vision error: {e}")
            return f"Error: {str(e)}"


class LLMServiceFactory:
    @staticmethod
    def create(
        api_key: str = None,
        provider: str = "gemini",
        local_model_url: str = None,
        local_model_name: str = None,
    ):
        selected = (provider or "gemini").lower()
        if selected == "openai":
            return OpenAIService(api_key=api_key)
        if selected == "local":
            return LocalModelService(base_url=local_model_url, model_name=local_model_name)
        return GeminiService(api_key=api_key)
