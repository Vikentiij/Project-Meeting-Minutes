from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import database, schemas
from ..repository import user

router = APIRouter(prefix="/user", tags=["users"])

get_db = database.get_db


@router.post("/", response_model=schemas.ShowUser)
def create_user(request: schemas.User, db: Session = Depends(get_db)):
    # hashedPassword = pwd_context.hash(request.password) ---- move to hashing.py
    return user.create(request, db)


@router.get("/{id}", response_model=schemas.ShowUser)
def show_user(id: int, db: Session = Depends(get_db)):
    return user.show(id, db)
