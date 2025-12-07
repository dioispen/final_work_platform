from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from models.review_repository import ReviewRepository
from sql_repository import ProjectRepository
from .dependencies import require_auth

router = APIRouter(prefix="/review", tags=["review"])
templates = Jinja2Templates(directory="templates")


# 顯示評價表單
@router.get("/form", response_class=HTMLResponse)
async def review_form(
    request: Request,
    project_id: int,
    target_id: int,
    user: dict = Depends(require_auth),
):
    reviewer_id = user["user_id"]
    role = user["role"]

    # 專案是否存在
    project = ProjectRepository.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 確認 reviewer 有參與這個專案（簡單檢查）
    if reviewer_id not in (project["client_id"], project.get("contractor_id")):
        raise HTTPException(status_code=403, detail="Not your project")

    # 已評價就直接導回
    if ReviewRepository.has_reviewed(project_id, reviewer_id):
        if role == "client":
            return RedirectResponse(
                f"/client/project/{project_id}/deliverable", status_code=303
            )
        else:
            return RedirectResponse(
                f"/contractor/project/{project_id}", status_code=303
            )

    return templates.TemplateResponse(
        "review_form.html",
        {
            "request": request,
            "project": project,
            "project_id": project_id,
            "target_id": target_id,
            "reviewer_id": reviewer_id,
            "role": role,
        },
    )


# 接收評價
@router.post("/submit")
async def submit_review(
    request: Request,
    project_id: int = Form(...),
    target_id: int = Form(...),
    dim1: int = Form(...),
    dim2: int = Form(...),
    dim3: int = Form(...),
    comment: str = Form(""),
    user: dict = Depends(require_auth),
):
    reviewer_id = user["user_id"]
    role = user["role"]

    if ReviewRepository.has_reviewed(project_id, reviewer_id):
        # 已評過直接導回
        if role == "client":
            return RedirectResponse(
                f"/client/project/{project_id}/deliverable", status_code=303
            )
        else:
            return RedirectResponse(
                f"/contractor/project/{project_id}", status_code=303
            )

    ReviewRepository.create_review(
        project_id=project_id,
        reviewer_id=reviewer_id,
        target_id=target_id,
        dim1=dim1,
        dim2=dim2,
        dim3=dim3,
        comment=comment,
    )

    # 根據身份導回對應畫面
    if role == "client":
        return RedirectResponse(
            f"/client/project/{project_id}/deliverable", status_code=303
        )
    else:
        return RedirectResponse(
            f"/contractor/project/{project_id}", status_code=303
        )
