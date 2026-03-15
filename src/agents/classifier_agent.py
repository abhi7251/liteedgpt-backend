import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from src.services.llm_service import LLMServiceFactory
from src.config import config

class ClassificationResult(BaseModel):
    is_educational: bool = Field(description="Whether the query is education-related")
    grade_level: Optional[str] = Field(description="Education level of the student")
    subject: Optional[str] = Field(description="Subject area of the query")
    language: str = Field(default="English", description="Preferred response language")
    query_type: str = Field(description="Type of educational query")
    topics: list[str] = Field(default_factory=list, description="Specific topics identified")
    complexity: str = Field(default="intermediate", description="Query complexity level")
    confidence: float = Field(default=0.0, description="Confidence score of classification")

class ClassifierAgent:
    def __init__(self, api_key: str = None):
        self.llm_service = LLMServiceFactory.create(api_key=api_key)
        
    async def classify(self, 
                      text_input: str, 
                      image_data: Optional[bytes] = None,
                      image_context: Optional[dict] = None) -> ClassificationResult:
        """
        Classify the educational query and extract metadata
        """
        
        # Build classification prompt
        classification_prompt = self._build_classification_prompt(
            text_input, 
            image_context
        )
        
        system_prompt = """You are an expert educational query classifier for LiteEdGPT.
        Your task is to analyze student queries and classify them accurately.
        
        You must:
        1. Determine if the query is education-related
        2. Identify the appropriate grade level (Class 1-12, Undergraduate, Postgraduate, PhD)
        3. Identify the subject area
        4. Detect the preferred language (English or Hindi)
        5. Categorize the query type
        6. Extract specific topics
        7. Assess complexity level
        
        Respond ONLY in valid JSON format."""
        
        try:
            # If image is provided, use vision model
            if image_data:
                response = await self.llm_service.generate_with_image(
                    prompt=classification_prompt,
                    image_data=image_data,
                    system_prompt=system_prompt
                )
            else:
                response = await self.llm_service.generate(
                    prompt=classification_prompt,
                    system_prompt=system_prompt,
                    temperature=0.3  # Lower temperature for more consistent classification
                )
            
            # Parse the response
            classification_data = self._parse_classification_response(response)
            
            # Validate against allowed values
            classification_data = self._validate_classification(classification_data)
            
            return ClassificationResult(**classification_data)
            
        except Exception as e:
            print(f"Classification error: {str(e)}")
            # Return default classification on error
            return ClassificationResult(
                is_educational=False,
                query_type="unknown",
                confidence=0.0
            )
    
    def _build_classification_prompt(self, 
                                    text_input: str, 
                                    image_context: Optional[dict]) -> str:
        prompt = f"""Analyze this student query and classify it:

Query: "{text_input}"
"""
        
        if image_context:
            prompt += f"""
Image Context:
- Contains Math: {image_context.get('contains_math', False)}
- Contains Diagram: {image_context.get('contains_diagram', False)}
- Extracted Text: {image_context.get('extracted_text', 'None')[:200]}
"""
        
        prompt += """
Provide classification in this exact JSON format:
{
    "is_educational": true/false,
    "grade_level": "specific class or level",
    "subject": "subject name",
    "language": "English or Hindi",
    "query_type": "concept_explanation|problem_solving|homework_help|exam_preparation|general_knowledge",
    "topics": ["topic1", "topic2"],
    "complexity": "basic|intermediate|advanced",
    "confidence": 0.0-1.0
}"""
        
        return prompt
    
    def _parse_classification_response(self, response: str) -> dict:
        """Parse LLM response to extract classification data"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Try to parse the entire response as JSON
                return json.loads(response)
        except json.JSONDecodeError:
            # If parsing fails, return minimal classification
            return {
                "is_educational": True,
                "query_type": "general",
                "confidence": 0.5
            }
    
    def _validate_classification(self, classification: dict) -> dict:
        """Validate and correct classification values"""
        
        # Validate grade level
        if classification.get('grade_level'):
            valid_levels = config.EDUCATION_LEVELS
            if classification['grade_level'] not in valid_levels:
                # Try to find closest match
                for level in valid_levels:
                    if level.lower() in classification['grade_level'].lower():
                        classification['grade_level'] = level
                        break
        
        # Validate subject
        if classification.get('subject'):
            valid_subjects = config.SUBJECTS
            if classification['subject'] not in valid_subjects:
                # Try to find closest match
                for subject in valid_subjects:
                    if subject.lower() in classification['subject'].lower():
                        classification['subject'] = subject
                        break
        
        # Validate language
        if classification.get('language') not in config.LANGUAGES:
            classification['language'] = 'English'  # Default to English
        
        # Validate complexity
        if classification.get('complexity') not in ['basic', 'intermediate', 'advanced']:
            classification['complexity'] = 'intermediate'
        
        return classification