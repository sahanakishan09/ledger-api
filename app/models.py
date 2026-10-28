import uuid
from decimal import Decimal
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class TransactionType(str, enum.Enum):
    credit = "credit"
    debit = "debit"

class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    balance = Column(Numeric(precision=14, scale=2), default=Decimal("0.00"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(precision=14, scale=2), nullable=False)
    description = Column(String(500), nullable=False)
    reference_id = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    account = relationship("Account", back_populates="transactions")

    # DB Level Constraint: Unique reference_id per account
    __table_args__ = (
        UniqueConstraint("account_id", "reference_id", name="uq_account_reference"),
    )