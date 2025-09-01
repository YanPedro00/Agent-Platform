import React, { useState, useEffect } from 'react';
import { Form, Button, Table, Alert, Card, Container, Modal, Row, Col, Badge } from 'react-bootstrap';
import api from '../services/api';

const LLMManager = () => {
  const [llms, setLlms] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    provider: 'openai',
    model_name: 'gpt-3.5-turbo',
    api_key: '',
    base_url: '',
    context_window: 4096,
    max_tokens: 1000,
    temperature: 0.1
  });
  const [editFormData, setEditFormData] = useState({
    id: '',
    name: '',
    provider: 'openai',
    model_name: '',
    api_key: '',
    base_url: '',
    context_window: 4096,
    max_tokens: 1000,
    temperature: 0.1,
    is_active: true
  });
  const [message, setMessage] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    fetchLLMs();
  }, []);

  const fetchLLMs = async () => {
    try {
      const response = await api.get('/llms/');
      setLlms(response.data);
    } catch (error) {
      console.error('Error fetching LLMs:', error);
    }
  };

  const getProviderPlaceholder = (provider) => {
    switch (provider) {
      case 'openai':
        return 'https://api.openai.com/v1';
      case 'lmstudio':
        return 'http://localhost:1234/v1';
      case 'ollama':
        return 'http://localhost:11434';
      case 'custom':
        return 'https://your-custom-api.com/v1';
      default:
        return 'https://api.example.com/v1';
    }
  };

  const getProviderHelpText = (provider) => {
    switch (provider) {
      case 'openai':
        return 'OpenAI API endpoint. Usually https://api.openai.com/v1';
      case 'lmstudio':
        return 'LM Studio usually runs on http://localhost:1234/v1';
      case 'ollama':
        return 'Ollama usually runs on http://localhost:11434';
      case 'custom':
        return 'Enter your custom API endpoint URL';
      default:
        return 'API endpoint URL';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/llms/', formData);
      setMessage('LLM added successfully!');
      setFormData({
        name: '',
        provider: 'openai',
        model_name: 'gpt-3.5-turbo',
        api_key: '',
        base_url: '',
        context_window: 4096,
        max_tokens: 1000,
        temperature: 0.1
      });
      fetchLLMs();
    } catch (error) {
      setMessage('Error adding LLM: ' + error.message);
    }
  };

  const handleEdit = (llm) => {
    setEditFormData(llm);
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.put(`/llms/${editFormData.id}`, editFormData);
      setMessage('LLM updated successfully!');
      setShowEditModal(false);
      fetchLLMs();
    } catch (error) {
      setMessage('Error updating LLM: ' + error.message);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this LLM?')) {
      try {
        await api.delete(`/llms/${id}`);
        setMessage('LLM deleted successfully!');
        fetchLLMs();
      } catch (error) {
        setMessage('Error deleting LLM: ' + error.message);
      }
    }
  };

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'number' ? parseFloat(value) : value
    });
  };

  const handleEditChange = (e) => {
    const { name, value, type } = e.target;
    setEditFormData({
      ...editFormData,
      [name]: type === 'number' ? parseFloat(value) : value
    });
  };

  const handleEditCheckboxChange = (e) => {
    setEditFormData({
      ...editFormData,
      [e.target.name]: e.target.checked
    });
  };

  return (
    <Container>
      <h2 className="my-4">LLM Management</h2>

      {message && <Alert variant="info" onClose={() => setMessage('')} dismissible>{message}</Alert>}

      <Card className="mb-4">
        <Card.Header>Add New LLM</Card.Header>
        <Card.Body>
          <Form onSubmit={handleSubmit}>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Name</Form.Label>
                  <Form.Control
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Provider</Form.Label>
                  <Form.Select
                    name="provider"
                    value={formData.provider}
                    onChange={handleChange}
                  >
                    <option value="openai">OpenAI</option>
                    <option value="lmstudio">LM Studio</option>
                    <option value="ollama">Ollama</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="huggingface">HuggingFace</option>
                    <option value="custom">Custom API</option>
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Model Name</Form.Label>
                  <Form.Control
                    type="text"
                    name="model_name"
                    value={formData.model_name}
                    onChange={handleChange}
                    required
                    placeholder="gpt-3.5-turbo, llama2, etc."
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>API Key (optional for some providers)</Form.Label>
                  <Form.Control
                    type="password"
                    name="api_key"
                    value={formData.api_key}
                    onChange={handleChange}
                    placeholder="Leave empty for local providers"
                  />
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>Base URL</Form.Label>
              <Form.Control
                type="text"
                name="base_url"
                value={formData.base_url}
                onChange={handleChange}
                placeholder={getProviderPlaceholder(formData.provider)}
              />
              <Form.Text className="text-muted">
                {getProviderHelpText(formData.provider)}
              </Form.Text>
            </Form.Group>

            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Context Window</Form.Label>
                  <Form.Control
                    type="number"
                    name="context_window"
                    value={formData.context_window}
                    onChange={handleChange}
                  />
                  <Form.Text className="text-muted">
                    Max context size
                  </Form.Text>
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Max Tokens</Form.Label>
                  <Form.Control
                    type="number"
                    name="max_tokens"
                    value={formData.max_tokens}
                    onChange={handleChange}
                  />
                  <Form.Text className="text-muted">
                    Response length limit
                  </Form.Text>
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Temperature</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    name="temperature"
                    value={formData.temperature}
                    onChange={handleChange}
                  />
                  <Form.Text className="text-muted">
                    0 = deterministic, 2 = creative
                  </Form.Text>
                </Form.Group>
              </Col>
            </Row>

            <Button variant="primary" type="submit">
              Add LLM
            </Button>
          </Form>
        </Card.Body>
      </Card>

      <Card>
        <Card.Header>Configured LLMs</Card.Header>
        <Card.Body>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>Name</th>
                <th>Provider</th>
                <th>Model</th>
                <th>Context</th>
                <th>Max Tokens</th>
                <th>Temp</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {llms.map(llm => (
                <tr key={llm.id}>
                  <td>{llm.name}</td>
                  <td>
                    <Badge bg="secondary">{llm.provider}</Badge>
                  </td>
                  <td>{llm.model_name}</td>
                  <td>{llm.context_window}</td>
                  <td>{llm.max_tokens}</td>
                  <td>{llm.temperature}</td>
                  <td>
                    <Badge bg={llm.is_active ? "success" : "secondary"}>
                      {llm.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td>
                    <Button
                      variant="outline-primary"
                      size="sm"
                      onClick={() => handleEdit(llm)}
                      className="me-2"
                    >
                      Edit
                    </Button>
                    <Button
                      variant="outline-danger"
                      size="sm"
                      onClick={() => handleDelete(llm.id)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Edit Modal */}
      <Modal show={showEditModal} onHide={() => setShowEditModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Edit LLM</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleEditSubmit}>
          <Modal.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Name</Form.Label>
                  <Form.Control
                    type="text"
                    name="name"
                    value={editFormData.name}
                    onChange={handleEditChange}
                    required
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Provider</Form.Label>
                  <Form.Select
                    name="provider"
                    value={editFormData.provider}
                    onChange={handleEditChange}
                  >
                    <option value="openai">OpenAI</option>
                    <option value="lmstudio">LM Studio</option>
                    <option value="ollama">Ollama</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="huggingface">HuggingFace</option>
                    <option value="custom">Custom API</option>
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Model Name</Form.Label>
                  <Form.Control
                    type="text"
                    name="model_name"
                    value={editFormData.model_name}
                    onChange={handleEditChange}
                    required
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>API Key</Form.Label>
                  <Form.Control
                    type="password"
                    name="api_key"
                    value={editFormData.api_key}
                    onChange={handleEditChange}
                    placeholder="Leave blank to keep current"
                  />
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>Base URL</Form.Label>
              <Form.Control
                type="text"
                name="base_url"
                value={editFormData.base_url}
                onChange={handleEditChange}
                placeholder={getProviderPlaceholder(editFormData.provider)}
              />
              <Form.Text className="text-muted">
                {getProviderHelpText(editFormData.provider)}
              </Form.Text>
            </Form.Group>

            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Context Window</Form.Label>
                  <Form.Control
                    type="number"
                    name="context_window"
                    value={editFormData.context_window}
                    onChange={handleEditChange}
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Max Tokens</Form.Label>
                  <Form.Control
                    type="number"
                    name="max_tokens"
                    value={editFormData.max_tokens}
                    onChange={handleEditChange}
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Temperature</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    name="temperature"
                    value={editFormData.temperature}
                    onChange={handleEditChange}
                  />
                </Form.Group>
              </Col>
            </Row>

            <Form.Check
              type="checkbox"
              name="is_active"
              label="Active"
              checked={editFormData.is_active}
              onChange={handleEditCheckboxChange}
            />
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Save Changes
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </Container>
  );
};

export default LLMManager;