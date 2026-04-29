"""/tool-schemas endpoint - Return distinct tool_schema values.

Python 3.6.8 compatible.
"""

from fastapi import APIRouter, Depends

from ...repositories.base import ExperimentRepository
from ...repositories.dependencies import get_experiment_repo
from .helpers import check_experiment_exists, query_traceql_distinct

router = APIRouter(
    tags=["analysis"],
)


@router.get("/tool-schemas")
async def analysis_tool_schemas(
    experiment_id: str,
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
):
    """Return distinct tool_schema values for the given experiment."""
    check_experiment_exists(experiment_id, exp_repo)
    schemas = await query_traceql_distinct(experiment_id, "tool_schema")
    return {"tool_schemas": schemas}
