import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas, crud, models
from typing import List

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("", response_model=schemas.AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(account_in: schemas.AccountCreate, db: Session = Depends(get_db)):
    return crud.create_account(db, account_in)

@router.get("", response_model=List[schemas.AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(models.Account).order_by(models.Account.created_at.desc()).all()

@router.get("/{account_id}/balance", response_model=schemas.AccountBalanceOut)
def get_balance(account_id: uuid.UUID, db: Session = Depends(get_db)):
    account = crud.get_account(db, account_id)
    return schemas.AccountBalanceOut(account_id=account.id, balance=account.balance)

@router.post("/{account_id}/transactions", response_model=schemas.TransactionResultOut, status_code=status.HTTP_201_CREATED)
def add_transaction(
    account_id: uuid.UUID,
    txn_in: schemas.TransactionCreate,
    db: Session = Depends(get_db)
):
    txn, current_balance = crud.add_transaction(db, account_id, txn_in)
    return schemas.TransactionResultOut(transaction=txn, current_balance=current_balance)

@router.get("/{account_id}/transactions", response_model=schemas.PaginatedTransactionsOut)
def get_transactions(
    account_id: uuid.UUID,
    type: Optional[models.TransactionType] = Query(None, description="credit or debit"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return crud.get_transactions(db, account_id, type, page, limit)