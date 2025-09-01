from sqlalchemy.orm import Session
from app import models, schemas
from app.llm_manager import LLMManager
from app.action_manager import ActionManager
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
            try:
                # Clean the response to extract JSON
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    extracted_params = json.loads(json_match.group())
                    # Filter out null values and validate against action parameters
                    valid_params = {}
                    for param_name, param_value in extracted_params.items():
                        if param_name in action.parameters and param_value is not None:
                            valid_params[param_name] = param_value
                    return valid_params
            except json.JSONDecodeError:
                pass
                
            return {}
            
        except Exception as e:
            print(f"Error extracting parameters for {action_name}: {e}")
            return {}

    @staticmethod
    def build_enhanced_context(context: Dict[str, Any], action_result: Dict[str, Any], action_name: str) -> Dict[str, Any]:
        """Build enhanced context with action results and extracted information"""
        enhanced_context = context.copy()
        
        # Add action result to context
        enhanced_context["action_results"][action_name] = action_result
        
        # Extract and store key information from action results
        if action_result.get("type") == "custom_action" and action_result.get("success"):
            # For custom actions, extract useful data
            result_data = action_result.get("result", {})
            if isinstance(result_data, dict):
                # Store filtered data if available (from YAML schema filtering)
                if "filtered_data" in result_data:
                    enhanced_context[f"{action_name}_data"] = result_data["filtered_data"]
                elif "data" in result_data:
                    enhanced_context[f"{action_name}_data"] = result_data["data"]
        
        # For thinking actions, add to thinking process
        if action_result.get("type") == "thinking":
            enhanced_context["thinking_process"].append({
                "action": action_name,
                "content": action_result.get("content", ""),
                "timestamp": "now"  # Could add actual timestamp
            })
        
        # Update conversation history
        if "conversation_history" not in enhanced_context:
            enhanced_context["conversation_history"] = []
        
        enhanced_context["conversation_history"].append({
            "action": action_name,
            "type": action_result.get("type", "unknown"),
            "content": action_result.get("content", ""),
            "background": action_result.get("background", False)
        })
        
        return enhanced_context

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
    def run_agent(db: Session, agent_id: int, input_data: schemas.AgentRun):
        try:
            agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
            if not agent:
                return {"error": f"Agent with id {agent_id} not found"}

            llm = db.query(models.LLM).filter(models.LLM.id == agent.llm_id).first()
            if not llm:
                return {"error": f"LLM with id {agent.llm_id} not found"}

            # Initialize enhanced context for intelligent action execution
            shared_context = {
                "user_input": input_data.input,
                "agent_name": agent.name,
                "available_actions": [action["action_name"] for action in agent.actions],
                "action_results": {},
                "thinking_process": [],
                "conversation_history": [],
                "extracted_entities": {},  # Store extracted IDs, names, etc.
                "session_data": {}  # Persistent data across actions
            }

            # Execute actions in sequence with intelligent parameter extraction
            actions_used = []
            background_actions = []
            user_facing_actions = []
            
            # Check if agent has required actions
            has_respond_action = any(action["action_name"] == "Respond" for action in agent.actions)
            if not has_respond_action:
                return {
                    "response": None,
                    "actions_used": [],
                    "background_actions": [],
                    "user_facing_actions": [],
                    "message": "Agent has no Respond action configured"
                }
            
            print(f"🤖 Agent {agent.name} starting execution with {len(agent.actions)} actions")
            
            # Execute each action in the configured order
            for i, action_config in enumerate(agent.actions):
                action_name = action_config["action_name"]
                print(f"📋 Executing action {i+1}/{len(agent.actions)}: {action_name}")
                
                actions_used.append(action_name)
                
                # Extract parameters intelligently from context for this action
                extracted_params = AgentManager.extract_parameters_from_context(
                    db, action_name, shared_context, llm
                )
                
                print(f"🔍 Extracted parameters for {action_name}: {extracted_params}")
                
                # Prepare action parameters
                action_parameters = {"input": input_data.input}
                action_parameters.update(extracted_params)
                
                # Execute the action with enhanced context and extracted parameters
                action_result = ActionManager.execute_action(
                    db, action_name, action_parameters, shared_context
                )
                
                print(f"✅ Action {action_name} completed: {action_result.get('type', 'unknown')} - Success: {action_result.get('success', True)}")
                
                # Update shared context with action result using enhanced context builder
                if action_result:
                    shared_context = AgentManager.build_enhanced_context(
                        shared_context, action_result, action_name
                    )
                    
                    # Handle different types of actions
                    if action_result.get("background", False):
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
            clean_background_actions = []
            for action in background_actions:
                clean_action = {
                    "action": action.get("action", "Unknown"),
                    "iteration": action.get("iteration", 0),
                    "parameters_used": action.get("parameters_used", {}),
                    "custom_action": action.get("custom_action", False),
                    "result": {
                        "type": action.get("result", {}).get("type", "unknown"),
                        "success": action.get("result", {}).get("success", True),
                        "background": action.get("result", {}).get("background", True)
                    }
                }
                
                # Add summary of result content without exposing sensitive data
                result = action.get("result", {})
                if result.get("type") == "thinking":
                    clean_action["result"]["summary"] = "Thinking process completed"
                elif result.get("type") == "custom_action":
                    if result.get("success"):
                        clean_action["result"]["summary"] = f"API call successful (status: {result.get('status_code', 'unknown')})"
                    else:
                        clean_action["result"]["summary"] = f"API call failed: {result.get('error', 'Unknown error')}"
                
                clean_background_actions.append(clean_action)
            
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