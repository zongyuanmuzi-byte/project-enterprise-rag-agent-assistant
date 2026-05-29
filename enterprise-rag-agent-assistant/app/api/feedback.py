from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas import FeedbackRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService


router = APIRouter(tags=["Feedback"])

feedback_service = FeedbackService()


@router.post("/feedback", response_model=FeedbackResponse)
def create_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
):
    try:
        result = feedback_service.create_feedback(
            db=db,
            chat_log_id=request.chat_log_id,
            rating=request.rating,
            comment=request.comment,
        )

        return FeedbackResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unknown server error when creating feedback.",
        ) from exc
