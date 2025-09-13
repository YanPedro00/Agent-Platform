from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging

from app import models, schemas, database
from app.llm_manager import LLMManager
from app.agent_manager import AgentManager
from app.action_manager import ActionManager

app = FastAPI(
    title="Agent Platform API",
    version="0.1.0",
    description="""
    ## Agent Platform API

    This API allows you to manage intelligent agents, custom actions, and LLMs.

    ### Main features:
    - **LLM Management**: Configure different language models
    - **Custom Actions**: Create custom actions via YAML/OpenAPI
    - **Intelligent Agents**: Create agents with configurable action flows
    - **Agent Execution**: Execute agents with intelligent context
    - **Action Testing**: Test custom actions with parameters

    ### Useful links:
    - **Frontend**: [http://localhost:3000](http://localhost:3000)
    - **Interactive Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
    - **Redoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
    """,
    contact={
        "name": "Agent Platform",
        "url": "http://localhost:3000",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Local Development"
        },
        {
            "url": "http://172.19.0.2:8000",
            "description": "Docker Container"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://172.19.0.3:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging to filter out webpack dev server noise
class WebpackLogFilter(logging.Filter):
    def filter(self, record):
        # Filter out webpack hot-update and favicon requests
        if hasattr(record, 'getMessage'):
            message = record.getMessage()
            if ('.hot-update.json' in message or 
                '.hot-update.js' in message or 
                'favicon.ico' in message):
                return False
        return True

# Apply filter to uvicorn access logger
logging.getLogger("uvicorn.access").addFilter(WebpackLogFilter())

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=database.engine)
    create_native_actions()
    print("Database tables created successfully")

def create_native_actions():
    db = database.SessionLocal()
    try:
        # Check if native actions already exist
        thinking_action = db.query(models.Action).filter(models.Action.name == "Thinking").first()
        if not thinking_action:
            thinking_action = models.Action(
                name="Thinking",
                description="Use the LLM to think step by step about a problem or situation. This action works in the background and is not shown to the user.",
                action_type="native",
                config={"prompt": "Think step by step about the following problem or situation: {input}\n\nConsider all available information and context. Break down the problem into smaller parts and analyze each one carefully. This thinking process will help determine the best course of action."}
            )
            db.add(thinking_action)

        respond_action = db.query(models.Action).filter(models.Action.name == "Respond").first()
        if not respond_action:
            respond_action = models.Action(
                name="Respond",
                description="Generate a focused and direct response to the user based on all available information and context.",
                action_type="native",
                config={"prompt": "Based on all the information gathered and the context available, provide a focused and helpful response to the user about: {input}\n\nMake sure your response is:\n- Clear and easy to understand\n- Based on the facts and context available\n- Actionable when possible\n- Professional and helpful"}
            )
            db.add(respond_action)

        # Wait action
        wait_action = db.query(models.Action).filter(models.Action.name == "Wait").first()
        if not wait_action:
            wait_action = models.Action(
                name="Wait",
                description="Pauses execution and prompts user for additional input",
                action_type="native",
                config={"prompt": "Please provide additional information to continue: {input}"}
            )
            db.add(wait_action)

        # Choice action
        choice_action = db.query(models.Action).filter(models.Action.name == "Choice").first()
        if not choice_action:
            choice_action = models.Action(
                name="Choice",
                description="Makes decisions based on validation criteria and creates conditional flows",
                action_type="native",
                config={"prompt": "Validate the following information based on the criteria: {input}"}
            )
            db.add(choice_action)

        db.commit()
    except Exception as e:
        print(f"Error creating native actions: {e}")
        db.rollback()
    finally:
        db.close()

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Agent Platform API"}

# LLM endpoints
@app.post("/llms/", response_model=schemas.LLM)
def create_llm(llm: schemas.LLMCreate, db: Session = Depends(get_db)):
    return LLMManager.create_llm(db=db, llm=llm)

@app.get("/llms/", response_model=List[schemas.LLM])
def read_llms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return LLMManager.get_llms(db=db, skip=skip, limit=limit)

# Agent endpoints
@app.post("/agents/", response_model=schemas.Agent)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    return AgentManager.create_agent(db=db, agent=agent)

@app.get("/agents/", response_model=List[schemas.Agent])
def read_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return AgentManager.get_agents(db=db, skip=skip, limit=limit)

@app.post("/agents/{agent_id}/run")
def run_agent(agent_id: int, input_data: schemas.AgentRun, db: Session = Depends(get_db)):
    try:
        return AgentManager.run_agent(db=db, agent_id=agent_id, input_data=input_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/agents/{agent_id}/continue")
def continue_agent(agent_id: int, continue_data: dict, db: Session = Depends(get_db)):
    """Continue agent execution after a Wait action with additional user input"""
    try:
        # Extract session context and new input
        session_context = continue_data.get("session_context", {})
        additional_input = continue_data.get("additional_input", "")
        
        # Ensure session_context has required fields
        if "action_results" not in session_context:
            session_context["action_results"] = {}
        if "thinking_process" not in session_context:
            session_context["thinking_process"] = []
        if "conversation_history" not in session_context:
            session_context["conversation_history"] = []
        if "extracted_entities" not in session_context:
            session_context["extracted_entities"] = {}
        if "session_data" not in session_context:
            session_context["session_data"] = {}
        
        # Update the context with new input
        original_input = session_context.get("user_input", "")
        combined_input = f"{original_input} {additional_input}".strip()
        session_context["user_input"] = combined_input
        session_context["additional_inputs"] = session_context.get("additional_inputs", [])
        session_context["additional_inputs"].append(additional_input)
        
        # Get the agent
        agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Get the LLM
        llm = db.query(models.LLM).filter(models.LLM.id == agent.llm_id).first()
        if not llm:
            raise HTTPException(status_code=404, detail="LLM not found")
        
        # Continue execution from where it left off
        # Find the next action after the last executed action
        actions_used = session_context.get("actions_used", [])
        if not actions_used:
            # If no actions were used, start from the beginning
            return AgentManager.run_agent(db=db, agent_id=agent_id, input_data=schemas.AgentRun(input=combined_input))
        
        # Find the next action to execute
        last_action_index = len(actions_used) - 1
        if last_action_index + 1 < len(agent.actions):
            # Continue with remaining actions
            remaining_actions = agent.actions[last_action_index + 1:]
            
            # Execute remaining actions
            agent_manager = AgentManager()
            execution_result = agent_manager._execute_action_flow(
                db, agent, remaining_actions, session_context, llm, schemas.AgentRun(input=combined_input)
            )
            
            # Merge with previous results
            all_actions_used = actions_used + execution_result["actions_used"]
            all_background_actions = session_context.get("background_actions", []) + execution_result["background_actions"]
            all_user_facing_actions = session_context.get("user_facing_actions", []) + execution_result["user_facing_actions"]
            
            # Handle Wait action result if present
            if execution_result.get("wait_required"):
                return {
                    "wait_required": True,
                    "wait_message": execution_result["wait_message"],
                    "wait_prompt": execution_result["wait_prompt"],
                    "session_context": execution_result["shared_context"],
                    "actions_used": all_actions_used,
                    "background_actions": all_background_actions,
                    "user_facing_actions": all_user_facing_actions
                }
            
            # Extract final response
            final_user_message = None
            if execution_result["user_facing_actions"]:
                for action in reversed(execution_result["user_facing_actions"]):
                    if action["action"] == "Respond" and action["result"].get("type") == "response":
                        final_user_message = action["result"]["content"]
                        break
            
            return {
                "response": final_user_message,
                "actions_used": all_actions_used,
                "background_actions": all_background_actions,
                "user_facing_actions": all_user_facing_actions,
                "context_summary": {
                    "entities_extracted": len(execution_result["shared_context"].get("extracted_entities", {})),
                    "thinking_steps": len(execution_result["shared_context"].get("thinking_process", [])),
                    "data_retrieved": len([k for k in execution_result["shared_context"].keys() if k.endswith("_data")])
                }
            }
        else:
            # No more actions to execute
            return {
                "response": "No more actions to execute",
                "actions_used": actions_used,
                "background_actions": session_context.get("background_actions", []),
                "user_facing_actions": session_context.get("user_facing_actions", [])
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error continuing agent execution: {str(e)}")

# Action endpoints
@app.post("/actions/", response_model=schemas.Action)
def create_action(action: schemas.ActionCreate, db: Session = Depends(get_db)):
    return ActionManager.create_action(db=db, action=action)

@app.get("/actions/", response_model=List[schemas.Action])
def read_actions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ActionManager.get_actions(db=db, skip=skip, limit=limit)

@app.get("/actions/native")
def get_native_actions():
    """Get available native actions with their descriptions and parameters"""
    return {
        "native_actions": [
            {
                "name": "Thinking",
                "description": "Analyzes user input and extracts key information for subsequent actions",
                "type": "native",
                "background": True,
                "parameters": {
                    "input": {"type": "string", "required": True, "description": "User input to analyze"}
                },
                "example_prompt": "Analyze the user's request and extract the incident ID they want to know about"
            },
            {
                "name": "Respond",
                "description": "Generates user-facing responses using the accumulated context",
                "type": "native",
                "background": False,
                "parameters": {
                    "input": {"type": "string", "required": True, "description": "User input to respond to"}
                },
                "example_prompt": "Present the incident information to the user in a clear and organized way"
            },
            {
                "name": "Wait",
                "description": "Pauses execution and prompts user for additional input",
                "type": "native",
                "background": False,
                "parameters": {
                    "message": {"type": "string", "required": False, "description": "Message to display to user"},
                    "prompt": {"type": "string", "required": False, "description": "Prompt for additional input"}
                },
                "example_prompt": "Please provide the incident ID you want to investigate",
                "special_properties": {
                    "pause_execution": True,
                    "user_input_required": True
                }
            },
            {
                "name": "Choice",
                "description": "Makes decisions based on validation criteria and creates conditional flows",
                "type": "native",
                "background": True,
                "parameters": {
                    "validation_criteria": {"type": "string", "required": True, "description": "Criteria to validate against"},
                    "input": {"type": "string", "required": True, "description": "Input to validate"}
                },
                "example_prompt": "Validate if the provided incident ID exists and is accessible",
                "special_properties": {
                    "conditional_flow": True,
                    "creates_branches": True,
                    "flows": ["valid_flow", "invalid_flow"]
                }
            }
        ]
    }

# LLM endpoints - Adicionar PUT e DELETE
@app.put("/llms/{llm_id}", response_model=schemas.LLM)
def update_llm(llm_id: int, llm: schemas.LLMUpdate, db: Session = Depends(get_db)):
    return LLMManager.update_llm(db=db, llm_id=llm_id, llm=llm)

@app.delete("/llms/{llm_id}")
def delete_llm(llm_id: int, db: Session = Depends(get_db)):
    return LLMManager.delete_llm(db=db, llm_id=llm_id)

# Agent endpoints - Adicionar PUT e DELETE
@app.put("/agents/{agent_id}", response_model=schemas.Agent)
def update_agent(agent_id: int, agent: schemas.AgentUpdate, db: Session = Depends(get_db)):
    return AgentManager.update_agent(db=db, agent_id=agent_id, agent=agent)

@app.delete("/agents/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    return AgentManager.delete_agent(db=db, agent_id=agent_id)

# Action endpoints - Adicionar PUT e DELETE
@app.put("/actions/{action_id}", response_model=schemas.Action)
def update_action(action_id: int, action: schemas.ActionUpdate, db: Session = Depends(get_db)):
    return ActionManager.update_action(db=db, action_id=action_id, action=action)

@app.delete("/actions/{action_id}")
def delete_action(action_id: int, db: Session = Depends(get_db)):
    return ActionManager.delete_action(db=db, action_id=action_id)

@app.post("/actions/parse-yaml/")
async def parse_yaml(yaml_data: dict, db: Session = Depends(get_db)):
    try:
        yaml_spec = yaml_data.get("yaml_spec", "")
        if not yaml_spec:
            raise HTTPException(status_code=400, detail="YAML specification is required")
        
        api_key = yaml_data.get("api_key", "")
        
        parameters = ActionManager.generate_parameters_from_yaml(yaml_spec)
        headers = ActionManager.generate_headers_from_yaml(yaml_spec, api_key)

        # Extract endpoint from YAML
        spec = ActionManager.parse_yaml_spec(yaml_spec)
        endpoint = ""
        if 'paths' in spec:
            # Get the server URL if available
            server_url = ""
            if 'servers' in spec and len(spec['servers']) > 0:
                server_url = spec['servers'][0].get('url', '')
            
            # Get the first path
            for path in spec['paths']:
                endpoint = server_url + path
                break

        # Extract response schema for preview
        response_schema = ActionManager.extract_response_schema_from_yaml(yaml_spec)
        
        return {
            "parameters": parameters,
            "headers": headers,
            "endpoint": endpoint,
            "response_schema": response_schema,
            "schema_preview": ActionManager._generate_schema_preview(response_schema) if response_schema else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error parsing YAML: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/actions/{action_id}/test")
def test_action(action_id: int, test_data: dict, db: Session = Depends(get_db)):
    """Test a custom action with provided parameters"""
    try:
        # Get the action
        action = db.query(models.Action).filter(models.Action.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        # Extract test parameters and context
        parameters = test_data.get("parameters", {})
        context = test_data.get("context", {})
        
        # Execute the action
        result = ActionManager.execute_action(db, action.name, parameters, context)
        
        return {
            "success": True,
            "action_name": action.name,
            "action_type": action.action_type,
            "parameters_used": parameters,
            "context_used": context,
            "result": result,
            "timestamp": str(db.query(models.Action).first())  # Just to get current time
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Action execution error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/actions/test-by-name/{action_name}")
def test_action_by_name(action_name: str, test_data: dict, db: Session = Depends(get_db)):
    """Test a custom action by name with provided parameters"""
    try:
        # Get the action by name
        action = db.query(models.Action).filter(models.Action.name == action_name).first()
        if not action:
            raise HTTPException(status_code=404, detail=f"Action '{action_name}' not found")
        
        # Extract test parameters and context
        parameters = test_data.get("parameters", {})
        context = test_data.get("context", {})
        
        # Execute the action
        result = ActionManager.execute_action(db, action_name, parameters, context)
        
        return {
            "success": True,
            "action_name": action.name,
            "action_type": action.action_type,
            "parameters_used": parameters,
            "context_used": context,
            "result": result,
            "execution_time": "immediate"  # Could add actual timing later
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Action execution error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/actions/{action_id}/fix-endpoint")
def fix_action_endpoint(action_id: int, db: Session = Depends(get_db)):
    """Fix incomplete endpoint URL for an action"""
    try:
        # Get the action
        action = db.query(models.Action).filter(models.Action.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        original_endpoint = action.endpoint
        fixed_endpoint = ActionManager._fix_endpoint_url(action.endpoint, action.name)
        
        if fixed_endpoint != original_endpoint:
            # Update the action with the fixed endpoint
            action.endpoint = fixed_endpoint
            db.commit()
            db.refresh(action)
            
            return {
                "success": True,
                "message": "Endpoint fixed successfully",
                "original_endpoint": original_endpoint,
                "fixed_endpoint": fixed_endpoint,
                "action_name": action.name
            }
        else:
            return {
                "success": False,
                "message": "Endpoint is already complete or could not be automatically fixed",
                "current_endpoint": original_endpoint,
                "action_name": action.name,
                "suggestion": "Please manually update the endpoint to include the full URL (e.g., https://api.rootly.com/v1/incidents/{id})"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Agent actions management endpoints
@app.put("/agents/{agent_id}/actions", response_model=schemas.Agent)
def update_agent_actions(agent_id: int, actions_data: dict, db: Session = Depends(get_db)):
    """Update the actions configuration for an agent"""
    try:
        agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        new_actions = actions_data.get("actions", [])
        
        # Validate that all referenced actions exist
        for action_config in new_actions:
            action_name = action_config.get("action_name")
            if not action_name:
                raise HTTPException(status_code=400, detail="Each action must have an action_name")
            
            action = db.query(models.Action).filter(models.Action.name == action_name).first()
            if not action:
                raise HTTPException(status_code=400, detail=f"Action '{action_name}' not found")
        
        # Update the agent's actions
        agent.actions = new_actions
        db.commit()
        db.refresh(agent)
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/agents/{agent_id}/actions")
def get_agent_actions(agent_id: int, db: Session = Depends(get_db)):
    """Get the actions configuration for an agent with detailed action information"""
    try:
        agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get detailed information about each action
        detailed_actions = []
        for action_config in agent.actions or []:
            action_name = action_config.get("action_name")
            action = db.query(models.Action).filter(models.Action.name == action_name).first()
            
            if action:
                detailed_action = {
                    "action_name": action.name,
                    "action_id": action.id,
                    "description": action.description,
                    "action_type": action.action_type,
                    "prompt": action_config.get("prompt", ""),
                    "order": action_config.get("order", 0),
                    "parameters": action.parameters,
                    "endpoint": action.endpoint,
                    "method": action.method,
                    "is_active": action.is_active
                }
            else:
                # Action not found - mark as invalid
                detailed_action = {
                    "action_name": action_name,
                    "action_id": None,
                    "description": "Action not found",
                    "action_type": "unknown",
                    "prompt": action_config.get("prompt", ""),
                    "order": action_config.get("order", 0),
                    "parameters": {},
                    "endpoint": "",
                    "method": "",
                    "is_active": False,
                    "error": "Action not found in database"
                }
            
            detailed_actions.append(detailed_action)
        
        return {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "actions": detailed_actions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)