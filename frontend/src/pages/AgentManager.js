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
    conditional_flows: [],
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
  
  // Conditional Flow Management States
  const [showConditionalFlowModal, setShowConditionalFlowModal] = useState(false);
  const [currentChoiceAction, setCurrentChoiceAction] = useState('');
  const [validFlowActions, setValidFlowActions] = useState([]);
  const [invalidFlowActions, setInvalidFlowActions] = useState([]);
  const [selectedValidAction, setSelectedValidAction] = useState('');
  const [selectedInvalidAction, setSelectedInvalidAction] = useState('');
  const [validActionPrompt, setValidActionPrompt] = useState('');
  const [invalidActionPrompt, setInvalidActionPrompt] = useState('');

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
      // Fetch custom actions
      const customActionsResponse = await api.get('/actions/');
      
      // Fetch native actions
      const nativeActionsResponse = await api.get('/actions/native');
      
      // Filter out custom actions that have the same name as native actions
      const nativeActionNames = nativeActionsResponse.data.native_actions.map(action => action.name);
      const filteredCustomActions = customActionsResponse.data.filter(
        action => !nativeActionNames.includes(action.name)
      );
      
      // Combine native actions first, then filtered custom actions
      const allActions = [
        ...nativeActionsResponse.data.native_actions,
        ...filteredCustomActions
      ];
      
      setAvailableActions(allActions);
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

    const selectedActionData = availableActions.find(action => action.name === selectedAction);
    const isChoiceAction = selectedActionData?.special_properties?.creates_branches;

    const actionConfig = {
      action_name: selectedAction,
      prompt: actionPrompt,
      order: formData.actions.length + 1,
      flow_type: "main"
    };

    // If it's a Choice action, we need to handle conditional flows
    if (isChoiceAction) {
      // Add a note that this creates branches
      actionConfig.creates_branches = true;
      actionConfig.validation_criteria = actionPrompt;
      
      // Open conditional flow modal
      setCurrentChoiceAction(selectedAction);
      setValidFlowActions([]);
      setInvalidFlowActions([]);
      setShowConditionalFlowModal(true);
      setShowFlowModal(false);
      
      // Add the choice action to the main flow
      setFormData({
        ...formData,
        actions: [...formData.actions, actionConfig]
      });
      
      setSelectedAction('');
      setActionPrompt('');
      return;
    }

    setFormData({
      ...formData,
      actions: [...formData.actions, actionConfig]
    });

    setSelectedAction('');
    setActionPrompt('');
    setShowFlowModal(false);
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

  // Conditional Flow Management Functions
  const addActionToValidFlow = () => {
    if (!selectedValidAction) {
      setMessage('Please select an action for the valid flow');
      return;
    }

    const actionConfig = {
      action_name: selectedValidAction,
      prompt: validActionPrompt,
      order: validFlowActions.length + 1,
      flow_type: "valid_flow"
    };

    setValidFlowActions([...validFlowActions, actionConfig]);
    setSelectedValidAction('');
    setValidActionPrompt('');
  };

  const addActionToInvalidFlow = () => {
    if (!selectedInvalidAction) {
      setMessage('Please select an action for the invalid flow');
      return;
    }

    const actionConfig = {
      action_name: selectedInvalidAction,
      prompt: invalidActionPrompt,
      order: invalidFlowActions.length + 1,
      flow_type: "invalid_flow"
    };

    setInvalidFlowActions([...invalidFlowActions, actionConfig]);
    setSelectedInvalidAction('');
    setInvalidActionPrompt('');
  };

  const removeActionFromValidFlow = (index) => {
    const newActions = [...validFlowActions];
    newActions.splice(index, 1);
    setValidFlowActions(newActions);
  };

  const removeActionFromInvalidFlow = (index) => {
    const newActions = [...invalidFlowActions];
    newActions.splice(index, 1);
    setInvalidFlowActions(newActions);
  };

  const saveConditionalFlow = () => {
    if (validFlowActions.length === 0 && invalidFlowActions.length === 0) {
      setMessage('Please add at least one action to either the valid or invalid flow');
      return;
    }

    // Check if at least one flow has a Respond action OR if main flow has Wait action
    const hasRespondInValid = validFlowActions.some(action => action.action_name === 'Respond');
    const hasRespondInInvalid = invalidFlowActions.some(action => action.action_name === 'Respond');
    const hasRespondInMainFlow = formData.actions.some(action => action.action_name === 'Respond');
    const hasWaitInMainFlow = formData.actions.some(action => action.action_name === 'Wait');

    if (!hasRespondInValid && !hasRespondInInvalid && !hasRespondInMainFlow && !hasWaitInMainFlow) {
      setMessage('At least one flow must contain a "Respond" action OR the main flow must have a "Wait" action for user interaction');
      return;
    }

    const conditionalFlow = {
      choice_action: currentChoiceAction,
      valid_flow: validFlowActions,
      invalid_flow: invalidFlowActions
    };

    setFormData({
      ...formData,
      conditional_flows: [...formData.conditional_flows, conditionalFlow]
    });

    setShowConditionalFlowModal(false);
    setMessage(`Conditional flows created for "${currentChoiceAction}" action!`);
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
                        {action.creates_branches && (
                          <Badge bg="warning" className="ms-2">Creates Branches</Badge>
                        )}
                        {action.action_name === 'Wait' && (
                          <Badge bg="info" className="ms-2">Pauses Execution</Badge>
                        )}
                      </div>
                      <div className="mt-1">
                        <small className="text-muted">{getActionDescription(action.action_name)}</small>
                      </div>
                      {action.prompt && (
                        <div className="mt-2">
                          <small><strong>
                            {action.action_name === 'Choice' ? 'Validation Criteria:' : 
                             action.action_name === 'Wait' ? 'Wait Message:' : 'Prompt:'}
                          </strong> {action.prompt}</small>
                        </div>
                      )}
                      {action.creates_branches && (
                        <div className="mt-2">
                          <small className="text-info">
                            <strong>Note:</strong> This action will create conditional flows (valid/invalid paths)
                          </small>
                          {/* Show conditional flows if they exist */}
                          {formData.conditional_flows.find(flow => flow.choice_action === action.action_name) && (
                            <div className="mt-2">
                              <Badge bg="success" className="me-1">
                                Valid Flow: {formData.conditional_flows.find(flow => flow.choice_action === action.action_name)?.valid_flow.length || 0} actions
                              </Badge>
                              <Badge bg="danger">
                                Invalid Flow: {formData.conditional_flows.find(flow => flow.choice_action === action.action_name)?.invalid_flow.length || 0} actions
                              </Badge>
                            </div>
                          )}
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
                <option key={action.id || action.name} value={action.name}>
                  {action.name} ({action.type || action.action_type || 'custom'})
                  {action.special_properties?.creates_branches && ' - Creates Branches'}
                  {action.special_properties?.pause_execution && ' - Pauses Execution'}
                </option>
              ))}
            </Form.Select>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>
              {selectedAction === 'Choice' ? 'Validation Criteria' : 
               selectedAction === 'Wait' ? 'Wait Message' : 'Prompt/Instructions'}
            </Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={actionPrompt}
              onChange={(e) => setActionPrompt(e.target.value)}
              placeholder={
                selectedAction === 'Choice' ? 'Enter criteria to validate (e.g., "Check if incident ID exists and is accessible")' :
                selectedAction === 'Wait' ? 'Enter message to show user (e.g., "Please provide the incident ID")' :
                'Enter instructions for this action (e.g., "Think about how to handle this request")'
              }
            />
            <Form.Text className="text-muted">
              {selectedAction === 'Choice' ? 'This action will create two conditional flows: one for valid results and one for invalid results.' :
               selectedAction === 'Wait' ? 'This action will pause execution and wait for additional user input.' :
               'This prompt will guide the LLM on how to use this action.'}
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
                        <option key={action.id || action.name} value={action.name}>
                          {action.name} ({action.type || action.action_type || 'custom'})
                          {action.special_properties?.creates_branches && ' - Creates Branches'}
                          {action.special_properties?.pause_execution && ' - Pauses Execution'}
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

      {/* Conditional Flow Modal */}
      <Modal show={showConditionalFlowModal} onHide={() => setShowConditionalFlowModal(false)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>Configure Conditional Flows for "{currentChoiceAction}"</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="info">
            <strong>How it works:</strong> When the "{currentChoiceAction}" action validates the input:
            <ul className="mb-0 mt-2">
              <li><strong>Valid Flow:</strong> Actions to execute when validation passes</li>
              <li><strong>Invalid Flow:</strong> Actions to execute when validation fails</li>
            </ul>
          </Alert>

          <Alert variant="warning">
            <strong>⚠️ Important:</strong> At least one flow (valid or invalid) must contain a <strong>"Respond"</strong> action to generate responses for the user, OR your main flow should have a <strong>"Wait"</strong> action for user interaction.
          </Alert>

          <Row>
            {/* Valid Flow Column */}
            <Col md={6}>
              <Card className="h-100">
                <Card.Header className="bg-success text-white">
                  <h5 className="mb-0">✅ Valid Flow</h5>
                  <small>Actions when validation passes</small>
                </Card.Header>
                <Card.Body>
                  {/* Add Action to Valid Flow */}
                  <Form.Group className="mb-3">
                    <Form.Label>Add Action</Form.Label>
                    <Form.Select
                      value={selectedValidAction}
                      onChange={(e) => setSelectedValidAction(e.target.value)}
                    >
                      <option value="">Choose an action</option>
                      {availableActions.map(action => (
                        <option key={action.id || action.name} value={action.name}>
                          {action.name} ({action.type || action.action_type || 'custom'})
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label>Prompt/Instructions</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={2}
                      value={validActionPrompt}
                      onChange={(e) => setValidActionPrompt(e.target.value)}
                      placeholder="Enter instructions for this action"
                    />
                  </Form.Group>

                  <Button 
                    variant="success" 
                    onClick={addActionToValidFlow}
                    className="w-100 mb-3"
                    disabled={!selectedValidAction}
                  >
                    Add to Valid Flow
                  </Button>

                  {/* Valid Flow Actions List */}
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {validFlowActions.length === 0 ? (
                      <div className="text-center text-muted py-3">
                        <small>No actions in valid flow yet</small>
                      </div>
                    ) : (
                      <ListGroup>
                        {validFlowActions.map((action, index) => (
                          <ListGroup.Item key={index}>
                            <div className="d-flex justify-content-between align-items-start">
                              <div className="flex-grow-1">
                                <div className="d-flex align-items-center">
                                  <Badge bg="success" className="me-2">Step {index + 1}</Badge>
                                  <strong>{action.action_name}</strong>
                                </div>
                                {action.prompt && (
                                  <div className="mt-1">
                                    <small className="text-muted">{action.prompt}</small>
                                  </div>
                                )}
                              </div>
                              <Button
                                variant="outline-danger"
                                size="sm"
                                onClick={() => removeActionFromValidFlow(index)}
                              >
                                ×
                              </Button>
                            </div>
                          </ListGroup.Item>
                        ))}
                      </ListGroup>
                    )}
                  </div>
                </Card.Body>
              </Card>
            </Col>

            {/* Invalid Flow Column */}
            <Col md={6}>
              <Card className="h-100">
                <Card.Header className="bg-danger text-white">
                  <h5 className="mb-0">❌ Invalid Flow</h5>
                  <small>Actions when validation fails</small>
                </Card.Header>
                <Card.Body>
                  {/* Add Action to Invalid Flow */}
                  <Form.Group className="mb-3">
                    <Form.Label>Add Action</Form.Label>
                    <Form.Select
                      value={selectedInvalidAction}
                      onChange={(e) => setSelectedInvalidAction(e.target.value)}
                    >
                      <option value="">Choose an action</option>
                      {availableActions.map(action => (
                        <option key={action.id || action.name} value={action.name}>
                          {action.name} ({action.type || action.action_type || 'custom'})
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label>Prompt/Instructions</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={2}
                      value={invalidActionPrompt}
                      onChange={(e) => setInvalidActionPrompt(e.target.value)}
                      placeholder="Enter instructions for this action"
                    />
                  </Form.Group>

                  <Button 
                    variant="danger" 
                    onClick={addActionToInvalidFlow}
                    className="w-100 mb-3"
                    disabled={!selectedInvalidAction}
                  >
                    Add to Invalid Flow
                  </Button>

                  {/* Invalid Flow Actions List */}
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {invalidFlowActions.length === 0 ? (
                      <div className="text-center text-muted py-3">
                        <small>No actions in invalid flow yet</small>
                      </div>
                    ) : (
                      <ListGroup>
                        {invalidFlowActions.map((action, index) => (
                          <ListGroup.Item key={index}>
                            <div className="d-flex justify-content-between align-items-start">
                              <div className="flex-grow-1">
                                <div className="d-flex align-items-center">
                                  <Badge bg="danger" className="me-2">Step {index + 1}</Badge>
                                  <strong>{action.action_name}</strong>
                                </div>
                                {action.prompt && (
                                  <div className="mt-1">
                                    <small className="text-muted">{action.prompt}</small>
                                  </div>
                                )}
                              </div>
                              <Button
                                variant="outline-danger"
                                size="sm"
                                onClick={() => removeActionFromInvalidFlow(index)}
                              >
                                ×
                              </Button>
                            </div>
                          </ListGroup.Item>
                        ))}
                      </ListGroup>
                    )}
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowConditionalFlowModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="primary" 
            onClick={saveConditionalFlow}
            disabled={validFlowActions.length === 0 && invalidFlowActions.length === 0}
          >
            Save Conditional Flows
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default AgentManager;