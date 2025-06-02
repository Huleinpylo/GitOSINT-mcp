"""
Basic test suite for GitOSINT-MCP
Author: Huleinpylo
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gitosint_mcp.server import GitOSINTAnalyzer, UserIntelligence, RepositoryIntel

class TestGitOSINTAnalyzer:
    """Test cases for GitOSINTAnalyzer class"""
    
    @pytest.fixture
    async def analyzer(self):
        """Create analyzer instance for testing"""
        analyzer = GitOSINTAnalyzer()
        yield analyzer
        await analyzer.close()
    
    @pytest.fixture
    def mock_github_repo_response(self):
        """Mock GitHub repository API response"""
        return {
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "description": "A test repository",
            "stargazers_count": 100,
            "forks_count": 25,
            "language": "Python",
            "topics": ["test", "python", "automation"],
            "has_security_policy": True,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-12-01T00:00:00Z"
        }
    
    @pytest.fixture
    def mock_github_user_response(self):
        """Mock GitHub user API response"""
        return {
            "login": "testuser",
            "name": "Test User",
            "bio": "Software developer",
            "location": "San Francisco",
            "company": "Test Company",
            "blog": "https://testuser.dev",
            "twitter_username": "testuser",
            "public_repos": 15,
            "followers": 100,
            "following": 50,
            "created_at": "2020-01-01T00:00:00Z"
        }
    
    @pytest.mark.asyncio
    async def test_analyze_github_repository(self, analyzer, mock_github_repo_response):
        """Test GitHub repository analysis"""
        with patch.object(analyzer.client, 'get') as mock_get:
            # Mock API responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_github_repo_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await analyzer.analyze_repository("https://github.com/testuser/test-repo")
            
            assert isinstance(result, RepositoryIntel)
            assert result.name == "testuser/test-repo"
            assert result.description == "A test repository"
            assert result.stars == 100
            assert result.forks == 25
            assert result.language == "Python"
            assert "test" in result.topics
    
    @pytest.mark.asyncio
    async def test_analyze_invalid_url(self, analyzer):
        """Test handling of invalid repository URLs"""
        with pytest.raises(ValueError, match="Invalid repository URL format"):
            await analyzer.analyze_repository("https://github.com/invalid")
    
    @pytest.mark.asyncio
    async def test_discover_github_user(self, analyzer, mock_github_user_response):
        """Test GitHub user discovery"""
        with patch.object(analyzer.client, 'get') as mock_get:
            # Mock user API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_github_user_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await analyzer.discover_user_info("testuser", "github")
            
            assert isinstance(result, UserIntelligence)
            assert result.username == "testuser"
            assert result.profile_data["name"] == "Test User"
            assert result.profile_data["company"] == "Test Company"
    
    @pytest.mark.asyncio
    async def test_find_emails_user_search(self, analyzer):
        """Test email discovery for users"""
        with patch.object(analyzer, 'discover_user_info') as mock_discover:
            mock_user = UserIntelligence(
                username="testuser",
                email_addresses=["test@example.com", "user@company.com"],
                repositories=[],
                commit_count=0,
                languages=[],
                activity_pattern={},
                social_connections=[],
                profile_data={}
            )
            mock_discover.return_value = mock_user
            
            result = await analyzer.find_emails("testuser", "user")
            
            assert "test@example.com" in result
            assert "user@company.com" in result
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_map_social_network(self, analyzer):
        """Test social network mapping"""
        with patch.object(analyzer, 'discover_user_info') as mock_discover, \
             patch.object(analyzer, 'analyze_repository') as mock_analyze:
            
            # Mock user info
            mock_user = UserIntelligence(
                username="testuser",
                email_addresses=[],
                repositories=[{"name": "test-repo"}],
                commit_count=1,
                languages=[],
                activity_pattern={},
                social_connections=[],
                profile_data={}
            )
            mock_discover.return_value = mock_user
            
            # Mock repository analysis
            mock_repo = RepositoryIntel(
                name="test-repo",
                description="",
                stars=0,
                forks=0,
                language="Python",
                topics=[],
                contributors=[
                    {"login": "collaborator1", "contributions": 10},
                    {"login": "collaborator2", "contributions": 5}
                ],
                commit_activity={},
                security_issues=[],
                dependencies=["dependency1", "dependency2"]
            )
            mock_analyze.return_value = mock_repo
            
            result = await analyzer.map_social_network("testuser", depth=2)
            
            assert result["center"] == "testuser"
            assert result["depth"] == 2
            assert "test-repo" in result["connections"]
    
    @pytest.mark.asyncio
    async def test_scan_security_issues(self, analyzer):
        """Test security issue scanning"""
        with patch.object(analyzer, 'analyze_repository') as mock_analyze:
            # Mock repository with security indicators
            mock_repo = RepositoryIntel(
                name="test-repo",
                description="Contains passwords and secret keys",
                stars=0,
                forks=0,
                language="Python",
                topics=[],
                contributors=[],
                commit_activity={"recent_activity": 0},
                security_issues=[],
                dependencies=["crypto-mining-lib"]
            )
            mock_analyze.return_value = mock_repo
            
            result = await analyzer.scan_security_issues("https://github.com/user/repo")
            
            # Should detect suspicious description and dependency
            issue_types = [issue['type'] for issue in result]
            assert 'potential_secret_exposure' in issue_types
            assert 'suspicious_dependency' in issue_types
            assert 'inactive_repository' in issue_types
    
    def test_process_commit_activity(self, analyzer):
        """Test commit activity processing"""
        activity_data = [
            {"total": 5},
            {"total": 10},
            {"total": 3},
            {"total": 8}
        ]
        
        result = analyzer._process_commit_activity(activity_data)
        
        assert result["total_commits"] == 26
        assert result["recent_activity"] == 26  # All 4 weeks
        assert result["peak_week"] == 10
    
    def test_extract_languages(self, analyzer):
        """Test language extraction from repositories"""
        repos_data = [
            {"language": "Python"},
            {"language": "JavaScript"},
            {"language": "Python"},  # Duplicate
            {"language": None}  # No language
        ]
        
        result = analyzer._extract_languages(repos_data)
        
        assert "Python" in result
        assert "JavaScript" in result
        assert len(result) == 2  # Duplicates removed


class TestMCPServer:
    """Test MCP server functionality"""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that all expected tools are listed"""
        from gitosint_mcp.server import handle_list_tools
        
        tools = await handle_list_tools()
        
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "analyze_repository",
            "discover_user_info",
            "find_emails",
            "map_social_network",
            "scan_security_issues"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    @pytest.mark.asyncio
    async def test_call_tool_analyze_repository(self):
        """Test analyze_repository tool call"""
        from gitosint_mcp.server import handle_call_tool
        
        with patch('gitosint_mcp.server.analyzer') as mock_analyzer:
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
                dependencies=["dependency1", "dependency2"]
            )
            mock_analyzer.analyze_repository.return_value = mock_result
            
            result = await handle_call_tool(
                "analyze_repository",
                {"repo_url": "https://github.com/test/repo"}
            )
            
            result_list = list(result)
            assert len(result_list) == 1
            assert result_list[0].type == "text"
            data = json.loads(result_list[0].text)
            assert data["name"] == "test/repo"
            assert data["stars"] == 100
    
    @pytest.mark.asyncio
    async def test_call_tool_invalid_name(self):
        """Test calling invalid tool name"""
        from gitosint_mcp.server import handle_call_tool
        
        result = await handle_call_tool("invalid_tool", {})
        
        result_list = list(result)
        assert len(result_list) == 1
        assert result_list[0].type == "text"
        data = json.loads(result_list[0].text)
        assert "error" in data
        assert "Unknown tool" in data["error"]
    
    @pytest.mark.asyncio
    async def test_call_tool_missing_arguments(self):
        """Test calling tool with missing required arguments"""
        from gitosint_mcp.server import handle_call_tool
        
        result = list(await handle_call_tool("analyze_repository", {}))
        
        assert len(result) == 1
        assert result[0].type == "text"
        data = json.loads(result[0].text)
        assert "error" in data
        assert "required" in data["error"].lower()


class TestDataStructures:
    """Test data structure classes"""
    
    def test_user_intelligence_creation(self):
        """Test UserIntelligence data structure"""
        user_intel = UserIntelligence(
            username="testuser",
            email_addresses=["test@example.com"],
            repositories=[{"name": "repo1"}],
            commit_count=5,
            languages=["Python", "JavaScript"],
            activity_pattern={"total_repos": 5},
            social_connections=["user1", "user2"],
            profile_data={"name": "Test User"}
        )
        
        assert user_intel.username == "testuser"
        assert len(user_intel.email_addresses) == 1
        assert len(user_intel.languages) == 2
        assert user_intel.profile_data["name"] == "Test User"
    
    def test_repository_intel_creation(self):
        """Test RepositoryIntel data structure"""
        repo_intel = RepositoryIntel(
            name="user/repo",
            description="Test repository",
            stars=100,
            forks=25,
            language="Python",
            topics=["test", "automation"],
            contributors=[{"login": "user1"}],
            commit_activity={"recent": 10},
            security_issues=["issue1"],
            dependencies=list({"Python": 1000}.keys())
        )
        
        assert repo_intel.name == "user/repo"
        assert repo_intel.stars == 100
        assert "test" in repo_intel.topics
        assert len(repo_intel.contributors) == 1


class TestUtilityFunctions:
    """Test utility and helper functions"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer for testing utility functions"""
        return GitOSINTAnalyzer()
    
    def test_url_parsing_github(self, analyzer):
        """Test URL parsing for GitHub repositories"""
        # This would test internal URL parsing logic
        # Implementation depends on how URL parsing is structured
        pass
    
    def test_rate_limiting(self, analyzer):
        """Test rate limiting functionality"""
        # Test that rate limiting delay is applied
        assert analyzer.rate_limit_delay == 1.0
    
    def test_security_indicators_detection(self, analyzer):
        """Test security indicators detection"""
        repo_data = {
            "topics": ["security", "vulnerability"],
            "has_security_policy": True
        }
        
        result = asyncio.run(analyzer._check_security_indicators(repo_data))
        
        assert len(result) >= 2  # Should detect security topics and policy
        assert any("security" in indicator.lower() for indicator in result)


# Integration tests
class TestIntegration:
    """Integration tests with external services (when enabled)"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_github_repo_analysis(self):
        """Test analysis of a real GitHub repository"""
        # This test only runs when INTEGRATION_TEST env var is set
        import os
        if not os.getenv('INTEGRATION_TEST'):
            pytest.skip("Integration tests disabled")
        
        analyzer = GitOSINTAnalyzer()
        try:
            # Test with a well-known public repository
            result = await analyzer.analyze_repository("https://github.com/octocat/Hello-World")
            
            assert isinstance(result, RepositoryIntel)
            assert result.name == "octocat/Hello-World"
            assert result.stars >= 0  # Should have some stars
            
        finally:
            await analyzer.close()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_user_discovery(self):
        """Test discovery of a real GitHub user"""
        import os
        if not os.getenv('INTEGRATION_TEST'):
            pytest.skip("Integration tests disabled")
        
        analyzer = GitOSINTAnalyzer()
        try:
            # Test with a well-known user
            result = await analyzer.discover_user_info("octocat", "github")
            
            assert isinstance(result, UserIntelligence)
            assert result.username == "octocat"
            assert len(result.repositories) > 0
            
        finally:
            await analyzer.close()


# Fixtures for pytest
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring network access"
    )


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])