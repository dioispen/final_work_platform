from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sql_repository import ProjectRepository, BidRepository, DeliverableRepository
from .dependencies import require_auth
import os

router = APIRouter(prefix="/contractor", tags=["contractor"])
templates = Jinja2Templates(directory="templates")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/dashboard", response_class=HTMLResponse)
async def contractor_dashboard(request: Request, user: dict = Depends(require_auth)):
    if user['role'] != 'contractor':
        raise HTTPException(status_code=403)
    my_projects = ProjectRepository.get_contractor_projects(user['user_id'])
    # 為每個專案檢查是否已有結案檔案，並加入 flag
    for p in my_projects:
        try:
            deliverable = DeliverableRepository.get_by_project_id(p.get("id"))
        except Exception:
            deliverable = None
        p["has_deliverable"] = bool(deliverable)
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
async def submit_bid(request: Request, project_id: int, price: int = Form(...), message: str = Form(...), user: dict = Depends(require_auth)):
    if user['role'] != 'contractor':
        raise HTTPException(status_code=403)
    BidRepository.create(project_id, user['user_id'], price, message)
    return RedirectResponse(f"/contractor/project/{project_id}", status_code=303)

@router.get("/project/{project_id}/upload", response_class=HTMLResponse)
async def upload_page(request: Request, project_id: int, user: dict = Depends(require_auth)):
    if user['role'] != 'contractor':
        raise HTTPException(status_code=403)
    project = ProjectRepository.get_project_by_contractor(project_id, user['user_id'])
    if not project:
        raise HTTPException(status_code=404)
    deliverable = DeliverableRepository.get_by_project_id(project_id)
    return templates.TemplateResponse("upload_deliverable.html", {"request": request, "user": user, "project": project, "deliverable": deliverable})

@router.post("/project/{project_id}/upload")
async def upload_deliverable(request: Request, project_id: int, message: str = Form(...), file: UploadFile = File(...), user: dict = Depends(require_auth)):
    if user['role'] != 'contractor':
        raise HTTPException(status_code=403)
    project = ProjectRepository.get_project_by_contractor(project_id, user['user_id'])
    if not project:
        raise HTTPException(status_code=404)
    if DeliverableRepository.get_by_project_id(project_id):
        DeliverableRepository.delete_by_project_id(project_id)
    filename = f"{project_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    DeliverableRepository.create(project_id, file.filename, file_path, message)
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