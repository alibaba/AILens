"""Trace API router."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..tracing.models import Trace, TraceSearchResult
from ..tracing.registry import get_trace_provider

router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("/search", response_model=List[TraceSearchResult])
async def search_traces(
    start_time: int = Query(..., description="Start time (millisecond timestamp)"),
    end_time: int = Query(..., description="End time (millisecond timestamp)"),
    service_name: Optional[str] = Query(None),
    operation_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
) -> List[TraceSearchResult]:
    """
    Search trace list.
    """
    try:
        trace_provider = get_trace_provider(provider)
        return await trace_provider.search_traces(
            start_time=start_time,
            end_time=end_time,
            service_name=service_name,
            operation_name=operation_name,
            status=status,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{trace_id}/url")
async def get_trace_url(
    trace_id: str,
    provider: Optional[str] = Query(None),
) -> dict:
    """
    Get trace external view URL.
    """
    try:
        trace_provider = get_trace_provider(provider)
        return {
            "trace_id": trace_id,
            "url": trace_provider.get_trace_url(trace_id),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{trace_id}", response_model=Trace)
async def get_trace(
    trace_id: str,
    provider: Optional[str] = Query(None, description="Trace provider name"),
) -> Trace:
    """
    Get trace details.
    """
    try:
        trace_provider = get_trace_provider(provider)
        trace = await trace_provider.get_trace(trace_id)

        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")

        return trace
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
