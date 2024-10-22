from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.models import (
    Base,
    TransactionModel,
    AccountModel,
)
from app.database import SessionLocal, engine
from app.schemas import Account, CreateAccount, Transaction, CreateTransaction

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@app.post("/transactions/")
def process_transaction(transaction: CreateTransaction, db: Session = Depends(get_db)):
    """
    Processes a transaction with an amount between two accounts.
    If successful, stores the transaction in the database and updates account balances.

    Args:
        transaction (TransactionModel): Transaction to be processed.
    Returns:
        dict: Processed transaction details.
    """

    success = False

    new_transaction = TransactionModel(**transaction.model_dump(), success=success)

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    if transaction.cash_amount < 0:
        raise HTTPException(400, "Cash amount must be positive.")

    source_account_id = transaction.source_account_id
    destination_account_id = transaction.destination_account_id

    if source_account_id == destination_account_id:
        raise HTTPException(400, "Source and destination accounts must be different.")

    try:
        source_account = (
            db.query(AccountModel)
            .filter(AccountModel.id == source_account_id)
            .with_for_update()
            .one()
        )
    except NoResultFound:
        raise HTTPException(404, "Source account not found.")

    try:
        destination_account = (
            db.query(AccountModel)
            .filter(AccountModel.id == destination_account_id)
            .with_for_update()
            .one()
        )
    except NoResultFound:
        raise HTTPException(404, "Destination account not found.")

    if source_account.available_cash >= transaction.cash_amount:
        try:
            source_account.available_cash -= transaction.cash_amount
            destination_account.available_cash += transaction.cash_amount
            new_transaction.success = True
            new_transaction.executed_time = datetime.now()
            db.commit()
            db.refresh(new_transaction)
            db.close()
        except Exception as e:
            db.rollback()
            db.close()
            raise HTTPException(
                500, f"An error occurred while processing the transaction: {e}"
            )
        return new_transaction
    else:
        raise HTTPException(400, "Insufficient funds in source account.")


@app.get("/transactions/")
def retrieve_transactions(db: Session = Depends(get_db)) -> List[Transaction]:
    """
    Retrieves all transactions.

    Returns:
        transactions (List[Transaction]): List of transactions.
    """

    transactions_retrieved = db.query(TransactionModel).all()
    return [
        Transaction.model_validate(transaction_model.__dict__)
        for transaction_model in transactions_retrieved
    ]


@app.post("/accounts/")
def create_account(account: CreateAccount, db: Session = Depends(get_db)):
    """
    Creates an account.

    Args:
        account (Account): Account to be created.
    Returns:
        account (Account): Created account.
    """
    new_account = AccountModel(**account.model_dump())

    db.add(new_account)
    db.commit()
    db.close()

    return account


@app.get("/accounts/")
def retrieve_accounts(db: Session = Depends(get_db)) -> List[Account]:
    """
    Retrieves all accounts.

    Returns:
        accounts (List[Account]): List of accounts.
    """
    accounts_retrieved = db.query(AccountModel).all()
    return [
        Account.model_validate(account_model.__dict__)
        for account_model in accounts_retrieved
    ]


@app.get("/accounts/{id}")
def retrieve_account(id: int, db: Session = Depends(get_db)) -> Account:
    """
    Retrieves an account by ID.

    Args:
        id (int): ID of the account to be retrieved.
    Returns:
        account (Account): Retrieved account.
    """
    try:
        account_model = db.query(AccountModel).filter(AccountModel.id == id).one()
        return Account.model_validate(account_model.__dict__)
    except NoResultFound:
        raise HTTPException(404, f"Account with id {id} does not exist")
    # try:
    #     account = get_account_from_database(account_id, db)
    # except ValueError:
    #     raise HTTPException(404, "Account not found.")
    #
    # return account


@app.get("/")
def read_root():
    return {"Hello": "World"}
