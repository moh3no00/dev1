"""FastAPI app exposing a /fix endpoint for PHP code patches."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend import analyzer
from backend.model_client import ModelClient

app = FastAPI(title="PHP Fix Service")
model_client = ModelClient()


class FixRequest(BaseModel):
    code: str
    path: str
    context: str


class FixResponse(BaseModel):
    patch: str
    explanation: str
    analysis: list


@app.post("/fix", response_model=FixResponse)
async def fix_code(payload: FixRequest) -> FixResponse:
    try:
        analysis_result = analyzer.run_php_analysis(payload.code, payload.path)
    except analyzer.AnalysisError as exc:  # type: ignore[attr-defined]
        raise HTTPException(status_code=400, detail=str(exc))

    condensed_errors = "\n".join(
        f"[{error['tool']}] {error['message']}" for error in analysis_result.get("errors", [])
    ) or "No errors reported, but a minimal patch was requested."

    patch = model_client.request_patch(
        errors=condensed_errors,
        code=payload.code,
        path=payload.path,
        context=payload.context,
    )

    return FixResponse(
        patch=patch.diff,
        explanation=patch.summary,
        analysis=analysis_result.get("errors", []),
    )
