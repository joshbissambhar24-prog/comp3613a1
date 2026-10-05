from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status

from app.dependencies import SessionDep
from app.dependencies.auth import AdminDep
from app.repositories.review import ReviewRepository
from app.services.review_service import ReviewService
from app.utilities.flash import flash

from . import router, templates


@router.get(
    "/reviews/{submission_id}",
    response_class=HTMLResponse,
    name="review_form_view",
)
async def review_form_view(
    request: Request,
    submission_id: int,
    db: SessionDep,
    reviewer: AdminDep,
):
    service = ReviewService(ReviewRepository(db))
    context = service.get_review_context(submission_id)
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    submission, student, review_history = context
    return templates.TemplateResponse(
        request=request,
        name="review-form.html",
        context={
            "user": reviewer,
            "submission": submission,
            "student": student,
            "review_history": review_history,
        },
    )


@router.post("/reviews/{submission_id}", name="submit_review")
async def submit_review(
    request: Request,
    submission_id: int,
    db: SessionDep,
    reviewer: AdminDep,
    feedback: str = Form(),
    outcome: str = Form(),
    presentation_date: str | None = Form(default=None),
    presentation_time: str | None = Form(default=None),
    location: str | None = Form(default=None),
):
    repository = ReviewRepository(db)
    service = ReviewService(repository)
    try:
        service.create_review(
            submission_id=submission_id,
            reviewer_id=reviewer.id,
            feedback=feedback,
            outcome=outcome,
            presentation_date=presentation_date,
            presentation_time=presentation_time,
            location=location,
        )
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(
            url=request.url_for("review_form_view", submission_id=submission_id),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    flash(request, "Review saved", "success")
    return RedirectResponse(
        url=request.url_for("admin_home_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )