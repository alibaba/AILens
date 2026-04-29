"""Proxy router — forwards TraceQL View queries to external service."""

import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/trace", tags=["trace"])


class TraceQueryRequest(BaseModel):
    query: str
    page_size: int = 1000
    page_num: int = 1
    start: Optional[int] = None
    end: Optional[int] = None


@router.post("/query")
async def proxy_trace_query(request: TraceQueryRequest) -> Dict[str, Any]:
    """Proxy TraceQL query to external service, enforcing scope=rl."""
    base_url = os.environ.get("TRACEQL_BASE_URL", "")
    if not base_url:
        raise HTTPException(status_code=503, detail="TRACEQL_BASE_URL not configured")
    auth_key = os.environ.get("TRACEQL_AUTH_KEY", "")

    payload: Dict[str, Any] = {
        "query": request.query,
        "page_size": request.page_size,
        "page_num": request.page_num,
        "scope": "rl",
    }
    if request.start is not None:
        payload["start"] = request.start
    if request.end is not None:
        payload["end"] = request.end

    try:
        async with httpx.AsyncClient() as client:
            params = {"authKey": auth_key} if auth_key else {}
            response = await client.post(
                f"{base_url}/api/v1/trace/query",
                json=payload,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"External TraceQL service error: {exc.response.text[:200]}",
        ) from exc
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="External TraceQL service unavailable")
