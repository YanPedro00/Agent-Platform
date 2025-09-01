import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar, Nav, Container } from 'react-bootstrap';
import Home from './pages/Home';
import LLMManager from './pages/LLMManager';
import AgentManager from './pages/AgentManager';
import ActionManager from './pages/ActionManager';
import AgentRunner from './pages/AgentRunner';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar bg="dark" variant="dark" expand="lg">
          <Container>
            <Navbar.Brand href="/">Agent Platform</Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
              <Nav className="me-auto">
                <Nav.Link href="/">Home</Nav.Link>
                <Nav.Link href="/llms">LLMs</Nav.Link>
                <Nav.Link href="/agents">Agents</Nav.Link>
                <Nav.Link href="/actions">Actions</Nav.Link>
                <Nav.Link href="/run">Run Agent</Nav.Link>
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/llms" element={<LLMManager />} />
          <Route path="/agents" element={<AgentManager />} />
          <Route path="/actions" element={<ActionManager />} />
          <Route path="/run" element={<AgentRunner />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;