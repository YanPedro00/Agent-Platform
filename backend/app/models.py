from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, JSON, Float
from sqlalchemy.orm import relationship

from app.database import Base

class LLM(Base):
    __tablename__ = "llms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    provider = Column(String)  # e.g., "openai", "anthropic", "huggingface", "lmstudio", "ollama"
    api_key = Column(String, nullable=True)   # encrypted in production
    base_url = Column(String, nullable=True)  # for custom endpoints
    model_name = Column(String)
    context_window = Column(Integer, default=4096)
    max_tokens = Column(Integer, default=1000)
    temperature = Column(Float, default=0.1)
    is_active = Column(Boolean, default=True)

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    endpoint = Column(String, nullable=True)
    method = Column(String, nullable=True)
    parameters = Column(JSON, nullable=True)
    headers = Column(JSON, nullable=True)
    action_type = Column(String, default="custom")
    config = Column(JSON, nullable=True)
    yaml_spec = Column(Text, nullable=True)
    api_key = Column(String, nullable=True) 
    is_active = Column(Boolean, default=True)

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    system_prompt = Column(Text)
    llm_id = Column(Integer, ForeignKey("llms.id"))
    actions = Column(JSON)  # list of action configurations with prompts
    config = Column(JSON)   # agent-specific configuration
    is_active = Column(Boolean, default=True)

    llm = relationship("LLM")

