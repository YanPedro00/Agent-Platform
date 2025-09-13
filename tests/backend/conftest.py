"""
Configuração de testes para o backend
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app import models


@pytest.fixture(scope="function")
def test_db():
    """Create temporary database for tests"""
    # Create temporary file for SQLite
    db_fd, db_path = tempfile.mkstemp()
    
    # Configurar engine de teste
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    
    # Criar tabelas
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    yield TestingSessionLocal
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create database session for tests"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Cliente de teste FastAPI"""
    def override_get_db():
        session = test_db()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_llm_data():
    """Dados de exemplo para LLM"""
    return {
        "name": "Test LLM",
        "provider": "openai",
        "api_key": "test-key-123",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-3.5-turbo",
        "context_window": 4096,
        "max_tokens": 1000,
        "temperature": 0.7
    }


@pytest.fixture
def sample_action_data():
    """Dados de exemplo para Action"""
    return {
        "name": "Test Action",
        "description": "Action for testing",
        "endpoint": "https://api.example.com/test",
        "method": "GET",
        "parameters": {"param1": {"type": "string", "required": True}},
        "headers": {"Content-Type": "application/json"},
        "action_type": "custom"
    }


@pytest.fixture
def sample_agent_data():
    """Dados de exemplo para Agent"""
    return {
        "name": "Test Agent",
        "description": "Agent for testing",
        "system_prompt": "You are a test agent",
        "llm_id": 1,
        "actions": [
            {
                "action_name": "Thinking",
                "prompt": "Think about the input",
                "order": 1
            },
            {
                "action_name": "Respond",
                "prompt": "Respond to the user",
                "order": 2
            }
        ],
        "conditional_flows": [],
        "config": {}
    }


@pytest.fixture
def created_llm(db_session, sample_llm_data):
    """Cria um LLM no banco de dados para testes"""
    llm = models.LLM(**sample_llm_data)
    db_session.add(llm)
    db_session.commit()
    db_session.refresh(llm)
    return llm


@pytest.fixture
def created_action(db_session, sample_action_data):
    """Cria uma Action no banco de dados para testes"""
    action = models.Action(**sample_action_data)
    db_session.add(action)
    db_session.commit()
    db_session.refresh(action)
    return action


@pytest.fixture
def created_agent(db_session, created_llm, sample_agent_data):
    """Cria um Agent no banco de dados para testes"""
    agent_data = sample_agent_data.copy()
    agent_data["llm_id"] = created_llm.id
    
    agent = models.Agent(**agent_data)
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent
