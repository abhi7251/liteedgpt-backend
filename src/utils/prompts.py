class PromptTemplates:
    """Collection of prompt templates for different scenarios"""
    
    @staticmethod
    def get_math_template(grade_level: str) -> str:
        return f"""
        As a mathematics tutor for {grade_level} students:
        1. Show clear step-by-step solutions
        2. Use appropriate mathematical notation
        3. Explain the reasoning behind each step
        4. Provide the final answer clearly
        5. Suggest similar practice problems
        """
    
    @staticmethod
    def get_science_template(grade_level: str, topic: str) -> str:
        return f"""
        As a science tutor for {grade_level} students explaining {topic}:
        1. Start with fundamental concepts
        2. Use real-world examples and applications
        3. Include relevant scientific principles
        4. Explain cause and effect relationships
        5. Suggest hands-on experiments if applicable
        """
    
    @staticmethod
    def get_language_template(language: str, skill: str) -> str:
        return f"""
        As a {language} language tutor focusing on {skill}:
        1. Provide clear grammar rules
        2. Give multiple examples in context
        3. Include common usage patterns
        4. Point out common mistakes to avoid
        5. Suggest practice exercises
        """
    
    @staticmethod
    def get_non_educational_response() -> str:
        return """
        I'm LiteEdGPT, an educational assistant designed to help students with their academic queries. 
        
        I can assist you with:
        📚 Academic subjects (Math, Science, English, Hindi, etc.)
        📝 Homework help and problem-solving
        🎓 Concept explanations for all grade levels
        📖 Exam preparation and study tips
        🔬 Educational projects and research
        
        Please ask me an education-related question, and I'll be happy to help!
        """