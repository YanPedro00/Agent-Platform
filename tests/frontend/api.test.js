/**
 * Testes para o serviço de API
 */
import api from '../../frontend/src/services/api';

// Mock do fetch
global.fetch = jest.fn();

describe('API Service', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  describe('LLM Operations', () => {
    test('should fetch LLMs successfully', async () => {
      // Arrange
      const mockLLMs = [
        { id: 1, name: 'Test LLM', provider: 'openai' },
        { id: 2, name: 'Another LLM', provider: 'ollama' }
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockLLMs
      });

      // Act
      const result = await api.get('/llms/');

      // Assert
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/llms/',
        expect.objectContaining({
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        })
      );
      expect(result).toEqual(mockLLMs);
    });

    test('should create LLM successfully', async () => {
      // Arrange
      const newLLM = {
        name: 'New LLM',
        provider: 'openai',
        model_name: 'gpt-3.5-turbo',
        api_key: 'test-key'
      };
      
      const createdLLM = { id: 1, ...newLLM };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => createdLLM
      });

      // Act
      const result = await api.post('/llms/', newLLM);

      // Assert
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/llms/',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(newLLM)
        })
      );
      expect(result).toEqual(createdLLM);
    });

    test('should handle API error', async () => {
      // Arrange
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Bad request' })
      });

      // Act & Assert
      await expect(api.get('/llms/')).rejects.toThrow('HTTP error! status: 400');
    });

    test('should handle network error', async () => {
      // Arrange
      fetch.mockRejectedValueOnce(new Error('Network error'));

      // Act & Assert
      await expect(api.get('/llms/')).rejects.toThrow('Network error');
    });
  });

  describe('Action Operations', () => {
    test('should fetch actions successfully', async () => {
      // Arrange
      const mockActions = [
        { id: 1, name: 'Test Action', action_type: 'custom' },
        { id: 2, name: 'Native Action', action_type: 'native' }
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockActions
      });

      // Act
      const result = await api.get('/actions/');

      // Assert
      expect(result).toEqual(mockActions);
    });

    test('should create action successfully', async () => {
      // Arrange
      const newAction = {
        name: 'New Action',
        description: 'Test action',
        endpoint: 'https://api.example.com/test',
        method: 'GET',
        action_type: 'custom'
      };
      
      const createdAction = { id: 1, ...newAction };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => createdAction
      });

      // Act
      const result = await api.post('/actions/', newAction);

      // Assert
      expect(result).toEqual(createdAction);
    });

    test('should test action successfully', async () => {
      // Arrange
      const testData = {
        parameters: { id: '123' },
        context: { user_input: 'test' }
      };
      
      const testResult = {
        success: true,
        result: { data: 'test response' }
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => testResult
      });

      // Act
      const result = await api.post('/actions/1/test', testData);

      // Assert
      expect(result).toEqual(testResult);
    });
  });

  describe('Agent Operations', () => {
    test('should fetch agents successfully', async () => {
      // Arrange
      const mockAgents = [
        { id: 1, name: 'Test Agent', llm_id: 1 },
        { id: 2, name: 'Another Agent', llm_id: 2 }
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgents
      });

      // Act
      const result = await api.get('/agents/');

      // Assert
      expect(result).toEqual(mockAgents);
    });

    test('should run agent successfully', async () => {
      // Arrange
      const runData = { input: 'Hello, agent!' };
      const runResult = {
        response: 'Hello! How can I help you?',
        actions_used: ['Thinking', 'Respond']
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => runResult
      });

      // Act
      const result = await api.post('/agents/1/run', runData);

      // Assert
      expect(result).toEqual(runResult);
    });

    test('should continue agent successfully', async () => {
      // Arrange
      const continueData = {
        session_context: { user_input: 'initial input' },
        additional_input: 'more information'
      };
      
      const continueResult = {
        response: 'Thanks for the additional information!',
        actions_used: ['Wait', 'Respond']
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => continueResult
      });

      // Act
      const result = await api.post('/agents/1/continue', continueData);

      // Assert
      expect(result).toEqual(continueResult);
    });
  });

  describe('HTTP Methods', () => {
    test('should make PUT request correctly', async () => {
      // Arrange
      const updateData = { name: 'Updated Name' };
      const updatedItem = { id: 1, ...updateData };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedItem
      });

      // Act
      const result = await api.put('/llms/1', updateData);

      // Assert
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/llms/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData)
        })
      );
      expect(result).toEqual(updatedItem);
    });

    test('should make DELETE request correctly', async () => {
      // Arrange
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      // Act
      const result = await api.delete('/llms/1');

      // Assert
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/llms/1',
        expect.objectContaining({
          method: 'DELETE'
        })
      );
      expect(result).toEqual({ success: true });
    });
  });

  describe('Error Handling', () => {
    test('should throw error for 404 response', async () => {
      // Arrange
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' })
      });

      // Act & Assert
      await expect(api.get('/llms/999')).rejects.toThrow('HTTP error! status: 404');
    });

    test('should throw error for 500 response', async () => {
      // Arrange
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' })
      });

      // Act & Assert
      await expect(api.get('/llms/')).rejects.toThrow('HTTP error! status: 500');
    });

    test('should handle malformed JSON response', async () => {
      // Arrange
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        }
      });

      // Act & Assert
      await expect(api.get('/llms/')).rejects.toThrow('Invalid JSON');
    });
  });
});
