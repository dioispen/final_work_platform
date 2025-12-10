from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sql_repository import ProjectRepository, BidRepository, DeliverableRepository
from .dependencies import require_auth
import os
from datetime import datetime, timezone
import time

router = APIRouter(prefix="/contractor", tags=["contractor"])
templates = Jinja2Templates(directory="templates")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _sanitize_filename(name: str) -> str:
    name = os.path.basename(name)
    # replace spaces and disallowed chars simply
    return "".join(c if c.isalnum() or c in (' ', '.', '_', '-') else '_' for c in name).replace(' ', '_')

@router.get("/dashboard", response_class=HTMLResponse)
async def contractor_dashboard(request: Request, user: dict = Depends(require_auth)):
    if user['role'] != 'contractor':
        raise HTTPException(status_code=403)
    my_projects = ProjectRepository.get_contractor_projects(user['user_id'])
    # 為每個專案檢查是否已有結案檔案，並加入 flag 與版本資訊
    for p in my_projects:
        try:
            deliverables = DeliverableRepository.get_all_by_project_id(p.get("id"))
        except Exception:
            deliverables = []
        p["has_deliverable"] = len(deliverables) > 0
        p["deliverable_versions"] = deliverables
    available_projects = ProjectRepository.get_available_projects()
    return templates.TemplateResponse("contractor_dashboard.html", {
        "request": request,
        "user": user,
        "my_projects": my_projects,
        "available_projects": available_projects
    })

@router.get("/project/{project_id}", response_class=HTMLResponse)
async def view_project(request: Request, project_id: int, user: dict = Depends(require_auth)):
    if user['role'] != 'contractor':
        raise HTTPException(status_code=403)
    project = ProjectRepository.get_project_with_client(project_id)
    if not project:
        raise HTTPException(status_code=404)
    my_bid = BidRepository.get_contractor_bid(project_id, user['user_id'])
    return templates.TemplateResponse("project_detail.html", {"request": request, "user": user, "project": project, "my_bid": my_bid})

@router.post("/project/{project_id}/bid")
async def submit_bid(request: Request, project_id: int, price: int = Form(...), message: str = Form(...), file: UploadFile = File(...), user: dict = Depends(require_auth)):
    if user['role'] != 'contractor':
        raise HTTPException(status_code=403)

    # 檢查 deadline
    project = ProjectRepository.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404)
    deadline = project.get('deadline')
    deadline = deadline.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if deadline and isinstance(deadline, datetime) and now > deadline:
        raise HTTPException(status_code=400, detail="投標截止日期已過，無法提交提案")

    # 檔案格式檢查（僅限 pdf）
    filename_orig = file.filename or ""
    if not filename_orig.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="僅接受 PDF 格式的提案檔案")

    safe_name = _sanitize_filename(filename_orig)
    unique_name = f"proposal_{project_id}_{user['user_id']}_{int(time.time())}_{safe_name}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # 儲存投標（含檔案路徑）
    BidRepository.create(project_id, user['user_id'], price, message, filename_orig, file_path)
    return RedirectResponse(f"/contractor/project/{project_id}", status_code=303)

@router.get("/project/{project_id}/upload", response_class=HTMLResponse)
async def upload_page(request: Request, project_id: int, user: dict = Depends(require_auth)):
    if user['role'] != 'contractor':
        raise HTTPException(status_code=403)
    project = ProjectRepository.get_project_by_contractor(project_id, user['user_id'])
    if not project:
        raise HTTPException(status_code=404)
    deliverables = DeliverableRepository.get_all_by_project_id(project_id)
    return templates.TemplateResponse("upload_deliverable.html", {"request": request, "user": user, "project": project, "deliverables": deliverables})

@router.post("/project/{project_id}/upload")
async def upload_deliverable(request: Request, project_id: int, message: str = Form(...), file: UploadFile = File(...), user: dict = Depends(require_auth)):
    if user['role'] != 'contractor':
        raise HTTPException(status_code=403)
    project = ProjectRepository.get_project_by_contractor(project_id, user['user_id'])
    if not project:
        raise HTTPException(status_code=404)

    filename_orig = file.filename or ""
    safe_name = _sanitize_filename(filename_orig)
    unique_name = f"deliverable_{project_id}_{user['user_id']}_{int(time.time())}_{safe_name}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    # 不刪除舊版本，建立新版本紀錄
    DeliverableRepository.create(project_id, filename_orig, file_path, message)
    return RedirectResponse("/contractor/dashboard", status_code=303)

@router.get("/completed", response_class=HTMLResponse)
async def completed_projects(request: Request, user: dict = Depends(require_auth)):
    if user['role'] != 'contractor':
        raise HTTPException(status_code=403)
    
    # 獲取所有已完成的專案
    all_projects = ProjectRepository.get_contractor_projects(user['user_id'])
    completed_projects = [p for p in all_projects if p['status'] == 'completed']
    
    return templates.TemplateResponse("contractor_completed.html", {
        "request": request,
        "user": user,
        "completed_projects": completed_projects
    })