"""
Agent Orchestrator for LiteEdGPT
"""
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
        """Process incoming request through classifier → response agent pipeline"""
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

            # Validate API key by creating GeminiService
            from src.services.llm_service import GeminiService
            llm = GeminiService(api_key=api_key)
            if not llm.model:
                return {
                    "success": False,
                    "message": "❌ Invalid API key. Please check your Gemini API key in Settings.",
                    "type": "error",
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                }

            # Step 1: Process image if provided
            image_context = None
            if image_data and self.image_service:
                try:
                    image_context = await self.image_service.process_image(image_data)
                    print("[Pipeline] Image processed")
                except Exception as e:
                    print(f"[Pipeline] Image processing error: {e}")

            # Step 2: Classify the query
            from src.agents.classifier_agent import ClassifierAgent
            classifier = ClassifierAgent(api_key=api_key)
            classification = await classifier.classify(
                text_input=text_input,
                image_data=image_data,
                image_context=image_context,
            )
            print(
                f"[Pipeline] Classified → subject={classification.subject}, "
                f"type={classification.query_type}, lang={classification.language}, "
                f"complexity={classification.complexity}, confidence={classification.confidence:.2f}"
            )

            # Step 3: Build conversation context from history
            context = None
            if session_id and session_id in self.conversation_history:
                history = self.conversation_history[session_id]
                if history:
                    context = {"previous_context": history[-1].get("response", "")}

            # Step 4: Generate response via ResponseAgent
            from src.agents.response_agent import ResponseAgent
            response_agent = ResponseAgent(api_key=api_key)
            result = await response_agent.generate_response(
                query=text_input,
                classification=classification,
                image_data=image_data,
                context=context,
            )

            if not result["success"]:
                return {
                    **result,
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                }

            # Step 5: Store in conversation history
            if session_id:
                if session_id not in self.conversation_history:
                    self.conversation_history[session_id] = []
                self.conversation_history[session_id].append({
                    "query": text_input,
                    "response": result["message"][:500],
                })

            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"[Pipeline] Response generated in {processing_time:.2f}s")

            return {
                **result,
                "metadata": {
                    **result.get("metadata", {}),
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