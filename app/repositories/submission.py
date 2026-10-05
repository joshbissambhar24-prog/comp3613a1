import logging

from sqlmodel import Session, select

from app.models.presentation import Presentation
from app.models.review import Review
from app.models.submission import Submission

logger = logging.getLogger(__name__)


class SubmissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, submission: Submission) -> Submission:
        try:
            self.db.add(submission)
            self.db.commit()
            self.db.refresh(submission)
            return submission
        except Exception:
            logger.exception("An error occurred while saving a submission")
            self.db.rollback()
            raise

    def get_by_id(self, submission_id: int) -> Submission | None:
        return self.db.get(Submission, submission_id)

    def list_by_student(self, student_id: int) -> list[Submission]:
        statement = (
            select(Submission)
            .where(Submission.student_id == student_id)
            .order_by(Submission.submitted_at.desc())
        )
        return list(self.db.exec(statement).all())

    def list_tracking_cards_by_student(
        self,
        student_id: int,
    ) -> list[tuple[Submission, Review | None, Presentation | None]]:
        submissions = self.list_by_student(student_id)
        if not submissions:
            return []

        submission_ids = [
            submission.id
            for submission in submissions
            if submission.id is not None
        ]
        reviews = self.db.exec(
            select(Review)
            .where(Review.submission_id.in_(submission_ids))
            .order_by(
                Review.submission_id,
                Review.reviewed_at.desc(),
                Review.id.desc(),
            )
        ).all()
        latest_reviews: dict[int, Review] = {}
        for review in reviews:
            latest_reviews.setdefault(review.submission_id, review)

        presentations = self.db.exec(
            select(Presentation).where(
                Presentation.submission_id.in_(submission_ids)
            )
        ).all()
        current_presentations = {
            presentation.submission_id: presentation
            for presentation in presentations
        }
        return [
            (
                submission,
                latest_reviews.get(submission.id),
                current_presentations.get(submission.id),
            )
            for submission in submissions
        ]

    def update(self, submission: Submission) -> Submission:
        try:
            self.db.add(submission)
            self.db.commit()
            self.db.refresh(submission)
            return submission
        except Exception:
            logger.exception("An error occurred while updating a submission")
            self.db.rollback()
            raise
