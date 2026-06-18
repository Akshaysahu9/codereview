from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class ReviewHistory(Base):
    __tablename__ = "review_history"

    id = Column(Integer, primary_key=True, index=True)
    language = Column(String(32), nullable=False)
    code_snippet = Column(Text, nullable=False)
    title = Column(String(255), nullable=True)
    review_type = Column(String(32), nullable=False, default="review")
    result_json = Column(Text, nullable=False)
    score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
