"""REST endpoints for research workflows. Cookie-based session authentication."""
from fastapi import HTTPException, status
from pydantic import BaseModel
from app.dependencies import SessionDep
from app.dependencies.auth import StudentDep, AdminDep, AuthDep
from app.repositories.submission import SubmissionRepository
from app.repositories.review import ReviewRepository
from app.services.submission_service import SubmissionService
from app.services.review_service import ReviewService
from . import api_router

class SubmissionCreate(BaseModel):
    title: str
    description: str
    research_type: str

class ReviewCreate(BaseModel):
    feedback: str
    outcome: str
    presentation_date: str | None = None
    presentation_time: str | None = None
    location: str | None = None

@api_router.get('/submissions')
def list_submissions(db: SessionDep, user: AuthDep):
    if user.role == 'admin':
        return [s for s, _ in ReviewRepository(db).list_submissions_to_review()]
    return SubmissionRepository(db).list_by_student(user.id)

@api_router.get('/submissions/{submission_id}')
def get_submission(submission_id: int, db: SessionDep, user: AuthDep):
    submission = SubmissionRepository(db).get_by_id(submission_id)
    if submission is None or (user.role != 'admin' and submission.student_id != user.id):
        raise HTTPException(status_code=404, detail='Submission not found')
    return submission

@api_router.post('/submissions', status_code=status.HTTP_201_CREATED)
async def post_submission(payload: SubmissionCreate, db: SessionDep, user: StudentDep):
    try:
        return await SubmissionService(SubmissionRepository(db)).create_submission(
            title=payload.title, description=payload.description,
            research_type=payload.research_type, research_file=None, student_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@api_router.post('/submissions/{submission_id}/reviews', status_code=status.HTTP_201_CREATED)
def post_review(submission_id: int, payload: ReviewCreate, db: SessionDep, user: AdminDep):
    try:
        return ReviewService(ReviewRepository(db)).create_review(
            submission_id=submission_id, reviewer_id=user.id,
            **payload.model_dump())
    except ValueError as exc:
        message = str(exc)
        code = 404 if message == 'Submission not found' else 422
        raise HTTPException(status_code=code, detail=message) from exc
