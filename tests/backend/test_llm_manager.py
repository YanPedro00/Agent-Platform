"""
Testes para LLMManager seguindo TDD
"""
import pytest
from unittest.mock import Mock, patch
from app.llm_manager import LLMManager
from app import models, schemas


class TestLLMManager:
    """Testes para o gerenciador de LLMs"""
    
    def test_create_llm_success(self, db_session, sample_llm_data):
        """Teste: Deve criar um LLM com sucesso"""
        # Arrange
        llm_create = schemas.LLMCreate(**sample_llm_data)
        
        # Act
        result = LLMManager.create_llm(db_session, llm_create)
        
        # Assert
        assert result.name == sample_llm_data["name"]
        assert result.provider == sample_llm_data["provider"]
        assert result.model_name == sample_llm_data["model_name"]
        assert result.id is not None
    
    def test_create_llm_duplicate_name(self, db_session, created_llm, sample_llm_data):
        """Teste: Deve falhar ao criar LLM com nome duplicado"""
        # Arrange
        llm_create = schemas.LLMCreate(**sample_llm_data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            LLMManager.create_llm(db_session, llm_create)
    
    def test_get_llms(self, db_session, created_llm):
        """Teste: Deve retornar lista de LLMs"""
        # Act
        result = LLMManager.get_llms(db_session)
        
        # Assert
        assert len(result) == 1
        assert result[0].id == created_llm.id
    
    def test_get_llms_with_pagination(self, db_session):
        """Test: Should apply pagination correctly"""
        # Arrange - Create multiple LLMs
        for i in range(5):
            llm = models.LLM(
                name=f"LLM {i}",
                provider="openai",
                model_name="gpt-3.5-turbo"
            )
            db_session.add(llm)
        db_session.commit()
        
        # Act
        result = LLMManager.get_llms(db_session, skip=1, limit=2)
        
        # Assert
        assert len(result) == 2
    
    @patch('app.llm_manager.OpenAI')
    def test_call_openai_success(self, mock_openai_class):
        """Teste: Deve chamar OpenAI API com sucesso"""
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        llm = models.LLM(
            name="Test LLM",
            provider="openai",
            api_key="test-key",
            model_name="gpt-3.5-turbo"
        )
        
        # Act
        result = LLMManager.call_llm(llm, "Test prompt")
        
        # Assert
        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('app.llm_manager.requests.post')
    def test_call_ollama_success(self, mock_post):
        """Teste: Deve chamar Ollama API com sucesso"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Ollama response"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        llm = models.LLM(
            name="Test Ollama",
            provider="ollama",
            model_name="llama2",
            base_url="http://localhost:11434"
        )
        
        # Act
        result = LLMManager.call_llm(llm, "Test prompt")
        
        # Assert
        assert result == "Ollama response"
        mock_post.assert_called_once()
    
    def test_call_llm_unsupported_provider(self):
        """Test: Should fail with unsupported provider"""
        # Arrange
        llm = models.LLM(
            name="Unsupported LLM",
            provider="unsupported",
            model_name="test-model"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            LLMManager.call_llm(llm, "Test prompt")
    
    def test_update_llm_success(self, db_session, created_llm):
        """Teste: Deve atualizar LLM com sucesso"""
        # Arrange
        update_data = schemas.LLMUpdate(
            name="Updated LLM",
            temperature=0.5
        )
        
        # Act
        result = LLMManager.update_llm(db_session, created_llm.id, update_data)
        
        # Assert
        assert result.name == "Updated LLM"
        assert result.temperature == 0.5
        assert result.provider == created_llm.provider  # Not changed
    
    def test_update_llm_not_found(self, db_session):
        """Test: Should return None for LLM not found"""
        # Arrange
        update_data = schemas.LLMUpdate(name="Non-existent")
        
        # Act
        result = LLMManager.update_llm(db_session, 999, update_data)
        
        # Assert
        assert result is None
    
    def test_delete_llm_success(self, db_session, created_llm):
        """Teste: Deve deletar LLM com sucesso"""
        # Act
        result = LLMManager.delete_llm(db_session, created_llm.id)
        
        # Assert
        assert result is True
        
        # Verificar se foi deletado
        deleted_llm = db_session.query(models.LLM).filter(
            models.LLM.id == created_llm.id
        ).first()
        assert deleted_llm is None
    
    def test_delete_llm_not_found(self, db_session):
        """Test: Should return False for LLM not found"""
        # Act
        result = LLMManager.delete_llm(db_session, 999)
        
        # Assert
        assert result is False
