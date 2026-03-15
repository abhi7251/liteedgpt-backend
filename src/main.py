from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
import asyncio
from datetime import datetime
from src.agents.orchestrator import AgentOrchestrator
from src.utils.validators import Validators
from src.config import config

# Initialize FastAPI app
app = FastAPI(
    title="LiteEdGPT API",
    description="Multi-agent Educational Assistant System",
    version=config.APP_VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = AgentOrchestrator()

# Rate limiting storage (simple in-memory for now)
rate_limit_storage = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware"""
    client_ip = request.client.host
    current_time = datetime.now()
    
    # Clean old entries
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage.get(client_ip, [])
        if (current_time - timestamp).seconds < 60
    ]
    
    # Check rate limit
    if len(rate_limit_storage.get(client_ip, [])) >= config.MAX_REQUESTS_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Please wait before making more requests."}
        )
    
    # Add current request
    if client_ip not in rate_limit_storage:
        rate_limit_storage[client_ip] = []
    rate_limit_storage[client_ip].append(current_time)
    
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "status": "operational",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": config.APP_NAME,
        "version": config.APP_VERSION
    }

@app.post("/api/chat")
async def chat(
    text: str = Form(...),
    image: Optional[UploadFile] = File(None),
    user_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None)
):
    """
    Main chat endpoint for processing educational queries
    
    Parameters:
    - text: The text query from the student
    - image: Optional image file (homework, diagram, etc.)
    - user_id: Optional user identifier for context
    - session_id: Optional session identifier for conversation continuity
    """
    
    try:
        # Validate text input
        is_valid, error_message = Validators.validate_text_input(text)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Sanitize text input
        text = Validators.sanitize_input(text)
        
        # Process image if provided
        image_data = None
        if image:
            # Read image data
            image_data = await image.read()
            
            # Validate image
            is_valid, error_message = Validators.validate_image(image_data)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_message)
        
        # Process request through orchestrator
        response = await orchestrator.process_request(
            text_input=text,
            image_data=image_data,
            user_id=user_id,
            session_id=session_id,
            api_key=api_key
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[LiteEdGPT] Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your request. Please try again."
        )

@app.post("/api/feedback")
async def submit_feedback(
    session_id: str = Form(...),
    rating: int = Form(...),
    feedback: Optional[str] = Form(None)
):
    """Submit feedback for a response"""
    
    # Validate rating
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Log feedback (implement actual storage as needed)
    feedback_data = {
        "session_id": session_id,
        "rating": rating,
        "feedback": feedback,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"[Feedback] {feedback_data}")
    
    return {"success": True, "message": "Thank you for your feedback!"}

if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════╗
    ║         LiteEdGPT Server             ║
    ║     Educational Assistant System      ║
    ╚══════════════════════════════════════╝
    
    Version: {config.APP_VERSION}
    Debug Mode: {config.DEBUG_MODE}
    Primary LLM: {config.PRIMARY_LLM}
    
    Starting server...
    """)
    
    uvicorn.run(
        "src.main:app",  # Changed from "main:app" to "src.main:app"
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG_MODE,
        log_level="info" if config.DEBUG_MODE else "error"
    )