from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean

from app.database import Base


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    executed_time = Column(DateTime, nullable=True)
    registered_time = Column(DateTime, default=datetime.now())
    success = Column(Boolean, default=False)

    cash_amount = Column(Float)

    source_account_id = Column(Integer, ForeignKey("accounts.id"))
    destination_account_id = Column(Integer, ForeignKey("accounts.id"))


class AccountModel(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    available_cash = Column(Float)
