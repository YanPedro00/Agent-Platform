from sqlalchemy.orm import Session
from app import models, schemas
from app.utils import (
    safe_json_parse, mask_sensitive_fields, validate_url, 
    extract_id_from_url, handle_exceptions, build_error_response,
    build_success_response, sanitize_yaml_content
)
import requests
import json
import yaml
from typing import Dict, Any

class ActionManager:
    @staticmethod
    def create_action(db: Session, action: schemas.ActionCreate):
        # Check for duplicate names
        existing_action = db.query(models.Action).filter(models.Action.name == action.name).first()
        if existing_action:
            raise ValueError(f"Action with name '{action.name}' already exists")
        
        # Sanitize YAML spec to remove API keys before storing
        sanitized_yaml_spec = sanitize_yaml_content(action.yaml_spec, action.api_key)
        
        db_action = models.Action(
            name=action.name,
            description=action.description,
            endpoint=action.endpoint,
            method=action.method,
            parameters=action.parameters,
            headers=action.headers,
            action_type=action.action_type,
            config=action.config,
            yaml_spec=sanitized_yaml_spec,
            api_key=action.api_key
        )
        db.add(db_action)
        db.commit()
        db.refresh(db_action)
        return db_action

    @staticmethod
    def get_actions(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Action).offset(skip).limit(limit).all()

    @staticmethod
    def execute_action(db: Session, action_name: str, parameters: dict, context: dict = None):
        action = db.query(models.Action).filter(models.Action.name == action_name).first()
        if not action:
            raise ValueError(f"Action with name {action_name} not found")

        if action.action_type == "native":
            return ActionManager._execute_native_action(db, action, parameters, context)
        else:
            return ActionManager._execute_custom_action(action, parameters, context)

    @staticmethod
    def _execute_native_action(db: Session, action: models.Action, parameters: dict, context: dict = None):
        # For native actions, we process them based on their type
        if action.name == "Thinking":
            # Thinking action analyzes user input and extracts key information for other actions
            user_input = parameters.get('input', context.get('user_input', 'No input provided'))
            
            thinking_prompt = f"""Analyze the user's request and extract key information that will be useful for subsequent actions.

USER REQUEST: {user_input}

ANALYSIS TASKS:
1. Identify the main intent/goal of the user's request
2. Extract specific entities (IDs, names, dates, etc.) mentioned
3. Determine what type of information or action the user needs
4. Note any specific requirements or constraints mentioned
5. Summarize the key points that other actions should focus on

Provide a focused analysis that highlights the most important aspects for fulfilling this request:"""
            
            return {
                "type": "thinking",
                "content": thinking_prompt,
                "background": True,  # This indicates it's a background process
                "purpose": "analysis_and_extraction"
            }
        
        elif action.name == "Wait":
            # Wait action pauses execution and prompts user for additional input
            wait_message = parameters.get('message', 'Please provide additional information to continue.')
            wait_prompt = parameters.get('prompt', 'What additional information would you like to provide?')
            
            return {
                "type": "wait",
                "content": wait_message,
                "prompt": wait_prompt,
                "background": False,
                "user_input_required": True,
                "pause_execution": True
            }
        
        elif action.name == "Choice":
            # Choice action makes decisions based on validation and creates conditional flows
            from app.llm_manager import LLMManager
            from app.models import Agent
            
            # Get the agent and LLM from context
            agent_name = context.get("agent_name") if context else None
            if agent_name:
                agent = db.query(Agent).filter(Agent.name == agent_name).first()
                if agent and agent.llm:
                    validation_criteria = parameters.get('validation_criteria', 'Validate the provided information')
                    user_input = parameters.get('input', context.get('user_input', ''))
                    context_data = context.get('shared_context', {}) if context else {}
                    
                    # Build validation prompt
                    choice_prompt = f"""You are making a decision based on validation criteria. Analyze the information and determine if it meets the specified criteria.

VALIDATION CRITERIA: {validation_criteria}

USER INPUT: {user_input}

AVAILABLE CONTEXT: {json.dumps(context_data, indent=2)}

INSTRUCTIONS:
1. Carefully evaluate the information against the validation criteria
2. Consider all available context and data
3. Make a clear decision: VALID or INVALID
4. Provide a brief explanation for your decision

Your response must start with either "VALID:" or "INVALID:" followed by your explanation.

Decision:"""
                    
                    try:
                        llm_response = LLMManager.call_llm(
                            agent.llm,
                            choice_prompt,
                            conversation_history=[],
                            temperature=0.3  # Lower temperature for more consistent decisions
                        )
                        
                        # Parse the LLM response to determine the choice
                        response_text = llm_response.strip()
                        is_valid = response_text.upper().startswith("VALID:")
                        explanation = response_text.split(":", 1)[1].strip() if ":" in response_text else response_text
                        
                        return {
                            "type": "choice",
                            "decision": "valid" if is_valid else "invalid",
                            "explanation": explanation,
                            "full_response": response_text,
                            "background": True,
                            "conditional_flow": True,
                            "next_flow": "valid_flow" if is_valid else "invalid_flow"
                        }
                    except Exception as e:
                        return {
                            "type": "choice",
                            "decision": "error",
                            "explanation": f"Error during validation: {str(e)}",
                            "background": True,
                            "conditional_flow": True,
                            "next_flow": "invalid_flow"  # Default to invalid flow on error
                        }
            
            return {
                "type": "choice",
                "decision": "error",
                "explanation": "No agent or LLM configured for choice validation",
                "background": True,
                "conditional_flow": True,
                "next_flow": "invalid_flow"
            }
        
        elif action.name == "Respond":
            # Respond action generates user-facing messages using the LLM with full context
            from app.llm_manager import LLMManager
            from app.models import Agent
            
            # Get the agent and LLM from context
            agent_name = context.get("agent_name") if context else None
            if agent_name:
                # Get the agent to access its LLM
                agent = db.query(Agent).filter(Agent.name == agent_name).first()
                if agent and agent.llm:
                    user_input = parameters.get("input", "")
                    custom_prompt = parameters.get("prompt", "")
                    
                    # If there's a custom prompt (from conditional flows), use it directly
                    if custom_prompt and custom_prompt.strip():
                        # Simple custom prompt execution
                        if custom_prompt.lower().startswith("respond"):
                            # Extract the response content from "Respond \"Valid\"" format
                            import re
                            match = re.search(r'respond\s*["\']([^"\']*)["\']', custom_prompt, re.IGNORECASE)
                            if match:
                                return {
                                    "type": "response",
                                    "content": match.group(1),
                                    "background": False,
                                    "user_message": True,
                                    "custom_prompt_used": True
                                }
                        
                        # Use custom prompt as is
                        response_prompt = custom_prompt
                    else:
                        # Build a focused response prompt that uses context internally but responds only to user request
                        response_prompt = f"""You are an intelligent assistant. The user has made a specific request, and you have gathered relevant information through various actions. Your job is to provide a direct, focused response to ONLY what the user asked for.

USER REQUEST: {user_input}

AVAILABLE INFORMATION:"""
                    
                    # Add data from custom actions (like Rootly API calls) in a structured way
                    available_data = {}
                    if context:
                        for key, value in context.items():
                            if key.endswith("_data") and isinstance(value, dict):
                                action_name = key.replace("_data", "")
                                available_data[action_name] = value
                    
                    if available_data:
                        response_prompt += "\n\nDATA RETRIEVED:"
                        for source, data in available_data.items():
                            response_prompt += f"\n\nFrom {source}:"
                            response_prompt += f"\n{json.dumps(data, indent=2)}"
                    
                    # Add thinking insights if relevant
                    if context and context.get("thinking_process"):
                        key_insights = []
                        for thought in context["thinking_process"]:
                            content = thought.get('content', '')
                            # Extract key insights, not the full thinking process
                            if any(keyword in content.lower() for keyword in ['identified', 'found', 'extracted', 'key', 'important']):
                                key_insights.append(content[:200] + "..." if len(content) > 200 else content)
                        
                        if key_insights:
                            response_prompt += "\n\nKEY INSIGHTS:"
                            for insight in key_insights[:2]:  # Limit to 2 most relevant insights
                                response_prompt += f"\n- {insight}"
                    
                    response_prompt += f"""

CRITICAL INSTRUCTIONS:
1. Answer ONLY what the user specifically asked for in their request
2. Use the available information to provide accurate, relevant details
3. Be concise and direct - don't include unnecessary context or explanations
4. If the user asked for specific information (like incident details), provide exactly that
5. Don't mention the thinking process or internal actions unless directly relevant
6. Format your response clearly and professionally
7. If information is missing, briefly mention what couldn't be retrieved
8. Focus on being helpful and answering the user's actual question

Respond directly to the user's request now:"""
                    
                    # Call the LLM to generate the response
                    try:
                        llm_response = LLMManager.call_llm(
                            agent.llm,
                            response_prompt,
                            conversation_history=[],  # Use context instead of conversation history
                            temperature=0.7
                        )
                        
                        return {
                            "type": "response",
                            "content": llm_response.strip(),
                            "background": False,
                            "user_message": True,
                            "context_used": {
                                "thinking_steps": len(context.get("thinking_process", [])),
                                "data_sources": len([k for k in context.keys() if k.endswith("_data")]),
                                "actions_executed": len(context.get("action_results", {}))
                            }
                        }
                    except Exception as e:
                        # Fallback with context information
                        fallback_response = f"I've processed your request about: {user_input}\n\n"
                        
                        # Try to include some context even in fallback
                        if context and context.get("thinking_process"):
                            fallback_response += "Based on my analysis, I understand you're asking about incident information. "
                        
                        if any(k.endswith("_data") for k in context.keys()):
                            fallback_response += "I was able to retrieve some data, but I'm having trouble formatting the response right now."
                        else:
                            fallback_response += "However, I encountered some issues retrieving the requested information."
                        
                        return {
                            "type": "response",
                            "content": fallback_response,
                            "background": False,
                            "user_message": True,
                            "error": str(e)
                        }
            
            # Fallback if no agent/LLM found
            fallback_response = f"Hello! I'm here to help. You asked: {parameters.get('input', 'No input provided')}"
            return {
                "type": "response",
                "content": fallback_response,
                "background": False,
                "user_message": True
            }
        
        else:
            # Generic native action
            prompt_template = action.config.get("prompt", "{input}")
            
            # Ensure we have an 'input' parameter, fallback to context if needed
            if 'input' not in parameters and context:
                parameters = {**parameters, 'input': context.get('user_input', 'No input provided')}
            elif 'input' not in parameters:
                parameters = {**parameters, 'input': 'No input provided'}
            
            return {
                "type": "generic",
                "content": prompt_template.format(**parameters),
                "background": False
            }

    @staticmethod
    def _fix_endpoint_url(endpoint: str, action_name: str) -> str:
        """Fix incomplete endpoint URLs by adding common base URLs"""
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        
        # Common API patterns - try to infer the base URL
        if '/incidents/' in endpoint and 'rootly' in action_name.lower():
            return f"https://api.rootly.com/v1{endpoint}"
        
        # If it starts with /, it's likely a path that needs a base URL
        if endpoint.startswith('/'):
            # Could add more intelligent base URL detection here
            # For now, return as-is and let validation catch it
            pass
            
        return endpoint

    @staticmethod
    def _execute_custom_action(action: models.Action, parameters: dict, context: dict = None):
        try:
            # Validate that we have an endpoint
            if not action.endpoint:
                raise ValueError(f"Action '{action.name}' has no endpoint configured")
            
            # Try to fix incomplete endpoint URLs
            original_endpoint = action.endpoint
            fixed_endpoint = ActionManager._fix_endpoint_url(action.endpoint, action.name)
            
            # Validate that endpoint is a complete URL
            if not validate_url(fixed_endpoint):
                raise ValueError(f"Action '{action.name}' endpoint must be a complete URL starting with http:// or https://. Current endpoint: '{original_endpoint}'. Please update the action with a complete URL like 'https://api.rootly.com/v1/incidents/{{id}}'")
            
            # Use the fixed endpoint
            base_endpoint = fixed_endpoint
            
            # Prepare request based on action method
            headers = action.headers or {}
            
            # Add default Content-Type if not present
            if 'Content-Type' not in headers and action.method.upper() == "POST":
                headers['Content-Type'] = 'application/json'

            # Add API Key to headers if provided
            if action.api_key:
                # Check if Authorization header already exists
                if 'Authorization' not in headers:
                    # For Rootly API, use Bearer token format
                    if 'rootly' in action.name.lower() or 'rootly.com' in base_endpoint:
                        headers['Authorization'] = f'Bearer {action.api_key}'
                    else:
                        # Default to Bearer token for most APIs
                        headers['Authorization'] = f'Bearer {action.api_key}'
                # If Authorization header exists but is a template, replace it
                elif headers['Authorization'].startswith('{{') and headers['Authorization'].endswith('}}'):
                    headers['Authorization'] = f'Bearer {action.api_key}'

            # Create a copy of parameters to avoid modifying the original
            request_params = parameters.copy()
            
            # Add context to parameters if available (but don't include in path replacement)
            if context:
                request_params["context"] = context

            # Replace path parameters in endpoint
            endpoint = base_endpoint
            path_params_used = []
            
            if endpoint and parameters:
                for key, value in parameters.items():
                    if f"{{{key}}}" in endpoint:
                        # Validate parameter value - extract ID from URL if needed
                        str_value = extract_id_from_url(str(value), key)
                        
                        endpoint = endpoint.replace(f"{{{key}}}", str_value)
                        path_params_used.append(key)

            # Validate that all path parameters were replaced
            import re
            remaining_params = re.findall(r'\{([^}]+)\}', endpoint)
            if remaining_params:
                raise ValueError(f"Missing required path parameters: {', '.join(remaining_params)}")

            # Make the HTTP request
            if action.method.upper() == "GET":
                # Remove path parameters from query params
                query_params = {k: v for k, v in request_params.items() 
                              if k not in path_params_used and k != "context"}
                
                response = requests.get(endpoint, params=query_params, headers=headers, timeout=30)
                
            elif action.method.upper() == "POST":
                # Remove path parameters from body
                body_params = {k: v for k, v in request_params.items() 
                             if k not in path_params_used}
                
                response = requests.post(endpoint, json=body_params, headers=headers, timeout=30)
                
            elif action.method.upper() == "PUT":
                # Remove path parameters from body
                body_params = {k: v for k, v in request_params.items() 
                             if k not in path_params_used}
                
                response = requests.put(endpoint, json=body_params, headers=headers, timeout=30)
                
            elif action.method.upper() == "DELETE":
                # Remove path parameters from query params
                query_params = {k: v for k, v in request_params.items() 
                              if k not in path_params_used and k != "context"}
                
                response = requests.delete(endpoint, params=query_params, headers=headers, timeout=30)
                
            else:
                raise ValueError(f"Unsupported HTTP method: {action.method}")

            # Check if the request was successful
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                raw_result = response.json()
                
                # Filter response based on YAML schema if available
                if action.yaml_spec:
                    response_schema = ActionManager.extract_response_schema_from_yaml(action.yaml_spec)
                    if response_schema:
                        filtered_result = ActionManager.filter_response_by_schema(raw_result, response_schema)
                        result = {
                            "filtered_data": filtered_result,
                            "raw_data": raw_result,
                            "schema_applied": True,
                            "schema_used": response_schema
                        }
                    else:
                        result = {
                            "data": raw_result,
                            "schema_applied": False,
                            "note": "No response schema found in YAML spec"
                        }
                else:
                    result = {
                        "data": raw_result,
                        "schema_applied": False,
                        "note": "No YAML spec available for filtering"
                    }
                    
            except ValueError:
                # If response is not JSON, return the text content
                result = {
                    "content": response.text,
                    "content_type": response.headers.get('content-type', 'text/plain'),
                    "schema_applied": False
                }
            
            # Return detailed result with context for future actions
            # Mask sensitive data for logging/display
            safe_headers = mask_sensitive_fields(headers)
            safe_params = mask_sensitive_fields(request_params)
            
            return {
                "type": "custom_action",
                "success": True,
                "status_code": response.status_code,
                "result": result,
                "context": context,
                "action_name": action.name,
                "endpoint_called": endpoint,
                "original_endpoint": original_endpoint,
                "method_used": action.method.upper(),
                "parameters_sent": safe_params,
                "headers_sent": safe_headers,
                "path_params_used": path_params_used,
                "authentication_used": bool(action.api_key),
                "background": False
            }
            
        except requests.exceptions.Timeout:
            return {
                "type": "custom_action",
                "success": False,
                "error": "Request timeout - the API took too long to respond",
                "action_name": action.name,
                "endpoint_called": original_endpoint,
                "background": False
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "type": "custom_action",
                "success": False,
                "error": "Connection error - could not reach the API endpoint",
                "action_name": action.name,
                "endpoint_called": original_endpoint,
                "background": False
            }
            
        except requests.exceptions.HTTPError as e:
            # Get error details from response
            error_detail = "Unknown error"
            try:
                if hasattr(e.response, 'json'):
                    error_detail = e.response.json()
                else:
                    error_detail = e.response.text
            except:
                error_detail = str(e)
                
            return {
                "type": "custom_action",
                "success": False,
                "error": f"HTTP {e.response.status_code}: {error_detail}",
                "status_code": e.response.status_code,
                "action_name": action.name,
                "endpoint_called": endpoint if 'endpoint' in locals() else action.endpoint,
                "background": False
            }
            
        except ValueError as e:
            return {
                "type": "custom_action",
                "success": False,
                "error": str(e),
                "action_name": action.name,
                "background": False
            }
            
        except Exception as e:
            return {
                "type": "custom_action",
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "action_name": action.name,
                "background": False
            }

    @staticmethod
    def parse_yaml_spec(yaml_content: str):
        try:
            spec = yaml.safe_load(yaml_content)
            return spec
        except Exception as e:
            raise ValueError(f"Error parsing YAML: {str(e)}")

    @staticmethod
    def generate_parameters_from_yaml(yaml_spec: str):
        spec = ActionManager.parse_yaml_spec(yaml_spec)
        parameters = {}

        # Extract parameters from OpenAPI spec
        if 'paths' in spec:
            for path, methods in spec['paths'].items():
                for method, details in methods.items():
                    if 'parameters' in details:
                        for param in details['parameters']:
                            param_name = param['name']
                            parameters[param_name] = {
                                'type': param.get('schema', {}).get('type', 'string'),
                                'required': param.get('required', False),
                                'description': param.get('description', '')
                            }

        return parameters

    @staticmethod
    def extract_response_schema_from_yaml(yaml_spec: str):
        """Extract the expected response schema from OpenAPI YAML"""
        try:
            spec = ActionManager.parse_yaml_spec(yaml_spec)
            response_schema = {}
            
            if 'paths' in spec:
                for path, methods in spec['paths'].items():
                    for method, details in methods.items():
                        if 'responses' in details:
                            # Look for successful responses (200, 201, etc.)
                            for status_code, response_info in details['responses'].items():
                                if status_code.startswith('2'):  # 2xx success codes
                                    if 'content' in response_info:
                                        for content_type, content_info in response_info['content'].items():
                                            if 'schema' in content_info:
                                                response_schema = content_info['schema']
                                                break
                                    break
                        if response_schema:
                            break
                    if response_schema:
                        break
            
            return response_schema
        except Exception as e:
            print(f"Error extracting response schema: {e}")
            return {}

    @staticmethod
    def filter_response_by_schema(response_data: dict, schema: dict):
        """Filter response data based on the expected schema"""
        if not schema or not response_data:
            return response_data
        
        def extract_by_schema(data, schema_part):
            if not isinstance(schema_part, dict) or not isinstance(data, dict):
                return data
            
            if 'properties' in schema_part:
                filtered = {}
                for prop_name, prop_schema in schema_part['properties'].items():
                    if prop_name in data:
                        if 'properties' in prop_schema:
                            # Nested object
                            filtered[prop_name] = extract_by_schema(data[prop_name], prop_schema)
                        else:
                            # Simple property
                            filtered[prop_name] = data[prop_name]
                return filtered
            else:
                return data
        
        return extract_by_schema(response_data, schema)

    @staticmethod
    def _generate_schema_preview(schema: dict):
        """Generate a preview of what data will be extracted based on schema"""
        if not schema or not isinstance(schema, dict):
            return None
        
        def build_preview(schema_part, level=0):
            if level > 3:  # Prevent infinite recursion
                return "..."
            
            if 'properties' in schema_part:
                preview = {}
                for prop_name, prop_schema in schema_part['properties'].items():
                    if 'properties' in prop_schema:
                        # Nested object
                        preview[prop_name] = build_preview(prop_schema, level + 1)
                    else:
                        # Simple property
                        prop_type = prop_schema.get('type', 'unknown')
                        preview[prop_name] = f"<{prop_type}>"
                return preview
            else:
                return f"<{schema_part.get('type', 'unknown')}>"
        
        return build_preview(schema)

    @staticmethod
    def generate_headers_from_yaml(yaml_spec: str, api_key: str = None):
        spec = ActionManager.parse_yaml_spec(yaml_spec)
        headers = {}

        # Extract security schemes from OpenAPI spec
        if 'components' in spec and 'securitySchemes' in spec['components']:
            for scheme_name, scheme_details in spec['components']['securitySchemes'].items():
                if scheme_details['type'] == 'apiKey' and scheme_details['in'] == 'header':
                    if api_key:
                        # If API key is provided, use it directly but don't expose in templates
                        if scheme_details['name'] == 'Authorization':
                            headers[scheme_details['name']] = f"Bearer {api_key}"
                        else:
                            headers[scheme_details['name']] = api_key
                    else:
                        # Use secure template that doesn't expose the actual key
                        headers[scheme_details['name']] = f"{{{{ {scheme_name} }}}}"

        return headers


    @staticmethod
    def update_action(db: Session, action_id: int, action: schemas.ActionUpdate):
        db_action = db.query(models.Action).filter(models.Action.id == action_id).first()
        if not db_action:
            return None

        # Check for duplicate names if name is being updated
        if action.name and action.name != db_action.name:
            existing_action = db.query(models.Action).filter(models.Action.name == action.name).first()
            if existing_action:
                raise ValueError(f"Action with name '{action.name}' already exists")

        update_data = action.dict(exclude_unset=True)
        
        # Sanitize YAML spec if it's being updated
        if 'yaml_spec' in update_data and update_data['yaml_spec']:
            api_key = update_data.get('api_key') or db_action.api_key
            update_data['yaml_spec'] = sanitize_yaml_content(update_data['yaml_spec'], api_key)
        
        for field, value in update_data.items():
            setattr(db_action, field, value)

        db.commit()
        db.refresh(db_action)
        return db_action

    @staticmethod
    def delete_action(db: Session, action_id: int):
        db_action = db.query(models.Action).filter(models.Action.id == action_id).first()
        if not db_action:
            return False

        db.delete(db_action)
        db.commit()
        return True