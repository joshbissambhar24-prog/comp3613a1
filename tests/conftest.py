"""Isolated SQLite test database with no production database writes."""
import os
os.environ['DATABASE_URI'] = 'sqlite:///./test_unused.db'
os.environ['ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'testing-only-secret-not-for-production'
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
import app.models  # noqa: F401
from app.main import app
from app.database import get_session
from app.models.user import User
from app.utilities.security import create_access_token, encrypt_password

@pytest.fixture
def db():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()

@pytest.fixture
def client(db):
    def override_session():
        yield db
    app.dependency_overrides[get_session] = override_session
    c = TestClient(app)
    try:
        yield c
    finally:
        c.close()
        app.dependency_overrides.clear()

@pytest.fixture
def users(db):
    created = []
    for name, role in [('student_a', 'regular_user'), ('student_b', 'regular_user'), ('reviewer', 'admin')]:
        u = User(username=name, email=f'{name}@example.org', password=encrypt_password('Example123!'), role=role)
        db.add(u)
        created.append(u)
    db.commit()
    for u in created:
        db.refresh(u)
    return created

@pytest.fixture
def login_as(client):
    def login(user):
        token = create_access_token({'sub': str(user.id), 'role': user.role})
        client.cookies.set('access_token', token)
    return login
