# Agent Platform - Build Your Customized AI Agents

A powerful platform for creating and managing AI agents with intelligent action execution, context sharing, and seamless API integrations.

## Starting the system

### Prerequisites
- Docker and Docker Compose installed
- 4GB+ available RAM
- Internet connection for LLM API calls
  - All tests cases were implemented with this LLM: "gpt-3.5-turbo" 
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
          │ HTTP Requests   │ Database Queries
          │                 │
          └─────────────────┼─────────────────────────────────────┐
                            │                                     │
                  ┌─────────▼─────────┐                           │
                  │   Action Manager  │                           │
                  │   Agent Manager   │                           │
                  │   LLM Manager     │                           │
                  └─────────┬─────────┘                           │
                            │                                     │
          ┌─────────────────┼─────────────────┐                   │
          │                 │                 │                   │
  ┌───────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐           │
  │ Native Actions │ │ Custom APIs │ │ LLM Providers  │           │
  │ • Thinking     │ │ • REST APIs │ │ • OpenAI       │           │ 
  │ • Respond      │ │ • Headers   │ │ • LM Studio    │           │ 
  │                │ │ • Auth      │ │ • Ollama       │           │
  └────────────────┘ └─────────────┘ └────────────────┘           │
                                                                  │
┌─────────────────────────────────────────────────────────────────┘
│                    External Services                            
├─────────────────┬─────────────────┬─────────────────────────────┐
│   OpenAI API    │   Custom APIs   │    Local LLM Servers        │
│   GPT Models    │   (Rootly, etc) │    (LM Studio, Ollama)      │
│   Internet      │   Internet      │    localhost:1234           │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

## 📋 Features Overview

### 🤖 **Intelligent Agent Management**
- **Smart Workflows**: Chain actions with intelligent context sharing
- **Background Processing**: Thinking actions work invisibly
- **Dynamic Parameters**: Extract parameters from user input automatically
- **Error Recovery**: Automatic endpoint fixing and error handling

### 🔗 **Custom Action Integration**
- **OpenAPI/YAML Support**: Upload API specifications for instant integration
- **Real-time Testing**: Test actions with parameters before deployment
- **Response Filtering**: Show only relevant data based on schema
- **Authentication**: Support for API keys, Bearer tokens, custom headers

### 🧠 **Multi-LLM Support**
- **OpenAI Integration**: GPT-3.5, GPT-4, and newer models
- **Local Models**: LM Studio and Ollama support
- **Custom Endpoints**: Any OpenAI-compatible API
- **Conversation History**: Maintain context across interactions

### 💾 **Data Management**
- **Persistent Storage**: SQLite database with automatic backups
- **Action Library**: Reusable actions across multiple agents
- **Configuration Management**: Export/import agent configurations
- **Security**: API key masking and secure storage

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

## 📁 Included Files

### Example Files
- **`rootly.yaml`**: Example OpenAPI specification for Rootly incident management API
- **`EXAMPLE_USAGE.md`**: Comprehensive usage guide with step-by-step examples
- **`TESTING_IMPROVEMENTS.md`**: Documentation of testing system features
- **`API_DOCUMENTATION_LINKS.md`**: Guide to accessing API documentation
- **`examples/agent_examples.md`**: Pre-configured agent examples and best practices

### Key Directories
- **`backend/app/`**: Core Python modules (managers, models, schemas)
- **`frontend/src/pages/`**: React components for each management interface
- **`frontend/src/services/`**: API client configuration

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

### Restart Services
```bash
# Restart specific service
docker-compose restart backend

# Rebuild and restart
docker-compose up --build backend
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

## 📈 Performance Tips

### Optimize for Production
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=WARNING
  frontend:
    command: npm run build && serve -s build
```

### Resource Limits
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

## 🤝 Contributing

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/YanPedro00/Agent-Platform.git
cd Agent-Platform

# Start development environment
docker-compose up --build

# Access the platform
Then visit http://localhost:3000 to begin!

# Read documentation for detailed usage
See EXAMPLE_USAGE.md for comprehensive examples and use cases
