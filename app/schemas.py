from datetime import datetime
from typing import Optional

from pydantic import BaseModel

"""
Pydantic models.

The Create models are used to not have to keep track of the ID when creating new accounts.
This also adds a level of security, since the user cannot define the ID themselves, because this could lead to
overwriting IDs of already existing accounts.

If auth is implemented later we could also extend this so the base classes (Account and Transaction) 
don't return the password of the user, and further separate into Public and Private models.

"""


class Account(BaseModel):
    id: int
    name: str
    available_cash: float


class CreateAccount(BaseModel):
    name: str
    available_cash: float


class Transaction(BaseModel):
    id: int
    cash_amount: float
    source_account_id: int
    destination_account_id: int
    registered_time: Optional[datetime] = None
    executed_time: Optional[datetime] = None
    success: Optional[bool] = None


class CreateTransaction(BaseModel):
    cash_amount: float
    source_account_id: int
    destination_account_id: int
