import React, { useState, useEffect } from 'react';
import {
  Form,
  Button,
  Table,
  Alert,
  Card,
  Container,
  Modal,
  Row,
  Col,
  Badge,
  ListGroup
} from 'react-bootstrap';
import api from '../services/api';

const AgentManager = () => {
  const [agents, setAgents] = useState([]);
  const [llms, setLlms] = useState([]);
  const [availableActions, setAvailableActions] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    system_prompt: 'You are a helpful assistant that can use available actions to help users.',
    llm_id: '',
    actions: [],
    config: {}
  });
  const [editFormData, setEditFormData] = useState({
    id: '',
    name: '',
    description: '',
    system_prompt: '',
    llm_id: '',
    actions: [],
    config: {},
    is_active: true
  });
  const [selectedAction, setSelectedAction] = useState('');
  const [actionPrompt, setActionPrompt] = useState('');
  const [message, setMessage] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);
  const [showFlowModal, setShowFlowModal] = useState(false);
  const [showEditActionsModal, setShowEditActionsModal] = useState(false);
  const [editingAgentActions, setEditingAgentActions] = useState({
    agent_id: null,
    agent_name: '',
    actions: []
  });
  const [selectedEditAction, setSelectedEditAction] = useState('');
  const [editActionPrompt, setEditActionPrompt] = useState('');

  useEffect(() => {
    fetchAgents();
    fetchLLMs();
    fetchActions();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await api.get('/agents/');
      setAgents(response.data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const fetchLLMs = async () => {
    try {
      const response = await api.get('/llms/');
      setLlms(response.data);
    } catch (error) {
      console.error('Error fetching LLMs:', error);
    }
  };

  const fetchActions = async () => {
    try {
      const response = await api.get('/actions/');
      setAvailableActions(response.data);
    } catch (error) {
      console.error('Error fetching actions:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/agents/', formData);
      setMessage('Agent created successfully!');
      setFormData({
        name: '',
        description: '',
        system_prompt: 'You are a helpful assistant that can use available actions to help users.',
        llm_id: '',
        actions: [],
        config: {}
      });
      fetchAgents();
    } catch (error) {
      setMessage('Error creating agent: ' + error.message);
    }
  };

  const handleEdit = (agent) => {
    setEditFormData({
      ...agent,
      actions: Array.isArray(agent.actions) ? agent.actions : []
    });
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.put(`/agents/${editFormData.id}`, editFormData);
      setMessage('Agent updated successfully!');
      setShowEditModal(false);
      fetchAgents();
    } catch (error) {
      setMessage('Error updating agent: ' + error.message);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      try {
        await api.delete(`/agents/${id}`);
        setMessage('Agent deleted successfully!');
        fetchAgents();
      } catch (error) {
        setMessage('Error deleting agent: ' + error.message);
      }
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleEditChange = (e) => {
    setEditFormData({
      ...editFormData,
      [e.target.name]: e.target.value
    });
  };

  const handleEditCheckboxChange = (e) => {
    setEditFormData({
      ...editFormData,
      [e.target.name]: e.target.checked
    });
  };

  const addActionToFlow = () => {
    if (!selectedAction) {
      setMessage('Please select an action');
      return;
    }

    const actionConfig = {
      action_name: selectedAction,
      prompt: actionPrompt,
      order: formData.actions.length + 1
    };

    setFormData({
      ...formData,
      actions: [...formData.actions, actionConfig]
    });

    setSelectedAction('');
    setActionPrompt('');
  };

  const removeActionFromFlow = (index) => {
    const newActions = [...formData.actions];
    newActions.splice(index, 1);
    setFormData({
      ...formData,
      actions: newActions
    });
  };

  const moveActionUp = (index) => {
    if (index === 0) return;

    const newActions = [...formData.actions];
    [newActions[index], newActions[index - 1]] = [newActions[index - 1], newActions[index]];

    setFormData({
      ...formData,
      actions: newActions
    });
  };

  const moveActionDown = (index) => {
    if (index === formData.actions.length - 1) return;

    const newActions = [...formData.actions];
    [newActions[index], newActions[index + 1]] = [newActions[index + 1], newActions[index]];

    setFormData({
      ...formData,
      actions: newActions
    });
  };

  const getActionDescription = (actionName) => {
    const action = availableActions.find(a => a.name === actionName);
    return action ? action.description : 'No description available';
  };

  // Agent Actions Management Functions
  const handleEditActions = async (agent) => {
    try {
      const response = await api.get(`/agents/${agent.id}/actions`);
      setEditingAgentActions(response.data);
      setShowEditActionsModal(true);
    } catch (error) {
      setMessage('Error loading agent actions: ' + error.message);
    }
  };

  const handleSaveAgentActions = async () => {
    try {
      await api.put(`/agents/${editingAgentActions.agent_id}/actions`, {
        actions: editingAgentActions.actions
      });
      setMessage('Agent actions updated successfully!');
      setShowEditActionsModal(false);
      fetchAgents();
    } catch (error) {
      setMessage('Error updating agent actions: ' + error.message);
    }
  };

  const addActionToEditFlow = () => {
    if (!selectedEditAction) {
      setMessage('Please select an action');
      return;
    }

    const actionConfig = {
      action_name: selectedEditAction,
      prompt: editActionPrompt,
      order: editingAgentActions.actions.length + 1
    };

    setEditingAgentActions({
      ...editingAgentActions,
      actions: [...editingAgentActions.actions, actionConfig]
    });

    setSelectedEditAction('');
    setEditActionPrompt('');
  };

  const removeActionFromEditFlow = (index) => {
    const newActions = [...editingAgentActions.actions];
    newActions.splice(index, 1);
    // Reorder remaining actions
    newActions.forEach((action, idx) => {
      action.order = idx + 1;
    });
    setEditingAgentActions({
      ...editingAgentActions,
      actions: newActions
    });
  };

  const moveEditActionUp = (index) => {
    if (index === 0) return;

    const newActions = [...editingAgentActions.actions];
    [newActions[index], newActions[index - 1]] = [newActions[index - 1], newActions[index]];
    
    // Update order numbers
    newActions.forEach((action, idx) => {
      action.order = idx + 1;
    });

    setEditingAgentActions({
      ...editingAgentActions,
      actions: newActions
    });
  };

  const moveEditActionDown = (index) => {
    if (index === editingAgentActions.actions.length - 1) return;

    const newActions = [...editingAgentActions.actions];
    [newActions[index], newActions[index + 1]] = [newActions[index + 1], newActions[index]];
    
    // Update order numbers
    newActions.forEach((action, idx) => {
      action.order = idx + 1;
    });

    setEditingAgentActions({
      ...editingAgentActions,
      actions: newActions
    });
  };

  const updateActionPrompt = (index, newPrompt) => {
    const newActions = [...editingAgentActions.actions];
    newActions[index].prompt = newPrompt;
    setEditingAgentActions({
      ...editingAgentActions,
      actions: newActions
    });
  };

  const renderActionFlow = () => {
    return (
      <Card className="mt-4">
        <Card.Header>
          <div className="d-flex justify-content-between align-items-center">
            <span>Action Flow</span>
            <Button variant="primary" size="sm" onClick={() => setShowFlowModal(true)}>
              Add Action
            </Button>
          </div>
        </Card.Header>
        <Card.Body>
          {formData.actions.length === 0 ? (
            <div className="text-center text-muted py-4">
              <p>No actions added yet.</p>
              <p>Click "Add Action" to start building your agent's workflow.</p>
            </div>
          ) : (
            <ListGroup variant="flush">
              <ListGroup.Item className="bg-light">
                <div className="d-flex justify-content-between align-items-center">
                  <strong>Step 0: Trigger (User Input)</strong>
                  <Badge bg="info">Always First</Badge>
                </div>
                <small className="text-muted">The user's message that starts the conversation</small>
              </ListGroup.Item>

              {formData.actions.map((action, index) => (
                <ListGroup.Item key={index}>
                  <div className="d-flex justify-content-between align-items-start">
                    <div className="flex-grow-1">
                      <div className="d-flex align-items-center">
                        <Badge bg="secondary" className="me-2">Step {index + 1}</Badge>
                        <strong>{action.action_name}</strong>
                      </div>
                      <div className="mt-1">
                        <small className="text-muted">{getActionDescription(action.action_name)}</small>
                      </div>
                      {action.prompt && (
                        <div className="mt-2">
                          <small><strong>Prompt:</strong> {action.prompt}</small>
                        </div>
                      )}
                    </div>
                    <div className="d-flex flex-column">
                      <Button
                        variant="outline-danger"
                        size="sm"
                        onClick={() => removeActionFromFlow(index)}
                        className="mb-1"
                      >
                        Remove
                      </Button>
                      <Button
                        variant="outline-secondary"
                        size="sm"
                        onClick={() => moveActionUp(index)}
                        disabled={index === 0}
                        className="mb-1"
                      >
                        ↑
                      </Button>
                      <Button
                        variant="outline-secondary"
                        size="sm"
                        onClick={() => moveActionDown(index)}
                        disabled={index === formData.actions.length - 1}
                      >
                        ↓
                      </Button>
                    </div>
                  </div>
                </ListGroup.Item>
              ))}
            </ListGroup>
          )}
        </Card.Body>
      </Card>
    );
  };

  return (
    <Container>
      <h2 className="my-4">Agent Management</h2>

      {message && <Alert variant="info" onClose={() => setMessage('')} dismissible>{message}</Alert>}

      <Card className="mb-4">
        <Card.Header>Create New Agent</Card.Header>
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
                  <Form.Label>LLM</Form.Label>
                  <Form.Select
                    name="llm_id"
                    value={formData.llm_id}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Select an LLM</option>
                    {llms.map(llm => (
                      <option key={llm.id} value={llm.id}>
                        {llm.name} ({llm.model_name})
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                name="description"
                value={formData.description}
                onChange={handleChange}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>System Prompt</Form.Label>
              <Form.Control
                as="textarea"
                rows={4}
                name="system_prompt"
                value={formData.system_prompt}
                onChange={handleChange}
                required
              />
              <Form.Text className="text-muted">
                This prompt will guide the agent's overall behavior and reasoning process.
              </Form.Text>
            </Form.Group>

            {renderActionFlow()}

            <Button variant="primary" type="submit" className="mt-3">
              Create Agent
            </Button>
          </Form>
        </Card.Body>
      </Card>

      <Card>
        <Card.Header>Agents</Card.Header>
        <Card.Body>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>LLM</th>
                <th>Actions</th>
                <th>Status</th>
                <th>Manage</th>
              </tr>
            </thead>
            <tbody>
              {agents.map(agent => (
                <tr key={agent.id}>
                  <td>{agent.name}</td>
                  <td>{agent.description}</td>
                  <td>{llms.find(llm => llm.id === agent.llm_id)?.name || 'Unknown'}</td>
                  <td>
                    <Badge bg="info">
                      {Array.isArray(agent.actions) ? agent.actions.length : 0} steps
                    </Badge>
                  </td>
                  <td>
                    <Badge bg={agent.is_active ? "success" : "secondary"}>
                      {agent.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td>
                    <Button
                      variant="outline-primary"
                      size="sm"
                      onClick={() => handleEdit(agent)}
                      className="me-2"
                    >
                      Edit
                    </Button>
                    <Button
                      variant="outline-info"
                      size="sm"
                      onClick={() => handleEditActions(agent)}
                      className="me-2"
                    >
                      Edit Actions
                    </Button>
                    <Button
                      variant="outline-danger"
                      size="sm"
                      onClick={() => handleDelete(agent.id)}
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
          <Modal.Title>Edit Agent</Modal.Title>
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
                  <Form.Label>LLM</Form.Label>
                  <Form.Select
                    name="llm_id"
                    value={editFormData.llm_id}
                    onChange={handleEditChange}
                    required
                  >
                    <option value="">Select an LLM</option>
                    {llms.map(llm => (
                      <option key={llm.id} value={llm.id}>
                        {llm.name} ({llm.model_name})
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                name="description"
                value={editFormData.description}
                onChange={handleEditChange}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>System Prompt</Form.Label>
              <Form.Control
                as="textarea"
                rows={4}
                name="system_prompt"
                value={editFormData.system_prompt}
                onChange={handleEditChange}
                required
              />
            </Form.Group>

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

      {/* Add Action Modal */}
      <Modal show={showFlowModal} onHide={() => setShowFlowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Add Action to Flow</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Select Action</Form.Label>
            <Form.Select
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value)}
            >
              <option value="">Choose an action</option>
              {availableActions.map(action => (
                <option key={action.id} value={action.name}>
                  {action.name} ({action.action_type})
                </option>
              ))}
            </Form.Select>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Prompt/Instructions</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={actionPrompt}
              onChange={(e) => setActionPrompt(e.target.value)}
              placeholder="Enter instructions for this action (e.g., 'Think about how to handle this request')"
            />
            <Form.Text className="text-muted">
              This prompt will guide the LLM on how to use this action.
            </Form.Text>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowFlowModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={addActionToFlow}>
            Add Action
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Edit Agent Actions Modal */}
      <Modal show={showEditActionsModal} onHide={() => setShowEditActionsModal(false)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>Edit Actions for {editingAgentActions.agent_name}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Row>
            <Col md={4}>
              <Card>
                <Card.Header>Add New Action</Card.Header>
                <Card.Body>
                  <Form.Group className="mb-3">
                    <Form.Label>Select Action</Form.Label>
                    <Form.Select
                      value={selectedEditAction}
                      onChange={(e) => setSelectedEditAction(e.target.value)}
                    >
                      <option value="">Choose an action</option>
                      {availableActions.map(action => (
                        <option key={action.id} value={action.name}>
                          {action.name} ({action.action_type})
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label>Prompt/Instructions</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={3}
                      value={editActionPrompt}
                      onChange={(e) => setEditActionPrompt(e.target.value)}
                      placeholder="Enter instructions for this action"
                    />
                  </Form.Group>

                  <Button 
                    variant="primary" 
                    onClick={addActionToEditFlow}
                    className="w-100"
                  >
                    Add Action
                  </Button>
                </Card.Body>
              </Card>
            </Col>

            <Col md={8}>
              <Card>
                <Card.Header>
                  <div className="d-flex justify-content-between align-items-center">
                    <span>Current Action Flow</span>
                    <Badge bg="info">{editingAgentActions.actions.length} actions</Badge>
                  </div>
                </Card.Header>
                <Card.Body style={{ maxHeight: '500px', overflowY: 'auto' }}>
                  {editingAgentActions.actions.length === 0 ? (
                    <div className="text-center text-muted py-4">
                      <p>No actions configured yet.</p>
                      <p>Add actions using the form on the left.</p>
                    </div>
                  ) : (
                    <ListGroup variant="flush">
                      <ListGroup.Item className="bg-light">
                        <div className="d-flex justify-content-between align-items-center">
                          <strong>Step 0: Trigger (User Input)</strong>
                          <Badge bg="info">Always First</Badge>
                        </div>
                        <small className="text-muted">The user's message that starts the conversation</small>
                      </ListGroup.Item>

                      {editingAgentActions.actions.map((action, index) => (
                        <ListGroup.Item key={index}>
                          <div className="d-flex justify-content-between align-items-start">
                            <div className="flex-grow-1">
                              <div className="d-flex align-items-center">
                                <Badge bg="secondary" className="me-2">Step {index + 1}</Badge>
                                <strong>{action.action_name}</strong>
                                {action.action_type && (
                                  <Badge bg={action.action_type === 'native' ? 'success' : 'warning'} className="ms-2">
                                    {action.action_type}
                                  </Badge>
                                )}
                                {action.error && (
                                  <Badge bg="danger" className="ms-2">
                                    Error
                                  </Badge>
                                )}
                              </div>
                              <div className="mt-1">
                                <small className="text-muted">
                                  {action.description || getActionDescription(action.action_name)}
                                </small>
                              </div>
                              <div className="mt-2">
                                <Form.Group>
                                  <Form.Label className="small">Prompt/Instructions:</Form.Label>
                                  <Form.Control
                                    as="textarea"
                                    rows={2}
                                    value={action.prompt || ''}
                                    onChange={(e) => updateActionPrompt(index, e.target.value)}
                                    placeholder="Enter instructions for this action"
                                  />
                                </Form.Group>
                              </div>
                              {action.error && (
                                <div className="mt-2">
                                  <small className="text-danger">
                                    <strong>Error:</strong> {action.error}
                                  </small>
                                </div>
                              )}
                            </div>
                            <div className="d-flex flex-column ms-3">
                              <Button
                                variant="outline-danger"
                                size="sm"
                                onClick={() => removeActionFromEditFlow(index)}
                                className="mb-1"
                              >
                                Remove
                              </Button>
                              <Button
                                variant="outline-secondary"
                                size="sm"
                                onClick={() => moveEditActionUp(index)}
                                disabled={index === 0}
                                className="mb-1"
                              >
                                ↑
                              </Button>
                              <Button
                                variant="outline-secondary"
                                size="sm"
                                onClick={() => moveEditActionDown(index)}
                                disabled={index === editingAgentActions.actions.length - 1}
                              >
                                ↓
                              </Button>
                            </div>
                          </div>
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEditActionsModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSaveAgentActions}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default AgentManager;