from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.repositories.review import ReviewRepository
from app.services.review_service import ReviewService

from . import router, templates


@router.get("/reviewer", response_class=HTMLResponse, name="admin_home_view")
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    service = ReviewService(ReviewRepository(db))
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "submissions": service.list_submissions_to_review(),
        },
    )
