from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import StudentDep
from app.dependencies.session import SessionDep
from app.repositories.submission import SubmissionRepository
from app.services.submission_service import SubmissionService

from . import router, templates


@router.get("/student", response_class=HTMLResponse, name="user_home_view")
async def user_home_view(
    request: Request,
    user: StudentDep,
    db: SessionDep,
):
    service = SubmissionService(SubmissionRepository(db))
    submissions = service.get_student_tracking_cards(user.id)

    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "submissions": submissions,
        },
    )