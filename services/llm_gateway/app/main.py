"""
LLM Gateway Service for Jarvis
Provides unified interface for multiple LLM providers with fallback support
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging
from openai import OpenAI
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Jarvis LLM Gateway", version="1.0.0")

# Configuration from environment variables
PRIMARY_PROVIDER = os.getenv("PRIMARY_LLM_PROVIDER", "openai")  # openai, ollama
PRIMARY_MODEL = os.getenv("PRIMARY_LLM_MODEL", "gpt-4.1-mini")
FALLBACK_PROVIDER = os.getenv("FALLBACK_LLM_PROVIDER", "ollama")
FALLBACK_MODEL = os.getenv("FALLBACK_LLM_MODEL", "llama3.1")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://llama:11434")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Initialize OpenAI client (works with OpenAI-compatible APIs)
openai_client = OpenAI() if OPENAI_API_KEY else None


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    tools: Optional[List[Dict[str, Any]]] = None


class ChatResponse(BaseModel):
    content: str
    model: str
    provider: str
    finish_reason: str
    usage: Optional[Dict[str, int]] = None


async def call_openai_api(messages: List[Dict], temperature: float, max_tokens: int, tools: Optional[List[Dict]] = None) -> Dict:
    """Call OpenAI or OpenAI-compatible API"""
    try:
        if not openai_client:
            raise ValueError("OpenAI client not initialized - API key missing")
        
        logger.info(f"Calling OpenAI API with model: {PRIMARY_MODEL}")
        
        # Prepare API call parameters
        params = {
            "model": PRIMARY_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if tools:
            params["tools"] = tools
        
        response = openai_client.chat.completions.create(**params)
        
        return {
            "content": response.choices[0].message.content or "",
            "model": response.model,
            "provider": "openai",
            "finish_reason": response.choices[0].finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        }
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise


async def call_ollama_api(messages: List[Dict], temperature: float, max_tokens: int) -> Dict:
    """Call Ollama API"""
    try:
        logger.info(f"Calling Ollama API with model: {FALLBACK_MODEL}")
        
        # Convert messages to Ollama format
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        
        prompt += "Assistant: "
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": FALLBACK_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
        
        return {
            "content": result.get("response", ""),
            "model": FALLBACK_MODEL,
            "provider": "ollama",
            "finish_reason": "stop",
            "usage": None
        }
    except Exception as e:
        logger.error(f"Ollama API error: {str(e)}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "primary_provider": PRIMARY_PROVIDER,
        "primary_model": PRIMARY_MODEL,
        "fallback_provider": FALLBACK_PROVIDER,
        "fallback_model": FALLBACK_MODEL,
        "openai_configured": openai_client is not None
    }


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Unified chat endpoint with automatic fallback
    Tries primary provider first, falls back to secondary on failure
    """
    # Convert Pydantic models to dicts
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # Try primary provider
    try:
        if PRIMARY_PROVIDER == "openai":
            result = await call_openai_api(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=request.tools
            )
            return ChatResponse(**result)
        elif PRIMARY_PROVIDER == "ollama":
            result = await call_ollama_api(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            return ChatResponse(**result)
        else:
            raise ValueError(f"Unknown primary provider: {PRIMARY_PROVIDER}")
    
    except Exception as primary_error:
        logger.warning(f"Primary provider ({PRIMARY_PROVIDER}) failed: {str(primary_error)}")
        logger.info(f"Falling back to {FALLBACK_PROVIDER}")
        
        # Try fallback provider
        try:
            if FALLBACK_PROVIDER == "ollama":
                result = await call_ollama_api(
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
                return ChatResponse(**result)
            elif FALLBACK_PROVIDER == "openai":
                result = await call_openai_api(
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    tools=request.tools
                )
                return ChatResponse(**result)
            else:
                raise ValueError(f"Unknown fallback provider: {FALLBACK_PROVIDER}")
        
        except Exception as fallback_error:
            logger.error(f"Fallback provider ({FALLBACK_PROVIDER}) also failed: {str(fallback_error)}")
            raise HTTPException(
                status_code=503,
                detail=f"All LLM providers failed. Primary: {str(primary_error)}, Fallback: {str(fallback_error)}"
            )


@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "primary": {
            "provider": PRIMARY_PROVIDER,
            "model": PRIMARY_MODEL
        },
        "fallback": {
            "provider": FALLBACK_PROVIDER,
            "model": FALLBACK_MODEL
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
