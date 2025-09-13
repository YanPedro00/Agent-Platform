from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

# Agent Action Config Schemas
class AgentActionConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    action_name: str
    prompt: str  # Prompt template for this action
    order: Optional[int] = None  # Order in the flow
    flow_type: Optional[str] = "main"  # main, valid_flow, invalid_flow
    parent_choice_action: Optional[str] = None  # For conditional flows
    
class ConditionalFlow(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    choice_action: str  # Name of the Choice action
    valid_flow: List[AgentActionConfig]  # Actions to execute if validation passes
    invalid_flow: List[AgentActionConfig]  # Actions to execute if validation fails

# LLM Schemas
class LLMBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str
    provider: str
    model_name: str
    base_url: Optional[str] = None
    context_window: Optional[int] = 4096
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.1

class LLMCreate(LLMBase):
    api_key: Optional[str] = None

class LLMUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    is_active: Optional[bool] = None

class LLM(LLMBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# Action Schemas
class ActionBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str
    description: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    action_type: str = "custom"
    config: Optional[Dict[str, Any]] = None
    yaml_spec: Optional[str] = None
    api_key: Optional[str] = None  # Novo campo

class ActionCreate(ActionBase):
    pass

class ActionUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    description: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    yaml_spec: Optional[str] = None
    api_key: Optional[str] = None  # Novo campo
    is_active: Optional[bool] = None

class Action(ActionBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# Agent Schemas
class AgentBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str
    description: str
    system_prompt: str
    llm_id: int
    actions: List[AgentActionConfig]  # List of action configurations
    conditional_flows: Optional[List[ConditionalFlow]] = []  # Conditional flows for Choice actions
    config: Dict[str, Any]

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_id: Optional[int] = None
    actions: Optional[List[AgentActionConfig]] = None
    conditional_flows: Optional[List[ConditionalFlow]] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class Agent(AgentBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class AgentRun(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    input: str
    parameters: Optional[Dict[str, Any]] = None