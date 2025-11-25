from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sql_repository import UserRepository

router = APIRouter(tags=["auth"])

templates = Jinja2Templates(directory="templates")

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...), role: str = Form(...)):
    if UserRepository.get_by_username(username):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "用戶名已存在"
        })
    UserRepository.create(username, password, role)
    return RedirectResponse("/login", status_code=303)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = UserRepository.get_by_username(username)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "用戶不存在"
        })
    # 簡單密碼比對（沒有hash）
    if password != user.get("password"):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "密碼錯誤"
        })
    request.session["user"] = {
        "user_id": user['id'],
        "username": user['username'],
        "role": user['role']
    }
    return RedirectResponse("/", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)