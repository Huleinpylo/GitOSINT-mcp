"""
Test suite for MCP protocol compliance
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List

# MCP imports
try:
    from mcp.types import TextContent, Tool
    from mcp.server.models import InitializationOptions
    from mcp.server import Server
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Mock MCP types for testing without MCP installed
    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text
    
    class Tool:
        def __init__(self, name: str, description: str, inputSchema: Dict):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema

from src.gitosint_mcp.server import (
    server,
    handle_list_tools,
    handle_call_tool,
    GitOSINTAnalyzer,
    UserIntelligence,
    RepositoryIntel
)


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP not available")
class TestMCPProtocolCompliance:
    """Test MCP protocol compliance"""
    
    @pytest.mark.asyncio
    async def test_server_instance_created(self):
        """Test that MCP server instance is properly created"""
        assert server is not None
        assert hasattr(server, 'list_tools')
        assert hasattr(server, 'call_tool')
    
    @pytest.mark.asyncio
    async def test_tools_list_format(self):
        """Test that tools list conforms to MCP format"""
        tools = await handle_list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 5
        
        for tool in tools:
            assert isinstance(tool, Tool)
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            
            # Validate tool name format
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0
            assert '_' in tool.name or tool.name.isalpha()
            
            # Validate description
            assert isinstance(tool.description, str)
            assert len(tool.description) > 10
            
            # Validate input schema
            assert isinstance(tool.inputSchema, dict)
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
            assert 'properties' in tool.inputSchema
            assert 'required' in tool.inputSchema
    
    @pytest.mark.asyncio
    async def test_tool_schemas_valid(self):
        """Test that all tool schemas are valid JSON Schema"""
        tools = await handle_list_tools()
        
        for tool in tools:
            schema = tool.inputSchema
            
            # Basic JSON Schema validation
            assert schema['type'] == 'object'
            assert isinstance(schema['properties'], dict)
            assert isinstance(schema['required'], list)
            
            # Check that required fields exist in properties
            for required_field in schema['required']:
                assert required_field in schema['properties']
            
            # Validate property types
            for prop_name, prop_def in schema['properties'].items():
                assert 'type' in prop_def
                assert prop_def['type'] in ['string', 'integer', 'boolean', 'array', 'object']
                
                if 'enum' in prop_def:
                    assert isinstance(prop_def['enum'], list)
                    assert len(prop_def['enum']) > 0
    
    @pytest.mark.asyncio
    async def test_tool_call_response_format(self):
        """Test that tool call responses conform to MCP format"""
        mock_result = RepositoryIntel(
            name="test/repo",
            description="Test repository",
            stars=100,
            forks=25,
            language="Python",
            topics=["test"],
            contributors=[],
            commit_activity={},
            security_issues=[],
            dependencies={}
        )
        
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.analyze_repository.return_value = mock_result
            
            result = await handle_call_tool(
                "analyze_repository",
                {"repo_url": "https://github.com/test/repo"}
            )
            
            # Validate response format
            assert isinstance(result, list)
            assert len(result) == 1
            
            content = result[0]
            assert isinstance(content, TextContent)
            assert content.type == "text"
            assert isinstance(content.text, str)
            
            # Validate JSON content
            data = json.loads(content.text)
            assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_error_handling_format(self):
        """Test that errors are properly formatted for MCP"""
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.analyze_repository.side_effect = Exception("Test error")
            
            result = await handle_call_tool(
                "analyze_repository",
                {"repo_url": "https://github.com/test/repo"}
            )
            
            assert isinstance(result, list)
            assert len(result) == 1
            
            content = result[0]
            assert isinstance(content, TextContent)
            assert content.type == "text"
            
            data = json.loads(content.text)
            assert "error" in data
            assert "Test error" in data["error"]
    
    @pytest.mark.asyncio
    async def test_all_tools_callable(self):
        """Test that all listed tools are actually callable"""
        tools = await handle_list_tools()
        
        for tool in tools:
            # Create minimal valid arguments for each tool
            if tool.name == "analyze_repository":
                args = {"repo_url": "https://github.com/test/repo"}
            elif tool.name == "discover_user_info":
                args = {"username": "testuser"}
            elif tool.name == "find_emails":
                args = {"target": "testuser"}
            elif tool.name == "map_social_network":
                args = {"username": "testuser"}
            elif tool.name == "scan_security_issues":
                args = {"repo_url": "https://github.com/test/repo"}
            else:
                pytest.fail(f"Unknown tool: {tool.name}")
            
            # Mock analyzer to avoid actual API calls
            with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
                # Set up appropriate mock return values
                if tool.name == "analyze_repository" or tool.name == "scan_security_issues":
                    mock_analyzer.analyze_repository.return_value = RepositoryIntel(
                        name="test/repo", description="", stars=0, forks=0, language="",
                        topics=[], contributors=[], commit_activity={}, security_issues=[], dependencies={}
                    )
                    mock_analyzer.scan_security_issues.return_value = []
                elif tool.name == "discover_user_info":
                    mock_analyzer.discover_user_info.return_value = UserIntelligence(
                        username="test", email_addresses=[], repositories=[], commit_count=0,
                        languages=[], activity_pattern={}, social_connections=[], profile_data={}
                    )
                elif tool.name == "find_emails":
                    mock_analyzer.find_emails.return_value = []
                elif tool.name == "map_social_network":
                    mock_analyzer.map_social_network.return_value = {"center": "test", "connections": {}}
                
                # Call the tool
                result = await handle_call_tool(tool.name, args)
                
                # Verify it returns proper format
                assert isinstance(result, list)
                assert len(result) >= 1
                assert isinstance(result[0], TextContent)


class TestMCPServerIntegration:
    """Test MCP server integration without requiring MCP runtime"""
    
    def test_server_registration_decorators(self):
        """Test that server decorators are properly applied"""
        # Test that the handlers are registered
        assert hasattr(server, '_tools_handler')
        assert hasattr(server, '_call_tool_handler')
        
        # Test that handlers are callable
        assert callable(server._tools_handler) if hasattr(server, '_tools_handler') else True
        assert callable(server._call_tool_handler) if hasattr(server, '_call_tool_handler') else True
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test that multiple tool calls can be handled concurrently"""
        mock_result = RepositoryIntel(
            name="test/repo", description="", stars=0, forks=0, language="",
            topics=[], contributors=[], commit_activity={}, security_issues=[], dependencies={}
        )
        
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.analyze_repository.return_value = mock_result
            
            # Create multiple concurrent tool calls
            tasks = [
                handle_call_tool("analyze_repository", {"repo_url": f"https://github.com/test/repo{i}"})
                for i in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert len(results) == 3
            for result in results:
                assert isinstance(result, list)
                assert len(result) == 1
                assert isinstance(result[0], TextContent)
    
    @pytest.mark.asyncio
    async def test_tool_argument_validation(self):
        """Test tool argument validation"""
        # Test missing required arguments
        result = await handle_call_tool("analyze_repository", {})
        
        assert isinstance(result, list)
        assert len(result) == 1
        content = result[0]
        assert isinstance(content, TextContent)
        
        data = json.loads(content.text)
        assert "error" in data
        assert "required" in data["error"].lower()
        
        # Test invalid argument types (if validation is implemented)
        result = await handle_call_tool("map_social_network", {"username": "test", "depth": "invalid"})
        
        # Should handle gracefully (either convert or error)
        assert isinstance(result, list)
        assert len(result) == 1


class TestMCPDataSerialization:
    """Test data serialization for MCP responses"""
    
    @pytest.mark.asyncio
    async def test_repository_intel_serialization(self):
        """Test that RepositoryIntel serializes properly for MCP"""
        repo_intel = RepositoryIntel(
            name="test/repo",
            description="Test repository",
            stars=100,
            forks=25,
            language="Python",
            topics=["test", "automation"],
            contributors=[
                {"login": "user1", "contributions": 50},
                {"login": "user2", "contributions": 25}
            ],
            commit_activity={"recent_activity": 10, "peak_week": 15},
            security_issues=["issue1", "issue2"],
            dependencies={"Python": 1000, "JavaScript": 500}
        )
        
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.analyze_repository.return_value = repo_intel
            
            result = await handle_call_tool(
                "analyze_repository",
                {"repo_url": "https://github.com/test/repo"}
            )
            
            data = json.loads(result[0].text)
            
            # Verify all fields are serializable and present
            assert data["name"] == "test/repo"
            assert data["description"] == "Test repository"
            assert data["stars"] == 100
            assert data["forks"] == 25
            assert data["language"] == "Python"
            assert data["topics"] == ["test", "automation"]
            assert len(data["contributors"]) == 2
            assert isinstance(data["commit_activity"], dict)
            assert isinstance(data["security_issues"], list)
            assert isinstance(data["dependencies"], dict)
    
    @pytest.mark.asyncio
    async def test_user_intelligence_serialization(self):
        """Test that UserIntelligence serializes properly for MCP"""
        user_intel = UserIntelligence(
            username="testuser",
            email_addresses=["test@example.com", "work@company.com"],
            repositories=[
                {"name": "repo1", "stars": 10},
                {"name": "repo2", "stars": 5}
            ],
            commit_count=25,
            languages=["Python", "JavaScript"],
            activity_pattern={"total_repos": 2, "active_repos": 2},
            social_connections=["friend1", "friend2"],
            profile_data={
                "name": "Test User",
                "company": "Test Corp",
                "location": "San Francisco"
            }
        )
        
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.discover_user_info.return_value = user_intel
            
            result = await handle_call_tool(
                "discover_user_info",
                {"username": "testuser"}
            )
            
            data = json.loads(result[0].text)
            
            # Verify all fields are serializable and present
            assert data["username"] == "testuser"
            assert data["email_addresses"] == ["test@example.com", "work@company.com"]
            assert len(data["repositories"]) == 2
            assert data["commit_count"] == 25
            assert data["languages"] == ["Python", "JavaScript"]
            assert isinstance(data["activity_pattern"], dict)
            assert data["social_connections"] == ["friend1", "friend2"]
            assert isinstance(data["profile_data"], dict)
            assert data["profile_data"]["name"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_json_serialization_edge_cases(self):
        """Test JSON serialization with edge cases"""
        # Test with None values
        repo_intel = RepositoryIntel(
            name="test/repo",
            description=None,  # None value
            stars=0,
            forks=0,
            language=None,  # None value
            topics=[],
            contributors=[],
            commit_activity={},
            security_issues=[],
            dependencies={}
        )
        
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.analyze_repository.return_value = repo_intel
            
            result = await handle_call_tool(
                "analyze_repository",
                {"repo_url": "https://github.com/test/repo"}
            )
            
            # Should not raise JSON serialization errors
            data = json.loads(result[0].text)
            assert isinstance(data, dict)
            assert data["name"] == "test/repo"


class TestMCPToolSchemas:
    """Test specific tool schemas and their validation"""
    
    @pytest.mark.asyncio
    async def test_analyze_repository_schema(self):
        """Test analyze_repository tool schema"""
        tools = await handle_list_tools()
        tool = next(t for t in tools if t.name == "analyze_repository")
        
        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "repo_url" in schema["properties"]
        assert "repo_url" in schema["required"]
        
        # Validate repo_url property
        repo_url_prop = schema["properties"]["repo_url"]
        assert repo_url_prop["type"] == "string"
        assert "description" in repo_url_prop
    
    @pytest.mark.asyncio
    async def test_discover_user_info_schema(self):
        """Test discover_user_info tool schema"""
        tools = await handle_list_tools()
        tool = next(t for t in tools if t.name == "discover_user_info")
        
        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "username" in schema["properties"]
        assert "platform" in schema["properties"]
        assert "username" in schema["required"]
        
        # Validate platform enum
        platform_prop = schema["properties"]["platform"]
        assert platform_prop["type"] == "string"
        assert "enum" in platform_prop
        assert "github" in platform_prop["enum"]
        assert "gitlab" in platform_prop["enum"]
    
    @pytest.mark.asyncio
    async def test_find_emails_schema(self):
        """Test find_emails tool schema"""
        tools = await handle_list_tools()
        tool = next(t for t in tools if t.name == "find_emails")
        
        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "target" in schema["properties"]
        assert "search_type" in schema["properties"]
        assert "target" in schema["required"]
        
        # Validate search_type enum
        search_type_prop = schema["properties"]["search_type"]
        assert search_type_prop["type"] == "string"
        assert "enum" in search_type_prop
        assert "user" in search_type_prop["enum"]
        assert "repo" in search_type_prop["enum"]
    
    @pytest.mark.asyncio
    async def test_map_social_network_schema(self):
        """Test map_social_network tool schema"""
        tools = await handle_list_tools()
        tool = next(t for t in tools if t.name == "map_social_network")
        
        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "username" in schema["properties"]
        assert "depth" in schema["properties"]
        assert "username" in schema["required"]
        
        # Validate depth constraints
        depth_prop = schema["properties"]["depth"]
        assert depth_prop["type"] == "integer"
        assert "minimum" in depth_prop
        assert "maximum" in depth_prop
        assert depth_prop["minimum"] == 1
        assert depth_prop["maximum"] == 3
    
    @pytest.mark.asyncio
    async def test_scan_security_issues_schema(self):
        """Test scan_security_issues tool schema"""
        tools = await handle_list_tools()
        tool = next(t for t in tools if t.name == "scan_security_issues")
        
        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "repo_url" in schema["properties"]
        assert "repo_url" in schema["required"]
        
        # Validate repo_url property
        repo_url_prop = schema["properties"]["repo_url"]
        assert repo_url_prop["type"] == "string"
        assert "description" in repo_url_prop


if __name__ == "__main__":
    pytest.main([__file__, "-v"])