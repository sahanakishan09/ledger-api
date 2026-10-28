import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models import TransactionType

class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")  # Rejects attempts to pass initial balance

class AccountOut(BaseModel):
    id: uuid.UUID
    name: str
    balance: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AccountBalanceOut(BaseModel):
    account_id: uuid.UUID
    balance: Decimal

class TransactionCreate(BaseModel):
    type: TransactionType
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: str = Field(..., min_length=1)
    reference_id: str = Field(..., min_length=1)

class TransactionOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    type: TransactionType
    amount: Decimal
    description: str
    reference_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionResultOut(BaseModel):
    transaction: TransactionOut
    current_balance: Decimal

class PaginatedTransactionsOut(BaseModel):
    account_id: uuid.UUID
    total: int
    page: int
    limit: int
    total_pages: int
    data: List[TransactionOut]

class TransferCreate(BaseModel):
    source_account_id: uuid.UUID
    destination_account_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    reference_id: str = Field(..., min_length=1)
    description: Optional[str] = "Funds Transfer"

    @model_validator(mode="after")
    def check_accounts_differ(self):
        if self.source_account_id == self.destination_account_id:
            raise ValueError("source_account_id and destination_account_id must be distinct")
        return self

class TransferOut(BaseModel):
    reference_id: str
    amount: Decimal
    source_account_id: uuid.UUID
    source_balance: Decimal
    destination_account_id: uuid.UUID
    destination_balance: Decimal