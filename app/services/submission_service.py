import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.models.presentation import Presentation
from app.models.review import Review
from app.models.submission import Submission
from app.repositories.submission import SubmissionRepository

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIRECTORY = PROJECT_ROOT / "data" / "uploads"
ALLOWED_RESEARCH_TYPES = {"Poster", "Presentation"}
REQUIRES_CHANGES = "Requires Changes"


class SubmissionService:
    def __init__(self, repository: SubmissionRepository):
        self.repository = repository

    async def create_submission(
        self,
        *,
        title: str,
        description: str,
        research_type: str,
        research_file: UploadFile | None,
        student_id: int,
    ) -> Submission:
        self._validate_research_type(research_type)
        self._validate_submission_details(title, description)
        title = title.strip()
        description = description.strip()
        file_url = await self._save_upload(research_file)
        submission = Submission(
            title=title,
            description=description,
            research_type=research_type,
            student_id=student_id,
            status="Pending",
            submitted_at=datetime.now(timezone.utc),
            file_url=file_url,
        )
        try:
            return self.repository.create(submission)
        except Exception:
            self._remove_upload(file_url)
            raise

    def list_for_student(self, student_id: int) -> list[Submission]:
        return self.repository.list_by_student(student_id)

    def get_student_tracking_cards(
        self,
        student_id: int,
    ) -> list[tuple[Submission, Review | None, Presentation | None]]:
        return self.repository.list_tracking_cards_by_student(student_id)

    def get_file_for_user(
        self,
        submission_id: int,
        *,
        user_id: int,
        is_reviewer: bool,
    ) -> Path | None:
        submission = self.repository.get_by_id(submission_id)
        if submission is None or (
            submission.student_id != user_id and not is_reviewer
        ):
            return None
        if not submission.file_url:
            return None

        stored_path = (PROJECT_ROOT / submission.file_url).resolve()
        if UPLOAD_DIRECTORY.resolve() not in stored_path.parents:
            raise RuntimeError(
                f"Submission {submission_id} contains an invalid stored file path"
            )
        if not stored_path.is_file():
            raise FileNotFoundError(
                f"Stored file for submission {submission_id} is missing"
            )
        return stored_path

    def get_resubmission(self, submission_id: int, student_id: int) -> Submission | None:
        submission = self.repository.get_by_id(submission_id)
        if (
            submission is None
            or submission.student_id != student_id
            or submission.status != REQUIRES_CHANGES
        ):
            return None
        return submission

    async def resubmit_submission(
        self,
        *,
        submission_id: int,
        student_id: int,
        title: str,
        description: str,
        research_file: UploadFile | None,
    ) -> Submission | None:
        submission = self.get_resubmission(submission_id, student_id)
        if submission is None:
            return None

        self._validate_submission_details(title, description)
        title = title.strip()
        description = description.strip()
        file_url = await self._save_upload(research_file)
        previous_file = submission.file_url
        submission.title = title
        submission.description = description
        submission.status = "Pending"
        submission.submitted_at = datetime.now(timezone.utc)
        if file_url is not None:
            submission.file_url = file_url

        try:
            updated = self.repository.update(submission)
        except Exception:
            self._remove_upload(file_url)
            raise
        if file_url is not None:
            self._remove_upload(previous_file)
        return updated

    @staticmethod
    def _validate_research_type(research_type: str) -> None:
        if research_type not in ALLOWED_RESEARCH_TYPES:
            raise ValueError("Research type must be Poster or Presentation")

    @staticmethod
    def _validate_submission_details(title: str, description: str) -> None:
        if not title.strip():
            raise ValueError("Title is required")
        if not description.strip():
            raise ValueError("Description is required")

    @staticmethod
    async def _save_upload(research_file: UploadFile | None) -> str | None:
        if research_file is None or not research_file.filename:
            return None

        suffix = Path(research_file.filename).suffix.lower()
        if suffix and (
            len(suffix) > 12 or re.fullmatch(r"\.[a-z0-9]+", suffix) is None
        ):
            suffix = ""
        UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}{suffix}"
        destination = UPLOAD_DIRECTORY / filename
        try:
            with destination.open("wb") as uploaded:
                while chunk := await research_file.read(1024 * 1024):
                    uploaded.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            logger.exception("Unable to store uploaded research file")
            raise
        return (Path("data") / "uploads" / filename).as_posix()

    @staticmethod
    def _remove_upload(file_url: str | None) -> None:
        if not file_url:
            return
        stored_path = (PROJECT_ROOT / file_url).resolve()
        if stored_path.parent == UPLOAD_DIRECTORY.resolve():
            stored_path.unlink(missing_ok=True)