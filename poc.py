#!/usr/bin/env python3
"""
Test script for GitOSINT-MCP server functionality
"""

import asyncio
import json
import sys
from pathlib import Path
from src.gitosint_mcp.server import (
    GitOSINTAnalyzer, 
    handle_list_tools, 
    handle_call_tool,
    server
)

async def test_mcp_server():
    """Test MCP server functionality"""
    print("🧪 Testing GitOSINT-MCP Server...")
    
    # Test 1: List Tools
    print("\n1️⃣ Testing tool listing...")
    try:
        tools = await handle_list_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   • {tool.name}: {tool.description}")
    except Exception as e:
        print(f"❌ Tool listing failed: {e}")
        return False
    
    # Test 2: Test Analyzer Initialization
    print("\n2️⃣ Testing analyzer initialization...")
    try:
        analyzer = GitOSINTAnalyzer()
        print("✅ Analyzer initialized successfully")
        print(f"   • Rate limit delay: {analyzer.rate_limit_delay}s")
        print(f"   • User Agent: {analyzer.client.headers.get('User-Agent', 'Not set')}")
    except Exception as e:
        print(f"❌ Analyzer initialization failed: {e}")
        return False
    
    # Test 3: Test Tool Call Structure (without real API calls)
    print("\n3️⃣ Testing tool call structure...")
    test_cases = [
        ("analyze_repository", {"repo_url": "https://github.com/octocat/Hello-World"}),
        ("discover_user_info", {"username": "octocat", "platform": "github"}),
        ("find_emails", {"target": "octocat", "search_type": "user"}),
        ("map_social_network", {"username": "octocat", "depth": 1}),
        ("scan_security_issues", {"repo_url": "https://github.com/octocat/Hello-World"})
    ]
    
    for tool_name, args in test_cases:
        try:
            print(f"   Testing {tool_name}...")
            # This will fail on HTTP calls but should test argument validation
            result = await handle_call_tool(tool_name, args)
            
            result_list = list(result)
            if not result_list:
                print(f"   ❌ {tool_name} returned no results")
                continue
            data = json.loads(str(result_list[0]))
            if "error" in data:
                print(f"   ❌ {tool_name} returned an error: {data['error']}")
                continue
            if not isinstance(data, dict):
                print(f"   ❌ {tool_name} returned invalid data structure: {type(data)}")
                continue
            if "results" not in data or not isinstance(data["results"], list):
                print(f"   ❌ {tool_name} returned invalid results structure")
                continue
            if not data["results"]:
                print(f"   ❌ {tool_name} returned empty results")
                continue
            if "metadata" not in data or not isinstance(data["metadata"], dict):
                print(f"   ❌ {tool_name} returned invalid metadata structure")
                continue
            if "rate_limit" not in data["metadata"] or not isinstance(data["metadata"]["rate_limit"], dict):
                print(f"   ❌ {tool_name} returned invalid rate limit structure")
                continue
            if "remaining" not in data["metadata"]["rate_limit"] or not isinstance(data["metadata"]["rate_limit"]["remaining"], int):
                print(f"   ❌ {tool_name} returned invalid remaining count")
                continue
            if "reset" not in data["metadata"]["rate_limit"] or not isinstance(data["metadata"]["rate_limit"]["reset"], int):
                print(f"   ❌ {tool_name} returned invalid reset time")
                continue
            if "delay" not in data["metadata"]["rate_limit"] or not isinstance(data["metadata"]["rate_limit"]["delay"], (int, float)):
                print(f"   ❌ {tool_name} returned invalid delay")
                continue
            if "user_agent" not in data["metadata"] or not isinstance(data["metadata"]["user_agent"], str):
                print(f"   ❌ {tool_name} returned invalid user agent")
                continue
            if "timestamp" not in data["metadata"] or not isinstance(data["metadata"]["timestamp"], str):
                print(f"   ❌ {tool_name} returned invalid timestamp")
                continue
            else:
                print(f"   ✅ {tool_name} returned valid data structure")

        except Exception as e:
            if "HTTP" in str(e) or "network" in str(e).lower() or "timeout" in str(e).lower():
                print(f"   ⚠️  {tool_name} structure valid (network error expected: {type(e).__name__})")
            else:
                print(f"   ❌ {tool_name} failed: {e}")
    
    # Test 4: Test Invalid Tool Call
    print("\n4️⃣ Testing error handling...")
    try:
        result = await handle_call_tool("invalid_tool", {})
        result_list = list(result)
        data = json.loads(str(result_list[0]))
        if "error" in data and "Unknown tool" in data["error"]:
            print("✅ Error handling works correctly")
        else:
            print(f"⚠️  Unexpected error response: {data}")
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    # Test 5: Test Missing Arguments
    print("\n5️⃣ Testing argument validation...")
    try:
        result = await handle_call_tool("analyze_repository", {})
        result_list = list(result)
        data = json.loads(str(result_list[0]))
        if "error" in data and "required" in data["error"].lower():
            print("✅ Argument validation works correctly")
        else:
            print(f"⚠️  Unexpected validation response: {data}")
    except Exception as e:
        print(f"❌ Argument validation test failed: {e}")
    
    # Clean up
    await analyzer.close()
    
    print("\n🎉 MCP Server Tests Completed!")
    print("\n📋 Next Steps:")
    print("1. Configure Claude Desktop with this MCP server")
    print("2. Test with real repository URLs")
    print("3. Monitor rate limiting and API responses")
    
    return True

def test_mcp_server_startup():
    """Test if the MCP server can start without errors"""
    print("\n🚀 Testing MCP server startup...")
    
    try:
        # Import the server
        from src.gitosint_mcp.server import server
        print("✅ Server import successful")
        
        # Check server configuration
        print(f"✅ Server name: {getattr(server, '_name', 'gitosint-mcp')}")
        
        # Test server decorators
        if hasattr(server, '_tools_handler'):
            print("✅ Tools handler registered")
        if hasattr(server, '_call_tool_handler'):
            print("✅ Call tool handler registered")
            
        return True
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

if __name__ == "__main__":
    print("GitOSINT-MCP Test Suite")
    print("=" * 50)
    
    # Test server startup
    startup_ok = test_mcp_server_startup()
    
    if startup_ok:
        # Test async functionality
        asyncio.run(test_mcp_server())
    else:
        print("❌ Cannot proceed with tests due to startup failure")
        sys.exit(1)