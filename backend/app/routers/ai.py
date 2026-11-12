"""POST /api/ai: Buddy AI. Builds an injection-safe prompt and asks the configured LLM."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ..schemas import AiRequest, AiResponse
from ..services.llm import LlmClient, LlmNotConfigured, LlmUnavailable
from ..services.prompts import SYSTEM_PROMPT, build_user_message
from .common import rate_limit

router = APIRouter(prefix="/api", tags=["ai"])

NOT_CONFIGURED_MESSAGE = (
    "Buddy AI isn't set up on this server. Set LLM_API_KEY and LLM_MODEL (and LLM_BASE_URL if your provider "
    "is OpenAI-compatible) in the backend .env file, then restart. See .env.example."
)


def get_llm(request: Request) -> LlmClient:
    return request.app.state.llm


@router.post("/ai", response_model=AiResponse, dependencies=[Depends(rate_limit("ai", "asking Buddy AI"))])
async def ask_buddy(body: AiRequest, llm: LlmClient = Depends(get_llm)) -> AiResponse:
    try:
        answer = await llm.complete(SYSTEM_PROMPT, build_user_message(body))
    except LlmNotConfigured:
        raise HTTPException(status_code=503, detail={"code": "ai_not_configured", "message": NOT_CONFIGURED_MESSAGE})
    except LlmUnavailable as exc:
        raise HTTPException(status_code=exc.http_status, detail={"code": exc.code, "message": exc.message})
    return AiResponse(mode=body.mode, answer=answer, model=llm.settings.llm_model)
