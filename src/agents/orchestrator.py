"""
Agent Orchestrator for LiteEdGPT
"""
from typing import Optional
from datetime import datetime
from src.config import config


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
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        model_provider: str = "gemini",
        local_model_url: Optional[str] = None,
        local_model_name: Optional[str] = None,
    ) -> dict:
        """Process incoming request through classifier → response agent pipeline"""
        start_time = datetime.now()

        try:
            provider = (model_provider or "gemini").lower()

            key_map = {
                "gemini": (
                    gemini_api_key
                    or (api_key if provider == "gemini" else None)
                    or config.GOOGLE_API_KEY
                ),
                "openai": (
                    openai_api_key
                    or (api_key if provider == "openai" else None)
                    or config.OPENAI_API_KEY
                ),
            }

            provider_chain = self._build_provider_chain(provider)

            # If selected provider is cloud and key is missing, still allow fallback if other key exists.
            cloud_chain = [p for p in provider_chain if p in ["gemini", "openai"]]
            if cloud_chain and not any(key_map.get(p) for p in cloud_chain):
                return {
                    "success": False,
                    "message": "⚠️ Please add at least one API key (Gemini or OpenAI) in Settings first!",
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

            last_error = None
            used_provider = provider
            result = {"success": False, "type": "error", "message": "No provider response"}

            for current_provider in provider_chain:
                current_api_key = key_map.get(current_provider) if current_provider in ["gemini", "openai"] else None

                # Skip provider if key is required but not present.
                if current_provider in ["gemini", "openai"] and not current_api_key:
                    continue

                print(f"[Pipeline] Trying provider: {current_provider}")

                try:
                    # Step 2: Classify the query
                    from src.agents.classifier_agent import ClassifierAgent
                    classifier = ClassifierAgent(
                        api_key=current_api_key,
                        provider=current_provider,
                        local_model_url=local_model_url,
                        local_model_name=local_model_name,
                    )
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
                    context = {}
                    if session_id and session_id in self.conversation_history:
                        history = self.conversation_history[session_id]
                        if history:
                            context["previous_context"] = history[-1].get("response", "")

                    if image_context:
                        if image_context.get("extracted_text"):
                            context["ocr_text"] = image_context.get("extracted_text")
                        context["image_metadata"] = image_context.get("metadata", {})

                    if not context:
                        context = None

                    # Step 4: Generate response via ResponseAgent
                    from src.agents.response_agent import ResponseAgent
                    response_agent = ResponseAgent(
                        api_key=current_api_key,
                        provider=current_provider,
                        local_model_url=local_model_url,
                        local_model_name=local_model_name,
                    )
                    result = await response_agent.generate_response(
                        query=text_input,
                        classification=classification,
                        image_data=image_data,
                        context=context,
                    )

                    # For non-error failures (ex: non_educational), return directly.
                    if not result.get("success") and result.get("type") != "error":
                        return {
                            **result,
                            "processing_time": (datetime.now() - start_time).total_seconds(),
                        }

                    # Retry only for provider errors.
                    if result.get("success"):
                        used_provider = current_provider
                        break

                    last_error = result.get("message", "Unknown provider error")
                    print(f"[Pipeline] Provider {current_provider} failed, trying fallback")
                except Exception as provider_error:
                    last_error = str(provider_error)
                    print(f"[Pipeline] Provider {current_provider} exception: {provider_error}")
                    continue

            if not result.get("success"):
                return {
                    "success": False,
                    "message": f"All providers failed. Last error: {last_error}",
                    "type": "error",
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
                    "provider": used_provider,
                    "fallback_chain": provider_chain,
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

    def _build_provider_chain(self, selected_provider: str) -> list[str]:
        """Build provider order for automatic fallback between Gemini and OpenAI."""
        selected = (selected_provider or "gemini").lower()

        if selected == "openai":
            return ["openai", "gemini"]

        if selected == "gemini":
            return ["gemini", "openai"]

        return [selected]