from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReviewHistory
from app.schemas import HistoryItem, HistoryListResponse, HistoryStatsResponse

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
def list_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    total = db.query(ReviewHistory).count()
    items = (
        db.query(ReviewHistory)
        .order_by(ReviewHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return HistoryListResponse(items=items, total=total)


@router.get("/stats", response_model=HistoryStatsResponse)
def history_stats(db: Session = Depends(get_db)):
    all_items = db.query(ReviewHistory).all()
    reviews = [i for i in all_items if i.review_type == "review" and i.score is not None]
    scores = [i.score for i in reviews if i.score is not None]
    by_language: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for item in all_items:
        by_language[item.language] = by_language.get(item.language, 0) + 1
        by_type[item.review_type] = by_type.get(item.review_type, 0) + 1
    return HistoryStatsResponse(
        total_analyses=len(all_items),
        total_reviews=len(reviews),
        average_score=round(sum(scores) / len(scores), 1) if scores else None,
        by_language=by_language,
        by_type=by_type,
    )


@router.get("/{history_id}", response_model=HistoryItem)
def get_history(history_id: int, db: Session = Depends(get_db)):
    item = db.query(ReviewHistory).filter(ReviewHistory.id == history_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="History item not found")
    return item


@router.delete("/{history_id}")
def delete_history(history_id: int, db: Session = Depends(get_db)):
    item = db.query(ReviewHistory).filter(ReviewHistory.id == history_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="History item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.delete("")
def clear_history(db: Session = Depends(get_db)):
    db.query(ReviewHistory).delete()
    db.commit()
    return {"ok": True}
