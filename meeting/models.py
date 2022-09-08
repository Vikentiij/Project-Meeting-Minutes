from typing import List, Optional

from sqlalchemy import Column, Integer, String, ForeignKey
from starlette.requests import Request

from .database import Base
from sqlalchemy.orm import relationship


class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    time = Column(String)
    body = Column(String)
    user_id =Column(Integer, ForeignKey("users.id"))
    creator = relationship("User", back_populates="meetings")


class User(Base):
    __tablename__ ="users"
    id = Column(Integer, primary_key=True, index=True)
    name= Column(String)
    email = Column(String)
    password= Column(String)

    meetings= relationship("Meeting", back_populates="creator")


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get(
            "email"
        )  # since outh works on username field we are considering email as username
        self.password = form.get("password")

    async def is_valid(self):
        if not self.username or not self.username.__contains__("@"):
            self.errors.append("Email is required")
        if not self.password or len(self.password) < 4:
            self.errors.append("A valid password is required")
        return not self.errors
