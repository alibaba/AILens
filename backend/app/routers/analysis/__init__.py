"""Analysis endpoints - Modular structure.

All endpoints are prefixed with /experiments/{experiment_id}/analysis
"""

from fastapi import APIRouter

from .cross_analysis import router as cross_analysis_router
from .extreme_cases import router as extreme_cases_router
from .languages import router as languages_router
from .pass_rate_diff import router as pass_rate_diff_router
from .repetition import router as repetition_router
from .scaffold import router as scaffold_router
from .task_difficulty import router as task_difficulty_router
from .tool_schemas import router as tool_schemas_router

router = APIRouter(
    prefix="/experiments/{experiment_id}/analysis",
    tags=["analysis"],
)

# Include all sub-routers
router.include_router(languages_router)
router.include_router(scaffold_router)
router.include_router(tool_schemas_router)
router.include_router(pass_rate_diff_router)
router.include_router(cross_analysis_router)
router.include_router(task_difficulty_router)
router.include_router(repetition_router)
router.include_router(extreme_cases_router)
