"""
Simple test to exercise Bedrock-backed OpenAIService.
Run from the `backend` folder:

    python tests/test_bedrock.py

Ensure `AWS_BEARER_TOKEN_BEDROCK` and optional `BEDROCK_BASE_URL` are set in `.env` or environment.
"""

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import sys
from pathlib import Path
import asyncio

# Ensure the repository `backend` root is on sys.path so `src` can be imported
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.services.llm_service import LLMServiceFactory

async def main():
    # pick token from env and construct bedrock base_url if not provided
    import os

    token = os.getenv("AWS_BEARER_TOKEN_BEDROCK") or os.getenv("AWS_BEARER_TOKEN")
    if not token:
        raise EnvironmentError("AWS_BEARER_TOKEN_BEDROCK not set in environment or .env file.")

    region = os.getenv("BEDROCK_REGION", "eu-north-1")
    base = os.getenv("BEDROCK_BASE_URL") or f"https://bedrock-mantle.{region}.api.aws/v1"

    svc = LLMServiceFactory.create(api_key=token, provider="bedrock", local_model_url=base)
    prompt = "Hello from test: please reply briefly and include your source identifier."
    resp = await svc.generate(prompt, system_prompt="You are a helpful assistant.")
    print("--- Response ---")
    print(resp)

if __name__ == "__main__":
    asyncio.run(main())
