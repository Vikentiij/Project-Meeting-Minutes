import time

from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request

from main import templates
from .. import database, models, token
from ..hashing import Hash
from ..repository import meeting, user

router = APIRouter(tags=["website_pages"])

get_db = database.get_db


@router.get("/")
async def index(request: Request):
    authenticated = request.user.is_authenticated
    return templates.TemplateResponse("index.html", {"request": request, "authenticated": authenticated})


@router.get("/user/signup")
def signup_get(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/user/signup")
def signup_post(request: Request, name: str = Form(), email: str = Form(), password: str = Form(),
                confirm_password: str = Form(), db: Session = Depends(database.get_db)):
    errors = []
    signup_context = {
        "request": request,
        "errors": errors,
        "name": name,
        "email": email,
    }

    if not name.strip():
        errors.append("Name is required")
    if not email.strip() or "@" not in email:
        errors.append("Invalid email")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters long")
    if password != confirm_password:
        errors.append("Password confirmation doesn't match")
    if db.query(models.User).filter(models.User.email == email).count() > 0:
        errors.append("A user with this email is already registered")

    if errors:
        return templates.TemplateResponse("signup.html", context=signup_context)

    user.create(models.User(name=name, email=email, password=password), db)

    # Automatically logging in as the created user and redirecting to the index page
    response = templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/"})
    access_token = token.create_access_token(data={"sub": email})
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@router.get("/user/login")
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/user/login")
def login_post(request: Request, oauth_request: OAuth2PasswordRequestForm = Depends(),
               db: Session = Depends(database.get_db)):
    login_context = {
        "msg": "",
        "request": request,
        "errors": [],
        "login_successful": False,
        "email": oauth_request.username,
        "password": oauth_request.password,
    }
    user = db.query(models.User).filter(models.User.email == oauth_request.username).first()
    if not user:
        login_context["errors"].append(f"Email {oauth_request.username} not found")
        return templates.TemplateResponse("login.html", login_context)

    if not Hash.verify(user.password, oauth_request.password):
        login_context["errors"].append("Incorrect Password")
        return templates.TemplateResponse("login.html", login_context)

    access_token = token.create_access_token(data={"sub": user.email})

    login_context["msg"] = "Logged in"
    login_context["login_successful"] = True
    response = templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/"})
    response.set_cookie(key="access_token", value=f"Bearer {access_token}",
                        httponly=True)  # set HttpOnly cookie in response
    return response


@router.get("/user/logout")
def logout():
    response = RedirectResponse("/")
    response.delete_cookie(key="access_token")
    return response


@router.get("/meetings")
def get_meetings(request: Request, db: Session = Depends(database.get_db)):
    if not request.user.is_authenticated:
        return templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/user/login"})

    current_user = db.query(models.User).filter(models.User.email == request.user.username).first()
    user_meetings = current_user.meetings if user else []
    return templates.TemplateResponse("meetings.html", {"request": request, "meetings": user_meetings})


@router.get("/meetings/create")
def create_meeting_get(request: Request):
    if not request.user.is_authenticated:
        return templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/user/login"})

    return templates.TemplateResponse(
        "meeting_create.html",
        {
            "request": request,
            "time": time.strftime("Meeting at %I:%M%p on %B %d, %Y")
        }
    )


@router.post("/meetings/create")
def create_meeting_post(request: Request, title: str = Form(), time: str=Form(), body: str = Form(), db: Session = Depends(database.get_db)):
    if not request.user.is_authenticated:
        return templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/user/login"})

    current_user = db.query(models.User).filter(models.User.email == request.user.username).first()
    new_meeting = models.Meeting(title=title, time=time, body=body, user_id=current_user.id)
    meeting.create(new_meeting, current_user.id, db)
    return templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/meetings"})


@router.get("/meetings/edit/{meeting_id}")
def edit_meeting_get(meeting_id: int, request: Request, db: Session = Depends(database.get_db)):
    if not request.user.is_authenticated:
        return templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/user/login"})

    meeting_to_edit = meeting.show(meeting_id, db)
    return templates.TemplateResponse("meeting_edit.html", {"request": request, "meeting": meeting_to_edit})


@router.post("/meetings/edit/{meeting_id}", status_code=status.HTTP_202_ACCEPTED)
def edit_meeting_post(meeting_id: int, request: Request, title: str = Form(), time: str =Form(), body: str = Form(), db: Session = Depends(database.get_db)):
    if not request.user.is_authenticated:
        return templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/user/login"})

    meeting_to_edit = meeting.show(meeting_id, db)
    meeting_to_edit.title = title
    meeting_to_edit.time = time
    meeting_to_edit.body = body
    meeting.update(meeting_id, meeting_to_edit, db)

    return templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/meetings"})


@router.get("/meetings/delete/{meeting_id}")
def delete_meeting_get(meeting_id: int, request: Request, db: Session = Depends(database.get_db)):
    if not request.user.is_authenticated:
        return templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/user/login"})

    meeting_to_delete = meeting.show(meeting_id, db)
    return templates.TemplateResponse("meeting_delete.html", {"request": request, "meeting": meeting_to_delete})


@router.post("/meetings/delete/{meeting_id}")
def delete_meeting_post(meeting_id: int, request: Request, db: Session = Depends(database.get_db)):
    if not request.user.is_authenticated:
        return templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/user/login"})

    meeting_to_delete = meeting.show(meeting_id, db)
    current_user = db.query(models.User).filter(models.User.email == request.user.username).first()
    assert meeting_to_delete.creator.id == current_user.id
    meeting.destroy(meeting_id, db)

    return templates.TemplateResponse("redirect.html", {"request": request, "redirect_to": "/meetings"})
