"""
LLM Service for LiteEdGPT - Supports per-user API keys
"""
import os
from typing import Optional

class GeminiService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = None
        self.vision_model = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
                print(f"[LiteEdGPT] Gemini Service initialized")
            except Exception as e:
                print(f"[LiteEdGPT] Gemini init error: {e}")
        else:
            print(f"[LiteEdGPT] Gemini Service: No API key")
    
    async def generate(self, prompt: str, system_prompt: str = None,
                      temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate text response"""
        if not self.model:
            return "Error: Please add your Gemini API key in Settings"
        
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"[Gemini] Error: {e}")
            return f"Error: {str(e)}"
    
    async def generate_with_image(self, prompt: str, image_data: bytes,
                                 system_prompt: str = None) -> str:
        """Generate response with image"""
        if not self.vision_model:
            return "Error: Please add your Gemini API key in Settings"
        
        try:
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self.vision_model.generate_content([full_prompt, image])
            return response.text
        except Exception as e:
            print(f"[Gemini] Vision error: {e}")
            return f"Error: {str(e)}"

class LLMServiceFactory:
    @staticmethod
    def create(api_key: str = None):
        return GeminiService(api_key=api_key)