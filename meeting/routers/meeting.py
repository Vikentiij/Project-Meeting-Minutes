from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import schemas, database, oauth2
from ..repository import meeting

router = APIRouter(prefix="/meeting", tags=["meetings"])
get_db = database.get_db


@router.get("/", response_model=List[schemas.ShowMeeting])
def all(db: Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    return meeting.get_all(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(request: schemas.Meeting, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    return meeting.create(request, 1, db)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def destroy(id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    return meeting.destroy(id, db)


@router.put("/{id}", status_code=status.HTTP_202_ACCEPTED)
def update(id: int, request: schemas.Meeting, db: Session = Depends(get_db),
           current_user: schemas.User = Depends(oauth2.get_current_user)):
    return meeting.update(id, request, db)


@router.get("/{id}", status_code=200, response_model=schemas.ShowMeeting)
def show(id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    return meeting.show(id, db)
