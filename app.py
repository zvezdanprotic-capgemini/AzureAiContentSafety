import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai_client import get_llm_response
from content_safety import is_content_safe
from prompt_shield import is_prompt_safe_from_jailbreak

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Vite dev server ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(message: ChatMessage):
    if not message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    # First check: Content Safety
    if not await is_content_safe(message.message):
        return {"response": "⚠️ Your message contains unsafe content and cannot be processed."}
    
    # Second check: Jailbreak Detection
    if not await is_prompt_safe_from_jailbreak(message.message):
        return {"response": "⚠️ Your message appears to be a jailbreak attempt and cannot be processed."}
    
    # If both checks pass, process the message
    response = await get_llm_response(message.message)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
