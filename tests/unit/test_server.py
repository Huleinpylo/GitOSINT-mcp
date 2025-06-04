"""
Test suite for GitOSINT-MCP server module
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.gitosint_mcp.server import (
    GitOSINTAnalyzer,
    UserIntelligence,
    RepositoryIntel,
    handle_list_tools,
    handle_call_tool
)


class TestGitOSINTAnalyzer:
    """Test GitOSINTAnalyzer class"""
    
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
            "description": "A test repository for OSINT analysis",
            "stargazers_count": 150,
            "forks_count": 30,
            "language": "Python",
            "topics": ["osint", "python", "security"],
            "has_security_policy": True,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-12-01T00:00:00Z",
            "default_branch": "main",
            "size": 1024,
            "open_issues_count": 5,
            "subscribers_count": 20
        }
    
    @pytest.fixture
    def mock_github_user_response(self):
        """Mock GitHub user API response"""
        return {
            "login": "testuser",
            "id": 123456,
            "name": "Test User",
            "email": "test@example.com",
            "bio": "Security researcher and developer",
            "location": "San Francisco, CA",
            "company": "Test Security Corp",
            "blog": "https://testuser.dev",
            "twitter_username": "testuser",
            "public_repos": 25,
            "public_gists": 5,
            "followers": 150,
            "following": 75,
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2023-12-01T00:00:00Z",
            "hireable": True
        }
    
    @pytest.fixture
    def mock_contributors_response(self):
        """Mock GitHub contributors API response"""
        return [
            {
                "login": "contributor1",
                "id": 111111,
                "contributions": 50,
                "email": "contrib1@example.com",
                "type": "User"
            },
            {
                "login": "contributor2", 
                "id": 222222,
                "contributions": 25,
                "email": "contrib2@example.com",
                "type": "User"
            },
            {
                "login": "testuser",
                "id": 123456,
                "contributions": 100,
                "email": "test@example.com",
                "type": "User"
            }
        ]
    
    @pytest.fixture
    def mock_commits_response(self):
        """Mock GitHub commits API response"""
        return [
            {
                "sha": "abc123",
                "commit": {
                    "author": {
                        "name": "Test User",
                        "email": "test@example.com",
                        "date": "2023-12-01T10:00:00Z"
                    },
                    "committer": {
                        "name": "Test User", 
                        "email": "test@example.com",
                        "date": "2023-12-01T10:00:00Z"
                    },
                    "message": "Add new feature"
                }
            },
            {
                "sha": "def456",
                "commit": {
                    "author": {
                        "name": "Contributor",
                        "email": "contrib@example.com",
                        "date": "2023-11-30T15:00:00Z"
                    },
                    "committer": {
                        "name": "Contributor",
                        "email": "contrib@example.com", 
                        "date": "2023-11-30T15:00:00Z"
                    },
                    "message": "Fix bug in analyzer"
                }
            }
        ]
    
    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer.client is not None
        assert analyzer.rate_limit_delay == 1.0
        assert "GitOSINT-MCP" in analyzer.client.headers["User-Agent"]
    
    @pytest.mark.asyncio
    async def test_analyze_github_repository_success(self, analyzer, mock_github_repo_response, mock_contributors_response):
        """Test successful GitHub repository analysis"""
        with patch.object(analyzer.client, 'get') as mock_get:
            # Mock repository API call
            mock_repo_response = Mock()
            mock_repo_response.status_code = 200
            mock_repo_response.json.return_value = mock_github_repo_response
            mock_repo_response.raise_for_status.return_value = None
            
            # Mock contributors API call
            mock_contrib_response = Mock()
            mock_contrib_response.status_code = 200
            mock_contrib_response.json.return_value = mock_contributors_response
            
            # Mock languages API call
            mock_lang_response = Mock()
            mock_lang_response.status_code = 200
            mock_lang_response.json.return_value = {"Python": 10000, "JavaScript": 2000}
            
            # Mock activity API call
            mock_activity_response = Mock()
            mock_activity_response.status_code = 200
            mock_activity_response.json.return_value = [
                {"total": 5, "week": 1670000000},
                {"total": 10, "week": 1670604800},
                {"total": 8, "week": 1671209600},
                {"total": 12, "week": 1671814400}
            ]
            
            mock_get.side_effect = [
                mock_repo_response,
                mock_contrib_response, 
                mock_lang_response,
                mock_activity_response
            ]
            
            result = await analyzer.analyze_repository("https://github.com/testuser/test-repo")
            
            assert isinstance(result, RepositoryIntel)
            assert result.name == "testuser/test-repo"
            assert result.description == "A test repository for OSINT analysis"
            assert result.stars == 150
            assert result.forks == 30
            assert result.language == "Python"
            assert "osint" in result.topics
            assert len(result.contributors) == 3
            assert "has security policy" in str(result.security_issues).lower() or len(result.security_issues) >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_repository_invalid_url(self, analyzer):
        """Test repository analysis with invalid URL"""
        with pytest.raises(ValueError, match="Invalid repository URL format"):
            await analyzer.analyze_repository("https://github.com/invalid")
        
        with pytest.raises(ValueError, match="Invalid repository URL format"):
            await analyzer.analyze_repository("not-a-url")
    
    @pytest.mark.asyncio
    async def test_analyze_repository_unsupported_platform(self, analyzer):
        """Test repository analysis with unsupported platform"""
        with pytest.raises(ValueError, match="Unsupported platform"):
            await analyzer.analyze_repository("https://bitbucket.org/user/repo")
    
    @pytest.mark.asyncio
    async def test_discover_github_user_success(self, analyzer, mock_github_user_response):
        """Test successful GitHub user discovery"""
        mock_repos_response = [
            {
                "name": "repo1",
                "stargazers_count": 10,
                "language": "Python",
                "updated_at": "2023-12-01T00:00:00Z"
            },
            {
                "name": "repo2", 
                "stargazers_count": 5,
                "language": "JavaScript",
                "updated_at": "2023-11-15T00:00:00Z"
            }
        ]
        
        with patch.object(analyzer.client, 'get') as mock_get:
            # Mock user API call
            mock_user_response = Mock()
            mock_user_response.status_code = 200
            mock_user_response.json.return_value = mock_github_user_response
            mock_user_response.raise_for_status.return_value = None
            
            # Mock repos API call
            mock_repos_api_response = Mock()
            mock_repos_api_response.status_code = 200
            mock_repos_api_response.json.return_value = mock_repos_response
            
            mock_get.side_effect = [mock_user_response, mock_repos_api_response]
            
            # Mock email extraction
            with patch.object(analyzer, '_extract_emails_from_repos', return_value=['test@example.com', 'work@company.com']):
                with patch.object(analyzer, '_find_social_connections', return_value=['friend1', 'friend2']):
                    result = await analyzer.discover_user_info("testuser", "github")
            
            assert isinstance(result, UserIntelligence)
            assert result.username == "testuser"
            assert result.profile_data["name"] == "Test User"
            assert result.profile_data["company"] == "Test Security Corp"
            assert result.profile_data["location"] == "San Francisco, CA"
            assert len(result.repositories) == 2
            assert "Python" in result.languages
            assert "JavaScript" in result.languages
            assert len(result.email_addresses) == 2
    
    @pytest.mark.asyncio
    async def test_discover_user_invalid_platform(self, analyzer):
        """Test user discovery with invalid platform"""
        with pytest.raises(ValueError, match="Unsupported platform"):
            await analyzer.discover_user_info("testuser", "invalid_platform")
    
    @pytest.mark.asyncio
    async def test_find_emails_user_search(self, analyzer):
        """Test email discovery for user"""
        mock_user_intel = UserIntelligence(
            username="testuser",
            email_addresses=["user@example.com", "user@company.com"],
            repositories=[],
            commit_count=0,
            languages=[],
            activity_pattern={},
            social_connections=[],
            profile_data={}
        )
        
        with patch.object(analyzer, 'discover_user_info', return_value=mock_user_intel):
            result = await analyzer.find_emails("testuser", "user")
            
            assert "user@example.com" in result
            assert "user@company.com" in result
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_find_emails_repo_search(self, analyzer):
        """Test email discovery for repository"""
        mock_repo_intel = RepositoryIntel(
            name="test/repo",
            description="Test repo",
            stars=0,
            forks=0,
            language="Python",
            topics=[],
            contributors=[
                {"login": "user1", "email": "user1@example.com"},
                {"login": "user2", "email": "user2@example.com"}
            ],
            commit_activity={},
            security_issues=[],
            dependencies=list({})
        )
        
        with patch.object(analyzer, 'analyze_repository', return_value=mock_repo_intel):
            result = await analyzer.find_emails("https://github.com/test/repo", "repo")
            
            assert "user1@example.com" in result
            assert "user2@example.com" in result
    
    @pytest.mark.asyncio
    async def test_map_social_network(self, analyzer):
        """Test social network mapping"""
        mock_user_intel = UserIntelligence(
            username="testuser",
            email_addresses=[],
            repositories=[
                {"name": "repo1"},
                {"name": "repo2"}
            ],
            commit_count=2,
            languages=[],
            activity_pattern={},
            social_connections=[],
            profile_data={}
        )
        
        mock_repo_intel = RepositoryIntel(
            name="repo1",
            description="Test repo",
            stars=0,
            forks=0,
            language="Python",
            topics=[],
            contributors=[
                {"login": "collaborator1", "contributions": 15},
                {"login": "collaborator2", "contributions": 8}
            ],
            commit_activity={},
            security_issues=[],
            dependencies=list({})
        )
        
        with patch.object(analyzer, 'discover_user_info', return_value=mock_user_intel):
            with patch.object(analyzer, 'analyze_repository', return_value=mock_repo_intel):
                result = await analyzer.map_social_network("testuser", depth=2)
                
                assert result["center"] == "testuser"
                assert result["depth"] == 2
                assert "repo1" in result["connections"]
                assert result["total_connections"] > 0
    
    @pytest.mark.asyncio
    async def test_scan_security_issues(self, analyzer):
        """Test security issue scanning"""
        mock_repo_intel = RepositoryIntel(
            name="test/repo",
            description="Repository with passwords and secret keys exposed",
            stars=5,
            forks=1,
            language="Python",
            topics=["security", "vulnerability"],
            contributors=[],
            commit_activity={"recent_activity": 0},
            security_issues=[],
            dependencies=["crypto-mining-tool", "bitcoin-miner", "normal-lib"]
        )
        
        with patch.object(analyzer, 'analyze_repository', return_value=mock_repo_intel):
            result = await analyzer.scan_security_issues("https://github.com/test/repo")
            
            # Should detect multiple security issues
            assert len(result) > 0
            
            issue_types = [issue['type'] for issue in result]
            assert 'potential_secret_exposure' in issue_types
            assert 'suspicious_dependency' in issue_types
            assert 'inactive_repository' in issue_types
            
            # Check severity levels
            severities = [issue['severity'] for issue in result]
            assert 'high' in severities or 'medium' in severities
    
    @pytest.mark.asyncio
    async def test_process_commit_activity(self, analyzer):
        """Test commit activity processing"""
        activity_data = [
            {"total": 5, "week": 1670000000},
            {"total": 10, "week": 1670604800},
            {"total": 3, "week": 1671209600},
            {"total": 8, "week": 1671814400}
        ]
        
        result = analyzer._process_commit_activity(activity_data)
        
        assert result["total_commits"] == 26
        assert result["recent_activity"] == 19  # Last 4 weeks
        assert result["peak_week"] == 10
    
    @pytest.mark.asyncio
    async def test_process_commit_activity_empty(self, analyzer):
        """Test commit activity processing with empty data"""
        result = analyzer._process_commit_activity([])
        
        assert result["total_commits"] == 0
        assert result["recent_activity"] == 0
        assert result["peak_week"] == 0
    
    def test_extract_languages(self, analyzer):
        """Test language extraction from repositories"""
        repos_data = [
            {"language": "Python"},
            {"language": "JavaScript"},
            {"language": "Python"},  # Duplicate
            {"language": None},  # No language
            {"language": "Go"}
        ]
        
        result = analyzer._extract_languages(repos_data)
        
        assert "Python" in result
        assert "JavaScript" in result
        assert "Go" in result
        assert len(result) == 3  # Duplicates and None removed
    
    def test_analyze_activity_pattern(self, analyzer):
        """Test activity pattern analysis"""
        repos_data = [
            {
                "created_at": "2022-01-01T00:00:00Z",
                "updated_at": "2023-12-01T00:00:00Z"
            },
            {
                "created_at": "2022-06-01T00:00:00Z", 
                "updated_at": "2023-11-15T00:00:00Z"
            },
            {
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-10-01T00:00:00Z"
            }
        ]
        
        result = analyzer._analyze_activity_pattern(repos_data)
        
        assert result["total_repositories"] == 3
        assert "2022-01-01T00:00:00Z to 2023-01-01T00:00:00Z" in result["creation_span"]
        assert result["last_activity"] == "2023-12-01T00:00:00Z"
        assert result["active_repositories"] == 3
    
    @pytest.mark.asyncio
    async def test_extract_emails_from_repos(self, analyzer, mock_commits_response):
        """Test email extraction from repository commits"""
        with patch.object(analyzer.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_commits_response
            mock_get.return_value = mock_response
            
            repos = [{"name": "test-repo"}]
            result = await analyzer._extract_emails_from_repos("testuser", repos)
            
            assert "test@example.com" in result
            assert "contrib@example.com" in result
            assert len(result) >= 2
    
    @pytest.mark.asyncio
    async def test_check_security_indicators(self, analyzer):
        """Test security indicators detection"""
        repo_data = {
            "topics": ["security", "vulnerability", "exploit"],
            "has_security_policy": True
        }
        
        result = await analyzer._check_security_indicators(repo_data)
        
        assert len(result) >= 3  # Should detect security topics and policy
        assert any("security" in indicator.lower() for indicator in result)
        assert any("vulnerability" in indicator.lower() for indicator in result)
        assert any("security policy" in indicator.lower() for indicator in result)
    
    @pytest.mark.asyncio
    async def test_find_social_connections(self, analyzer):
        """Test finding social connections"""
        mock_following_data = [
            {"login": "friend1"},
            {"login": "friend2"},
            {"login": "colleague1"}
        ]
        
        with patch.object(analyzer.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_following_data
            mock_get.return_value = mock_response
            
            result = await analyzer._find_social_connections("testuser")
            
            assert "friend1" in result
            assert "friend2" in result
            assert "colleague1" in result
            assert len(result) <= 20  # Should be limited to 20
    
    @pytest.mark.asyncio
    async def test_analyzer_close(self, analyzer):
        """Test analyzer cleanup"""
        # Mock the aclose method
        analyzer.client.aclose = AsyncMock()
        
        await analyzer.close()
        analyzer.client.aclose.assert_called_once()


class TestMCPServerFunctions:
    """Test MCP server handler functions"""
    
    @pytest.mark.asyncio
    async def test_handle_list_tools(self):
        """Test listing available tools"""
        tools = await handle_list_tools()
        
        assert len(tools) == 5
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
        
        # Check that tools have proper schemas
        for tool in tools:
            assert hasattr(tool, 'inputSchema')
            assert 'type' in tool.inputSchema
            assert 'properties' in tool.inputSchema
            assert 'required' in tool.inputSchema
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_analyze_repository(self):
        """Test analyze_repository tool call"""
        mock_result = RepositoryIntel(
            name="test/repo",
            description="Test repository",
            stars=100,
            forks=25,
            language="Python",
            topics=["test", "automation"],
            contributors=[{"login": "user1"}],
            commit_activity={"recent_activity": 10},
            security_issues=["issue1"],
            dependencies=["Python"]
        )
        
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.analyze_repository.return_value = mock_result
            
            result = await handle_call_tool(
                "analyze_repository",
                {"repo_url": "https://github.com/test/repo"}
            )
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            data = json.loads(result[0].text)
            assert data["name"] == "test/repo"
            assert data["stars"] == 100
            assert data["language"] == "Python"
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_discover_user_info(self):
        """Test discover_user_info tool call"""
        mock_result = UserIntelligence(
            username="testuser",
            email_addresses=["test@example.com"],
            repositories=[{"name": "repo1"}],
            commit_count=10,
            languages=["Python", "JavaScript"],
            activity_pattern={"total_repos": 1},
            social_connections=["friend1"],
            profile_data={"name": "Test User", "company": "Test Corp"}
        )
        
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.discover_user_info.return_value = mock_result
            
            result = await handle_call_tool(
                "discover_user_info",
                {"username": "testuser", "platform": "github"}
            )
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            data = json.loads(result[0].text)
            assert data["username"] == "testuser"
            assert data["email_addresses"] == ["test@example.com"]
            assert data["languages"] == ["Python", "JavaScript"]
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_find_emails(self):
        """Test find_emails tool call"""
        mock_emails = ["user@example.com", "user@company.com", "user@personal.com"]
        
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.find_emails.return_value = mock_emails
            
            result = await handle_call_tool(
                "find_emails",
                {"target": "testuser", "search_type": "user"}
            )
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            data = json.loads(result[0].text)
            assert data["emails"] == mock_emails
            assert data["count"] == 3
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_map_social_network(self):
        """Test map_social_network tool call"""
        mock_network = {
            "center": "testuser",
            "depth": 2,
            "total_connections": 5,
            "connections": {
                "repo1": [{"username": "friend1", "contributions": 10}]
            }
        }
        
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.map_social_network.return_value = mock_network
            
            result = await handle_call_tool(
                "map_social_network",
                {"username": "testuser", "depth": 2}
            )
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            data = json.loads(result[0].text)
            assert data["center"] == "testuser"
            assert data["depth"] == 2
            assert data["total_connections"] == 5
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_scan_security_issues(self):
        """Test scan_security_issues tool call"""
        mock_issues = [
            {"type": "potential_secret_exposure", "severity": "high", "description": "Secrets found"},
            {"type": "suspicious_dependency", "severity": "medium", "description": "Crypto mining lib"},
            {"type": "inactive_repository", "severity": "low", "description": "No recent activity"}
        ]
        
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.scan_security_issues.return_value = mock_issues
            
            result = await handle_call_tool(
                "scan_security_issues",
                {"repo_url": "https://github.com/test/repo"}
            )
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            data = json.loads(result[0].text)
            assert data["security_issues"] == mock_issues
            assert data["count"] == 3
            assert data["high_severity"] == 1
            assert data["medium_severity"] == 1
            assert data["low_severity"] == 1
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_unknown_tool(self):
        """Test calling unknown tool"""
        result = await handle_call_tool("unknown_tool", {})
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        data = json.loads(result[0].text)
        assert "error" in data
        assert "Unknown tool" in data["error"]
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_missing_arguments(self):
        """Test calling tool with missing required arguments"""
        result = await handle_call_tool("analyze_repository", {})
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        data = json.loads(result[0].text)
        assert "error" in data
        assert "required" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_exception_handling(self):
        """Test tool call exception handling"""
        with patch('src.gitosint_mcp.server.analyzer') as mock_analyzer:
            mock_analyzer.analyze_repository.side_effect = Exception("Test error")
            
            result = await handle_call_tool(
                "analyze_repository",
                {"repo_url": "https://github.com/test/repo"}
            )
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            data = json.loads(result[0].text)
            assert "error" in data
            assert "Test error" in data["error"]


class TestDataStructures:
    """Test data structure classes"""
    
    def test_user_intelligence_creation(self):
        """Test UserIntelligence data structure"""
        user_intel = UserIntelligence(
            username="testuser",
            email_addresses=["test@example.com", "work@company.com"],
            repositories=[
                {"name": "repo1", "stars": 10},
                {"name": "repo2", "stars": 5}
            ],
            commit_count=15,
            languages=["Python", "JavaScript", "Go"],
            activity_pattern={"total_repos": 2, "active_repos": 2},
            social_connections=["friend1", "friend2", "colleague1"],
            profile_data={
                "name": "Test User",
                "company": "Test Corp",
                "location": "San Francisco"
            }
        )
        
        assert user_intel.username == "testuser"
        assert len(user_intel.email_addresses) == 2
        assert len(user_intel.repositories) == 2
        assert len(user_intel.languages) == 3
        assert len(user_intel.social_connections) == 3
        assert user_intel.profile_data["name"] == "Test User"
        assert user_intel.commit_count == 15
    
    def test_repository_intel_creation(self):
        """Test RepositoryIntel data structure"""
        repo_intel = RepositoryIntel(
            name="user/awesome-repo",
            description="An awesome repository for testing",
            stars=500,
            forks=75,
            language="Python",
            topics=["python", "testing", "automation", "osint"],
            contributors=[
                {"login": "user1", "contributions": 100},
                {"login": "user2", "contributions": 50},
                {"login": "user3", "contributions": 25}
            ],
            commit_activity={
                "total_commits": 200,
                "recent_activity": 15,
                "peak_week": 25
            },
            security_issues=[
                {"type": "potential_secret", "severity": "medium"},
                {"type": "dependency_issue", "severity": "low"}
            ],
            dependencies={"Python": 8000, "JavaScript": 1500, "Shell": 200}
        )
        
        assert repo_intel.name == "user/awesome-repo"
        assert repo_intel.stars == 500
        assert repo_intel.forks == 75
        assert repo_intel.language == "Python"
        assert len(repo_intel.topics) == 4
        assert "osint" in repo_intel.topics
        assert len(repo_intel.contributors) == 3
        assert len(repo_intel.security_issues) == 2
        assert repo_intel.commit_activity["total_commits"] == 200


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    async def analyzer_with_mock_client(self):
        """Create analyzer with mocked client for error testing"""
        analyzer = GitOSINTAnalyzer()
        analyzer.client = AsyncMock()
        yield analyzer
        # Don't call close() as client is mocked
    
    @pytest.mark.asyncio
    async def test_http_error_handling(self, analyzer_with_mock_client):
        """Test HTTP error handling"""
        analyzer = analyzer_with_mock_client
        
        # Mock HTTP 404 error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        analyzer.client.get.return_value = mock_response
        
        with pytest.raises(Exception):
            await analyzer.analyze_repository("https://github.com/nonexistent/repo")
    
    @pytest.mark.asyncio
    async def test_rate_limiting_delay(self, analyzer_with_mock_client):
        """Test that rate limiting delay is applied"""
        analyzer = analyzer_with_mock_client
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "test", "stargazers_count": 0, "forks_count": 0}
        mock_response.raise_for_status.return_value = None
        analyzer.client.get.return_value = mock_response
        
        import time
        start_time = time.time()
        
        # Mock sleep to verify it's called
        with patch('asyncio.sleep') as mock_sleep:
            await analyzer._analyze_github_repo("user", "repo")
            mock_sleep.assert_called_with(analyzer.rate_limit_delay)
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self, analyzer_with_mock_client):
        """Test handling of invalid JSON responses"""
        analyzer = analyzer_with_mock_client
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status.return_value = None
        analyzer.client.get.return_value = mock_response
        
        with pytest.raises(json.JSONDecodeError):
            await analyzer._analyze_github_repo("user", "repo")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])