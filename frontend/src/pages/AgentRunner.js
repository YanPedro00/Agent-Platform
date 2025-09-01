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

      // Only add agent message if there's actually a response
      if (response.data.response) {
        const agentMessage = {
          id: Date.now() + 1,
          sender: 'agent',
          content: response.data.response,
          timestamp: new Date().toLocaleTimeString()
        };
        setConversation(prev => [...prev, agentMessage]);
      } else {
        // Agent has no Respond action or didn't generate a response
        const systemMessage = {
          id: Date.now() + 1,
          sender: 'system',
          content: response.data.message || 'Agent processed your request but has no Respond action configured',
          timestamp: new Date().toLocaleTimeString()
        };
        setConversation(prev => [...prev, systemMessage]);
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

  const clearConversation = () => {
    setConversation([]);
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
          isAgent ? 'bg-success bg-opacity-10' : 
          isUser ? 'bg-primary bg-opacity-10' : 
          'bg-warning bg-opacity-10'
        }`}>
          <strong>
            {isAgent ? '🤖 Agent' : isUser ? '👤 You' : '⚠️ System'}
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
          <Form onSubmit={handleRun}>
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
                  <Form.Label>Input Message</Form.Label>
                  <Form.Control
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Enter your message here..."
                    required
                  />
                </Form.Group>
              </Col>
            </Row>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Running...
                </>
              ) : (
                'Run Agent'
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