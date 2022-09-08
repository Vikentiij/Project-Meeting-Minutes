from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from starlette.authentication import AuthenticationError, SimpleUser, AuthCredentials
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware

from . import models
from .database import engine
from .routers import meeting, user, pages, authentication
from .token import SECRET_KEY, ALGORITHM


class JwtCookieAuthBackend:
    async def authenticate(self, conn):
        if "access_token" not in conn.cookies:
            return None

        auth = conn.cookies["access_token"]
        try:
            scheme, token = auth.split()
            if scheme.lower() != 'bearer':
                return None
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except (ValueError, JWTError) as exc:
            raise AuthenticationError('Invalid basic auth credentials')

        # sub comes from meeting/routers/authentication.py:21
        return AuthCredentials(["authenticated"]), SimpleUser(decoded["sub"])


app = FastAPI(middleware=[Middleware(AuthenticationMiddleware, backend=JwtCookieAuthBackend())])

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

models.Base.metadata.create_all(engine)

app.include_router(pages.router)
app.include_router(authentication.router)
app.include_router(meeting.router)
app.include_router(user.router)

# def get_db():     # move to database.py
# db = SessionLocal()
# try:
#    yield db
# finally:
#   db.close


# @app.post("/meeting", status_code=status.HTTP_201_CREATED, tags=["meetings"])
# def create(request: schemas.Meeting, db: Session = Depends(get_db)):
# return db
# new_meeting = models.Meeting(title=request.title, body=request.body, user_id=1)
# db.add(new_meeting)
# db.commit()
# db.refresh(new_meeting)
# return new_meeting


# @app.get("/meeting", response_model=List[schemas.ShowMeeting], tags=["meetings"])
# def all(db: Session = Depends(get_db)):
# meetings = db.query(models.Meeting).all()
# return meetings


# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  --- move to hashing.py
