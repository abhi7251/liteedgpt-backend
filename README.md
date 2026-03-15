# 🎓 LiteEdGPT - Multi-Agent Educational Assistant

<div align="center">

![LiteEdGPT Logo](https://img.shields.io/badge/LiteEdGPT-Educational%20AI-blue?style=for-the-badge&logo=robot&logoColor=white)

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Cody](https://img.shields.io/badge/Cody-Sourcegraph-FF6B6B?style=flat-square&logo=sourcegraph&logoColor=white)](https://sourcegraph.com/cody)

**An intelligent, multi-agent educational assistant system that helps students learn effectively.**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [API Docs](#-api-documentation) • [Configuration](#-configuration)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Multi-Agent System](#-multi-agent-system)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Server](#-running-the-server)
- [API Documentation](#-api-documentation)
- [LLM Providers](#-llm-providers)
- [Future Enhancements](#-future-enhancements)

---

## 🎯 Overview

**LiteEdGPT** is a multi-agent educational assistant system designed to help students from Class 1 to PhD level with their academic queries. The system uses advanced AI models to:

- Understand and classify educational queries
- Detect subject, grade level, and complexity
- Generate tailored, age-appropriate responses
- Support multiple languages (English & Hindi)
- Process images (diagrams, homework, classwork etc.)

### Why LiteEdGPT?

| Problem                  | LiteEdGPT Solution                            |
| ------------------------ | --------------------------------------------- |
| Generic AI responses     | Tailored responses based on grade level       |
| One-size-fits-all        | Adapts complexity to student level            |
| No context understanding | Multi-agent classification system             |
| Single LLM dependency    | Multi-provider support (Cody, Gemini, OpenAI) |

---

## ✨ Features

### Core Features

| Feature                     | Description                                   |
| --------------------------- | --------------------------------------------- |
| 🤖 **Multi-Agent System**   | Classifier + Response agents working together |
| 📚 **Educational Focus**    | Specialized for academic queries              |
| 🎯 **Smart Classification** | Auto-detects subject, grade level, complexity |
| 🌐 **Multi-Language**       | Supports English and Hindi                    |
| 📷 **Image Support**        | Process homework photos, diagrams             |
| 🔄 **Multi-Provider LLM**   | Cody, Gemini, OpenAI, Local models            |
| 💾 **Session Memory**       | Maintains conversation context                |
| ⚡ **Rate Limiting**        | Built-in request throttling                   |
| 📝 **Markdown Responses**   | Well-formatted, readable answers              |

### Educational Capabilities

| Capability       | Supported Levels                                                                                                      |
| ---------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Grade Levels** | Class 1-12, Undergraduate, Postgraduate, PhD                                                                          |
| **Subjects**     | Math, Science, Physics, Chemistry, Biology, English, Hindi, History, Geography, Computer Science, Commerce, Economics |
| **Query Types**  | Concept Explanation, Problem Solving, Homework Help, Exam Preparation                                                 |
| **Complexity**   | Basic, Intermediate, Advanced                                                                                         |

---

## 🏗 Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│              (Android App / Web App / API Client)               │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP/HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                               │
│                    FastAPI Application                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   /api/chat │  │   /health   │  │   /api/feedback         │ │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘ │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR LAYER                           │
│                   AgentOrchestrator                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Processing Pipeline                    │  │
│  │  ┌─────────┐   ┌─────────────┐   ┌──────────────────┐   │  │
│  │  │ Image   │ → │ Classifier  │ → │ Response Agent   │   │  │
│  │  │ Service │   │ Agent       │   │                  │   │  │
│  │  └─────────┘   └─────────────┘   └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ LLM Service │  │ Cache       │  │ Image Service           │ │
│  │ (Factory)   │  │ Service     │  │                         │ │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘ │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM PROVIDERS                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐   │
│  │  Cody   │  │ Gemini  │  │ OpenAI  │  │ Local (Ollama)  │   │
│  │(Default)│  │         │  │         │  │                 │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
1. User sends query (text + optional image)
                    ↓
2. FastAPI receives request at /api/chat
                    ↓
3. Validators sanitize and validate input
                    ↓
4. Orchestrator begins pipeline:
   │
   ├─→ Step 1: Image Processing (if image provided)
   │            Extract metadata, compress if needed
   │
   ├─→ Step 2: Classification
   │            - Is it educational?
   │            - What subject?
   │            - What grade level?
   │            - What language?
   │            - What type of query?
   │            - Complexity level?
   │
   └─→ Step 3: Response Generation
                - Build system prompt based on classification
                - Generate tailored response
                - Format with markdown
                - Add helpful footer
                    ↓
5. Return JSON response with metadata
```

---

## 🤖 Multi-Agent System

### Why Multi-Agent?

| Single Agent           | Multi-Agent (LiteEdGPT)      |
| ---------------------- | ---------------------------- |
| One prompt for all     | Specialized prompts per task |
| Generic responses      | Context-aware responses      |
| No query understanding | Deep query classification    |
| Hard to maintain       | Modular, maintainable        |

### Agent Descriptions

#### 1. Classifier Agent (`classifier_agent.py`)

**Purpose:** Analyze and classify incoming queries

**Responsibilities:**

- Determine if query is educational
- Identify subject area
- Detect grade level
- Recognize language preference
- Categorize query type
- Assess complexity level
- Calculate confidence score

**Output:**

```python
ClassificationResult(
    is_educational=True,
    subject="Biology",
    grade_level="Class 6",
    language="English",
    query_type="concept_explanation",
    topics=["photosynthesis", "plants"],
    complexity="basic",
    confidence=0.95
)
```

#### 2. Response Agent (`response_agent.py`)

**Purpose:** Generate tailored educational responses

**Responsibilities:**

- Build system prompt based on classification
- Adapt language and complexity
- Follow query-type specific guidelines
- Format response with markdown
- Add helpful footers and tips

**Prompt Customization:**

```
Classification → System Prompt
─────────────────────────────────
Grade: Class 6  → Simple language, basic examples
Subject: Math   → Show step-by-step, include formulas
Type: Homework  → Guide, don't give direct answers
Language: Hindi → Respond in Hindi
```

#### 3. Orchestrator (`orchestrator.py`)

**Purpose:** Coordinate all agents and services

**Responsibilities:**

- Manage request pipeline
- Route to appropriate agents
- Maintain conversation history
- Handle errors gracefully
- Measure processing time

---

## 🛠 Technology Stack

### Core Framework

| Technology   | Version | Why We Chose It                                  |
| ------------ | ------- | ------------------------------------------------ |
| **Python**   | 3.9+    | Industry standard for AI/ML, extensive libraries |
| **FastAPI**  | 0.100+  | Modern, fast, async support, auto-documentation  |
| **Pydantic** | 2.0+    | Data validation, type hints, serialization       |
| **Uvicorn**  | 0.23+   | ASGI server, high performance, async             |

### Why FastAPI over Flask/Django?

| Feature         | FastAPI     | Flask      | Django     |
| --------------- | ----------- | ---------- | ---------- |
| Async Support   | ✅ Native   | ⚠️ Limited | ⚠️ Limited |
| Auto API Docs   | ✅ Built-in | ❌ Manual  | ❌ Manual  |
| Type Validation | ✅ Pydantic | ❌ Manual  | ⚠️ Forms   |
| Performance     | ⭐⭐⭐      | ⭐⭐       | ⭐         |
| Learning Curve  | Easy        | Easy       | Medium     |

### LLM Integration

| Provider   | Library/Method        | Why                                   |
| ---------- | --------------------- | ------------------------------------- |
| **Cody**   | CLI (`cody chat`)     | Enterprise Sourcegraph, Claude models |
| **Gemini** | `google-generativeai` | Free tier, good performance           |
| **OpenAI** | `openai`              | Industry standard, GPT-4              |
| **Local**  | HTTP API              | Privacy, no API costs                 |

### Why Cody as Default?

1. **Enterprise Ready** - Sourcegraph integration
2. **Claude Models** - State-of-the-art AI
3. **No API Costs** - Uses existing Sourcegraph license
4. **Secure** - On-premise deployment option

### Additional Libraries

| Library         | Purpose                              |
| --------------- | ------------------------------------ |
| `python-dotenv` | Environment variable management      |
| `Pillow`        | Image processing                     |
| `aiohttp`       | Async HTTP client (for local models) |

---

## 📁 Project Structure

```
LiteEdGPT/
├── backend/
│   ├── .env                    # Environment configuration
│   ├── requirements.txt        # Python dependencies
│   ├── README.md              # This documentation
│   │
│   └── src/
│       ├── __init__.py
│       ├── main.py            # FastAPI application entry point
│       ├── config.py          # Configuration management
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── orchestrator.py      # Main pipeline coordinator
│       │   ├── classifier_agent.py  # Query classification
│       │   └── response_agent.py    # Response generation
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── llm_service.py       # Multi-provider LLM service
│       │   ├── cache_service.py     # In-memory caching
│       │   └── image_service.py     # Image processing
│       │
│       └── utils/
│           ├── __init__.py
│           ├── validators.py        # Input validation
│           └── prompts.py           # Prompt templates
│
├── venv/                       # Virtual environment
├── setup.bat                   # Windows setup script
├── start_server.bat            # Server startup script
└── run.bat                     # Quick run script
```

### File Descriptions

| File                  | Purpose              | Key Components                   |
| --------------------- | -------------------- | -------------------------------- |
| `main.py`             | API entry point      | FastAPI app, routes, middleware  |
| `config.py`           | Configuration        | Environment variables, constants |
| `orchestrator.py`     | Pipeline coordinator | Multi-agent orchestration        |
| `classifier_agent.py` | Query analysis       | Classification logic             |
| `response_agent.py`   | Response generation  | Prompt building, formatting      |
| `llm_service.py`      | LLM abstraction      | Cody, Gemini, OpenAI, Local      |
| `cache_service.py`    | Caching              | In-memory response cache         |
| `image_service.py`    | Image handling       | Processing, compression          |
| `validators.py`       | Input validation     | Sanitization, security           |
| `prompts.py`          | Prompt templates     | Reusable prompt patterns         |

---

## 🚀 Installation

### Prerequisites

| Requirement | Version | Check Command                   |
| ----------- | ------- | ------------------------------- |
| Python      | 3.9+    | `python --version`              |
| pip         | Latest  | `pip --version`                 |
| Node.js     | 16+     | `node --version` (for Cody CLI) |
| npm         | 8+      | `npm --version` (for Cody CLI)  |

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/LiteEdGPT.git
cd LiteEdGPT
```

### Step 2: Run Setup Script (Windows)

```bash
setup.bat
```

Or manually:

```bash
python -m venv venv
```

```bash
venv\Scripts\activate
```

```bash
pip install -r backend/requirements.txt
```

### Step 3: Install Cody CLI (for Cody provider)

```bash
npm install -g @sourcegraph/cody
```

### Step 4: Authenticate Cody

```bash
set SRC_ENDPOINT=https://sourcegraph.sw.nxp.com
```

```bash
cody auth login
```

### Step 5: Configure Environment

Copy and edit the `.env` file:

```bash
copy backend\.env.example backend\.env
```

Edit `backend/.env` with your credentials.

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# ============================================================================
# LiteEdGPT Configuration
# ============================================================================

# App Settings
APP_NAME=LiteEdGPT
APP_VERSION=1.0.0
DEBUG_MODE=True

# ============================================================================
# LLM Provider Selection
# Options: cody, gemini, openai, local
# ============================================================================
PRIMARY_LLM=cody

# ============================================================================
# CODY Configuration (Sourcegraph)
# ============================================================================
SRC_ACCESS_TOKEN=your_sourcegraph_token
SRC_ENDPOINT=https://sourcegraph.sw.nxp.com
CODY_MODEL=anthropic::2024-10-22::claude-sonnet-4-5-latest

# ============================================================================
# Google Gemini Configuration
# ============================================================================
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-1.5-flash
GEMINI_VISION_MODEL=gemini-1.5-flash

# ============================================================================
# OpenAI Configuration
# ============================================================================
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o

# ============================================================================
# Local Model Configuration (Ollama, LM Studio, etc.)
# ============================================================================
LOCAL_MODEL_ENABLED=false
LOCAL_MODEL_URL=http://localhost:11434
LOCAL_MODEL_NAME=llama3
LOCAL_MODEL_API_TYPE=ollama

# ============================================================================
# Security & Rate Limiting
# ============================================================================
API_SECRET_KEY=your_secret_key
MAX_REQUESTS_PER_MINUTE=30

# ============================================================================
# Cache Settings
# ============================================================================
USE_CACHE=False
```

### Available Cody Models

| Model                                             | Description                     |
| ------------------------------------------------- | ------------------------------- |
| `anthropic::2024-10-22::claude-sonnet-4-5-latest` | Claude Sonnet 4.5 (Recommended) |
| `anthropic::2024-10-22::claude-opus-4-5-latest`   | Claude Opus 4.5 (Most powerful) |
| `anthropic::2024-10-22::claude-haiku-4-5-latest`  | Claude Haiku 4.5 (Fastest)      |

### Switching LLM Providers

```env
# Use Cody (default)
PRIMARY_LLM=cody

# Use Google Gemini
PRIMARY_LLM=gemini

# Use OpenAI
PRIMARY_LLM=openai

# Use Local Model
PRIMARY_LLM=local
```

---

## 🏃 Running the Server

### Option 1: Using Batch Script (Windows)

```bash
start_server.bat
```

### Option 2: Manual Run

```bash
cd backend
```

```bash
..\venv\Scripts\activate
```

```bash
python -m src.main
```

### Expected Output

```
╔══════════════════════════════════════╗
║         LiteEdGPT Server             ║
║     Educational Assistant System      ║
╚══════════════════════════════════════╝

Version: 1.0.0
Debug Mode: True
Primary LLM: cody

Starting server...

[LiteEdGPT] Initializing Agent Orchestrator...
[LiteEdGPT] Creating CODY service...
[LiteEdGPT] Cody Service initialized
[LiteEdGPT] Endpoint: https://sourcegraph.sw.nxp.com
[LiteEdGPT] Model: anthropic::2024-10-22::claude-sonnet-4-5-latest
[LiteEdGPT] All agents loaded successfully
[LiteEdGPT] Multi-Agent System: ENABLED

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Access Points

| URL                          | Description                       |
| ---------------------------- | --------------------------------- |
| http://localhost:8000        | Root endpoint                     |
| http://localhost:8000/docs   | Swagger UI (Interactive API docs) |
| http://localhost:8000/health | Health check                      |
| http://localhost:8000/redoc  | ReDoc documentation               |

---

## 📡 API Documentation

### Endpoints Overview

| Method | Endpoint        | Description        |
| ------ | --------------- | ------------------ |
| GET    | `/`             | Root info          |
| GET    | `/health`       | Health check       |
| POST   | `/api/chat`     | Main chat endpoint |
| POST   | `/api/feedback` | Submit feedback    |

### POST `/api/chat`

**Description:** Process educational query through multi-agent pipeline

**Request:**

```
Content-Type: multipart/form-data

Parameters:
- text (required): string - The educational query
- image (optional): file - Image file (homework, diagram)
- user_id (optional): string - User identifier
- session_id (optional): string - Session for conversation continuity
```

**Example Request (cURL):**

```bash
curl -X POST http://localhost:8000/api/chat \
  -F "text=Explain photosynthesis for a Class 6 student"
```

**Example Request (with image):**

```bash
curl -X POST http://localhost:8000/api/chat \
  -F "text=Solve this math problem" \
  -F "image=@homework.jpg"
```

**Success Response:**

```json
{
  "success": true,
  "message": "# Photosynthesis\n\n**Photosynthesis** is the process by which plants...\n\n---\n💡 **Tip:** Try explaining this concept to someone else!",
  "type": "educational_response",
  "metadata": {
    "has_image": false,
    "user_id": null,
    "session_id": null,
    "timestamp": "2024-01-15T10:30:00.000000",
    "pipeline": "multi-agent",
    "classification": {
      "is_educational": true,
      "subject": "Biology",
      "grade_level": "Class 6",
      "language": "English",
      "query_type": "concept_explanation",
      "complexity": "basic",
      "confidence": 0.95
    }
  },
  "processing_time": 5.23
}
```

**Non-Educational Response:**

```json
{
  "success": false,
  "message": "I'm **LiteEdGPT**, an educational assistant...",
  "type": "non_educational",
  "metadata": {
    "pipeline": "multi-agent",
    "classification": {
      "is_educational": false,
      ...
    }
  }
}
```

### GET `/health`

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000",
  "service": "LiteEdGPT",
  "version": "1.0.0"
}
```

### POST `/api/feedback`

**Request:**

```
Content-Type: multipart/form-data

Parameters:
- session_id (required): string
- rating (required): integer (1-5)
- feedback (optional): string
```

**Response:**

```json
{
  "success": true,
  "message": "Thank you for your feedback!"
}
```

---

## 🔌 LLM Providers

### Provider Comparison

| Feature     | Cody               | Gemini    | OpenAI        | Local     |
| ----------- | ------------------ | --------- | ------------- | --------- |
| **Cost**    | Enterprise license | Free tier | Pay per token | Free      |
| **Speed**   | Fast               | Fast      | Medium        | Varies    |
| **Quality** | Excellent          | Good      | Excellent     | Varies    |
| **Privacy** | Enterprise         | Cloud     | Cloud         | Full      |
| **Vision**  | ❌                 | ✅        | ✅            | ✅ (some) |

### Adding a New Provider

1. Create a new class extending `BaseLLMService`:

```python
class MyProviderService(BaseLLMService):
    def __init__(self):
        # Initialize your provider
        pass

    async def generate(self, prompt, system_prompt=None,
                       temperature=0.7, max_tokens=2000):
        # Implement generation
        pass

    async def generate_with_image(self, prompt, image_data,
                                   system_prompt=None):
        # Implement vision capability
        pass
```

2. Register in `LLMServiceFactory`:

```python
PROVIDERS = {
    "cody": CodyService,
    "gemini": GeminiService,
    "openai": OpenAIService,
    "local": LocalModelService,
    "myprovider": MyProviderService,  # Add here
}
```

---

## 🔮 Future Enhancements

### Planned Features

| Feature           | Priority | Status         |
| ----------------- | -------- | -------------- |
| Android App       | High     | 🔄 In Progress |
| iOS App           | Medium   | 📋 Planned     |
| Web Frontend      | Medium   | 📋 Planned     |
| Voice Input       | Low      | 📋 Planned     |
| PDF Processing    | Medium   | 📋 Planned     |
| Quiz Generation   | Medium   | 📋 Planned     |
| Progress Tracking | Low      | 📋 Planned     |
| Multi-turn Memory | Medium   | 📋 Planned     |
| Redis Caching     | Low      | 📋 Planned     |

### Potential Improvements

- [ ] Add more subjects (Law, Medicine, Arts)
- [ ] Support more languages
- [ ] Implement streaming responses
- [ ] Add authentication/user accounts
- [ ] Create admin dashboard
- [ ] Add analytics and logging
- [ ] Implement RAG for textbook content

---

## 📝 License

MIT License - See LICENSE file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📞 Support

- **Issues:** GitHub Issues
- **Email:** your-email@example.com

---

<div align="center">

**Made with ❤️ for Students**

[⬆ Back to Top](#-liteedgpt---multi-agent-educational-assistant)

</div>
