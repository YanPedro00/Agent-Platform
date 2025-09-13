"""
Testes para AgentManager seguindo TDD
"""
import pytest
from unittest.mock import Mock, patch
from app.agent_manager import AgentManager
from app import models, schemas


class TestAgentManager:
    """Testes para o gerenciador de Agents"""
    
    def test_create_agent_success(self, db_session, created_llm, sample_agent_data):
        """Teste: Deve criar um Agent com sucesso"""
        # Arrange
        # Create necessary actions
        thinking_action = models.Action(
            name="Thinking",
            description="Think about input",
            action_type="native"
        )
        respond_action = models.Action(
            name="Respond", 
            description="Respond to user",
            action_type="native"
        )
        db_session.add(thinking_action)
        db_session.add(respond_action)
        db_session.commit()
        
        agent_data = sample_agent_data.copy()
        agent_data["llm_id"] = created_llm.id
        
        agent_create = schemas.AgentCreate(**agent_data)
        
        # Act
        result = AgentManager.create_agent(db_session, agent_create)
        
        # Assert
        assert result.name == agent_data["name"]
        assert result.description == agent_data["description"]
        assert result.llm_id == created_llm.id
        assert len(result.actions) == 2
        assert result.id is not None
    
    def test_create_agent_duplicate_name(self, db_session, created_agent, sample_agent_data):
        """Teste: Deve falhar ao criar Agent com nome duplicado"""
        # Arrange
        agent_create = schemas.AgentCreate(**sample_agent_data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            AgentManager.create_agent(db_session, agent_create)
    
    def test_create_agent_invalid_llm(self, db_session, sample_agent_data):
        """Teste: Deve falhar com LLM inexistente"""
        # Arrange
        agent_data = sample_agent_data.copy()
        agent_data["llm_id"] = 999  # LLM inexistente
        
        agent_create = schemas.AgentCreate(**agent_data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="LLM with id 999 not found"):
            AgentManager.create_agent(db_session, agent_create)
    
    def test_create_agent_invalid_action(self, db_session, created_llm, sample_agent_data):
        """Teste: Deve falhar com Action inexistente"""
        # Arrange
        agent_data = sample_agent_data.copy()
        agent_data["llm_id"] = created_llm.id
        agent_data["actions"] = [
            {
                "action_name": "NonExistentAction",
                "prompt": "Test",
                "order": 1
            }
        ]
        
        agent_create = schemas.AgentCreate(**agent_data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Action with name 'NonExistentAction' not found"):
            AgentManager.create_agent(db_session, agent_create)
    
    def test_get_agents(self, db_session, created_agent):
        """Teste: Deve retornar lista de Agents"""
        # Act
        result = AgentManager.get_agents(db_session)
        
        # Assert
        assert len(result) >= 1
        agent_names = [agent.name for agent in result]
        assert created_agent.name in agent_names
    
    def test_extract_parameters_from_context(self, db_session, created_llm):
        """Teste: Deve extrair parâmetros do contexto usando LLM"""
        # Arrange
        action = models.Action(
            name="Test Action",
            description="Test action",
            action_type="custom",
            parameters={
                "id": {"type": "string", "required": True},
                "status": {"type": "string", "required": False}
            }
        )
        db_session.add(action)
        db_session.commit()
        
        context = {
            "user_input": "Check incident 1234-auth-failure with status open"
        }
        
        # Act
        with patch('app.llm_manager.LLMManager.call_llm') as mock_llm:
            mock_llm.return_value = '{"id": "1234-auth-failure", "status": "open"}'
            
            result = AgentManager.extract_parameters_from_context(
                db_session, "Test Action", context, created_llm
            )
        
        # Assert
        assert result["id"] == "1234-auth-failure"
        assert result["status"] == "open"
    
    def test_extract_parameters_invalid_json(self, db_session, created_llm):
        """Teste: Deve retornar dict vazio com JSON inválido"""
        # Arrange
        action = models.Action(
            name="Test Action",
            description="Test action",
            action_type="custom",
            parameters={"id": {"type": "string", "required": True}}
        )
        db_session.add(action)
        db_session.commit()
        
        context = {"user_input": "test input"}
        
        # Act
        with patch('app.llm_manager.LLMManager.call_llm') as mock_llm:
            mock_llm.return_value = "Invalid JSON response"
            
            result = AgentManager.extract_parameters_from_context(
                db_session, "Test Action", context, created_llm
            )
        
        # Assert
        assert result == {}
    
    def test_build_enhanced_context(self):
        """Teste: Deve construir contexto aprimorado"""
        # Arrange
        context = {
            "user_input": "test input",
            "action_results": {},
            "thinking_process": [],
            "conversation_history": []
        }
        
        action_result = {
            "type": "custom_action",
            "success": True,
            "result": {
                "filtered_data": {"incident_id": "123", "status": "open"}
            }
        }
        
        # Act
        result = AgentManager.build_enhanced_context(
            context, action_result, "GetIncident"
        )
        
        # Assert
        assert "GetIncident" in result["action_results"]
        assert "GetIncident_data" in result
        assert result["GetIncident_data"]["incident_id"] == "123"
        assert len(result["conversation_history"]) == 1
    
    def test_build_enhanced_context_thinking_action(self):
        """Teste: Deve adicionar ação de pensamento ao contexto"""
        # Arrange
        context = {
            "action_results": {},
            "thinking_process": [],
            "conversation_history": []
        }
        
        action_result = {
            "type": "thinking",
            "content": "Analyzing user request for incident information",
            "background": True
        }
        
        # Act
        result = AgentManager.build_enhanced_context(
            context, action_result, "Thinking"
        )
        
        # Assert
        assert len(result["thinking_process"]) == 1
        assert result["thinking_process"][0]["action"] == "Thinking"
        assert "Analyzing user request" in result["thinking_process"][0]["content"]
    
    @patch('app.agent_manager.AgentManager._execute_action_flow')
    def test_run_agent_success(self, mock_execute_flow, db_session, created_agent):
        """Teste: Deve executar agent com sucesso"""
        # Arrange
        mock_execute_flow.return_value = {
            "actions_used": ["Thinking", "Respond"],
            "background_actions": [
                {
                    "action": "Thinking",
                    "result": {"type": "thinking", "success": True},
                    "parameters_used": {},
                    "iteration": 1
                }
            ],
            "user_facing_actions": [
                {
                    "action": "Respond",
                    "result": {
                        "type": "response",
                        "content": "Hello! How can I help you?",
                        "user_message": True
                    },
                    "parameters_used": {},
                    "iteration": 1
                }
            ],
            "shared_context": {}
        }
        
        input_data = schemas.AgentRun(input="Hello")
        
        # Act
        result = AgentManager.run_agent(db_session, created_agent.id, input_data)
        
        # Assert
        assert "response" in result
        assert result["response"] == "Hello! How can I help you?"
        assert len(result["actions_used"]) == 2
        assert len(result["background_actions"]) == 1
        assert len(result["user_facing_actions"]) == 1
    
    def test_run_agent_not_found(self, db_session):
        """Teste: Deve retornar erro para agent não encontrado"""
        # Arrange
        input_data = schemas.AgentRun(input="test")
        
        # Act
        result = AgentManager.run_agent(db_session, 999, input_data)
        
        # Assert
        assert "error" in result
        assert "not found" in result["error"]
    
    def test_run_agent_no_respond_action(self, db_session, created_llm):
        """Teste: Deve retornar mensagem para agent sem ação Respond"""
        # Arrange
        # Create agent without Respond action
        agent = models.Agent(
            name="No Respond Agent",
            description="Agent without respond action",
            system_prompt="Test",
            llm_id=created_llm.id,
            actions=[
                {
                    "action_name": "Thinking",
                    "prompt": "Think",
                    "order": 1
                }
            ]
        )
        db_session.add(agent)
        db_session.commit()
        
        input_data = schemas.AgentRun(input="test")
        
        # Act
        result = AgentManager.run_agent(db_session, agent.id, input_data)
        
        # Assert
        assert "message" in result
        assert "Respond action" in result["message"]
    
    @patch('app.agent_manager.AgentManager._execute_action_flow')
    def test_run_agent_with_wait_action(self, mock_execute_flow, db_session, created_agent):
        """Teste: Deve tratar ação Wait corretamente"""
        # Arrange
        mock_execute_flow.return_value = {
            "wait_required": True,
            "wait_message": "Please provide more information",
            "wait_prompt": "What else do you need?",
            "actions_used": ["Thinking", "Wait"],
            "background_actions": [],
            "user_facing_actions": [],
            "shared_context": {}
        }
        
        input_data = schemas.AgentRun(input="test")
        
        # Act
        result = AgentManager.run_agent(db_session, created_agent.id, input_data)
        
        # Assert
        assert result["wait_required"] is True
        assert result["wait_message"] == "Please provide more information"
        assert result["wait_prompt"] == "What else do you need?"
    
    def test_update_agent_success(self, db_session, created_agent):
        """Teste: Deve atualizar Agent com sucesso"""
        # Arrange
        update_data = schemas.AgentUpdate(
            description="Updated description",
            system_prompt="Updated prompt"
        )
        
        # Act
        result = AgentManager.update_agent(db_session, created_agent.id, update_data)
        
        # Assert
        assert result.description == "Updated description"
        assert result.system_prompt == "Updated prompt"
        assert result.name == created_agent.name  # Not changed
    
    def test_update_agent_not_found(self, db_session):
        """Teste: Deve retornar None para Agent não encontrado"""
        # Arrange
        update_data = schemas.AgentUpdate(description="Non-existent")
        
        # Act
        result = AgentManager.update_agent(db_session, 999, update_data)
        
        # Assert
        assert result is None
    
    def test_delete_agent_success(self, db_session, created_agent):
        """Teste: Deve deletar Agent com sucesso"""
        # Act
        result = AgentManager.delete_agent(db_session, created_agent.id)
        
        # Assert
        assert result is True
        
        # Verificar se foi deletado
        deleted_agent = db_session.query(models.Agent).filter(
            models.Agent.id == created_agent.id
        ).first()
        assert deleted_agent is None
    
    def test_delete_agent_not_found(self, db_session):
        """Teste: Deve retornar False para Agent não encontrado"""
        # Act
        result = AgentManager.delete_agent(db_session, 999)
        
        # Assert
        assert result is False
