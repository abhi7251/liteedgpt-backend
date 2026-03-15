"""
Agent Orchestrator for LiteEdGPT
Multi-Agent Educational Assistant System
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime


class AgentOrchestrator:
    def __init__(self):
        print("[LiteEdGPT] Initializing Agent Orchestrator...")
        self.conversation_history = {}

        # Import all components
        try:
            from src.agents.classifier_agent import ClassifierAgent
            from src.agents.response_agent import ResponseAgent
            from src.services.cache_service import CacheService
            from src.services.image_service import ImageService
            from src.services.llm_service import LLMServiceFactory

            self.classifier = ClassifierAgent()
            self.responder = ResponseAgent()
            self.cache = CacheService()
            self.image_service = ImageService()
            self.llm = LLMServiceFactory.create()

            self.use_multi_agent = True  # Flag to enable multi-agent system
            print("[LiteEdGPT] All agents loaded successfully")
            print("[LiteEdGPT] Multi-Agent System: ENABLED")

        except ImportError as e:
            print(f"[LiteEdGPT] Error loading agents: {e}")
            self.classifier = None
            self.responder = None
            self.cache = None
            self.image_service = None
            self.llm = None
            self.use_multi_agent = False

    async def process_request(
        self,
        text_input: str,
        image_data: Optional[bytes] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> dict:
        """
        Process incoming request through multi-agent pipeline

        Pipeline:
        1. Image Processing (if image provided)
        2. Classification (detect subject, grade, language, etc.)
        3. Response Generation (tailored to classification)
        """
        start_time = datetime.now()

        try:
            # Create LLM with user's api key if provided
            if api_key:
                from src.services.llm_service import GeminiService
                self.llm = GeminiService(api_key=api_key)
                
            # ================================================================
            # STEP 1: Process Image (if provided)
            # ================================================================
            image_context = None
            if image_data and self.image_service:
                print("[Pipeline] Step 1: Processing image...")
                try:
                    image_context = await self.image_service.process_image(image_data)
                    print(f"[Pipeline] Image processed: {image_context.get('metadata', {})}")
                except Exception as e:
                    print(f"[Pipeline] Image processing error: {e}")

            # ================================================================
            # STEP 2: Classification (Multi-Agent)
            # ================================================================
            if self.use_multi_agent and self.classifier:
                print("[Pipeline] Step 2: Classifying query...")

                classification = await self.classifier.classify(
                    text_input=text_input, image_data=image_data, image_context=image_context
                )

                print(f"[Pipeline] Classification Result:")
                print(f"  - Is Educational: {classification.is_educational}")
                print(f"  - Subject: {classification.subject}")
                print(f"  - Grade Level: {classification.grade_level}")
                print(f"  - Language: {classification.language}")
                print(f"  - Query Type: {classification.query_type}")
                print(f"  - Complexity: {classification.complexity}")
                print(f"  - Confidence: {classification.confidence}")

                # ============================================================
                # STEP 3: Generate Response (Using Classification)
                # ============================================================
                print("[Pipeline] Step 3: Generating tailored response...")

                # Build context from conversation history
                context = None
                if session_id and session_id in self.conversation_history:
                    context = {
                        "previous_context": (
                            self.conversation_history[session_id][-1]
                            if self.conversation_history[session_id]
                            else None
                        )
                    }

                response = await self.responder.generate_response(
                    query=text_input,
                    classification=classification,
                    image_data=image_data,
                    context=context,
                )

                # Store in conversation history
                if session_id:
                    if session_id not in self.conversation_history:
                        self.conversation_history[session_id] = []
                    self.conversation_history[session_id].append(
                        {
                            "query": text_input,
                            "response": response.get("message", "")[:500],  # Store truncated
                            "classification": {
                                "subject": classification.subject,
                                "grade_level": classification.grade_level,
                            },
                        }
                    )

                # Add metadata
                response["metadata"] = {
                    **response.get("metadata", {}),
                    "has_image": image_data is not None,
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "pipeline": "multi-agent",
                    "classification": {
                        "is_educational": classification.is_educational,
                        "subject": classification.subject,
                        "grade_level": classification.grade_level,
                        "language": classification.language,
                        "query_type": classification.query_type,
                        "complexity": classification.complexity,
                        "confidence": classification.confidence,
                    },
                }
                response["processing_time"] = (datetime.now() - start_time).total_seconds()

                print(f"[Pipeline] Response generated in {response['processing_time']:.2f}s")
                return response

            # ================================================================
            # FALLBACK: Direct LLM Call (if multi-agent not available)
            # ================================================================
            else:
                print("[Pipeline] Using direct LLM call (multi-agent disabled)")

                if self.llm:
                    system_prompt = """You are LiteEdGPT, an educational assistant. 
                    Help students with their academic questions in a clear, helpful way.
                    Provide step-by-step explanations when appropriate."""

                    if image_data:
                        response_text = await self.llm.generate_with_image(
                            text_input, image_data, system_prompt
                        )
                    else:
                        response_text = await self.llm.generate(text_input, system_prompt)

                    return {
                        "success": True,
                        "message": response_text,
                        "type": "educational_response",
                        "metadata": {
                            "has_image": image_data is not None,
                            "user_id": user_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat(),
                            "pipeline": "direct",
                        },
                        "processing_time": (datetime.now() - start_time).total_seconds(),
                    }
                else:
                    return {
                        "success": False,
                        "message": "No LLM service available. Please check configuration.",
                        "type": "error",
                        "processing_time": (datetime.now() - start_time).total_seconds(),
                    }

        except Exception as e:
            print(f"[LiteEdGPT] Error processing request: {str(e)}")
            import traceback

            traceback.print_exc()

            return {
                "success": False,
                "message": "An error occurred processing your request. Please try again.",
                "error": str(e) if True else None,  # Set to False in production
                "type": "error",
                "processing_time": (datetime.now() - start_time).total_seconds(),
            }

    def clear_history(self, session_id: str) -> bool:
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            return True
        return False

    def get_history(self, session_id: str) -> list:
        """Get conversation history for a session"""
        return self.conversation_history.get(session_id, [])
