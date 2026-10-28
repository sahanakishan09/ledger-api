import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app import models, schemas

def create_account(db: Session, account_in: schemas.AccountCreate) -> models.Account:
    account = models.Account(name=account_in.name, balance=Decimal("0.00"))
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

def get_account(db: Session, account_id: uuid.UUID) -> models.Account:
    account = db.get(models.Account, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account

def add_transaction(
    db: Session, account_id: uuid.UUID, txn_in: schemas.TransactionCreate
) -> tuple[models.Transaction, Decimal]:
    try:
        # Atomic lock row for update to prevent concurrent double-spending
        stmt = select(models.Account).where(models.Account.id == account_id).with_for_update()
        account = db.execute(stmt).scalar_one_or_none()

        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        if txn_in.type == models.TransactionType.debit and account.balance < txn_in.amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Insufficient balance for debit"
            )

        if txn_in.type == models.TransactionType.credit:
            account.balance += txn_in.amount
        else:
            account.balance -= txn_in.amount

        txn = models.Transaction(
            account_id=account_id,
            type=txn_in.type,
            amount=txn_in.amount,
            description=txn_in.description,
            reference_id=txn_in.reference_id,
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)
        return txn, account.balance
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate transaction reference_id for this account"
        )
    except Exception:
        db.rollback()
        raise

def get_transactions(
    db: Session,
    account_id: uuid.UUID,
    txn_type: Optional[models.TransactionType] = None,
    page: int = 1,
    limit: int = 10,
):
    get_account(db, account_id)  # Validate exists

    query = select(models.Transaction).where(models.Transaction.account_id == account_id)
    if txn_type:
        query = query.where(models.Transaction.type == txn_type)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    txns = db.scalars(
        query.order_by(models.Transaction.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return {
        "account_id": account_id,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "data": txns,
    }

def transfer_money(db: Session, transfer_in: schemas.TransferCreate):
    try:
        # Enforce deterministic locking order to prevent DB deadlocks
        ids = sorted([transfer_in.source_account_id, transfer_in.destination_account_id])
        locked_accounts = {}
        for acc_id in ids:
            acc = db.execute(
                select(models.Account).where(models.Account.id == acc_id).with_for_update()
            ).scalar_one_or_none()
            if not acc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account {acc_id} not found"
                )
            locked_accounts[acc.id] = acc

        src = locked_accounts[transfer_in.source_account_id]
        dst = locked_accounts[transfer_in.destination_account_id]

        if src.balance < transfer_in.amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Source account has insufficient balance"
            )

        src.balance -= transfer_in.amount
        dst.balance += transfer_in.amount

        # Write transaction records for both legs
        debit_txn = models.Transaction(
            account_id=src.id,
            type=models.TransactionType.debit,
            amount=transfer_in.amount,
            description=f"{transfer_in.description} to {dst.id}",
            reference_id=f"{transfer_in.reference_id}_DEBIT",
        )
        credit_txn = models.Transaction(
            account_id=dst.id,
            type=models.TransactionType.credit,
            amount=transfer_in.amount,
            description=f"{transfer_in.description} from {src.id}",
            reference_id=f"{transfer_in.reference_id}_CREDIT",
        )
        db.add_all([debit_txn, credit_txn])
        db.commit()

        return schemas.TransferOut(
            reference_id=transfer_in.reference_id,
            amount=transfer_in.amount,
            source_account_id=src.id,
            source_balance=src.balance,
            destination_account_id=dst.id,
            destination_balance=dst.balance,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A transfer with this reference_id already exists"
        )
    except Exception:
        db.rollback()
        raise