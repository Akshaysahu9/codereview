from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReviewHistory
from app.schemas import (
    ExplainRequest,
    ExplainResponse,
    FixCodeRequest,
    FixCodeResponse,
    GenerateTestsRequest,
    GenerateTestsResponse,
    ReviewRequest,
    ReviewResponse,
)
from app.services.review_service import review_to_json, run_review
from app.services.tool_service import tool_service

router = APIRouter(prefix="/api", tags=["review"])


def _save_history(db: Session, request, review_type: str, result_json: str, score: int | None = None):
    entry = ReviewHistory(
        language=request.language.value if hasattr(request.language, "value") else request.language,
        code_snippet=request.code[:10000],
        title=getattr(request, "title", None),
        review_type=review_type,
        result_json=result_json,
        score=score,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/review", response_model=ReviewResponse)
async def review_code(request: ReviewRequest, db: Session = Depends(get_db)):
    result = await run_review(request)
    _save_history(db, request, "review", review_to_json(result), result.score)
    return result


@router.post("/explain", response_model=ExplainResponse)
async def explain_code(request: ExplainRequest, db: Session = Depends(get_db)):
    result = await tool_service.explain_code(request.code, request.language, request.focus)
    _save_history(db, request, "explain", result.model_dump_json())
    return result


@router.post("/generate-tests", response_model=GenerateTestsResponse)
async def generate_tests(request: GenerateTestsRequest, db: Session = Depends(get_db)):
    result = await tool_service.generate_tests(request.code, request.language, request.framework)
    _save_history(db, request, "tests", result.model_dump_json())
    return result


@router.post("/fix", response_model=FixCodeResponse)
async def fix_code(request: FixCodeRequest, db: Session = Depends(get_db)):
    result = await tool_service.fix_code(request.code, request.language, request.issues)
    _save_history(db, request, "fix", result.model_dump_json())
    return result
