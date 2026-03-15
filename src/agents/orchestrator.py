"""
Agent Orchestrator for LiteEdGPT
"""
import json
from typing import Optional
from datetime import datetime


class AgentOrchestrator:
    def __init__(self):
        print("[LiteEdGPT] Initializing Agent Orchestrator...")
        self.conversation_history = {}
        
        try:
            from src.services.cache_service import CacheService
            from src.services.image_service import ImageService
            
            self.cache = CacheService()
            self.image_service = ImageService()
            print("[LiteEdGPT] All services loaded successfully")
        except ImportError as e:
            print(f"[LiteEdGPT] Error loading services: {e}")
            self.cache = None
            self.image_service = None

    async def process_request(
        self,
        text_input: str,
        image_data: Optional[bytes] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Process incoming request"""
        start_time = datetime.now()

        try:
            # Check if API key is provided
            if not api_key:
                return {
                    "success": False,
                    "message": "⚠️ Please add your Gemini API key in Settings first!\n\n1. Go to Settings\n2. Enter your free Gemini API key\n3. Click 'Save Key'\n\nGet your free key at: https://makersuite.google.com/app/apikey",
                    "type": "error",
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                }

            # Create LLM with user's API key
            from src.services.llm_service import GeminiService
            llm = GeminiService(api_key=api_key)

            # Check if LLM initialized properly
            if not llm.model:
                return {
                    "success": False,
                    "message": "❌ Invalid API key. Please check your Gemini API key in Settings.",
                    "type": "error",
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                }

            # Process image if provided
            image_context = None
            if image_data and self.image_service:
                try:
                    image_context = await self.image_service.process_image(image_data)
                    print(f"[Pipeline] Image processed")
                except Exception as e:
                    print(f"[Pipeline] Image processing error: {e}")

            # Build system prompt
            system_prompt = """You are LiteEdGPT, a friendly and helpful educational assistant for students.

Your role:
- Help students understand concepts clearly
- Solve problems step-by-step
- Explain in simple, easy-to-understand language
- Be encouraging and supportive
- Support both English and Hindi

Guidelines:
- For math problems: Show each step clearly
- For concepts: Use examples and analogies
- For homework: Guide, don't just give answers
- Keep responses concise but complete

Always be patient and helpful! 📚"""

            # Generate response
            print(f"[Pipeline] Generating response for: {text_input[:50]}...")
            
            if image_data:
                response_text = await llm.generate_with_image(
                    prompt=text_input,
                    image_data=image_data,
                    system_prompt=system_prompt
                )
            else:
                response_text = await llm.generate(
                    prompt=text_input,
                    system_prompt=system_prompt
                )

            # Check for errors in response
            if response_text.startswith("Error:"):
                return {
                    "success": False,
                    "message": response_text,
                    "type": "error",
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                }

            # Store in conversation history
            if session_id:
                if session_id not in self.conversation_history:
                    self.conversation_history[session_id] = []
                self.conversation_history[session_id].append({
                    "query": text_input,
                    "response": response_text[:500],
                })

            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"[Pipeline] Response generated in {processing_time:.2f}s")

            return {
                "success": True,
                "message": response_text,
                "type": "educational_response",
                "metadata": {
                    "has_image": image_data is not None,
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                },
                "processing_time": processing_time,
            }

        except Exception as e:
            print(f"[LiteEdGPT] Error: {str(e)}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "message": f"An error occurred: {str(e)}",
                "type": "error",
                "processing_time": (datetime.now() - start_time).total_seconds(),
            }

    def clear_history(self, session_id: str) -> bool:
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            return True
        return False

    def get_history(self, session_id: str) -> list:
        return self.conversation_history.get(session_id, [])