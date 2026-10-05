from typing import Annotated

from fastapi import File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from starlette import status

from app.dependencies import SessionDep
from app.dependencies.auth import AuthDep, StudentDep
from app.repositories.submission import SubmissionRepository
from app.services.submission_service import SubmissionService
from app.utilities.flash import flash

from . import router, templates


@router.get("/submissions/new", response_class=HTMLResponse, name="submission_form_view")
async def submission_form_view(request: Request, user: StudentDep):
    return templates.TemplateResponse(
        request=request,
        name="submission-form.html",
        context={"user": user, "submission": None},
    )


@router.get(
    "/submissions/{submission_id}/file",
    name="submission_file_download",
)
async def submission_file_download(
    submission_id: int,
    user: AuthDep,
    db: SessionDep,
):
    service = SubmissionService(SubmissionRepository(db))
    stored_path = service.get_file_for_user(
        submission_id,
        user_id=user.id,
        is_reviewer=user.role == "admin",
    )
    if stored_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return FileResponse(stored_path, filename=stored_path.name)


@router.get(
    "/submissions/{submission_id}/resubmit",
    response_class=HTMLResponse,
    name="resubmission_form_view",
)
async def resubmission_form_view(
    request: Request,
    submission_id: int,
    user: StudentDep,
    db: SessionDep,
):
    service = SubmissionService(SubmissionRepository(db))
    submission = service.get_resubmission(submission_id, user.id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="submission-form.html",
        context={"user": user, "submission": submission},
    )


@router.post("/submissions", name="create_submission")
async def create_submission(
    request: Request,
    db: SessionDep,
    user: StudentDep,
    title: str = Form(),
    description: str = Form(),
    research_type: str = Form(),
    research_file: Annotated[UploadFile | None, File()] = None,
):
    repository = SubmissionRepository(db)
    service = SubmissionService(repository)
    try:
        await service.create_submission(
            title=title,
            description=description,
            research_type=research_type,
            research_file=research_file,
            student_id=user.id,
        )
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(
            url=request.url_for("submission_form_view"),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    flash(request, "Research submitted for review", "success")
    return RedirectResponse(
        url=request.url_for("user_home_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/submissions/{submission_id}/resubmit",
    name="resubmit_submission",
)
async def resubmit_submission(
    request: Request,
    submission_id: int,
    db: SessionDep,
    user: StudentDep,
    title: str = Form(),
    description: str = Form(),
    research_file: Annotated[UploadFile | None, File()] = None,
):
    service = SubmissionService(SubmissionRepository(db))
    try:
        submission = await service.resubmit_submission(
            submission_id=submission_id,
            student_id=user.id,
            title=title,
            description=description,
            research_file=research_file,
        )
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(
            url=request.url_for(
                "resubmission_form_view", submission_id=submission_id
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    flash(request, "Research resubmitted for review", "success")
    return RedirectResponse(
        url=request.url_for("user_home_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )