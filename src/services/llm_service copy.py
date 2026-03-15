"""
LLM Service for LiteEdGPT
Supports: Cody (default), Gemini, OpenAI, and Custom Local Models
"""

import os
import re
import subprocess
import platform
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class BaseLLMService(ABC):
    """Abstract base class for all LLM services"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text response"""
        pass

    @abstractmethod
    async def generate_with_image(
        self, prompt: str, image_data: bytes, system_prompt: str = None
    ) -> str:
        """Generate response with image"""
        pass


# ============================================================================
# CODY SERVICE (Default)
# ============================================================================


class CodyService(BaseLLMService):
    """Cody CLI-based LLM Service (Sourcegraph)"""

    def __init__(self):
        self.src_access_token = os.getenv("SRC_ACCESS_TOKEN", "")
        self.src_endpoint = os.getenv("SRC_ENDPOINT", "")
        self.model = os.getenv("CODY_MODEL", "anthropic/claude-sonnet-4-20250514")
        self.max_retries = 3

        # Set environment variables
        if self.src_access_token:
            os.environ["SRC_ACCESS_TOKEN"] = self.src_access_token
        if self.src_endpoint:
            os.environ["SRC_ENDPOINT"] = self.src_endpoint

        if self.src_access_token and self.src_endpoint:
            print(f"[LiteEdGPT] Cody Service initialized")
            print(f"[LiteEdGPT] Endpoint: {self.src_endpoint}")
            print(f"[LiteEdGPT] Model: {self.model}")
        else:
            print(f"[LiteEdGPT] Cody Service: Missing credentials")
            print(f"[LiteEdGPT] Please set SRC_ACCESS_TOKEN and SRC_ENDPOINT in .env")

    def _is_cancelled(self) -> bool:
        """Check if batch processing was cancelled"""
        return os.environ.get("LITEEDGPT_CANCELLED", "0") == "1"

    def _get_env(self) -> dict:
        """Get environment variables for Cody CLI"""
        env = os.environ.copy()
        env["SRC_ACCESS_TOKEN"] = self.src_access_token
        env["SRC_ENDPOINT"] = self.src_endpoint
        env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
        return env

    def _verify_auth(self, env: dict) -> bool:
        """Verify Cody authentication with retry logic"""
        cody_executable = "cody.cmd" if platform.system() == "Windows" else "cody"

        for attempt in range(self.max_retries):
            if self._is_cancelled():
                print("🛑 Authentication cancelled")
                return False

            try:
                login_cmd = [cody_executable, "auth", "whoami"]
                result = subprocess.run(
                    login_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                    env=env,
                    encoding="utf-8",
                    errors="replace",
                )

                if result.returncode == 0:
                    print(f"✓ Cody authentication verified")
                    return True
                else:
                    print(f"✗ Auth failed attempt {attempt + 1}/{self.max_retries}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2**attempt)
                        continue

            except subprocess.TimeoutExpired:
                print(f"✗ Auth timeout attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
            except Exception as e:
                print(f"✗ Auth exception: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue

        return False

    def _cody_chat_sync(self, prompt: str, context_file: str = None) -> str:
        """Execute synchronous chat with Cody CLI"""
        if self._is_cancelled():
            return "Error: Request was cancelled"

        env = self._get_env()

        # Validate credentials
        if not self.src_access_token:
            return "Error: SRC_ACCESS_TOKEN not set. Please configure in backend/.env"
        if not self.src_endpoint:
            return "Error: SRC_ENDPOINT not set. Please configure in backend/.env"

        # Verify authentication
        if not self._verify_auth(env):
            if self._is_cancelled():
                return "Error: Request was cancelled"
            return (
                "Error: Cody authentication failed. Check your SRC_ACCESS_TOKEN and SRC_ENDPOINT."
            )

        cody_executable = "cody.cmd" if platform.system() == "Windows" else "cody"

        # Build command
        cmd = [
            cody_executable,
            "chat",
            f"--model={self.model}",
            "--ignore-context-window-errors",
            "--stdin",
        ]

        # Add context file if provided
        if context_file and os.path.exists(context_file):
            cmd.insert(3, "--context-file")
            cmd.insert(4, context_file)

        print(f"[Cody] Executing: {' '.join(cmd)}")

        # Retry loop
        for attempt in range(self.max_retries):
            if self._is_cancelled():
                return "Error: Request was cancelled"

            try:
                result = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env=env,
                    encoding="utf-8",
                    errors="replace",
                )

                if self._is_cancelled():
                    return "Error: Request was cancelled"

                if result.returncode == 0 and result.stdout:
                    output = result.stdout.strip()
                    if len(output) > 50:
                        print(f"✓ Cody response received ({len(output)} chars)")
                        return output
                    else:
                        print(f"⚠️ Short response: {output}")
                        if attempt < self.max_retries - 1:
                            time.sleep(2**attempt)
                            continue
                        return output

                elif result.returncode != 0:
                    error_msg = result.stderr if result.stderr else "Unknown error"
                    print(f"✗ Command failed: {error_msg[:200]}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2**attempt)
                        continue
                    return f"Error: {error_msg}"

                else:
                    if attempt < self.max_retries - 1:
                        time.sleep(2**attempt)
                        continue
                    return "Error: No output from Cody"

            except subprocess.TimeoutExpired:
                print(f"✗ Timeout attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    continue
                return "Error: Request timed out after 5 minutes"

            except Exception as e:
                print(f"✗ Exception: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    continue
                return f"Error: {str(e)}"

        return "Error: All retry attempts exhausted"

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text response using Cody"""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        # Run sync function in thread pool to not block event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self._cody_chat_sync, full_prompt)
        return response

    async def generate_with_image(
        self, prompt: str, image_data: bytes, system_prompt: str = None
    ) -> str:
        """Generate response with image - Cody doesn't support images directly"""
        # For image support, we can save the image temporarily and reference it
        # or fall back to a vision-capable model
        return await self.generate(
            f"{prompt}\n\n[Note: An image was provided but Cody CLI doesn't support direct image input. Please describe the image or use a vision-capable model.]",
            system_prompt,
        )


# ============================================================================
# GEMINI SERVICE
# ============================================================================


class GeminiService(BaseLLMService):
    """Google Gemini API Service"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.vision_model_name = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-flash")

        if self.api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.vision_model = genai.GenerativeModel(self.vision_model_name)
                self.genai = genai
                print(f"[LiteEdGPT] Gemini Service initialized")
                print(f"[LiteEdGPT] Model: {self.model_name}")
            except Exception as e:
                print(f"[LiteEdGPT] Gemini Service init error: {e}")
                self.model = None
                self.vision_model = None
        else:
            self.model = None
            self.vision_model = None
            print(f"[LiteEdGPT] Gemini Service: No API key found")

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text response"""
        if not self.model:
            return "Error: Gemini API key not configured. Please set GOOGLE_API_KEY in backend/.env"

        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"[Gemini] Error: {e}")
            return f"Error generating response: {str(e)}"

    async def generate_with_image(
        self, prompt: str, image_data: bytes, system_prompt: str = None
    ) -> str:
        """Generate response with image"""
        if not self.vision_model:
            return "Error: Gemini API key not configured. Please set GOOGLE_API_KEY in backend/.env"

        try:
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(image_data))
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self.vision_model.generate_content([full_prompt, image])
            return response.text
        except Exception as e:
            print(f"[Gemini] Vision error: {e}")
            return f"Error generating response: {str(e)}"


# ============================================================================
# OPENAI SERVICE (Placeholder)
# ============================================================================


class OpenAIService(BaseLLMService):
    """OpenAI API Service"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.vision_model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")

        if self.api_key:
            try:
                from openai import AsyncOpenAI

                self.client = AsyncOpenAI(api_key=self.api_key)
                print(f"[LiteEdGPT] OpenAI Service initialized")
                print(f"[LiteEdGPT] Model: {self.model}")
            except Exception as e:
                print(f"[LiteEdGPT] OpenAI Service init error: {e}")
                self.client = None
        else:
            self.client = None
            print(f"[LiteEdGPT] OpenAI Service: No API key found")

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text response"""
        if not self.client:
            return "Error: OpenAI API key not configured. Please set OPENAI_API_KEY in backend/.env"

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[OpenAI] Error: {e}")
            return f"Error generating response: {str(e)}"

    async def generate_with_image(
        self, prompt: str, image_data: bytes, system_prompt: str = None
    ) -> str:
        """Generate response with image"""
        if not self.client:
            return "Error: OpenAI API key not configured. Please set OPENAI_API_KEY in backend/.env"

        try:
            import base64

            base64_image = base64.b64encode(image_data).decode("utf-8")

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
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            )

            response = await self.client.chat.completions.create(
                model=self.vision_model, messages=messages, max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[OpenAI] Vision error: {e}")
            return f"Error generating response: {str(e)}"


# ============================================================================
# LOCAL MODEL SERVICE (Placeholder for Custom Trained Models)
# ============================================================================


class LocalModelService(BaseLLMService):
    """
    Local/Custom Model Service

    This is a placeholder for running your own trained models locally.
    Supports: Ollama, LM Studio, vLLM, Text Generation WebUI, etc.
    """

    def __init__(self):
        self.base_url = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434")
        self.model = os.getenv("LOCAL_MODEL_NAME", "llama3")
        self.api_type = os.getenv(
            "LOCAL_MODEL_API_TYPE", "ollama"
        )  # ollama, openai-compatible, custom

        self.enabled = os.getenv("LOCAL_MODEL_ENABLED", "false").lower() == "true"

        if self.enabled:
            print(f"[LiteEdGPT] Local Model Service initialized")
            print(f"[LiteEdGPT] URL: {self.base_url}")
            print(f"[LiteEdGPT] Model: {self.model}")
            print(f"[LiteEdGPT] API Type: {self.api_type}")
        else:
            print(f"[LiteEdGPT] Local Model Service: Disabled")

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text response using local model"""
        if not self.enabled:
            return "Error: Local model not enabled. Set LOCAL_MODEL_ENABLED=true in backend/.env"

        try:
            import aiohttp

            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            if self.api_type == "ollama":
                return await self._ollama_generate(full_prompt, temperature)
            elif self.api_type == "openai-compatible":
                return await self._openai_compatible_generate(
                    full_prompt, system_prompt, temperature, max_tokens
                )
            else:
                return await self._custom_generate(full_prompt, temperature, max_tokens)

        except Exception as e:
            print(f"[LocalModel] Error: {e}")
            return f"Error generating response: {str(e)}"

    async def _ollama_generate(self, prompt: str, temperature: float) -> str:
        """Generate using Ollama API"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "No response")
                else:
                    error = await response.text()
                    return f"Error: Ollama returned {response.status}: {error}"

    async def _openai_compatible_generate(
        self, prompt: str, system_prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Generate using OpenAI-compatible API (LM Studio, vLLM, etc.)"""
        import aiohttp

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error = await response.text()
                    return f"Error: API returned {response.status}: {error}"

    async def _custom_generate(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """
        Custom API implementation
        Override this method for your specific model API
        """
        return "Error: Custom API not implemented. Please override _custom_generate() method."

    async def generate_with_image(
        self, prompt: str, image_data: bytes, system_prompt: str = None
    ) -> str:
        """Generate response with image using local model"""
        if not self.enabled:
            return "Error: Local model not enabled. Set LOCAL_MODEL_ENABLED=true in backend/.env"

        try:
            import aiohttp
            import base64

            if self.api_type == "ollama":
                # Ollama supports images with llava and similar models
                return await self._ollama_generate_with_image(prompt, image_data, system_prompt)
            else:
                return "Error: Image support not implemented for this API type"

        except Exception as e:
            print(f"[LocalModel] Vision error: {e}")
            return f"Error generating response: {str(e)}"

    async def _ollama_generate_with_image(
        self, prompt: str, image_data: bytes, system_prompt: str
    ) -> str:
        """Generate with image using Ollama (requires llava or similar model)"""
        import aiohttp
        import base64

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        base64_image = base64.b64encode(image_data).decode("utf-8")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "images": [base64_image],
                    "stream": False,
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "No response")
                else:
                    error = await response.text()
                    return f"Error: Ollama returned {response.status}: {error}"


# ============================================================================
# LLM SERVICE FACTORY
# ============================================================================


class LLMServiceFactory:
    """Factory to create appropriate LLM service based on configuration"""

    # Available providers
    PROVIDERS = {
        "cody": CodyService,
        "gemini": GeminiService,
        "google": GeminiService,  # Alias
        "openai": OpenAIService,
        "local": LocalModelService,
        "custom": LocalModelService,  # Alias
    }

    @staticmethod
    def create(provider: str = None) -> BaseLLMService:
        """
        Create LLM service instance

        Parameters:
            provider: One of 'cody', 'gemini', 'openai', 'local'
                     If None, uses PRIMARY_LLM from config

        Returns:
            BaseLLMService instance
        """
        if provider is None:
            provider = os.getenv("PRIMARY_LLM", "cody").lower()

        provider = provider.lower()

        if provider in LLMServiceFactory.PROVIDERS:
            print(f"[LiteEdGPT] Creating {provider.upper()} service...")
            return LLMServiceFactory.PROVIDERS[provider]()
        else:
            print(f"[LiteEdGPT] Unknown provider '{provider}', defaulting to Cody")
            return CodyService()

    @staticmethod
    def get_available_providers() -> list:
        """Get list of available providers"""
        return list(set(LLMServiceFactory.PROVIDERS.keys()))
