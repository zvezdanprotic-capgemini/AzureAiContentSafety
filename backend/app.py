import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .env import load_env, validate_required_env

load_env()
validate_required_env()

from .content_safety import is_content_safe
from .openai_client import get_llm_response
from .pii_protection import restore_pii
from .prompt_shield import is_prompt_safe_from_jailbreak

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Vite dev server ports
    allow_origins=["*"],  # Vite dev server ports
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

    # Collect PII mappings from all safety checks
    combined_pii_mapping = {}

    # First check: Content Safety (with PII masking)
    is_safe, pii_mapping_content = await is_content_safe(message.message)
    combined_pii_mapping.update(pii_mapping_content)
    
    if not is_safe:
        return {"response": "⚠️ Your message contains unsafe content and cannot be processed."}

    # Second check: Jailbreak Detection (with PII masking)
    is_safe_jailbreak, pii_mapping_jailbreak = await is_prompt_safe_from_jailbreak(message.message)
    combined_pii_mapping.update(pii_mapping_jailbreak)
    
    if not is_safe_jailbreak:
        return {"response": "⚠️ Your message appears to be a jailbreak attempt and cannot be processed."}

    # If both checks pass, process the message
    # Note: We send the original message (with PII) to the LLM for better context
    # The LLM is Azure OpenAI which has appropriate data handling policies
    response = await get_llm_response(message.message)
    
    # If the response contains any PII placeholders (unlikely but possible),
    # restore them. This would happen if the safety APIs returned messages
    # that included the placeholders.
    if combined_pii_mapping:
        response = restore_pii(response, combined_pii_mapping)
    
    return {"response": response}


@app.get("/api/health")
async def health():
    """Health check endpoint to verify the app is running."""

    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
