from app.models import TransactionModel
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app, AccountModel, get_db
from app.schemas import Account

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create a new engine instance
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

test_accounts = [
    Account(id=1, name="Alice", available_cash=1000.0),
    Account(id=2, name="Bob", available_cash=500.0),
    Account(id=3, name="Charlie", available_cash=300.0),
]


# Dependency override to use the testing database session
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency in the FastAPI app
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def setup_database():
    """Create database tables for testing."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def db_session(setup_database):
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    # Rollback the transaction and close the connection after each test
    session.close()
    transaction.rollback()
    connection.close()
    # Delete database file
    engine.dispose()


@pytest.fixture(scope="session")
def client():
    """Create a TestClient for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def setup_data(db_session):
    """Set up test data before each test and clean up afterwards."""
    db_session.add_all([AccountModel(**acc.model_dump()) for acc in test_accounts])
    db_session.flush()
    yield
    db_session.query(AccountModel).delete()
    db_session.query(TransactionModel).delete()
    db_session.commit()


def test_successful_transaction(client):
    """Test a successful transaction between two accounts."""
    source_account_id = 1
    destination_account_id = 2

    payload = {
        "cash_amount": 200.0,
        "source_account_id": source_account_id,
        "destination_account_id": destination_account_id,
    }
    response = client.post("/transactions", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] == True
    assert data["cash_amount"] == 200.0
    assert data["source_account_id"] == source_account_id
    assert data["destination_account_id"] == destination_account_id

    # Check the new balances of the accounts from the database
    response = client.get(f"/accounts/{source_account_id}")
    assert response.status_code == 200
    source_account_data = response.json()
    assert source_account_data["available_cash"] == 800.0

    response = client.get(f"/accounts/{destination_account_id}")
    assert response.status_code == 200
    destination_account_data = response.json()
    assert destination_account_data["available_cash"] == 700.0


def test_insufficient_funds(client):
    """Test transaction failure due to insufficient funds."""
    payload = {
        "cash_amount": 1500.0,
        "source_account_id": 1,
        "destination_account_id": 2,
    }
    response = client.post("/transactions", json=payload)
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Insufficient funds in source account."


def test_negative_cash_amount(client):
    """Test transaction failure due to negative cash amount."""
    payload = {
        "cash_amount": -100.0,
        "source_account_id": 1,
        "destination_account_id": 2,
    }
    response = client.post("/transactions", json=payload)
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Cash amount must be positive."


def test_same_source_and_destination_account(client):
    """Test transaction failure when source and destination accounts are the same."""
    payload = {
        "cash_amount": 100.0,
        "source_account_id": 1,
        "destination_account_id": 1,
    }
    response = client.post("/transactions", json=payload)
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Source and destination accounts must be different."


def test_nonexistent_source_account(client):
    """Test transaction failure when source account does not exist."""
    payload = {
        "cash_amount": 100.0,
        "source_account_id": 99,
        "destination_account_id": 2,
    }
    response = client.post("/transactions", json=payload)
    assert response.status_code == 404

    data = response.json()
    assert data["detail"] == "Source account not found."


def test_nonexistent_destination_account(client):
    """Test transaction failure when destination account does not exist."""
    payload = {
        "cash_amount": 100.0,
        "source_account_id": 1,
        "destination_account_id": 99,
    }
    response = client.post("/transactions", json=payload)
    assert response.status_code == 404

    data = response.json()
    assert data["detail"] == "Destination account not found."


def test_transaction_persistence(client):
    """Test that transactions are stored and can be retrieved."""

    # Test successful transaction
    success_payload = {
        "cash_amount": 100.0,
        "source_account_id": 1,
        "destination_account_id": 2,
    }
    success_response = client.post("/transactions", json=success_payload)
    assert success_response.status_code == 200

    # Retrieve transactions (assuming an endpoint exists)
    success_response = client.get("/transactions")
    assert success_response.status_code == 200

    data = success_response.json()
    assert len(data) == 1
    assert data[0]["success"] == True
    assert data[0]["cash_amount"] == 100.0

    # Test unsuccessful transaction
    failure_payload = {
        "cash_amount": -100.0,
        "source_account_id": 1,
        "destination_account_id": 2,
    }
    failure_response = client.post("/transactions", json=failure_payload)
    assert failure_response.status_code == 400

    # Retrieve transaction
    failure_response = client.get("/transactions")
    assert failure_response.status_code == 200

    data = failure_response.json()
    assert len(data) == 2
    assert data[1]["success"] == False
