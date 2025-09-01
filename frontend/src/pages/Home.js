import React from 'react';
import { Card, Row, Col, Container } from 'react-bootstrap';

const Home = () => {
  return (
    <Container>
      <h1 className="my-4">Welcome to Agent Platform</h1>
      <p className="lead">Manage your LLMs, create agents, define actions, and run intelligent workflows.</p>

      <Row className="my-5">
        <Col md={3}>
          <Card className="h-100">
            <Card.Body>
              <Card.Title>LLMs</Card.Title>
              <Card.Text>
                Add and manage different Large Language Models with your API keys and configurations.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="h-100">
            <Card.Body>
              <Card.Title>Agents</Card.Title>
              <Card.Text>
                Create intelligent agents with custom system prompts and chain-of-thought reasoning.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="h-100">
            <Card.Body>
              <Card.Title>Actions</Card.Title>
              <Card.Text>
                Define API actions that your agents can use to retrieve or send information.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="h-100">
            <Card.Body>
              <Card.Title>Run</Card.Title>
              <Card.Text>
                Execute your agents and see them reason step-by-step using available actions.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Home;