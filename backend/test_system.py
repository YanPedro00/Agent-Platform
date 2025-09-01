#!/usr/bin/env python3
"""
Test script to verify the Agent Platform system is working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import LLM, Action, Agent
from app.llm_manager import LLMManager
from app.action_manager import ActionManager
from app.agent_manager import AgentManager
from app.schemas import LLMCreate, ActionCreate, AgentCreate, AgentActionConfig

def test_database_connection():
    """Test database connection and table creation"""
    print("Testing database connection...")
    try:
        db = SessionLocal()
        # Test if we can query the database
        llms = db.query(LLM).all()
        actions = db.query(Action).all()
        agents = db.query(Agent).all()
        print(f"✅ Database connection successful")
        print(f"   - LLMs: {len(llms)}")
        print(f"   - Actions: {len(actions)}")
        print(f"   - Agents: {len(agents)}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_native_actions():
    """Test if native actions are properly created"""
    print("\nTesting native actions...")
    try:
        db = SessionLocal()
        
        # Check if Thinking action exists
        thinking_action = db.query(Action).filter(Action.name == "Thinking").first()
        if thinking_action:
            print(f"✅ Thinking action found: {thinking_action.description}")
        else:
            print("❌ Thinking action not found")
            
        # Check if Respond action exists
        respond_action = db.query(Action).filter(Action.name == "Respond").first()
        if respond_action:
            print(f"✅ Respond action found: {respond_action.description}")
        else:
            print("❌ Respond action not found")
            
        db.close()
        return thinking_action and respond_action
    except Exception as e:
        print(f"❌ Error testing native actions: {e}")
        return False

def test_duplicate_name_validation():
    """Test duplicate name validation"""
    print("\nTesting duplicate name validation...")
    try:
        db = SessionLocal()
        
        # Test LLM duplicate name validation
        try:
            llm1 = LLMCreate(
                name="Test LLM",
                provider="openai",
                model_name="gpt-3.5-turbo",
                api_key="test-key"
            )
            LLMManager.create_llm(db, llm1)
            print("✅ First LLM created successfully")
            
            # Try to create another LLM with the same name
            llm2 = LLMCreate(
                name="Test LLM",  # Same name
                provider="openai",
                model_name="gpt-4",
                api_key="test-key-2"
            )
            LLMManager.create_llm(db, llm2)
            print("❌ Duplicate name validation failed for LLM")
            return False
        except ValueError as e:
            if "already exists" in str(e):
                print("✅ LLM duplicate name validation working")
            else:
                print(f"❌ Unexpected error in LLM validation: {e}")
                return False
                
        db.close()
        return True
    except Exception as e:
        print(f"❌ Error testing duplicate name validation: {e}")
        return False

def test_action_execution():
    """Test action execution with context"""
    print("\nTesting action execution...")
    try:
        db = SessionLocal()
        
        # Test Thinking action execution
        thinking_action = db.query(Action).filter(Action.name == "Thinking").first()
        if thinking_action:
            result = ActionManager.execute_action(
                db, 
                "Thinking", 
                {"input": "Test input"}, 
                {"test_context": "test_value"}
            )
            if result and result.get("type") == "thinking" and result.get("background"):
                print("✅ Thinking action execution successful")
                print(f"   - Type: {result.get('type')}")
                print(f"   - Background: {result.get('background')}")
                print(f"   - Content: {result.get('content')[:100]}...")
            else:
                print("❌ Thinking action execution failed")
                return False
        else:
            print("❌ Thinking action not found for testing")
            return False
            
        # Test Respond action execution
        respond_action = db.query(Action).filter(Action.name == "Respond").first()
        if respond_action:
            result = ActionManager.execute_action(
                db, 
                "Respond", 
                {"input": "Test input"}, 
                {"test_context": "test_value"}
            )
            if result and result.get("type") == "response" and not result.get("background"):
                print("✅ Respond action execution successful")
                print(f"   - Type: {result.get('type')}")
                print(f"   - Background: {result.get('background')}")
                print(f"   - User message: {result.get('user_message')}")
            else:
                print("❌ Respond action execution failed")
                return False
        else:
            print("❌ Respond action not found for testing")
            return False
            
        db.close()
        return True
    except Exception as e:
        print(f"❌ Error testing action execution: {e}")
        return False

def test_custom_action_execution():
    """Test custom action execution with mock endpoint"""
    print("\nTesting custom action execution...")
    try:
        db = SessionLocal()
        
        # Create a test custom action that calls a mock endpoint
        test_action = ActionCreate(
            name="Test Custom Action",
            description="Test action for testing custom action execution",
            endpoint="https://httpbin.org/post",  # Using httpbin for testing
            method="POST",
            parameters={"test_param": "test_value"},
            headers={"Content-Type": "application/json"},
            action_type="custom"
        )
        
        created_action = ActionManager.create_action(db, test_action)
        print(f"✅ Test custom action created: {created_action.name}")
        
        # Test the custom action execution
        result = ActionManager.execute_action(
            db,
            "Test Custom Action",
            {"test_param": "hello_world", "additional_param": "test"},
            {"test_context": "context_value"}
        )
        
        if result and result.get("type") == "custom_action":
            if result.get("success"):
                print("✅ Custom action execution successful")
                print(f"   - Status Code: {result.get('status_code')}")
                print(f"   - Endpoint Called: {result.get('endpoint_called')}")
                print(f"   - Method Used: {result.get('method_used')}")
                success = True
            else:
                print("❌ Custom action execution failed")
                print(f"   - Error: {result.get('error')}")
                success = False
        else:
            print("❌ Custom action execution returned unexpected result")
            success = False
            
        # Clean up test action
        db.delete(created_action)
        db.commit()
        print("✅ Test custom action cleaned up")
        
        db.close()
        return success
        
    except Exception as e:
        print(f"❌ Error testing custom action execution: {e}")
        return False

def test_custom_action_error_handling():
    """Test custom action error handling with invalid endpoint"""
    print("\nTesting custom action error handling...")
    try:
        db = SessionLocal()
        
        # Create a test custom action with invalid endpoint
        test_action = ActionCreate(
            name="Test Error Action",
            description="Test action for testing error handling",
            endpoint="https://invalid-endpoint-that-does-not-exist.com/api",
            method="GET",
            parameters={},
            headers={},
            action_type="custom"
        )
        
        created_action = ActionManager.create_action(db, test_action)
        print(f"✅ Test error action created: {created_action.name}")
        
        # Test the custom action execution (should fail)
        result = ActionManager.execute_action(
            db,
            "Test Error Action",
            {},
            {}
        )
        
        if result and result.get("type") == "custom_action" and not result.get("success"):
            print("✅ Custom action error handling working")
            print(f"   - Error Type: Connection error detected")
            print(f"   - Error Message: {result.get('error')}")
            success = True
        else:
            print("❌ Custom action error handling not working properly")
            success = False
            
        # Clean up test action
        db.delete(created_action)
        db.commit()
        print("✅ Test error action cleaned up")
        
        db.close()
        return success
        
    except Exception as e:
        print(f"❌ Error testing custom action error handling: {e}")
        return False

def test_yaml_parsing():
    """Test YAML parsing functionality"""
    print("\nTesting YAML parsing...")
    try:
        # Test with the provided YAML spec
        yaml_content = """
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /test/{id}:
    get:
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
        - name: format
          in: query
          required: false
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: object
                    properties:
                      attributes:
                        type: object
                        properties:
                          title:
                            type: string
                          summary:
                            type: string
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: Authorization
"""
        
        # Test parsing
        spec = ActionManager.parse_yaml_spec(yaml_content)
        if spec and 'paths' in spec:
            print("✅ YAML parsing successful")
            
            # Test parameter generation
            parameters = ActionManager.generate_parameters_from_yaml(yaml_content)
            if 'id' in parameters and 'format' in parameters:
                print("✅ Parameter generation successful")
                print(f"   - Generated parameters: {list(parameters.keys())}")
            else:
                print("❌ Parameter generation failed")
                return False
                
            # Test header generation
            headers = ActionManager.generate_headers_from_yaml(yaml_content)
            if 'Authorization' in headers:
                print("✅ Header generation successful")
                print(f"   - Generated headers: {list(headers.keys())}")
            else:
                print("❌ Header generation failed")
                return False
            
            # Test response schema extraction
            response_schema = ActionManager.extract_response_schema_from_yaml(yaml_content)
            if response_schema and 'properties' in response_schema:
                print("✅ Response schema extraction successful")
                print(f"   - Schema properties: {list(response_schema['properties'].keys())}")
            else:
                print("❌ Response schema extraction failed")
                return False
            
            # Test response filtering
            mock_response = {
                "data": {
                    "attributes": {
                        "title": "Test Title",
                        "summary": "Test Summary"
                    },
                    "extra_field": "Should be filtered out"
                },
                "metadata": {
                    "should_be_filtered": True
                }
            }
            
            filtered_response = ActionManager.filter_response_by_schema(mock_response, response_schema)
            if (filtered_response and 
                'data' in filtered_response and 
                'attributes' in filtered_response['data'] and
                'title' in filtered_response['data']['attributes'] and
                'metadata' not in filtered_response):
                print("✅ Response filtering successful")
                print(f"   - Filtered keys: {list(filtered_response.keys())}")
            else:
                print("❌ Response filtering failed")
                return False
                
            return True
        else:
            print("❌ YAML parsing failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing YAML parsing: {e}")
        return False

def test_agent_actions_management():
    """Test agent actions management functionality"""
    print("\nTesting agent actions management...")
    
    db = SessionLocal()
    try:
        # Get existing LLM and actions for testing
        llm = db.query(LLM).first()
        thinking_action = db.query(Action).filter(Action.name == "Thinking").first()
        respond_action = db.query(Action).filter(Action.name == "Respond").first()
        
        if not llm or not thinking_action or not respond_action:
            print("❌ Required test data not available")
            return False
        
        # Create a test agent
        test_agent = Agent(
            name="Test Actions Agent",
            description="Agent for testing actions management",
            system_prompt="Test agent for actions management",
            llm_id=llm.id,
            actions=[
                {"action_name": "Thinking", "prompt": "Think about the request", "order": 1},
                {"action_name": "Respond", "prompt": "Respond to the user", "order": 2}
            ]
        )
        db.add(test_agent)
        db.commit()
        db.refresh(test_agent)
        
        print("✅ Test agent created for actions management")
        print(f"   - Agent ID: {test_agent.id}")
        print(f"   - Initial actions: {len(test_agent.actions)}")
        
        # Test getting agent actions (simulating GET /agents/{id}/actions)
        detailed_actions = []
        for action_config in test_agent.actions:
            action_name = action_config.get("action_name")
            action = db.query(Action).filter(Action.name == action_name).first()
            
            if action:
                detailed_action = {
                    "action_name": action.name,
                    "action_id": action.id,
                    "description": action.description,
                    "action_type": action.action_type,
                    "prompt": action_config.get("prompt", ""),
                    "order": action_config.get("order", 0)
                }
                detailed_actions.append(detailed_action)
        
        print("✅ Agent actions retrieval working")
        print(f"   - Retrieved {len(detailed_actions)} detailed actions")
        
        # Test updating agent actions (simulating PUT /agents/{id}/actions)
        new_actions = [
            {"action_name": "Thinking", "prompt": "Updated thinking prompt", "order": 1},
            {"action_name": "Respond", "prompt": "Updated response prompt", "order": 2}
        ]
        
        # Validate that all referenced actions exist
        for action_config in new_actions:
            action_name = action_config.get("action_name")
            action = db.query(Action).filter(Action.name == action_name).first()
            if not action:
                print(f"❌ Action '{action_name}' not found")
                return False
        
        # Update the agent's actions
        test_agent.actions = new_actions
        db.commit()
        db.refresh(test_agent)
        
        print("✅ Agent actions update working")
        print(f"   - Updated actions: {len(test_agent.actions)}")
        print(f"   - First action prompt: {test_agent.actions[0]['prompt']}")
        
        # Test adding a new action to the flow
        updated_actions = test_agent.actions.copy()
        # Add Thinking action again (simulating user adding it in the middle)
        updated_actions.insert(1, {"action_name": "Thinking", "prompt": "Additional thinking step", "order": 2})
        
        # Reorder actions
        for idx, action in enumerate(updated_actions):
            action["order"] = idx + 1
        
        test_agent.actions = updated_actions
        db.commit()
        db.refresh(test_agent)
        
        print("✅ Agent actions reordering working")
        print(f"   - Final actions count: {len(test_agent.actions)}")
        print(f"   - Action flow: {[a['action_name'] for a in test_agent.actions]}")
        
        # Clean up
        db.delete(test_agent)
        db.commit()
        print("✅ Test agent cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in agent actions management test: {e}")
        return False
    finally:
        db.close()

def cleanup_test_data():
    """Clean up test data"""
    print("\nCleaning up test data...")
    try:
        db = SessionLocal()
        
        # Remove test LLM
        test_llm = db.query(LLM).filter(LLM.name == "Test LLM").first()
        if test_llm:
            db.delete(test_llm)
            db.commit()
            print("✅ Test LLM removed")
            
        # Remove any remaining test actions
        test_actions = db.query(Action).filter(
            Action.name.in_(["Test Custom Action", "Test Error Action"])
        ).all()
        for action in test_actions:
            db.delete(action)
        if test_actions:
            db.commit()
            print(f"✅ {len(test_actions)} test actions removed")
        
        # Remove any remaining test agents
        test_agents = db.query(Agent).filter(Agent.name == "Test Actions Agent").all()
        for agent in test_agents:
            db.delete(agent)
        if test_agents:
            db.commit()
            print(f"✅ {len(test_agents)} test agents removed")
            
        db.close()
        return True
    except Exception as e:
        print(f"❌ Error cleaning up test data: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Agent Platform System Tests\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Native Actions", test_native_actions),
        ("Duplicate Name Validation", test_duplicate_name_validation),
        ("Action Execution", test_action_execution),
        ("Custom Action Execution", test_custom_action_execution),
        ("Custom Action Error Handling", test_custom_action_error_handling),
        ("YAML Parsing", test_yaml_parsing),
        ("Agent Actions Management", test_agent_actions_management),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    # Cleanup
    cleanup_test_data()
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
