import React, { useState, useEffect } from 'react';
import { Form, Button, Table, Alert, Card, Container, Modal, Row, Col, Badge, Tabs, Tab } from 'react-bootstrap';
import api from '../services/api';

const ActionManager = () => {
  const [actions, setActions] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    endpoint: '',
    method: 'GET',
    parameters: '{}',
    headers: '{"Content-Type": "application/json"}',
    action_type: 'custom',
    yaml_spec: '',
    api_key: ''
  });
  const [editFormData, setEditFormData] = useState({
    id: '',
    name: '',
    description: '',
    endpoint: '',
    method: 'GET',
    parameters: '{}',
    headers: '{"Content-Type": "application/json"}',
    action_type: 'custom',
    yaml_spec: '',
    api_key: '',
    is_active: true
  });
  const [yamlData, setYamlData] = useState('');
  const [generatedFields, setGeneratedFields] = useState({});
  const [message, setMessage] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);
  const [activeTab, setActiveTab] = useState('form');
  const [testResults, setTestResults] = useState({});
  const [testParameters, setTestParameters] = useState({});
  const [testContext, setTestContext] = useState('{}');
  const [testingActionId, setTestingActionId] = useState(null);
  const [showTestModal, setShowTestModal] = useState(false);
  const [selectedActionForTest, setSelectedActionForTest] = useState(null);
  const [displayYamlData, setDisplayYamlData] = useState('');

  useEffect(() => {
    fetchActions();
  }, []);

  const fetchActions = async () => {
    try {
      const response = await api.get('/actions/');
      setActions(response.data);
    } catch (error) {
      console.error('Error fetching actions:', error);
    }
  };

  const maskApiKeyInYaml = (yamlContent, apiKey) => {
    if (!apiKey || !yamlContent) return yamlContent;
    
    // Replace the actual API key with masked version in the display
    const maskedKey = apiKey.length > 8 ? `***${apiKey.slice(-4)}` : '***';
    return yamlContent.replace(new RegExp(apiKey.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), maskedKey);
  };

  const handleYamlUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target.result;
        setYamlData(content); // Keep original for processing
        setDisplayYamlData(content); // Will be updated with masked version
        setFormData(prev => ({ ...prev, yaml_spec: content }));

        // Parse YAML and generate fields
        try {
          api.post('/actions/parse-yaml/', { 
            yaml_spec: content,
            api_key: formData.api_key 
          })
            .then(response => {
              setGeneratedFields(response.data);
              // Auto-fill form fields from YAML
              if (response.data.endpoint) {
                setFormData(prev => ({ ...prev, endpoint: response.data.endpoint }));
              }
              if (response.data.parameters) {
                setFormData(prev => ({
                  ...prev,
                  parameters: JSON.stringify(response.data.parameters, null, 2)
                }));
              }
              if (response.data.headers) {
                setFormData(prev => ({
                  ...prev,
                  headers: JSON.stringify(response.data.headers, null, 2)
                }));
              }
              
              // Update display with masked API key if present
              if (formData.api_key) {
                const maskedYaml = maskApiKeyInYaml(content, formData.api_key);
                setDisplayYamlData(maskedYaml);
              }
            })
            .catch(error => {
              console.error('Error parsing YAML:', error);
              setMessage('Error parsing YAML: ' + error.message);
            });
        } catch (error) {
          console.error('Error parsing YAML:', error);
          setMessage('Error parsing YAML: ' + error.message);
        }
      };
      reader.readAsText(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Parse JSON strings to objects
      const actionData = {
        ...formData,
        parameters: JSON.parse(formData.parameters),
        headers: JSON.parse(formData.headers)
      };
      await api.post('/actions/', actionData);
      setMessage('Action created successfully!');
      setFormData({
        name: '',
        description: '',
        endpoint: '',
        method: 'GET',
        parameters: '{}',
        headers: '{"Content-Type": "application/json"}',
        action_type: 'custom',
        yaml_spec: '',
        api_key: ''
      });
      setYamlData('');
      setGeneratedFields({});
      fetchActions();
    } catch (error) {
      setMessage('Error creating action: ' + error.message);
    }
  };

  const handleEdit = (action) => {
    // Convert objects to JSON strings for editing
    setEditFormData({
      ...action,
      parameters: JSON.stringify(action.parameters, null, 2),
      headers: JSON.stringify(action.headers, null, 2),
      yaml_spec: action.yaml_spec || '',
      api_key: action.api_key || ''
    });
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      // Parse JSON strings to objects
      const actionData = {
        ...editFormData,
        parameters: JSON.parse(editFormData.parameters),
        headers: JSON.parse(editFormData.headers)
      };
      await api.put(`/actions/${editFormData.id}`, actionData);
      setMessage('Action updated successfully!');
      setShowEditModal(false);
      fetchActions();
    } catch (error) {
      setMessage('Error updating action: ' + error.message);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this action?')) {
      try {
        await api.delete(`/actions/${id}`);
        setMessage('Action deleted successfully!');
        fetchActions();
      } catch (error) {
        setMessage('Error deleting action: ' + error.message);
      }
    }
  };

  const handleChange = (e) => {
    const newFormData = {
      ...formData,
      [e.target.name]: e.target.value
    };
    
    setFormData(newFormData);
    
    // Update masked YAML display when API key changes
    if (e.target.name === 'api_key' && yamlData) {
      const maskedYaml = maskApiKeyInYaml(yamlData, e.target.value);
      setDisplayYamlData(maskedYaml);
    }
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

  const handleTestAction = async (action) => {
    setSelectedActionForTest(action);
    setTestParameters({});
    setTestContext('{}');
    setTestResults({});
    
    // Initialize test parameters based on action's parameters
    if (action.parameters && typeof action.parameters === 'object') {
      const initialParams = {};
      Object.keys(action.parameters).forEach(key => {
        initialParams[key] = '';
      });
      setTestParameters(initialParams);
    }
    
    setShowTestModal(true);
  };

  const handleTestParameterChange = (paramName, value) => {
    setTestParameters(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  const executeActionTest = async () => {
    if (!selectedActionForTest) return;
    
    setTestingActionId(selectedActionForTest.id);
    setTestResults({});
    
    try {
      let context = {};
      try {
        context = JSON.parse(testContext);
      } catch (e) {
        context = {};
      }
      
      const response = await api.post(`/actions/${selectedActionForTest.id}/test`, {
        parameters: testParameters,
        context: context
      });
      
      setTestResults({
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      
      // Check if it's an endpoint URL error
      if (errorMessage.includes('endpoint must be a complete URL')) {
        setTestResults({
          success: false,
          error: errorMessage,
          timestamp: new Date().toISOString(),
          canFixEndpoint: true
        });
      } else {
        setTestResults({
          success: false,
          error: errorMessage,
          timestamp: new Date().toISOString()
        });
      }
    } finally {
      setTestingActionId(null);
    }
  };

  const fixActionEndpoint = async () => {
    if (!selectedActionForTest) return;
    
    try {
      const response = await api.post(`/actions/${selectedActionForTest.id}/fix-endpoint`);
      
      if (response.data.success) {
        setMessage(`Endpoint fixed successfully! Changed from '${response.data.original_endpoint}' to '${response.data.fixed_endpoint}'`);
        fetchActions(); // Refresh the actions list
        setTestResults({
          success: true,
          message: 'Endpoint fixed successfully. You can now test the action again.',
          timestamp: new Date().toISOString()
        });
      } else {
        setTestResults({
          success: false,
          error: response.data.message + ' ' + response.data.suggestion,
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      setTestResults({
        success: false,
        error: 'Failed to fix endpoint: ' + (error.response?.data?.detail || error.message),
        timestamp: new Date().toISOString()
      });
    }
  };

  const renderTestResults = () => {
    if (!testResults.timestamp) return null;
    
    return (
      <Card className="mt-3">
        <Card.Header className={testResults.success ? "bg-success text-white" : "bg-danger text-white"}>
          Test Results - {testResults.success ? "Success" : "Error"}
        </Card.Header>
        <Card.Body>
          {testResults.success ? (
            <div>
              {testResults.data.result && testResults.data.result.schema_applied ? (
                <div>
                  <h6>Filtered Response (Based on YAML Schema):</h6>
                  <div className="alert alert-success">
                    <small>✅ Response filtered according to YAML schema</small>
                  </div>
                  <pre className="bg-light p-3 rounded" style={{fontSize: '12px', maxHeight: '300px', overflow: 'auto'}}>
                    {JSON.stringify(testResults.data.result.filtered_data, null, 2)}
                  </pre>
                  
                  <details className="mt-3">
                    <summary className="btn btn-sm btn-outline-secondary">Show Raw Response</summary>
                    <pre className="bg-light p-3 rounded mt-2" style={{fontSize: '10px', maxHeight: '200px', overflow: 'auto'}}>
                      {JSON.stringify(testResults.data.result.raw_data, null, 2)}
                    </pre>
                  </details>
                  
                  <details className="mt-2">
                    <summary className="btn btn-sm btn-outline-info">Show Schema Used</summary>
                    <pre className="bg-info bg-opacity-10 p-3 rounded mt-2" style={{fontSize: '10px', maxHeight: '150px', overflow: 'auto'}}>
                      {JSON.stringify(testResults.data.result.schema_used, null, 2)}
                    </pre>
                  </details>
                </div>
              ) : (
                <div>
                  <h6>Response Details:</h6>
                  {testResults.data.result && testResults.data.result.note && (
                    <div className="alert alert-warning">
                      <small>ℹ️ {testResults.data.result.note}</small>
                    </div>
                  )}
                  <pre className="bg-light p-3 rounded" style={{fontSize: '12px', maxHeight: '400px', overflow: 'auto'}}>
                    {JSON.stringify(testResults.data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : testResults.message ? (
            <div>
              <h6 className="text-success">Success:</h6>
              <div className="alert alert-success">
                {testResults.message}
              </div>
            </div>
          ) : (
            <div>
              <h6 className="text-danger">Error:</h6>
              <div className="alert alert-danger">
                {testResults.error}
                {testResults.canFixEndpoint && (
                  <div className="mt-3">
                    <Button 
                      variant="warning" 
                      size="sm" 
                      onClick={fixActionEndpoint}
                    >
                      🔧 Try to Fix Endpoint Automatically
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}
          <small className="text-muted">
            Executed at: {new Date(testResults.timestamp).toLocaleString()}
          </small>
        </Card.Body>
      </Card>
    );
  };

  const renderTestForm = () => {
    if (!generatedFields.parameters) return null;

    return (
      <Card className="mt-4">
        <Card.Header>Test Action (From YAML)</Card.Header>
        <Card.Body>
          <Form>
            {Object.entries(generatedFields.parameters).map(([paramName, paramConfig]) => (
              <Form.Group key={paramName} className="mb-3">
                <Form.Label>{paramName} ({paramConfig.type})</Form.Label>
                <Form.Control
                  type="text"
                  placeholder={`Enter ${paramName}`}
                  value={testParameters[paramName] || ''}
                  onChange={(e) => handleTestParameterChange(paramName, e.target.value)}
                />
                {paramConfig.description && (
                  <Form.Text className="text-muted">{paramConfig.description}</Form.Text>
                )}
              </Form.Group>
            ))}
            
            <Form.Group className="mb-3">
              <Form.Label>Context (JSON)</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                value={testContext}
                onChange={(e) => setTestContext(e.target.value)}
                placeholder='{"key": "value"}'
              />
              <Form.Text className="text-muted">
                Optional context data to pass to the action
              </Form.Text>
            </Form.Group>
            
            <Button 
              variant="secondary" 
              onClick={executeActionTest}
              disabled={testingActionId !== null}
            >
              {testingActionId ? 'Testing...' : 'Test Action'}
            </Button>
          </Form>
          
          {renderTestResults()}
        </Card.Body>
      </Card>
    );
  };

  return (
    <Container>
      <h2 className="my-4">Action Management</h2>

      {message && <Alert variant="info" onClose={() => setMessage('')} dismissible>{message}</Alert>}

      <Card className="mb-4">
        <Card.Header>Create New Action</Card.Header>
        <Card.Body>
          <Tabs activeKey={activeTab} onSelect={setActiveTab} className="mb-3">
            <Tab eventKey="form" title="Form">
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
                      <Form.Label>Method</Form.Label>
                      <Form.Select
                        name="method"
                        value={formData.method}
                        onChange={handleChange}
                      >
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="DELETE">DELETE</option>
                      </Form.Select>
                    </Form.Group>
                  </Col>
                </Row>

                <Form.Group className="mb-3">
                  <Form.Label>Description</Form.Label>
                  <Form.Control
                    type="text"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Endpoint URL</Form.Label>
                  <Form.Control
                    type="text"
                    name="endpoint"
                    value={formData.endpoint}
                    onChange={handleChange}
                    required
                    placeholder="https://api.example.com/data"
                  />
                </Form.Group>

                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Parameters (JSON)</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={3}
                        name="parameters"
                        value={formData.parameters}
                        onChange={handleChange}
                        placeholder='{"param1": "value1", "param2": "value2"}'
                      />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Headers (JSON)</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={3}
                        name="headers"
                        value={formData.headers}
                        onChange={handleChange}
                        placeholder='{"Content-Type": "application/json", "Authorization": "Bearer token"}'
                      />
                    </Form.Group>
                  </Col>
                </Row>

                <Form.Group className="mb-3">
                  <Form.Label>API Key (optional)</Form.Label>
                  <Form.Control
                    type="password"
                    name="api_key"
                    value={formData.api_key}
                    onChange={handleChange}
                    placeholder="Enter API Key if required"
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Action Type</Form.Label>
                  <Form.Select
                    name="action_type"
                    value={formData.action_type}
                    onChange={handleChange}
                  >
                    <option value="custom">Custom</option>
                    <option value="native">Native</option>
                  </Form.Select>
                </Form.Group>

                <Button variant="primary" type="submit">
                  Create Action
                </Button>
              </Form>
            </Tab>

            <Tab eventKey="yaml" title="YAML Upload">
              <Form.Group className="mb-3">
                <Form.Label>Upload YAML Specification</Form.Label>
                <Form.Control
                  type="file"
                  accept=".yaml,.yml"
                  onChange={handleYamlUpload}
                />
                <Form.Text className="text-muted">
                  Upload an OpenAPI YAML specification file. Use the API Key field in the Form tab for authentication.
                </Form.Text>
              </Form.Group>

              {yamlData && (
                <>
                  <Form.Group className="mb-3">
                    <Form.Label>YAML Content</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={10}
                      name="yaml_spec"
                      value={displayYamlData}
                      onChange={(e) => {
                        const newValue = e.target.value;
                        setDisplayYamlData(newValue);
                        
                        // If the user is editing the YAML directly, we need to handle it carefully
                        // For now, we'll update the original yamlData but warn about API key exposure
                        setYamlData(newValue);
                        setFormData(prev => ({ ...prev, yaml_spec: newValue }));
                        
                        // If there's an API key and it appears in the YAML, show warning
                        if (formData.api_key && newValue.includes(formData.api_key)) {
                          setMessage('⚠️ Warning: API key detected in YAML content. Consider using the API Key field in the Form tab instead.');
                        }
                      }}
                    />
                  </Form.Group>

                  {Object.keys(generatedFields).length > 0 && (
                    <div className="mb-3">
                      <h5>Generated Fields</h5>
                      <pre>{JSON.stringify(generatedFields, null, 2)}</pre>
                      
                      {generatedFields.schema_preview && (
                        <div className="mt-3">
                          <h6>Expected Response Structure:</h6>
                          <div className="alert alert-info">
                            <small>Based on the YAML schema, the API response will be filtered to return only:</small>
                            <pre className="mt-2 mb-0" style={{fontSize: '12px'}}>
                              {JSON.stringify(generatedFields.schema_preview, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  <Button variant="primary" onClick={handleSubmit}>
                    Create Action from YAML
                  </Button>
                </>
              )}
            </Tab>
          </Tabs>
        </Card.Body>
      </Card>

      {renderTestForm()}

      <Card>
        <Card.Header>Actions</Card.Header>
        <Card.Body>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {actions.map(action => (
                <tr key={action.id}>
                  <td>{action.name}</td>
                  <td>
                    <Badge bg={action.action_type === 'native' ? 'primary' : 'secondary'}>
                      {action.action_type}
                    </Badge>
                  </td>
                  <td>{action.method}</td>
                  <td className="text-truncate" style={{maxWidth: '200px'}}>
                    {action.endpoint}
                  </td>
                  <td>
                    <Badge bg={action.is_active ? "success" : "secondary"}>
                      {action.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td>
                    <Button
                      variant="outline-success"
                      size="sm"
                      onClick={() => handleTestAction(action)}
                      className="me-2"
                      disabled={testingActionId === action.id}
                    >
                      {testingActionId === action.id ? 'Testing...' : 'Test'}
                    </Button>
                    <Button
                      variant="outline-primary"
                      size="sm"
                      onClick={() => handleEdit(action)}
                      className="me-2"
                    >
                      Edit
                    </Button>
                    <Button
                      variant="outline-danger"
                      size="sm"
                      onClick={() => handleDelete(action.id)}
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
          <Modal.Title>Edit Action</Modal.Title>
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
                  <Form.Label>Method</Form.Label>
                  <Form.Select
                    name="method"
                    value={editFormData.method}
                    onChange={handleEditChange}
                  >
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control
                type="text"
                name="description"
                value={editFormData.description}
                onChange={handleEditChange}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Endpoint URL</Form.Label>
              <Form.Control
                type="text"
                name="endpoint"
                value={editFormData.endpoint}
                onChange={handleEditChange}
                required
                placeholder="https://api.example.com/data"
              />
            </Form.Group>

            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Parameters (JSON)</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    name="parameters"
                    value={editFormData.parameters}
                    onChange={handleEditChange}
                    placeholder='{"param1": "value1", "param2": "value2"}'
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Headers (JSON)</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    name="headers"
                    value={editFormData.headers}
                    onChange={handleEditChange}
                    placeholder='{"Content-Type": "application/json", "Authorization": "Bearer token"}'
                  />
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>API Key</Form.Label>
              <Form.Control
                type="password"
                name="api_key"
                value={editFormData.api_key}
                onChange={handleEditChange}
                placeholder="Enter API Key if required"
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Action Type</Form.Label>
              <Form.Select
                name="action_type"
                value={editFormData.action_type}
                onChange={handleEditChange}
              >
                <option value="custom">Custom</option>
                <option value="native">Native</option>
              </Form.Select>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>YAML Specification</Form.Label>
              <Form.Control
                as="textarea"
                rows={5}
                name="yaml_spec"
                value={editFormData.yaml_spec}
                onChange={handleEditChange}
                placeholder="Paste OpenAPI YAML specification here"
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

      {/* Test Action Modal */}
      <Modal show={showTestModal} onHide={() => setShowTestModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Test Action: {selectedActionForTest?.name}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedActionForTest && (
            <div>
              <div className="mb-3">
                <strong>Action Details:</strong>
                <ul className="mt-2">
                  <li><strong>Type:</strong> {selectedActionForTest.action_type}</li>
                  <li><strong>Method:</strong> {selectedActionForTest.method}</li>
                  <li><strong>Endpoint:</strong> {selectedActionForTest.endpoint}</li>
                </ul>
              </div>

              <Form>
                <h5>Parameters</h5>
                {selectedActionForTest.parameters && Object.keys(selectedActionForTest.parameters).length > 0 ? (
                  Object.entries(selectedActionForTest.parameters).map(([paramName, paramConfig]) => (
                    <Form.Group key={paramName} className="mb-3">
                      <Form.Label>
                        {paramName}
                        {typeof paramConfig === 'object' && paramConfig.type && (
                          <span className="text-muted"> ({paramConfig.type})</span>
                        )}
                        {typeof paramConfig === 'object' && paramConfig.required && (
                          <span className="text-danger"> *</span>
                        )}
                      </Form.Label>
                      <Form.Control
                        type="text"
                        placeholder={`Enter ${paramName}`}
                        value={testParameters[paramName] || ''}
                        onChange={(e) => handleTestParameterChange(paramName, e.target.value)}
                      />
                      {typeof paramConfig === 'object' && paramConfig.description && (
                        <Form.Text className="text-muted">{paramConfig.description}</Form.Text>
                      )}
                    </Form.Group>
                  ))
                ) : (
                  <p className="text-muted">No parameters defined for this action.</p>
                )}

                <Form.Group className="mb-3">
                  <Form.Label>Context (JSON)</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    value={testContext}
                    onChange={(e) => setTestContext(e.target.value)}
                    placeholder='{"key": "value"}'
                  />
                  <Form.Text className="text-muted">
                    Optional context data to pass to the action
                  </Form.Text>
                </Form.Group>

                <Button 
                  variant="success" 
                  onClick={executeActionTest}
                  disabled={testingActionId !== null}
                  className="me-2"
                >
                  {testingActionId ? 'Testing...' : 'Execute Test'}
                </Button>
                
                <Button 
                  variant="secondary" 
                  onClick={() => setShowTestModal(false)}
                >
                  Close
                </Button>
              </Form>

              {renderTestResults()}
            </div>
          )}
        </Modal.Body>
      </Modal>
    </Container>
  );
};

export default ActionManager;