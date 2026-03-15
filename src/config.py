import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()


class LLMProvider(Enum):
    CODY = "cody"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GEMINI = "gemini"
    LOCAL = "local"


class Config:
    # App Settings
    APP_NAME = os.getenv("APP_NAME", "LiteEdGPT")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

    # LLM Settings - Default to Cody
    PRIMARY_LLM = os.getenv("PRIMARY_LLM", "cody")

    # Cody Settings (Sourcegraph)
    SRC_ACCESS_TOKEN = os.getenv("SRC_ACCESS_TOKEN", "")
    SRC_ENDPOINT = os.getenv("SRC_ENDPOINT", "https://sourcegraph.sw.nxp.com")
    CODY_MODEL = os.getenv("CODY_MODEL", "anthropic/claude-sonnet-4-20250514")

    # OpenAI Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")

    # Google Gemini Settings
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-flash")

    # Local/Custom Model Settings
    LOCAL_MODEL_ENABLED = os.getenv("LOCAL_MODEL_ENABLED", "false").lower() == "true"
    LOCAL_MODEL_URL = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434")
    LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "llama3")
    LOCAL_MODEL_API_TYPE = os.getenv("LOCAL_MODEL_API_TYPE", "ollama")

    # Legacy Model Names (for backwards compatibility)
    CLASSIFIER_MODEL = os.getenv("CLASSIFIER_MODEL", CODY_MODEL)
    RESPONSE_MODEL = os.getenv("RESPONSE_MODEL", CODY_MODEL)
    VISION_MODEL = os.getenv("VISION_MODEL", GEMINI_VISION_MODEL)

    # Cache Settings
    USE_CACHE = os.getenv("USE_CACHE", "False").lower() == "true"

    # Security
    API_SECRET_KEY = os.getenv("API_SECRET_KEY", "default_secret_key")
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", 30))

    # Supported Education Levels
    EDUCATION_LEVELS = [
        "Class 1",
        "Class 2",
        "Class 3",
        "Class 4",
        "Class 5",
        "Class 6",
        "Class 7",
        "Class 8",
        "Class 9",
        "Class 10",
        "Class 11",
        "Class 12",
        "Undergraduate",
        "Postgraduate",
        "PhD",
    ]

    # Supported Subjects
    SUBJECTS = [
        "Mathematics",
        "Science",
        "Physics",
        "Chemistry",
        "Biology",
        "English",
        "Hindi",
        "History",
        "Geography",
        "Computer Science",
        "Commerce",
        "Economics",
        "Accounting",
        "Business Studies",
        "General Knowledge",
        "Environmental Science",
    ]

    # Supported Languages
    LANGUAGES = ["English", "Hindi"]

    @classmethod
    def get_llm_model(cls) -> str:
        """Get the current LLM model name based on provider"""
        provider = cls.PRIMARY_LLM.lower()
        if provider == "cody":
            return cls.CODY_MODEL
        elif provider in ["gemini", "google"]:
            return cls.GEMINI_MODEL
        elif provider == "openai":
            return cls.OPENAI_MODEL
        elif provider == "local":
            return cls.LOCAL_MODEL_NAME
        return cls.CODY_MODEL


config = Config()
