from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models import ChatLog, Feedback
from app.utils.logger import get_logger


logger = get_logger(__name__)


class FeedbackService:
    """
    Service for writing user feedback for a chat log.
    """

    def create_feedback(
        self,
        db: Session,
        chat_log_id: int,
        rating: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        chat_log = db.get(ChatLog, chat_log_id)

        if chat_log is None:
            raise ValueError(f"chat_log_id does not exist: {chat_log_id}")

        feedback = Feedback(
            chat_log_id=chat_log_id,
            rating=rating,
            comment=comment,
        )

        try:
            db.add(feedback)
            db.commit()
            db.refresh(feedback)

        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception(
                "Failed to create feedback | chat_log_id=%s | rating=%s",
                chat_log_id,
                rating,
            )
            raise RuntimeError("Failed to create feedback.") from exc

        logger.info(
            "Feedback created | feedback_id=%s | chat_log_id=%s | rating=%s",
            feedback.id,
            chat_log_id,
            rating,
        )

        return {
            "feedback_id": feedback.id,
            "chat_log_id": feedback.chat_log_id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "status": "created",
        }
