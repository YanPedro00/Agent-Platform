from sqlalchemy.orm import Session
from app import models, schemas
from app.llm_manager import LLMManager
from app.action_manager import ActionManager
from app.utils import (
    safe_json_parse, ContextBuilder, clean_action_result,
    handle_exceptions, format_llm_prompt
)
from typing import List, Dict, Any
import json
import re

class AgentManager:
    @staticmethod
    def extract_parameters_from_context(db: Session, action_name: str, context: Dict[str, Any], llm: models.LLM) -> Dict[str, Any]:
        """Extract parameters for an action from the conversation context using LLM"""
        try:
            # Get the action to understand what parameters it needs
            action = db.query(models.Action).filter(models.Action.name == action_name).first()
            if not action or not action.parameters:
                return {}
            
            # Build a focused prompt to extract only the necessary parameters
            extraction_prompt = f"""Extract specific parameters for the {action_name} action from the user's request and context.

ACTION: {action_name}
REQUIRED PARAMETERS: {json.dumps(action.parameters, indent=2)}

USER REQUEST: {context.get('user_input', '')}

EXTRACTION RULES:
1. Look for exact matches to the required parameters in the user's request
2. For "id" parameters: Extract incident IDs, ticket numbers, case numbers, etc.
3. For "name" parameters: Extract usernames, service names, etc.
4. For "status" parameters: Extract status values like "open", "closed", "pending"
5. For "date" parameters: Extract dates, times, or relative terms like "today"
6. Only include parameters that are clearly mentioned or can be inferred
7. Return ONLY a JSON object with the found parameters
8. If no relevant parameters are found, return an empty object {{}}

EXAMPLES:
- "incident 1124-auth-failure" → {{"id": "1124-auth-failure"}}
- "user john.doe tickets" → {{"user": "john.doe"}}
- "open incidents today" → {{"status": "open", "date": "today"}}

Extract parameters now (JSON only):"""

            # Use LLM to extract parameters
            response = LLMManager.call_llm(llm, extraction_prompt, temperature=0.1)
            
            # Try to parse the JSON response
            extracted_params = safe_json_parse(response)
            if extracted_params:
                # Filter out null values and validate against action parameters
                valid_params = {}
                for param_name, param_value in extracted_params.items():
                    if param_name in action.parameters and param_value is not None:
                        valid_params[param_name] = param_value
                return valid_params
                
            return {}
            
        except Exception as e:
            print(f"Error extracting parameters for {action_name}: {e}")
            return {}

    @staticmethod
    def build_enhanced_context(context: Dict[str, Any], action_result: Dict[str, Any], action_name: str) -> Dict[str, Any]:
        """Build enhanced context with action results and extracted information"""
        # Use ContextBuilder for cleaner context management
        builder = ContextBuilder(
            context.get("user_input", ""),
            context.get("agent_name", "")
        )
        
        # Copy existing context
        builder.context.update(context)
        
        # Add action result
        builder.add_action_result(action_name, action_result)
        
        # Add thinking if it's a thinking action
        if action_result.get("type") == "thinking":
            builder.add_thinking(action_name, action_result.get("content", ""))
        
        # Add conversation entry
        builder.add_conversation_entry(
            action_name,
            action_result.get("type", "unknown"),
            action_result.get("content", ""),
            action_result.get("background", False)
        )
        
        return builder.build()

    @staticmethod
    def create_agent(db: Session, agent: schemas.AgentCreate):
        # Check for duplicate names
        existing_agent = db.query(models.Agent).filter(models.Agent.name == agent.name).first()
        if existing_agent:
            raise ValueError(f"Agent with name '{agent.name}' already exists")
        
        # Validate that the LLM exists
        llm = db.query(models.LLM).filter(models.LLM.id == agent.llm_id).first()
        if not llm:
            raise ValueError(f"LLM with id {agent.llm_id} not found")
        
        # Validate that all actions exist
        for action_config in agent.actions:
            action = db.query(models.Action).filter(models.Action.name == action_config.action_name).first()
            if not action:
                raise ValueError(f"Action with name '{action_config.action_name}' not found")
        
        db_agent = models.Agent(
            name=agent.name,
            description=agent.description,
            system_prompt=agent.system_prompt,
            llm_id=agent.llm_id,
            actions=[action.dict() for action in agent.actions],
            conditional_flows=[flow.dict() for flow in agent.conditional_flows] if agent.conditional_flows else [],
            config=agent.config
        )
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        return db_agent

    @staticmethod
    def get_agents(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Agent).offset(skip).limit(limit).all()

    @staticmethod
    def _execute_action_flow(db: Session, agent: models.Agent, actions: List[Dict], shared_context: Dict, llm: models.LLM, input_data: schemas.AgentRun, flow_type: str = "main"):
        """Execute a flow of actions with support for conditional branching and Wait actions"""
        actions_used = []
        background_actions = []
        user_facing_actions = []
        
        for i, action_config in enumerate(actions):
            # Skip actions that don't belong to this flow
            if action_config.get("flow_type", "main") != flow_type:
                continue
                
            action_name = action_config["action_name"]
            print(f"📋 Executing action {i+1}/{len(actions)}: {action_name} (flow: {flow_type})")
            
            actions_used.append(action_name)
            
            # Extract parameters intelligently from context for this action
            extracted_params = AgentManager.extract_parameters_from_context(
                db, action_name, shared_context, llm
            )
            
            print(f"🔍 Extracted parameters for {action_name}: {extracted_params}")
            
            # Prepare action parameters
            action_parameters = {"input": input_data.input}
            action_parameters.update(extracted_params)
            
            # Add validation criteria for Choice actions
            if action_name == "Choice":
                action_parameters["validation_criteria"] = action_config.get("prompt", "Validate the provided information")
            
            # Add wait message for Wait actions
            if action_name == "Wait":
                action_parameters["message"] = action_config.get("prompt", "Please provide additional information to continue.")
                action_parameters["prompt"] = action_config.get("wait_prompt", "What additional information would you like to provide?")
            
            # Add custom prompt for Respond actions
            if action_name == "Respond":
                action_parameters["prompt"] = action_config.get("prompt", "")
            
            # Execute the action with enhanced context and extracted parameters
            action_result = ActionManager.execute_action(
                db, action_name, action_parameters, shared_context
            )
            
            print(f"✅ Action {action_name} completed: {action_result.get('type', 'unknown')} - Success: {action_result.get('success', True)}")
            
            # Handle Wait action - pause execution and return
            if action_result.get("pause_execution"):
                return {
                    "wait_required": True,
                    "wait_message": action_result.get("content", "Please provide additional information."),
                    "wait_prompt": action_result.get("prompt", "What would you like to add?"),
                    "actions_used": actions_used,
                    "background_actions": background_actions,
                    "user_facing_actions": user_facing_actions,
                    "shared_context": shared_context
                }
            
            # Update shared context with action result
            if action_result:
                shared_context = AgentManager.build_enhanced_context(
                    shared_context, action_result, action_name
                )
                
                # Handle Choice action - execute conditional flow
                if action_result.get("conditional_flow"):
                    decision = action_result.get("decision", "invalid")
                    next_flow = "valid_flow" if decision == "valid" else "invalid_flow"
                    
                    print(f"🔀 Choice action decided: {decision} -> executing {next_flow}")
                    
                    # Find and execute the appropriate conditional flow
                    conditional_flows = getattr(agent, 'conditional_flows', []) or []
                    for flow in conditional_flows:
                        if flow.get("choice_action") == action_name:
                            flow_actions = flow.get(next_flow, [])
                            if flow_actions:
                                # Recursively execute the conditional flow
                                agent_manager = AgentManager()
                                conditional_result = agent_manager._execute_action_flow(
                                    db, agent, flow_actions, shared_context, llm, input_data, next_flow
                                )
                                
                                # Merge results
                                actions_used.extend(conditional_result["actions_used"])
                                background_actions.extend(conditional_result["background_actions"])
                                user_facing_actions.extend(conditional_result["user_facing_actions"])
                                shared_context = conditional_result["shared_context"]
                                
                                # Handle wait from conditional flow
                                if conditional_result.get("wait_required"):
                                    return conditional_result
                            break
                    
                    # Add the choice action to background actions
                    background_actions.append({
                        "action": action_name,
                        "result": action_result,
                        "parameters_used": extracted_params,
                        "iteration": len(background_actions) + 1,
                        "choice_decision": decision
                    })
                    
                # Handle other action types
                elif action_result.get("background", False):
                    # Background action (like Thinking) - enriches context
                    background_actions.append({
                        "action": action_name,
                        "result": action_result,
                        "parameters_used": extracted_params,
                        "iteration": len(background_actions) + 1
                    })
                    print(f"🧠 Background action {action_name} added to context")
                    
                elif action_name == "Respond":
                    # User-facing response action
                    user_facing_actions.append({
                        "action": action_name,
                        "result": action_result,
                        "parameters_used": extracted_params,
                        "iteration": len(user_facing_actions) + 1
                    })
                    print(f"💬 Response action {action_name} completed")
                    
                else:
                    # Custom actions (like Rootly API calls)
                    background_actions.append({
                        "action": action_name,
                        "result": action_result,
                        "parameters_used": extracted_params,
                        "iteration": len(background_actions) + 1,
                        "custom_action": True
                    })
                    print(f"🔧 Custom action {action_name} completed and added to context")
        
        return {
            "actions_used": actions_used,
            "background_actions": background_actions,
            "user_facing_actions": user_facing_actions,
            "shared_context": shared_context
        }

    @staticmethod
    def run_agent(db: Session, agent_id: int, input_data: schemas.AgentRun):
        try:
            agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
            if not agent:
                return {"error": f"Agent with id {agent_id} not found"}

            llm = db.query(models.LLM).filter(models.LLM.id == agent.llm_id).first()
            if not llm:
                return {"error": f"LLM with id {agent.llm_id} not found"}

            # Initialize enhanced context using ContextBuilder
            context_builder = ContextBuilder(input_data.input, agent.name)
            context_builder.context.update({
                "available_actions": [action["action_name"] for action in agent.actions],
                "extracted_entities": {},  # Store extracted IDs, names, etc.
                "session_data": {}  # Persistent data across actions
            })
            shared_context = context_builder.build()

            # Execute actions in sequence with intelligent parameter extraction
            actions_used = []
            background_actions = []
            user_facing_actions = []
            
            # Check if agent has required actions (in main flow or conditional flows)
            has_respond_action = any(action["action_name"] == "Respond" for action in agent.actions)
            has_wait_action = any(action["action_name"] == "Wait" for action in agent.actions)
            
            # Also check conditional flows for Respond actions
            if not has_respond_action and hasattr(agent, 'conditional_flows') and agent.conditional_flows:
                for flow in agent.conditional_flows:
                    if isinstance(flow, dict):
                        # Check valid_flow
                        if flow.get("valid_flow"):
                            has_respond_action = has_respond_action or any(
                                action.get("action_name") == "Respond" for action in flow["valid_flow"]
                            )
                        # Check invalid_flow
                        if flow.get("invalid_flow"):
                            has_respond_action = has_respond_action or any(
                                action.get("action_name") == "Respond" for action in flow["invalid_flow"]
                            )
            
            # If agent has Wait action, it's valid even without immediate Respond
            # because Respond will come after user provides additional input
            if not has_respond_action and not has_wait_action:
                return {
                    "response": None,
                    "actions_used": [],
                    "background_actions": [],
                    "user_facing_actions": [],
                    "message": "Agent must have either a Respond action or a Wait action to interact with users"
                }
            
            print(f"🤖 Agent {agent.name} starting execution with {len(agent.actions)} actions")
            
            # Execute actions with support for conditional flows and Wait actions
            execution_result = AgentManager._execute_action_flow(
                db, agent, agent.actions, shared_context, llm, input_data
            )
            
            actions_used = execution_result["actions_used"]
            background_actions = execution_result["background_actions"]
            user_facing_actions = execution_result["user_facing_actions"]
            shared_context = execution_result["shared_context"]
            
            # Handle Wait action result if present
            if execution_result.get("wait_required"):
                return {
                    "wait_required": True,
                    "wait_message": execution_result["wait_message"],
                    "wait_prompt": execution_result["wait_prompt"],
                    "session_context": shared_context,
                    "actions_used": actions_used,
                    "background_actions": background_actions,
                    "user_facing_actions": user_facing_actions
                }

            # Extract final response from Respond actions
            final_user_message = None
            if user_facing_actions:
                for action in reversed(user_facing_actions):
                    if action["action"] == "Respond" and action["result"].get("type") == "response":
                        final_user_message = action["result"]["content"]
                        break
            
            if final_user_message is None:
                return {
                    "response": None,
                    "actions_used": actions_used,
                    "background_actions": [],
                    "user_facing_actions": [],
                    "message": "No response generated by Respond action"
                }

            # Clean up actions for response (remove circular references and sensitive data)
            clean_background_actions = [clean_action_result(action) for action in background_actions]
            
            clean_user_facing_actions = []
            for action in user_facing_actions:
                clean_action = {
                    "action": action.get("action", "Unknown"),
                    "iteration": action.get("iteration", 0),
                    "parameters_used": action.get("parameters_used", {}),
                    "result": {
                        "type": action.get("result", {}).get("type", "unknown"),
                        "content": action.get("result", {}).get("content", "No content"),
                        "background": action.get("result", {}).get("background", False),
                        "user_message": action.get("result", {}).get("user_message", False)
                    }
                }
                clean_user_facing_actions.append(clean_action)
            
            print(f"🎉 Agent execution completed successfully. Response generated: {bool(final_user_message)}")
            
            return {
                "response": final_user_message,
                "actions_used": actions_used,
                "background_actions": clean_background_actions,
                "user_facing_actions": clean_user_facing_actions,
                "context_summary": {
                    "entities_extracted": len(shared_context.get("extracted_entities", {})),
                    "thinking_steps": len(shared_context.get("thinking_process", [])),
                    "data_retrieved": len([k for k in shared_context.keys() if k.endswith("_data")])
                }
            }

        except Exception as e:
            print(f"❌ Error running agent: {str(e)}")
            return {"error": f"Error running agent: {str(e)}"}

    @staticmethod
    def _parse_action_call(response: str):
        # Try to find action call in the response
        # Look for patterns like "ACTION: action_name" or "USE_ACTION: action_name"
        action_patterns = [
            r'ACTION:\s*(\w+)',
            r'USE_ACTION:\s*(\w+)',
            r'EXECUTE:\s*(\w+)',
            r'CALL:\s*(\w+)'
        ]
        
        for pattern in action_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                action_name = match.group(1)
                # Try to extract parameters from the response
                parameters = AgentManager._parse_parameters(response)
                return {
                    "action_name": action_name,
                    "parameters": parameters
                }
        return None

    @staticmethod
    def _parse_parameters(response: str):
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {}

    @staticmethod
    def update_agent(db: Session, agent_id: int, agent: schemas.AgentUpdate):
        db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
        if not db_agent:
            return None

        # Check for duplicate names if name is being updated
        if agent.name and agent.name != db_agent.name:
            existing_agent = db.query(models.Agent).filter(models.Agent.name == agent.name).first()
            if existing_agent:
                raise ValueError(f"Agent with name '{agent.name}' already exists")

        # Validate that the LLM exists if llm_id is being updated
        if agent.llm_id and agent.llm_id != db_agent.llm_id:
            llm = db.query(models.LLM).filter(models.LLM.id == agent.llm_id).first()
            if not llm:
                raise ValueError(f"LLM with id {agent.llm_id} not found")

        # Validate that all actions exist if actions are being updated
        if agent.actions:
            for action_config in agent.actions:
                action = db.query(models.Action).filter(models.Action.name == action_config.action_name).first()
                if not action:
                    raise ValueError(f"Action with name '{action_config.action_name}' not found")

        update_data = agent.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_agent, field, value)

        db.commit()
        db.refresh(db_agent)
        return db_agent

    @staticmethod
    def delete_agent(db: Session, agent_id: int):
        db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
        if not db_agent:
            return False

        db.delete(db_agent)
        db.commit()
        return True