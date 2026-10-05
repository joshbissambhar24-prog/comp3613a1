import logging

from sqlmodel import Session, select

from app.models.presentation import Presentation
from app.models.review import Review
from app.models.submission import Submission
from app.models.user import User

logger = logging.getLogger(__name__)


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_submission(self, submission_id: int) -> Submission | None:
        return self.db.get(Submission, submission_id)

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def list_submissions_to_review(self) -> list[tuple[Submission, User]]:
        statement = (
            select(Submission, User)
            .join(User, Submission.student_id == User.id)
            .where(Submission.status.in_(("Pending", "Requires Changes")))
            .order_by(Submission.submitted_at.asc())
        )
        return list(self.db.exec(statement).all())

    def list_review_history(self, submission_id: int) -> list[tuple[Review, User]]:
        statement = (
            select(Review, User)
            .join(User, Review.reviewer_id == User.id)
            .where(Review.submission_id == submission_id)
            .order_by(Review.reviewed_at.desc())
        )
        return list(self.db.exec(statement).all())

    def save_review(
        self,
        review: Review,
        submission: Submission,
        presentation: Presentation | None,
    ) -> Review:
        try:
            existing_presentation = self.db.exec(
                select(Presentation).where(
                    Presentation.submission_id == submission.id
                )
            ).one_or_none()

            if presentation is not None:
                if existing_presentation is None:
                    self.db.add(presentation)
                else:
                    existing_presentation.presentation_date = (
                        presentation.presentation_date
                    )
                    existing_presentation.presentation_time = (
                        presentation.presentation_time
                    )
                    existing_presentation.location = presentation.location
                    self.db.add(existing_presentation)
            elif submission.status != "Accepted" and existing_presentation is not None:
                self.db.delete(existing_presentation)

            self.db.add(submission)
            self.db.add(review)
            self.db.commit()
            self.db.refresh(review)
            return review
        except Exception:
            logger.exception("An error occurred while saving a review")
            self.db.rollback()
            raise
