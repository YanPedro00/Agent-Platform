"""
Utilitários comuns para simplificar o código
"""
import json
import re
from typing import Dict, Any, Optional, List
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def safe_json_parse(json_string: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON de forma segura, retornando None em caso de erro
    """
    try:
        # Limpar a string e extrair JSON
        json_match = re.search(r'\{.*\}', json_string, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


def mask_sensitive_fields(data: Dict[str, Any], 
                         sensitive_fields: List[str] = None) -> Dict[str, Any]:
    """
    Mascara campos sensíveis em dicionários
    """
    if sensitive_fields is None:
        sensitive_fields = ['api_key', 'Authorization', 'password', 'token', 'secret']
    
    if not isinstance(data, dict):
        return data
    
    masked_data = data.copy()
    for key, value in masked_data.items():
        if any(field.lower() in key.lower() for field in sensitive_fields):
            if isinstance(value, str) and len(value) > 4:
                if value.startswith('Bearer '):
                    token = value[7:]
                    masked_data[key] = f"Bearer ***{token[-4:]}" if len(token) > 4 else "Bearer ***"
                else:
                    masked_data[key] = f"***{value[-4:]}"
            else:
                masked_data[key] = "***"
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_fields(value, sensitive_fields)
    
    return masked_data


def validate_url(url: str) -> bool:
    """
    Valida se uma URL é válida
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def extract_id_from_url(url: str, param_name: str = "id") -> Optional[str]:
    """
    Extrai ID de uma URL quando o parâmetro deveria ser um ID simples
    """
    if not url.startswith(('http://', 'https://')):
        return url
    
    url_parts = url.split('/')
    if len(url_parts) > 1:
        potential_id = url_parts[-1]
        # Looks like an ID (alphanumeric with hyphens/underscores)
        if re.match(r'^[a-zA-Z0-9\-_]+$', potential_id) and len(potential_id) > 3:
            logger.warning(f"Extracted ID '{potential_id}' from URL for parameter '{param_name}'")
            return potential_id
    
    return url


def handle_exceptions(default_return=None, log_error=True):
    """
    Decorator para tratamento de exceções
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                return default_return
        return wrapper
    return decorator


def build_error_response(error_type: str, message: str, **kwargs) -> Dict[str, Any]:
    """
    Build standardized error response
    """
    return {
        "type": error_type,
        "success": False,
        "error": message,
        "background": False,
        **kwargs
    }


def build_success_response(response_type: str, content: Any = None, **kwargs) -> Dict[str, Any]:
    """
    Build standardized success response
    """
    response = {
        "type": response_type,
        "success": True,
        **kwargs
    }
    
    if content is not None:
        response["content"] = content
    
    return response


def clean_action_result(action_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean action result removing circular and sensitive data
    """
    if not isinstance(action_result, dict):
        return {}
    
    cleaned = {
        "action": action_result.get("action", "Unknown"),
        "iteration": action_result.get("iteration", 0),
        "parameters_used": mask_sensitive_fields(action_result.get("parameters_used", {})),
        "custom_action": action_result.get("custom_action", False)
    }
    
    # Limpar resultado
    result = action_result.get("result", {})
    if isinstance(result, dict):
        cleaned["result"] = {
            "type": result.get("type", "unknown"),
            "success": result.get("success", True),
            "background": result.get("background", True)
        }
        
        # Adicionar resumo baseado no tipo
        if result.get("type") == "thinking":
            cleaned["result"]["summary"] = "Thinking process completed"
        elif result.get("type") == "custom_action":
            if result.get("success"):
                cleaned["result"]["summary"] = f"API call successful (status: {result.get('status_code', 'unknown')})"
            else:
                cleaned["result"]["summary"] = f"API call failed: {result.get('error', 'Unknown error')}"
    
    return cleaned


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Valida campos obrigatórios e retorna lista de campos faltantes
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)
    return missing_fields


def sanitize_yaml_content(yaml_content: str, api_key: str = None) -> str:
    """
    Remove chaves de API do conteúdo YAML
    """
    if not yaml_content or not api_key:
        return yaml_content
    
    sanitized = yaml_content.replace(api_key, "{{ API_KEY }}")
    sanitized = sanitized.replace(f"Bearer {api_key}", "Bearer {{ API_KEY }}")
    
    return sanitized


class ContextBuilder:
    """
    Classe para construir contexto de forma mais limpa
    """
    
    def __init__(self, user_input: str, agent_name: str):
        self.context = {
            "user_input": user_input,
            "agent_name": agent_name,
            "action_results": {},
            "thinking_process": [],
            "conversation_history": [],
            "extracted_entities": {},
            "session_data": {}
        }
    
    def add_action_result(self, action_name: str, result: Dict[str, Any]) -> 'ContextBuilder':
        """Add action result to context"""
        self.context["action_results"][action_name] = result
        
        # Extract useful data
        if result.get("type") == "custom_action" and result.get("success"):
            result_data = result.get("result", {})
            if isinstance(result_data, dict):
                if "filtered_data" in result_data:
                    self.context[f"{action_name}_data"] = result_data["filtered_data"]
                elif "data" in result_data:
                    self.context[f"{action_name}_data"] = result_data["data"]
        
        return self
    
    def add_thinking(self, action_name: str, content: str) -> 'ContextBuilder':
        """Adiciona processo de pensamento"""
        self.context["thinking_process"].append({
            "action": action_name,
            "content": content,
            "timestamp": "now"
        })
        return self
    
    def add_conversation_entry(self, action_name: str, entry_type: str, 
                             content: str, background: bool = False) -> 'ContextBuilder':
        """Add entry to conversation history"""
        self.context["conversation_history"].append({
            "action": action_name,
            "type": entry_type,
            "content": content,
            "background": background
        })
        return self
    
    def build(self) -> Dict[str, Any]:
        """Return the built context"""
        return self.context.copy()


def format_llm_prompt(template: str, **kwargs) -> str:
    """
    Formata prompt para LLM de forma segura
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning(f"Missing parameter in prompt template: {e}")
        return template
    except Exception as e:
        logger.error(f"Error formatting prompt: {e}")
        return template
