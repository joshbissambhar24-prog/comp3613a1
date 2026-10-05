from datetime import date, datetime, time, timezone

from app.models.presentation import Presentation
from app.models.review import Review
from app.models.submission import Submission
from app.models.user import User
from app.repositories.review import ReviewRepository

REVIEW_OUTCOMES = {"Accepted", "Rejected", "Requires Changes"}
ACTIVE_REVIEW_STATUSES = {"Pending", "Requires Changes"}


class ReviewService:
    def __init__(self, repository: ReviewRepository):
        self.repository = repository

    def create_review(
        self,
        *,
        submission_id: int,
        reviewer_id: int,
        feedback: str,
        outcome: str,
        presentation_date: str | None,
        presentation_time: str | None,
        location: str | None,
    ) -> Review:
        feedback = feedback.strip()
        if not feedback:
            raise ValueError("Feedback is required")

        if outcome not in REVIEW_OUTCOMES:
            raise ValueError("Invalid review outcome")

        presentation_date = (
            date.fromisoformat(presentation_date.strip())
            if presentation_date and presentation_date.strip()
            else None
        )
        presentation_time = (
            time.fromisoformat(presentation_time.strip())
            if presentation_time and presentation_time.strip()
            else None
        )
        location = location.strip() if location and location.strip() else None
        has_any_presentation_value = (
            presentation_date is not None
            or presentation_time is not None
            or bool(location and location.strip())
        )
        has_complete_presentation = (
            presentation_date is not None
            and presentation_time is not None
            and bool(location and location.strip())
        )
        if has_any_presentation_value and not has_complete_presentation:
            raise ValueError(
                "Presentation date, time, and location are all required"
            )
        if outcome != "Accepted" and has_any_presentation_value:
            raise ValueError(
                "Presentation details can only be set for Accepted reviews"
            )

        submission = self.repository.get_submission(submission_id)

        if submission is None:
            raise ValueError("Submission not found")
        if submission.status not in ACTIVE_REVIEW_STATUSES:
            raise ValueError("This submission is not awaiting review")

        review = Review(
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            feedback=feedback,
            outcome=outcome,
            reviewed_at=datetime.now(timezone.utc),
        )

        submission.status = outcome

        presentation = None
        if (
            outcome == "Accepted"
            and presentation_date is not None
            and presentation_time is not None
            and location is not None
        ):
            presentation = Presentation(
                submission_id=submission_id,
                presentation_date=presentation_date,
                presentation_time=presentation_time,
                location=location,
            )

        return self.repository.save_review(
            review,
            submission,
            presentation,
        )

    def list_submissions_to_review(self) -> list[tuple[Submission, User]]:
        return self.repository.list_submissions_to_review()

    def get_review_context(
        self,
        submission_id: int,
    ) -> tuple[Submission, User, list[tuple[Review, User]]] | None:
        submission = self.repository.get_submission(submission_id)
        if submission is None or submission.status not in ACTIVE_REVIEW_STATUSES:
            return None
        student = self.repository.get_user(submission.student_id)
        if student is None:
            raise RuntimeError(
                f"Submission {submission_id} refers to missing student {submission.student_id}"
            )
        return (
            submission,
            student,
            self.repository.list_review_history(submission_id),
        )