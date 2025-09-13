import React, { useState, useEffect, useRef } from 'react';
import {
  Form,
  Button,
  Card,
  Alert,
  Container,
  Spinner,
  Row,
  Col
} from 'react-bootstrap';
import api from '../services/api';

const AgentRunner = () => {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('');
  const [input, setInput] = useState('');
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [waitingForInput, setWaitingForInput] = useState(false);
  const [sessionContext, setSessionContext] = useState(null);
  const [waitPrompt, setWaitPrompt] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchAgents = async () => {
    try {
      const response = await api.get('/agents/');
      setAgents(response.data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const handleRun = async (e) => {
    e.preventDefault();
    if (!selectedAgent) {
      setMessage('Please select an agent');
      return;
    }
    if (!input.trim()) {
      setMessage('Please enter a message');
      return;
    }

    setLoading(true);
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString()
    };

    setConversation(prev => [...prev, userMessage]);
    setInput('');
    setMessage('');

    try {
      const response = await api.post(`/agents/${selectedAgent}/run`, {
        input: input
      });

      // Check if agent is waiting for input
      if (response.data.wait_required) {
        // Agent is waiting for additional input
        const waitMessage = {
          id: Date.now() + 1,
          sender: 'agent',
          content: response.data.wait_message || 'Please provide additional information to continue.',
          timestamp: new Date().toLocaleTimeString(),
          isWaiting: true
        };
        setConversation(prev => [...prev, waitMessage]);
        setWaitingForInput(true);
        // Include actions_used in session_context for continue endpoint
        const contextWithActions = {
          ...response.data.session_context,
          actions_used: response.data.actions_used || []
        };
        setSessionContext(contextWithActions);
        setWaitPrompt(response.data.wait_prompt || 'Please provide additional information:');
      } else if (response.data.response) {
        // Normal response
        const agentMessage = {
          id: Date.now() + 1,
          sender: 'agent',
          content: response.data.response,
          timestamp: new Date().toLocaleTimeString()
        };
        setConversation(prev => [...prev, agentMessage]);
        setWaitingForInput(false);
        setSessionContext(null);
      } else {
        // Agent has no Respond action or didn't generate a response
        const systemMessage = {
          id: Date.now() + 1,
          sender: 'system',
          content: response.data.message || 'Agent processed your request but has no Respond action configured',
          timestamp: new Date().toLocaleTimeString()
        };
        setConversation(prev => [...prev, systemMessage]);
        setWaitingForInput(false);
        setSessionContext(null);
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'system',
        content: 'Error: ' + error.message,
        timestamp: new Date().toLocaleTimeString()
      };
      setConversation(prev => [...prev, errorMessage]);
      setMessage('Error running agent: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = async (e) => {
    e.preventDefault();
    if (!input.trim()) {
      setMessage('Please enter additional information');
      return;
    }

    setLoading(true);
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString()
    };

    setConversation(prev => [...prev, userMessage]);
    setInput('');
    setMessage('');

    try {
      const response = await api.post(`/agents/${selectedAgent}/continue`, {
        session_context: sessionContext,
        additional_input: input
      });

      // Check if agent is waiting for more input
      if (response.data.wait_required) {
        const waitMessage = {
          id: Date.now() + 1,
          sender: 'agent',
          content: response.data.wait_message || 'Please provide additional information to continue.',
          timestamp: new Date().toLocaleTimeString(),
          isWaiting: true
        };
        setConversation(prev => [...prev, waitMessage]);
        setSessionContext(response.data.session_context);
        setWaitPrompt(response.data.wait_prompt || 'Please provide additional information:');
      } else if (response.data.response) {
        // Final response
        const agentMessage = {
          id: Date.now() + 1,
          sender: 'agent',
          content: response.data.response,
          timestamp: new Date().toLocaleTimeString()
        };
        setConversation(prev => [...prev, agentMessage]);
        setWaitingForInput(false);
        setSessionContext(null);
        setWaitPrompt('');
      } else {
        // Error or no response
        const systemMessage = {
          id: Date.now() + 1,
          sender: 'system',
          content: response.data.message || 'Agent could not continue processing',
          timestamp: new Date().toLocaleTimeString()
        };
        setConversation(prev => [...prev, systemMessage]);
        setWaitingForInput(false);
        setSessionContext(null);
        setWaitPrompt('');
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'system',
        content: 'Error: ' + error.message,
        timestamp: new Date().toLocaleTimeString()
      };
      setConversation(prev => [...prev, errorMessage]);
      setMessage('Error continuing agent: ' + error.message);
      setWaitingForInput(false);
      setSessionContext(null);
      setWaitPrompt('');
    } finally {
      setLoading(false);
    }
  };

  const clearConversation = () => {
    setConversation([]);
    setWaitingForInput(false);
    setSessionContext(null);
    setWaitPrompt('');
  };

  const renderMessage = (message) => {
    const isAgent = message.sender === 'agent';
    const isUser = message.sender === 'user';

    return (
      <Card 
        key={message.id} 
        className={`mb-3 ${isAgent ? 'border-success' : isUser ? 'border-primary' : 'border-warning'}`}
      >
        <Card.Header className={`d-flex justify-content-between align-items-center ${
          isAgent ? (message.isWaiting ? 'bg-info bg-opacity-10' : 'bg-success bg-opacity-10') : 
          isUser ? 'bg-primary bg-opacity-10' : 
          'bg-warning bg-opacity-10'
        }`}>
          <strong>
            {isAgent ? (message.isWaiting ? '⏳ Agent (Waiting)' : '🤖 Agent') : isUser ? '👤 You' : '⚠️ System'}
          </strong>
          <small className="text-muted">{message.timestamp}</small>
        </Card.Header>
        <Card.Body>
          <Card.Text>{message.content}</Card.Text>
        </Card.Body>
      </Card>
    );
  };

  return (
    <Container>
      <h2 className="my-4">Agent Runner</h2>
      
      <Card className="mb-4">
        <Card.Body>
          <Form onSubmit={waitingForInput ? handleContinue : handleRun}>
            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Select Agent</Form.Label>
                  <Form.Select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    required
                  >
                    <option value="">Choose an agent...</option>
                    {agents.map((agent) => (
                      <option key={agent.id} value={agent.id}>
                        {agent.name}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={8}>
                <Form.Group className="mb-3">
                  <Form.Label>{waitingForInput ? waitPrompt : 'Input Message'}</Form.Label>
                  <Form.Control
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={waitingForInput ? 'Enter additional information...' : 'Enter your message here...'}
                    required
                  />
                </Form.Group>
              </Col>
            </Row>
            <Button type="submit" disabled={loading} variant={waitingForInput ? 'success' : 'primary'}>
              {loading ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  {waitingForInput ? 'Continuing...' : 'Running...'}
                </>
              ) : (
                waitingForInput ? 'Continue Agent' : 'Run Agent'
              )}
            </Button>
          </Form>
          
          {message && (
            <Alert variant="info" dismissible onClose={() => setMessage('')}>
              {message}
            </Alert>
          )}
        </Card.Body>
      </Card>

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>Conversation</h4>
        <Button variant="outline-secondary" onClick={clearConversation}>
          Clear Conversation
        </Button>
      </div>

      <div className="conversation-container">
        {conversation.map(renderMessage)}
        <div ref={messagesEndRef} />
      </div>
    </Container>
  );
};

export default AgentRunner;