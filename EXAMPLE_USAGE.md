# Agent Platform - Complete Usage Guide

## 🚀 Getting Started: Setting Up Your First LLM

Before creating agents and actions, you need to configure at least one LLM provider. Here are two common approaches:

### Option 1: Local LLM with LM Studio (Recommended for Testing)

#### Step 1: Install and Setup LM Studio
1. **Download LM Studio**: Visit [lmstudio.ai](https://lmstudio.ai) and download for your OS
2. **Install a Model**: 
   - Open LM Studio
   - Go to "Discover" tab
   - Search and download: `meta-llama-3.1-8b-instruct` (recommended for testing)
   - Wait for download to complete

#### Step 2: Start Local Server
1. **Load the Model**:
   - Go to "Chat" tab in LM Studio
   - Select `meta-llama-3.1-8b-instruct` from dropdown
   - Click "Start Server"
   - Note the server URL (usually `http://localhost:1234`)

#### Step 3: Configure in Agent Platform
1. **Access LLM Manager**:
   - Open Agent Platform: http://localhost:3000
   - Navigate to "LLM Manager"
   - Click "Create New LLM"

2. **Fill LLM Configuration**:
   ```json
   {
     "name": "Local Llama 3.1 8B",
     "provider": "lmstudio",
     "model_name": "meta-llama-3.1-8b-instruct",
     "base_url": "http://localhost:1234/v1",
     "api_key": "lm-studio",
     "max_tokens": 2000,
     "temperature": 0.7
   }
   ```

3. **Save and Test**:
   - Click "Create LLM"
   - The LLM is now ready for use in agents

### Option 2: Cloud-Based LLM with OpenAI

#### Step 1: Get OpenAI API Key
1. **Create OpenAI Account**: Visit [platform.openai.com](https://platform.openai.com)
2. **Generate API Key**:
   - Go to API Keys section
   - Click "Create new secret key"
   - Copy the key (starts with `sk-...`)
   - **Important**: Keep this key secure!

#### Step 2: Configure in Agent Platform
1. **Access LLM Manager**:
   - Open Agent Platform: http://localhost:3000
   - Navigate to "LLM Manager"
   - Click "Create New LLM"

2. **Fill LLM Configuration**:
   ```json
   {
     "name": "OpenAI GPT-4",
     "provider": "openai",
     "model_name": "gpt-4",
     "api_key": "sk-your-actual-api-key-here",
     "max_tokens": 2000,
     "temperature": 0.7
   }
   ```

3. **Alternative Models**:
   - For **GPT-3.5**: Use `"model_name": "gpt-3.5-turbo"`
   - For **GPT-4 Turbo**: Use `"model_name": "gpt-4-turbo"`

4. **Save and Test**:
   - Click "Create LLM"
   - The LLM is now ready for use in agents

### Option 3: Other LLM Providers

#### Ollama (Local Alternative)
```json
{
  "name": "Ollama Llama 3.1",
  "provider": "ollama",
  "model_name": "llama3.1:8b",
  "base_url": "http://localhost:11434/v1",
  "api_key": "ollama",
  "max_tokens": 2000,
  "temperature": 0.7
}
```

#### Custom OpenAI-Compatible API
```json
{
  "name": "Custom API",
  "provider": "custom",
  "model_name": "your-model-name",
  "base_url": "https://your-api-endpoint.com/v1",
  "api_key": "your-api-key",
  "max_tokens": 2000,
  "temperature": 0.7
}
```

### 🎯 Quick Verification

After setting up your LLM, verify it's working:

1. **Create a Simple Agent**:
   - Go to "Agent Manager"
   - Click "Create New Agent"
   - Fill basic info:
     ```json
     {
       "name": "Test Agent",
       "description": "Simple test agent",
       "system_prompt": "You are a helpful assistant.",
       "llm_id": 1
     }
     ```
   - Add a Respond action.

2. **Test the Agent**:
   - Go to "Agent Runner"
   - Select your "Test Agent"
   - Send a simple message: "Hello, can you help me?"
   - You should receive a response from your configured LLM

### 🔧 LLM Troubleshooting

#### Common Issues:

**LM Studio Connection Issues:**
- Ensure LM Studio server is running (green "Server Running" indicator)
- Check the server URL matches your configuration
- Verify the model is loaded in LM Studio

**OpenAI API Issues:**
- Verify your API key is correct and active
- Check your OpenAI account has sufficient credits
- Ensure the model name is spelled correctly

**General LLM Issues:**
- Check the Agent Platform backend logs: `docker-compose logs backend`
- Verify the LLM configuration in the database
- Test with a simple prompt first

---

## 📋 Practical Example: Testing Custom Actions

### Scenario: Rootly API for Incident Lookup

Now that you have an LLM configured, let's use the example from the `rootly.yaml` file to demonstrate how to test a custom action.

### 1. Creating the Custom Action

**Action Data:**
- **Name**: Rootly Incident Lookup
- **Description**: Get title and description of an incident ticket by ID
- **Endpoint**: https://api.rootly.com/v1/incidents/{id}
- **Method**: GET
- **Parameters**: `{"id": {"type": "string", "required": true, "description": "Incident ID"}}`
- **Headers**: `{"Authorization": "Bearer YOUR_API_KEY"}`

### 2. Testing the Action

#### Option 1: YAML Upload
1. Go to the "YAML Upload" tab in Action Manager
2. Upload the `rootly.yaml` file
3. Fields will be filled automatically
4. Click "Create Action from YAML"

#### Option 2: Manual Form Fill
1. Fill the form fields:
   ```
   Name: Rootly Incident Lookup
   Endpoint: https://api.rootly.com/v1/incidents/{id}
   Method: GET
   Parameters: {"id": {"type": "string", "required": true}}
   Headers: {"Authorization": "Bearer YOUR_API_KEY"}
   ```

### 3. Testing with Parameters

After creating the action, click the **"Test"** button and use these parameters:

```json
{
  "id": "1124-user-authentication-service-failure"
}
```

### 4. Expected Results

#### Success Response:
```json
{
  "success": true,
  "action_name": "Rootly Incident Lookup",
  "action_type": "custom",
  "parameters_used": {
    "id": "1124-user-authentication-service-failure"
  },
  "result": {
    "type": "custom_action",
    "success": true,
    "status_code": 200,
    "endpoint_called": "https://api.rootly.com/v1/incidents/1124-user-authentication-service-failure",
    "method_used": "GET",
    "filtered_data": {
      "data": {
        "attributes": {
          "title": "User Authentication Service Failure",
          "summary": "Multiple users reporting login failures across the authentication service"
        }
      }
    },
    "schema_used": {
      "type": "object",
      "properties": {
        "data": {
          "type": "object",
          "properties": {
            "attributes": {
              "type": "object",
              "properties": {
                "title": {"type": "string"},
                "summary": {"type": "string"}
              }
            }
          }
        }
      }
    }
  }
}
```

#### Error Response (Invalid API Key):
```json
{
  "success": true,
  "action_name": "Rootly Incident Lookup",
  "result": {
    "type": "custom_action",
    "success": false,
    "error": "HTTP 401: {'errors': [{'title': 'Invalid token', 'status': '401'}]}",
    "status_code": 401,
    "endpoint_called": "https://api.rootly.com/v1/incidents/1124-user-authentication-service-failure"
  }
}
```

## 5. Creating an Intelligent Agent

### Agent Configuration:
```json
{
  "name": "Incident Assistant",
  "description": "Helps users get information about incidents",
  "system_prompt": "You are a helpful assistant that can retrieve incident information from Rootly API.",
  "llm_id": 1,
  "actions": [
    {
      "action_name": "Thinking",
      "prompt": "Analyze the user's request and extract the incident ID they want to know about",
      "order": 1
    },
    {
      "action_name": "Rootly Incident Lookup",
      "prompt": "Use the incident ID to get details from Rootly API",
      "order": 2
    },
    {
      "action_name": "Respond",
      "prompt": "Present the incident information to the user in a clear and organized way",
      "order": 3
    }
  ]
}
```

**Note**: Make sure to use the correct `llm_id` that corresponds to your configured LLM (Local Llama or OpenAI).

### Testing the Agent:
```json
{
  "input": "Can you tell me about incident 1124-user-authentication-service-failure?"
}
```

### Expected Agent Response:
```
**Incident 1124-user-authentication-service-failure**

**Title:** User Authentication Service Failure
**Summary:** Multiple users reporting login failures across the authentication service
**Status:** Under investigation
```

## 6. Advanced Features

### Response Filtering
The system automatically filters API responses based on the YAML schema:
- Only returns `data.attributes.title` and `data.attributes.summary`
- Removes unnecessary metadata and other fields
- Provides clean, focused data for the agent

### Error Handling
- **Connection errors**: Graceful handling of network issues
- **Authentication errors**: Clear messages for invalid API keys
- **Endpoint errors**: Automatic endpoint fixing suggestions
- **Parameter validation**: Ensures required parameters are provided

### Security Features
- **API key masking**: Keys are hidden in logs and responses
- **YAML sanitization**: API keys are removed from stored YAML specs
- **Secure headers**: Sensitive headers are masked in results

## 7. Troubleshooting

### Common Issues:

#### 1. "Invalid URL" Error
**Problem**: Missing `http://` or `https://` in endpoint
**Solution**: Use the "Try to Fix Endpoint Automatically" button

#### 2. "HTTP 401: Invalid token"
**Problem**: Missing or incorrect API key
**Solution**: Add your Rootly API key in the API Key field

#### 3. "No connection adapters"
**Problem**: Malformed URL (e.g., full URL passed as ID parameter)
**Solution**: Check parameter values - use only the ID, not the full URL

#### 4. Empty Response
**Problem**: API returns data but it's filtered out
**Solution**: Check the response schema in your YAML file

### Getting Help:
1. Check the test results for detailed error messages
2. Use the API documentation at `http://localhost:8000/docs`
3. Review the YAML file structure
4. Verify your API key is valid

## 8. Next Steps

After successfully testing your custom action:

1. **Create more actions** for different APIs
2. **Build complex agents** with multiple action flows
3. **Test different scenarios** with various parameters
4. **Monitor performance** and optimize as needed

The platform provides a robust foundation for building sophisticated AI agents that can interact with external APIs and provide intelligent responses to users.
