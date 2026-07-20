import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Use separate test database
TEST_SQLALCHEMY_DATABASE_URI = "sqlite:///./test.db"

# Override settings to use SQLite for tests
os.environ["DB_HOST"] = "localhost"
os.environ["DB_NAME"] = "docmind_test"
os.environ["DB_USER"] = "postgres"
os.environ["DB_PASSWORD"] = "postgres"
os.environ["USE_S3"] = "False"

from app.core.config import settings
# Override password policy defaults in test runner to preserve compatibility with legacy test suites
settings.PASSWORD_MIN_LENGTH = 1
settings.PASSWORD_REQUIRE_UPPERCASE = False
settings.PASSWORD_REQUIRE_LOWERCASE = False
settings.PASSWORD_REQUIRE_NUMBER = False
settings.PASSWORD_REQUIRE_SPECIAL = False

from app.main import app
from app.db.session import get_db, Base
from app.core.security import get_password_hash
from app.db.models import User

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create test tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop test tables
    Base.metadata.drop_all(bind=engine)
    # Clean up test.db file if exists
    if os.path.exists("./test.db"):
        try:
            os.remove("./test.db")
        except PermissionError:
            pass


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    hashed_password = get_password_hash("password123")
    user = User(
        email="test@docmind.com",
        hashed_password=hashed_password,
        full_name="Test User",
        is_active=True,
        is_admin=False,
        role="USER"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session):
    hashed_password = get_password_hash("adminpassword")
    user = User(
        email="admin@docmind.com",
        hashed_password=hashed_password,
        full_name="Admin User",
        is_active=True,
        is_admin=True,
        role="ADMIN"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
