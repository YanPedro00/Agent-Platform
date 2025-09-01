# 📚 API Documentation Links

### **Interactive Documentation (Swagger UI)**
```
✅ http://localhost:8000/docs
```
**Or via container IP:**
```
✅ http://172.19.0.2:8000/docs
```

### **Redoc Documentation (Alternative)**
```
✅ http://localhost:8000/redoc
```

### **OpenAPI JSON Schema**
```
✅ http://localhost:8000/openapi.json
```

### **Frontend Application**
```
✅ http://localhost:3000
```
**Or via container IP:**
```
✅ http://172.19.0.3:3000
```

##**Container Information**

### **Backend (FastAPI)**
- **Container**: `agent-platform-backend-1`
- **IP**: `172.19.0.2`
- **Port**: `8000`
- **Services**: REST API, Documentation, OpenAPI

### **Frontend (React)**
- **Container**: `agent-platform-frontend-1`
- **IP**: `172.19.0.3`
- **Port**: `3000`
- **Services**: Web Interface, Agent Management

## **How to Access**

### **1. Via Localhost (Recommended)**
```bash
# API Documentation
open http://localhost:8000/docs

# Frontend Application
open http://localhost:3000
```

### **2. Via Container IPs**
```bash
# API Documentation
open http://172.19.0.2:8000/docs

# Frontend Application
open http://172.19.0.3:3000
```

### **3. Check Container Status**
```bash
docker-compose ps
```

## **Main API Endpoints**

### **Agents**
- `GET /agents/` - List agents
- `POST /agents/` - Create agent
- `PUT /agents/{id}` - Update agent
- `DELETE /agents/{id}` - Delete agent
- `POST /agents/{id}/run` - Execute agent

### Actions**
- `GET /actions/` - List actions
- `POST /actions/` - Create action
- `PUT /actions/{id}` - Update action
- `DELETE /actions/{id}` - Delete action
- `POST /actions/{id}/test` - Test action

### **LLMs**
- `GET /llms/` - List LLMs
- `POST /llms/` - Create LLM
- `PUT /llms/{id}` - Update LLM
- `DELETE /llms/{id}` - Delete LLM

### **Utilities**
- `POST /actions/parse-yaml/` - Parse YAML
- `POST /actions/{id}/fix-endpoint` - Fix endpoint

## **Enhanced Documentation**

The API documentation now includes:

### **Complete Description**
```
Agent Platform API

This API allows you to manage intelligent agents, custom actions, and LLMs.

Main features:
- LLM Management: Configure different language models
- Custom Actions: Create custom actions via YAML/OpenAPI
- Intelligent Agents: Create agents with configurable action flows
- Agent Execution: Execute agents with intelligent context
- Action Testing: Test custom actions with parameters
```

### **Useful Links**
- **Frontend**: http://localhost:3000
- **Interactive Documentation**: http://localhost:8000/docs
- **Redoc Documentation**: http://localhost:8000/redoc

### **Configured Servers**
- **Local Development**: http://localhost:8000
- **Docker Container**: http://172.19.0.2:8000

## **Testing the API**

### **1. Check if it's working:**
```bash
curl http://localhost:8000/docs
```

### **2. Test basic endpoint:**
```bash
curl http://localhost:8000/
```
**Expected response:**
```json
{"message": "Agent Platform API"}
```

### **3. List agents:**
```bash
curl http://localhost:8000/agents/
```

### **4. Get OpenAPI schema:**
```bash
curl http://localhost:8000/openapi.json | jq '.info'
```

## **Troubleshooting**

### **If documentation doesn't load:**

#### **1. Check containers:**
```bash
docker-compose ps
```

#### **2. Check backend logs:**
```bash
docker-compose logs backend
```

#### **3. Restart services:**
```bash
docker-compose restart
```

#### **1. Rebuild containers:**
```bash
docker-compose down
docker-compose up --build
```

The backend is configured to accept:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://172.19.0.3:3000`
