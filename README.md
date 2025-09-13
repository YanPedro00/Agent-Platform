# Agent Platform - Build Your Customized AI Agents

A powerful, enterprise-grade platform for creating and managing AI agents with intelligent action execution, context sharing, and seamless API integrations. Now with comprehensive testing, improved architecture, and production-ready scalability planning.

## Starting the system

### Prerequisites
- Docker and Docker Compose installed
- 4GB+ available RAM
- Internet connection for LLM API calls
- LLM Studio for local tests
  - All local tests cases were implemented with this LLM: "meta-llama-3.1-8b-instruct" 

### Start the Platform
```bash
# Clone the repository
git clone https://github.com/YanPedro00/Agent-Platform.git
cd Agent-Platform

# Build and start all services
docker-compose up --build
```

### Access the Platform
- **🌐 Web Interface**: http://localhost:3000
- **📚 API Documentation**: http://localhost:8000/docs
- **🔧 API Alternative Docs**: http://localhost:8000/redoc

### Stop the Platform
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (reset database)
docker-compose down -v
```

## 🎯 What You Can Do

### 1. **Create LLM Providers**
Configure your AI models:
- **OpenAI GPT**: Use OpenAI API with your API key
- **LM Studio**: Connect to local LM Studio server
- **Ollama**: Use local Ollama models
- **Custom APIs**: Any OpenAI-compatible endpoint

### 2. **Build Custom Actions**
Create API integrations via YAML/OpenAPI:
- **Upload YAML specs** for instant action creation
- **Test actions** with real parameters
- **Automatic parameter extraction** from user input
- **Response filtering** based on schema

### 3. **Design Intelligent Agents**
Combine actions into workflows:
- **System prompts** define agent personality
- **Action chains** create complex behaviors
- **Context sharing** between all actions
- **Background thinking** for better decisions

### 4. **Execute and Monitor**
Run agents with real-time feedback:
- **Intelligent parameter extraction** from user input
- **Step-by-step execution** with context building
- **Filtered responses** showing only relevant data
- **Error handling** with automatic fixes

## 🏗️ Platform Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Environment                       │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Frontend      │    Backend      │        Database             │
│   (React)       │   (FastAPI)     │       (SQLite)              │
│   Node 18       │   Python 3.11   │    Volume: db_data          │
│   Port: 3000    │   Port: 8000    │    File: app.db             │
└─────────┬───────┴─────────┬───────┴─────────────────────────────┘
          │                 │
          │ HTTP/REST API   │ SQLAlchemy ORM
          │                 │
          └─────────────────┼─────────────────────────────────────┐
                            │                                     │
                  ┌─────────▼─────────┐                           │
                  │   Core Managers   │                           │
                  │ • LLM Manager     │                           │
                  │ • Agent Manager   │                           │
                  │ • Action Manager  │                           │
                  │ • Utils Module    │                           │
                  └─────────┬─────────┘                           │
                            │                                     │
          ┌─────────────────┼─────────────────┐                   │
          │                 │                 │                   │
  ┌───────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐           │
  │ Native Actions │ │ Custom APIs │ │ LLM Providers  │           │
  │ • Thinking     │ │ • REST APIs │ │ • OpenAI       │           │ 
  │ • Respond      │ │ • YAML/OAS  │ │ • LM Studio    │           │ 
  │ • Wait         │ │ • Headers   │ │ • Ollama       │           │
  │ • Choice       │ │ • Auth      │ │ • Custom APIs  │           │
  └────────────────┘ └─────────────┘ └────────────────┘           │
                                                                  │
┌─────────────────────────────────────────────────────────────────┘
│                    External Services                            
├─────────────────┬─────────────────┬─────────────────────────────┐
│   OpenAI API    │   Custom APIs   │    Local LLM Servers        │
│   GPT-3.5/4     │   (Rootly, etc) │    (LM Studio, Ollama)      │
│   Internet      │   Internet      │    localhost:1234           │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Core Components

#### **Frontend Layer (React)**
- **UI Framework**: React 18.2.0 with Bootstrap 5.2.3
- **State Management**: React Hooks and Context API
- **HTTP Client**: Axios for API communication
- **Routing**: React Router DOM for SPA navigation
- **Testing**: Jest + React Testing Library

#### **Backend Layer (FastAPI)**
- **API Framework**: FastAPI with automatic OpenAPI documentation
- **Database ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Authentication**: JWT-ready architecture
- **Validation**: Pydantic models for request/response validation
- **Testing**: Pytest with 80%+ coverage

#### **Data Layer**
- **Development**: SQLite with file-based storage
- **Production Ready**: PostgreSQL migration path documented
- **Caching**: Redis integration planned for sessions
- **Persistence**: Docker volumes for data retention

### Manager Architecture

#### **LLM Manager**
```python
# Multi-provider LLM integration
- OpenAI (GPT-3.5, GPT-4)
- LM Studio (Local models)
- Ollama (Open-source models)
- Custom API endpoints
- Conversation history management
- Temperature and token control
```

#### **Agent Manager**
```python
# Intelligent agent orchestration
- Action flow execution
- Context sharing between actions
- Parameter extraction via LLM
- Conditional flow support
- Wait action handling
- Error recovery mechanisms
```

#### **Action Manager**
```python
# Action execution engine
- Native actions (Thinking, Respond, Wait, Choice)
- Custom API integration via YAML/OpenAPI
- Parameter validation and extraction
- Response filtering and transformation
- Authentication handling (API keys, Bearer tokens)
```

### Data Flow Architecture

```
User Input → Frontend → Backend API → Agent Manager
                                          ↓
                                    Action Execution
                                          ↓
                              ┌─────────────────────┐
                              │   Context Builder   │
                              │ • User input        │
                              │ • Action results    │
                              │ • Thinking process  │
                              │ • Extracted entities│
                              │ • Session data      │
                              └─────────────────────┘
                                          ↓
                                  LLM Processing
                                          ↓
                              ┌─────────────────────┐
                              │   Response Chain    │
                              │ • Background actions│
                              │ • User-facing actions│
                              │ • Conditional flows │
                              │ • Wait handling     │
                              └─────────────────────┘
                                          ↓
                                   Final Response
```

### Scalability Architecture (Production)

For detailed scaling to 10K+ users, see `docs/architecture-analysis.md`:

```
Load Balancer (Nginx)
        ↓
┌─────────────────────┐
│ Backend Instances   │
│ • Instance 1:8000   │
│ • Instance 2:8000   │
│ • Instance 3:8000   │
└─────────────────────┘
        ↓
┌─────────────────────┐
│ Cache Layer (Redis) │
│ • Sessions          │
│ • Context data      │
│ • LLM responses     │
└─────────────────────┘
        ↓
┌─────────────────────┐
│ Database Cluster    │
│ • PostgreSQL Primary│
│ • Read Replicas     │
│ • Backup Strategy   │
└─────────────────────┘
```

## 📋 Features Overview

### **Intelligent Agent Management**
- **Smart Workflows**: Chain actions with intelligent context sharing
- **Background Processing**: Thinking actions work invisibly
- **Dynamic Parameters**: Extract parameters from user input automatically
- **Error Recovery**: Automatic endpoint fixing and error handling
- **Conditional Flows**: Advanced decision-making with Choice actions
- **Wait Actions**: Pause execution for additional user input

### **Custom Action Integration**
- **OpenAPI/YAML Support**: Upload API specifications for instant integration
- **Real-time Testing**: Test actions with parameters before deployment
- **Response Filtering**: Show only relevant data based on schema
- **Authentication**: Support for API keys, Bearer tokens, custom headers
- **Automatic Parameter Extraction**: Intelligent parsing from user input

### **Multi-LLM Support**
- **OpenAI Integration**: GPT-3.5, GPT-4, and newer models
- **Local Models**: LM Studio and Ollama support
- **Custom Endpoints**: Any OpenAI-compatible API
- **Conversation History**: Maintain context across interactions
- **Provider Flexibility**: Switch between providers seamlessly

### **Data Management & Quality**
- **Persistent Storage**: SQLite database with automatic backups
- **Action Library**: Reusable actions across multiple agents
- **Configuration Management**: Export/import agent configurations
- **Security**: API key masking and secure storage
- **Comprehensive Testing**: 80%+ test coverage with TDD approach
- **Code Quality**: Refactored codebase with utility functions

## 🛠️ Container Details

### Backend Container
- **Image**: Python 3.11-slim with FastAPI
- **Port**: 8000 (mapped to localhost:8000)
- **Features**: REST API, action execution, database management
- **Volume**: `./backend:/app` for live code updates

### Frontend Container
- **Image**: Node.js 18-alpine with React
- **Port**: 3000 (mapped to localhost:3000)
- **Features**: Web interface, agent management, action testing
- **Volume**: `./frontend:/app` for live code updates
- **Hot Reload**: Development mode with live updates

### Database
- **Type**: SQLite file-based database
- **Location**: `./backend/data/app.db` (Docker volume: `db_data`)
- **Persistence**: Data survives container restarts via named volume
- **Schema**: Automatic table creation and migration on startup

## 📁 Project Structure

### Documentation & Examples
- **`docs/guides/`**: Comprehensive documentation and usage guides
- **`docs/examples/`**: Example configurations and test files
- **`docs/architecture-analysis.md`**: Detailed architecture analysis and scalability planning
- **`IMPROVEMENTS_SUMMARY.md`**: Summary of recent improvements and enhancements

### Core Directories
- **`backend/app/`**: Core Python modules (managers, models, schemas, utils)
- **`frontend/src/pages/`**: React components for each management interface
- **`frontend/src/services/`**: API client configuration
- **`tests/backend/`**: Comprehensive backend test suite (80%+ coverage)
- **`tests/frontend/`**: Frontend test suite with React Testing Library
- **`config/`**: Configuration files and Docker setup

## 📖 Usage Examples

### Example 1: Create a Research Agent

1. **Setup LLM Provider**:
   ```json
   {
     "name": "OpenAI GPT-4",
     "provider": "openai",
     "model_name": "gpt-4",
     "api_key": "your-api-key-here"
   }
   ```

2. **Create Custom Action** (Optional):
   Upload YAML for external APIs like Wikipedia, weather services, etc.
   - Use the included `rootly.yaml` as an example
   - See `EXAMPLE_USAGE.md` for detailed walkthrough

3. **Build Agent**:
   ```json
   {
     "name": "Research Assistant",
     "system_prompt": "You are a helpful research assistant that thinks through problems step by step.",
     "actions": [
       {"action_name": "Thinking", "order": 1},
       {"action_name": "Custom API", "order": 2},
       {"action_name": "Respond", "order": 3}
     ]
   }
   ```

4. **Execute Agent**:
   ```json
   {
     "input": "Research the latest developments in AI safety"
   }
   ```

### Example 2: API Integration Workflow

1. **Upload YAML Specification**:
   - Go to Actions → YAML Upload
   - Upload your OpenAPI/YAML file (try `rootly.yaml` included in the repo)
   - Add API key if required

2. **Test the Action**:
   - Click "Test" button
   - Provide test parameters
   - Verify response format

3. **Create Agent Using Action**:
   - Add action to agent workflow
   - Configure prompts for each step
   - Test end-to-end execution

## 🧪 Testing & Quality Assurance

### Running Tests
```bash
# Backend tests (80%+ coverage)
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Coverage reports
pytest --cov=app --cov-report=html
```

### Test Structure
- **Unit Tests**: Individual function testing
- **Integration Tests**: Component interaction testing
- **API Tests**: Full endpoint testing
- **Mock Tests**: External dependency simulation

## 🔧 Development & Debugging

### View Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

### Database Access
```bash
# Access SQLite database
docker-compose exec backend sqlite3 /app/data/app.db

# View tables
.tables

# Query data
SELECT * FROM agents;
```

### Development Setup
```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development
cd frontend
npm install
npm start

# Run tests during development
pytest --watch
npm test -- --watch
```

### Reset Everything
```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Fresh start
docker-compose up --build
```

## 🚨 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the ports
lsof -i :3000
lsof -i :8000

# Kill processes if needed
kill -9 <PID>
```

#### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up --build
```

#### API Connection Problems
- Check your API keys in LLM configuration
- Verify internet connection for external APIs
- Check firewall settings

#### Frontend Not Loading
- Clear browser cache
- Check if backend is running: http://localhost:8000/docs
- Verify CORS settings in backend

### Getting Help

1. **Check Logs**: `docker-compose logs -f`
2. **API Documentation**: http://localhost:8000/docs
3. **Test Endpoints**: Use the interactive API docs
4. **Database State**: Check data via SQLite commands

## 🔐 Security Considerations

### API Keys
- **Never commit API keys** to version control
- **Use environment variables** for production
- **API keys are masked** in logs and UI
- **Secure storage** in database

### Network Security
- **CORS configured** for frontend-backend communication
- **No external ports** exposed except 3000 and 8000
- **Container isolation** between services

### Data Privacy
- **Local database** - no external data transmission
- **API calls** only to configured endpoints
- **No telemetry** or usage tracking

## 📈 Performance & Scalability

### Current Capacity
- **Users**: ~100 simultaneous users
- **Database**: SQLite (development)
- **Architecture**: Monolithic containerized

### Production Scaling (10K+ Users)
For detailed scaling plans, see `docs/architecture-analysis.md`:
- **Database**: PostgreSQL with replicas
- **Cache**: Redis for sessions and context
- **Load Balancer**: Nginx with multiple backend instances
- **Monitoring**: Prometheus + Grafana

### Optimize for Production
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=WARNING
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
  frontend:
    command: npm run build && serve -s build
```

## 🤝 Contributing

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/YanPedro00/Agent-Platform.git
cd Agent-Platform

# Start development environment
docker-compose up --build

# Run tests to ensure everything works
cd backend && pytest
cd ../frontend && npm test

# Access the platform
Then visit http://localhost:3000 to begin!

# Read documentation for detailed usage
See EXAMPLE_USAGE.md for comprehensive examples and use cases