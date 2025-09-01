# Agent Examples

This file contains examples of how to create and configure agents using the Agent Platform.

## Example 1: Research Agent

A research agent that can think through problems and provide comprehensive answers.

### Agent Configuration
```json
{
  "name": "Research Agent",
  "description": "An intelligent agent that researches topics and provides detailed answers",
  "system_prompt": "You are a research assistant. When given a question, think through it step by step, research relevant information, and provide a comprehensive answer with sources when possible.",
  "llm_id": 1,
  "actions": [
    {
      "action_name": "Thinking",
      "prompt": "Analyze this research question step by step: {input}"
    },
    {
      "action_name": "Respond",
      "prompt": "Based on your research and analysis, provide a comprehensive answer to: {input}"
    }
  ],
  "config": {
    "max_research_iterations": 3,
    "require_sources": true
  }
}
```

### Expected Workflow
1. User asks: "What are the main causes of climate change?"
2. **Thinking Action** (Background): Analyzes the question, identifies key areas to research
3. **Research Actions**: Gathers information from various sources
4. **Respond Action**: Synthesizes information into a comprehensive answer

## Example 2: Customer Support Agent

An agent that can understand customer issues and provide helpful solutions.

### Agent Configuration
```json
{
  "name": "Customer Support Agent",
  "description": "Helps customers with technical issues and product questions",
  "system_prompt": "You are a helpful customer support agent. Listen to customer issues, think through solutions, and provide clear, actionable help. Always be polite and professional.",
  "llm_id": 1,
  "actions": [
    {
      "action_name": "Thinking",
      "prompt": "Analyze this customer issue and think through possible solutions: {input}"
    },
    {
      "action_name": "Respond",
      "prompt": "Provide a helpful solution to the customer's issue: {input}"
    }
  ],
  "config": {
    "escalation_threshold": 3,
    "tone": "friendly_professional"
  }
}
```

### Expected Workflow
1. Customer reports: "My app keeps crashing when I try to upload photos"
2. **Thinking Action** (Background): Analyzes the issue, identifies common causes
3. **Troubleshooting Actions**: Runs diagnostic checks, tests solutions
4. **Respond Action**: Provides step-by-step solution with troubleshooting tips

## Example 3: Data Analysis Agent

An agent that can analyze data and provide insights.

### Agent Configuration
```json
{
  "name": "Data Analysis Agent",
  "description": "Analyzes data sets and provides insights and recommendations",
  "system_prompt": "You are a data analyst. When given data or analysis requests, think through the problem, analyze the data systematically, and provide clear insights with actionable recommendations.",
  "llm_id": 1,
  "actions": [
    {
      "action_name": "Thinking",
      "prompt": "Analyze this data analysis request step by step: {input}"
    },
    {
      "action_name": "Respond",
      "prompt": "Based on your analysis, provide insights and recommendations for: {input}"
    }
  ],
  "config": {
    "analysis_depth": "comprehensive",
    "include_visualizations": true
  }
}
```

### Expected Workflow
1. User asks: "Analyze this sales data and identify trends"
2. **Thinking Action** (Background): Plans analysis approach, identifies key metrics
3. **Analysis Actions**: Processes data, calculates statistics, identifies patterns
4. **Respond Action**: Provides trend analysis with charts and recommendations

## Example 4: Creative Writing Agent

An agent that can help with creative writing tasks.

### Agent Configuration
```json
{
  "name": "Creative Writing Agent",
  "description": "Assists with creative writing, brainstorming, and content creation",
  "system_prompt": "You are a creative writing assistant. Help users brainstorm ideas, develop stories, and create engaging content. Think creatively and provide constructive feedback.",
  "llm_id": 1,
  "actions": [
    {
      "action_name": "Thinking",
      "prompt": "Think creatively about this writing request and brainstorm ideas: {input}"
    },
    {
      "action_name": "Respond",
      "prompt": "Based on your creative thinking, provide writing assistance for: {input}"
    }
  ],
  "config": {
    "creativity_level": "high",
    "genre_specialties": ["fiction", "non-fiction", "poetry"]
  }
}
```

### Expected Workflow
1. User asks: "Help me write a short story about time travel"
2. **Thinking Action** (Background): Brainstorms plot ideas, character concepts, themes
3. **Creative Actions**: Develops story outline, character profiles, plot points
4. **Respond Action**: Provides story outline with writing tips and suggestions

## Key Benefits of the New System

### 1. **Background Thinking**
- The "Thinking" action processes information invisibly
- Users see only the final, polished results
- Agents can work through complex problems step-by-step

### 2. **Context Sharing**
- All actions share information and context
- Previous action results inform future decisions
- Agents maintain memory across the entire conversation

### 3. **Intelligent Response Generation**
- The "Respond" action creates user-friendly messages
- Responses are based on all available context
- Information is presented clearly and actionably

### 4. **Seamless Integration**
- Native and custom actions work together
- Context flows naturally between all components
- Agents can handle complex, multi-step tasks

## Best Practices

1. **Always include both Thinking and Respond actions** in your agent configuration
2. **Use descriptive system prompts** that guide the agent's behavior
3. **Configure actions with specific prompts** that match your use case
4. **Test your agents** with various inputs to ensure they work as expected
5. **Monitor the shared context** to understand how information flows between actions

## Troubleshooting

### Agent not using Thinking action
- Ensure the "Thinking" action is included in the agent's actions list
- Check that the system prompt encourages step-by-step thinking
- Verify the action name matches exactly: "Thinking"

### Agent not generating proper responses
- Ensure the "Respond" action is included in the agent's actions list
- Check that the system prompt guides the agent to provide user-facing responses
- Verify the action name matches exactly: "Respond"

### Context not being shared
- Check that all actions are properly configured
- Ensure the agent has access to the actions it needs
- Verify that the LLM is working correctly
