from typing import Dict, Any, Optional
from src.services.llm_service import LLMServiceFactory
from src.agents.classifier_agent import ClassificationResult
from src.utils.prompts import PromptTemplates


class ResponseAgent:
    def __init__(
        self,
        api_key: str = None,
        provider: str = "gemini",
        local_model_url: str = None,
        local_model_name: str = None,
    ):
        self.llm_service = LLMServiceFactory.create(
            api_key=api_key,
            provider=provider,
            local_model_url=local_model_url,
            local_model_name=local_model_name,
        )
        self.prompt_templates = PromptTemplates()

    async def generate_response(
        self,
        query: str,
        classification: ClassificationResult,
        image_data: Optional[bytes] = None,
        context: Optional[dict] = None,
    ) -> dict:
        """
        Generate educational response based on classification
        """

        # Check if query is educational
        if not classification.is_educational:
            return {
                "success": False,
                "message": self._get_non_educational_response(),
                "type": "non_educational",
                "metadata": {},
            }

        # Build appropriate prompt based on classification
        system_prompt = self._build_system_prompt(classification)
        user_prompt = self._build_user_prompt(query, classification, context)

        try:
            # Generate response
            if image_data:
                response = await self.llm_service.generate_with_image(
                    prompt=user_prompt, image_data=image_data, system_prompt=system_prompt
                )

                # Fallback: if multimodal fails, continue with OCR/text-only context.
                if isinstance(response, str) and response.startswith("Error:"):
                    response = await self.llm_service.generate(
                        prompt=user_prompt,
                        system_prompt=system_prompt,
                        temperature=0.7,
                        max_tokens=2500,
                    )
            else:
                response = await self.llm_service.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=0.7,
                    max_tokens=2500,
                )

            if isinstance(response, str) and response.startswith("Error:"):
                return {
                    "success": False,
                    "message": response,
                    "type": "error",
                    "metadata": {},
                }

            # Format and structure the response
            formatted_response = self._format_response(response, classification)

            return {
                "success": True,
                "message": formatted_response,
                "type": "educational_response",
                "metadata": {
                    "grade_level": classification.grade_level,
                    "subject": classification.subject,
                    "language": classification.language,
                    "query_type": classification.query_type,
                    "topics": classification.topics,
                    "complexity": classification.complexity,
                },
            }

        except Exception as e:
            print(f"Response generation error: {str(e)}")
            return {
                "success": False,
                "message": "I apologize, but I encountered an error while generating your response. Please try again.",
                "type": "error",
                "metadata": {},
            }

    def _build_system_prompt(self, classification: ClassificationResult) -> str:
        """Build system prompt based on classification"""

        base_prompt = f"""You are LiteEdGPT, an expert educational tutor specializing in {classification.subject or 'all subjects'}.
You are helping a {classification.grade_level or 'student'} level student.

Core Guidelines:
1. Use {classification.language} language for explanations
2. Adapt complexity to {classification.complexity} level
3. Be encouraging, supportive, and patient
4. Use age-appropriate examples and language
5. Break down complex concepts into simple, digestible steps
"""

        # Add query-type specific instructions
        if classification.query_type == "problem_solving":
            base_prompt += """
Problem Solving Approach:
- Show step-by-step solution
- Explain each step clearly
- Provide the reasoning behind each step
- Include final answer clearly marked
- Suggest similar practice problems
"""
        elif classification.query_type == "concept_explanation":
            base_prompt += """
Concept Explanation Approach:
- Start with simple definition
- Use real-world analogies
- Provide multiple examples
- Build up to complex ideas gradually
- Include visual descriptions when helpful
"""
        elif classification.query_type == "homework_help":
            base_prompt += """
Homework Help Approach:
- Guide without giving direct answers immediately
- Ask leading questions
- Provide hints and clues
- Teach problem-solving methodology
- Ensure student understands the process
"""
        elif classification.query_type == "exam_preparation":
            base_prompt += """
Exam Preparation Approach:
- Focus on key concepts
- Provide practice questions
- Share memory techniques
- Give time management tips
- Include common mistakes to avoid
"""

        # Add subject-specific instructions
        if classification.subject in ["Mathematics", "Physics", "Chemistry"]:
            base_prompt += """
STEM-Specific Guidelines:
- Use proper mathematical notation
- Show all calculations clearly
- Include units in answers
- Provide formulas when relevant
- Check answers for reasonableness
"""
        elif classification.subject in ["English", "Hindi"]:
            base_prompt += """
Language-Specific Guidelines:
- Focus on grammar and vocabulary
- Provide examples in context
- Include pronunciation tips if relevant
- Suggest practice exercises
- Correct errors constructively
"""

        return base_prompt

    def _build_user_prompt(
        self, query: str, classification: ClassificationResult, context: Optional[dict]
    ) -> str:
        """Build user prompt with query and context"""

        prompt = f"Student Query: {query}\n\n"

        if context and context.get("previous_context"):
            prompt += f"Previous Context: {context['previous_context']}\n\n"

        if context and context.get("ocr_text"):
            prompt += f"OCR Text From Image: {context['ocr_text'][:1500]}\n\n"

        if context and context.get("image_metadata"):
            prompt += f"Image Metadata: {context['image_metadata']}\n\n"

        if classification.topics:
            prompt += f"Identified Topics: {', '.join(classification.topics)}\n\n"

        prompt += "Please provide a comprehensive, educational response following the guidelines."

        return prompt

    def _format_response(self, response: str, classification: ClassificationResult) -> str:
        """Format the response for better readability"""

        # Add language-specific formatting
        if classification.language == "Hindi":
            response = self._add_hindi_formatting(response)

        # Add markdown formatting for better structure
        response = self._add_markdown_formatting(response)

        # Add footer with additional resources suggestion
        response += self._add_footer(classification)

        return response

    def _add_markdown_formatting(self, text: str) -> str:
        """Add markdown formatting to improve readability"""
        import re

        # Format mathematical expressions
        text = re.sub(r"\b(\d+)\s*([+\-*/=])\s*(\d+)\b", r"`\1 \2 \3`", text)

        # Format step indicators
        text = re.sub(r"^(Step \d+:)", r"**\1**", text, flags=re.MULTILINE)

        return text

    def _add_hindi_formatting(self, text: str) -> str:
        """Add specific formatting for Hindi responses"""
        # Add any Hindi-specific formatting if needed
        return text

    def _add_footer(self, classification: ClassificationResult) -> str:
        """Add helpful footer based on classification"""

        footer = "\n\n---\n"

        if classification.query_type == "concept_explanation":
            footer += "💡 **Tip:** Try explaining this concept to someone else to reinforce your understanding!"
        elif classification.query_type == "problem_solving":
            footer += "📝 **Practice:** Try solving similar problems to master this concept!"
        elif classification.query_type == "homework_help":
            footer += "✅ **Remember:** Understanding the process is more important than just getting the answer!"
        elif classification.query_type == "exam_preparation":
            footer += "🎯 **Exam Tip:** Review this topic regularly and practice with past papers!"
        else:
            footer += "📚 **Keep Learning:** Feel free to ask follow-up questions!"

        # Add subject-specific resources
        if classification.subject == "Mathematics":
            footer += "\n🔢 *Need more math help? Try practicing with different numbers!*"
        elif classification.subject == "Science" or classification.subject == "Biology":
            footer += "\n🔬 *Science is all about curiosity - keep asking questions!*"
        elif classification.subject == "Physics":
            footer += "\n⚡ *Physics connects to everything around us - observe the world!*"
        elif classification.subject == "Chemistry":
            footer += "\n🧪 *Chemistry is everywhere - from cooking to medicine!*"

        return footer

    def _get_non_educational_response(self) -> str:
        """Return response for non-educational queries"""
        return """
I'm **LiteEdGPT**, an educational assistant designed to help students with their academic queries.

I can assist you with:
- 📚 **Academic subjects** (Math, Science, English, Hindi, etc.)
- 📝 **Homework help** and problem-solving
- 🎓 **Concept explanations** for all grade levels
- 📖 **Exam preparation** and study tips
- 🔬 **Educational projects** and research

Please ask me an education-related question, and I'll be happy to help!

*Examples:*
- "Explain photosynthesis"
- "Solve: 2x + 5 = 15"
- "What caused World War II?"
- "Help me understand Newton's laws"
"""
