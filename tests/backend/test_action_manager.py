"""
Testes para ActionManager seguindo TDD
"""
import pytest
from unittest.mock import Mock, patch
import json
from app.action_manager import ActionManager
from app import models, schemas


class TestActionManager:
    """Testes para o gerenciador de Actions"""
    
    def test_create_action_success(self, db_session, sample_action_data):
        """Teste: Deve criar uma Action com sucesso"""
        # Arrange
        action_create = schemas.ActionCreate(**sample_action_data)
        
        # Act
        result = ActionManager.create_action(db_session, action_create)
        
        # Assert
        assert result.name == sample_action_data["name"]
        assert result.description == sample_action_data["description"]
        assert result.endpoint == sample_action_data["endpoint"]
        assert result.method == sample_action_data["method"]
        assert result.id is not None
    
    def test_create_action_duplicate_name(self, db_session, created_action, sample_action_data):
        """Teste: Deve falhar ao criar Action com nome duplicado"""
        # Arrange
        action_create = schemas.ActionCreate(**sample_action_data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            ActionManager.create_action(db_session, action_create)
    
    def test_get_actions(self, db_session, created_action):
        """Teste: Deve retornar lista de Actions"""
        # Act
        result = ActionManager.get_actions(db_session)
        
        # Assert
        assert len(result) >= 1
        action_names = [action.name for action in result]
        assert created_action.name in action_names
    
    def test_execute_native_thinking_action(self, db_session):
        """Teste: Deve executar ação nativa Thinking"""
        # Arrange
        thinking_action = models.Action(
            name="Thinking",
            description="Think about input",
            action_type="native",
            config={"prompt": "Think about: {input}"}
        )
        db_session.add(thinking_action)
        db_session.commit()
        
        parameters = {"input": "test input"}
        context = {"user_input": "test input"}
        
        # Act
        result = ActionManager.execute_action(
            db_session, "Thinking", parameters, context
        )
        
        # Assert
        assert result["type"] == "thinking"
        assert result["background"] is True
        assert "test input" in result["content"]
    
    def test_execute_native_respond_action(self, db_session, created_llm):
        """Teste: Deve executar ação nativa Respond"""
        # Arrange
        respond_action = models.Action(
            name="Respond",
            description="Respond to user",
            action_type="native",
            config={"prompt": "Respond to: {input}"}
        )
        db_session.add(respond_action)
        db_session.commit()
        
        # Criar agent para contexto
        agent = models.Agent(
            name="Test Agent",
            description="Test",
            system_prompt="Test prompt",
            llm_id=created_llm.id,
            actions=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        parameters = {"input": "Hello"}
        context = {
            "agent_name": "Test Agent",
            "user_input": "Hello",
            "thinking_process": [],
            "action_results": {}
        }
        
        # Act
        with patch('app.llm_manager.LLMManager.call_llm') as mock_llm:
            mock_llm.return_value = "Hello! How can I help you?"
            
            result = ActionManager.execute_action(
                db_session, "Respond", parameters, context
            )
        
        # Assert
        assert result["type"] == "response"
        assert result["background"] is False
        assert result["user_message"] is True
        assert "Hello! How can I help you?" in result["content"]
    
    def test_execute_native_wait_action(self, db_session):
        """Teste: Deve executar ação nativa Wait"""
        # Arrange
        wait_action = models.Action(
            name="Wait",
            description="Wait for user input",
            action_type="native",
            config={}
        )
        db_session.add(wait_action)
        db_session.commit()
        
        parameters = {
            "message": "Please provide more info",
            "prompt": "What else do you need?"
        }
        
        # Act
        result = ActionManager.execute_action(
            db_session, "Wait", parameters, {}
        )
        
        # Assert
        assert result["type"] == "wait"
        assert result["pause_execution"] is True
        assert result["user_input_required"] is True
        assert result["content"] == "Please provide more info"
        assert result["prompt"] == "What else do you need?"
    
    @patch('app.action_manager.requests.get')
    def test_execute_custom_action_success(self, mock_get, db_session):
        """Teste: Deve executar ação customizada com sucesso"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test response"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        action = models.Action(
            name="Test Custom Action",
            description="Test custom action",
            endpoint="https://api.example.com/test/{id}",
            method="GET",
            action_type="custom",
            parameters={"id": {"type": "string", "required": True}}
        )
        db_session.add(action)
        db_session.commit()
        
        parameters = {"id": "123"}
        
        # Act
        result = ActionManager.execute_action(
            db_session, "Test Custom Action", parameters, {}
        )
        
        # Assert
        assert result["type"] == "custom_action"
        assert result["success"] is True
        assert result["status_code"] == 200
        assert "data" in result["result"]
    
    @patch('app.action_manager.requests.get')
    def test_execute_custom_action_http_error(self, mock_get, db_session):
        """Teste: Deve tratar erro HTTP em ação customizada"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not Found")
        mock_get.return_value = mock_response
        
        action = models.Action(
            name="Test Error Action",
            description="Test error handling",
            endpoint="https://api.example.com/notfound",
            method="GET",
            action_type="custom"
        )
        db_session.add(action)
        db_session.commit()
        
        # Act
        result = ActionManager.execute_action(
            db_session, "Test Error Action", {}, {}
        )
        
        # Assert
        assert result["type"] == "custom_action"
        assert result["success"] is False
        assert "error" in result
    
    def test_parse_yaml_spec_valid(self):
        """Teste: Deve parsear YAML válido"""
        # Arrange
        yaml_content = """
        openapi: 3.0.0
        info:
          title: Test API
          version: 1.0.0
        paths:
          /test:
            get:
              summary: Test endpoint
        """
        
        # Act
        result = ActionManager.parse_yaml_spec(yaml_content)
        
        # Assert
        assert "openapi" in result
        assert result["info"]["title"] == "Test API"
        assert "/test" in result["paths"]
    
    def test_parse_yaml_spec_invalid(self):
        """Teste: Deve falhar com YAML inválido"""
        # Arrange
        invalid_yaml = "invalid: yaml: content: ["
        
        # Act & Assert
        with pytest.raises(ValueError, match="Error parsing YAML"):
            ActionManager.parse_yaml_spec(invalid_yaml)
    
    def test_generate_parameters_from_yaml(self):
        """Teste: Deve extrair parâmetros do YAML"""
        # Arrange
        yaml_content = """
        openapi: 3.0.0
        paths:
          /test/{id}:
            get:
              parameters:
                - name: id
                  in: path
                  required: true
                  schema:
                    type: string
                - name: limit
                  in: query
                  required: false
                  schema:
                    type: integer
        """
        
        # Act
        result = ActionManager.generate_parameters_from_yaml(yaml_content)
        
        # Assert
        assert "id" in result
        assert "limit" in result
        assert result["id"]["type"] == "string"
        assert result["id"]["required"] is True
        assert result["limit"]["type"] == "integer"
        assert result["limit"]["required"] is False
    
    def test_mask_sensitive_data(self):
        """Teste: Deve mascarar dados sensíveis"""
        # Arrange
        data = {
            "api_key": "secret123456",
            "Authorization": "Bearer token123456",
            "normal_field": "visible_data",
            "password": "secret"
        }
        
        # Act
        result = ActionManager.mask_sensitive_data(data)
        
        # Assert
        assert result["api_key"] == "***3456"
        assert result["Authorization"] == "Bearer ***3456"
        assert result["normal_field"] == "visible_data"
        assert result["password"] == "***"
    
    def test_sanitize_yaml_spec(self):
        """Teste: Deve sanitizar YAML removendo API keys"""
        # Arrange
        yaml_content = """
        security:
          - bearerAuth: []
        components:
          securitySchemes:
            bearerAuth:
              type: http
              scheme: bearer
              bearerFormat: JWT
        """
        api_key = "secret123"
        
        # Act
        result = ActionManager.sanitize_yaml_spec(yaml_content, api_key)
        
        # Assert
        assert api_key not in result
        assert "{{ API_KEY }}" in result or yaml_content == result  # If no key, no change
    
    def test_update_action_success(self, db_session, created_action):
        """Teste: Deve atualizar Action com sucesso"""
        # Arrange
        update_data = schemas.ActionUpdate(
            description="Updated description",
            endpoint="https://api.example.com/updated"
        )
        
        # Act
        result = ActionManager.update_action(db_session, created_action.id, update_data)
        
        # Assert
        assert result.description == "Updated description"
        assert result.endpoint == "https://api.example.com/updated"
        assert result.name == created_action.name  # Not changed
    
    def test_delete_action_success(self, db_session, created_action):
        """Teste: Deve deletar Action com sucesso"""
        # Act
        result = ActionManager.delete_action(db_session, created_action.id)
        
        # Assert
        assert result is True
        
        # Verificar se foi deletado
        deleted_action = db_session.query(models.Action).filter(
            models.Action.id == created_action.id
        ).first()
        assert deleted_action is None
