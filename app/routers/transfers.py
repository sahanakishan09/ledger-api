from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas, crud

router = APIRouter(prefix="/transfers", tags=["Transfers"])

@router.post("", response_model=schemas.TransferOut, status_code=status.HTTP_200_OK)
def transfer_funds(transfer_in: schemas.TransferCreate, db: Session = Depends(get_db)):
    return crud.transfer_money(db, transfer_in)