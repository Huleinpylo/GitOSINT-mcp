"""
Unit Tests for Repository Analyzer

Tests the repository analysis functionality for the MCP addon.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from gitosint_mcp.analyzers.repository import RepositoryAnalyzer, RepositoryInfo, ContributorInfo
from gitosint_mcp.config import MCPConfig as Config

pytestmark = pytest.mark.unit

class TestRepositoryAnalyzer:
    """Test repository analyzer for MCP addon."""
    
    @pytest.fixture
    def analyzer(self, test_config):
        """Create repository analyzer instance."""
        return RepositoryAnalyzer(test_config)
    
    def test_parse_repository_url_github(self, analyzer):
        """Test GitHub repository URL parsing."""
        url = "https://github.com/microsoft/vscode"
        platform, owner, repo = analyzer._parse_repository_url(url)
        
        assert platform == "github.com"
        assert owner == "microsoft"
        assert repo == "vscode"
    
    def test_parse_repository_url_with_git_suffix(self, analyzer):
        """Test repository URL parsing with .git suffix."""
        url = "https://github.com/microsoft/vscode.git"
        platform, owner, repo = analyzer._parse_repository_url(url)
        
        assert platform == "github.com"
        assert owner == "microsoft"
        assert repo == "vscode"
    
    def test_parse_repository_url_gitlab(self, analyzer):
        """Test GitLab repository URL parsing."""
        url = "https://gitlab.com/gitlab-org/gitlab"
        platform, owner, repo = analyzer._parse_repository_url(url)
        
        assert platform == "gitlab.com"
        assert owner == "gitlab-org"
        assert repo == "gitlab"
    
    def test_parse_invalid_repository_url(self, analyzer):
        """Test parsing invalid repository URL."""
        with pytest.raises(ValueError, match="Invalid repository URL format"):
            analyzer._parse_repository_url("https://github.com/invalid")
    
    def test_parse_unsupported_platform(self, analyzer):
        """Test parsing URL from unsupported platform."""
        with pytest.raises(ValueError, match="Unsupported platform"):
            analyzer._parse_repository_url("https://unsupported.com/user/repo")
    
    @pytest.mark.asyncio
    async def test_analyze_basic(self, analyzer, mock_github_api):
        """Test basic repository analysis."""
        with patch.object(analyzer, '_get_repository_info') as mock_repo_info, \
             patch.object(analyzer, '_get_contributors') as mock_contributors, \
             patch.object(analyzer, '_get_languages') as mock_languages:
            
            # Setup mocks
            mock_repo_info.return_value = RepositoryInfo(
                name="test-repo",
                owner="testuser",
                full_name="testuser/test-repo",
                description="Test repository",
                primary_language="Python",
                languages={},
                stars=50,
                forks=10,
                watchers=45,
                size_kb=1024,
                created_at="2020-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
                pushed_at="2024-01-01T00:00:00Z",
                is_fork=False,
                is_archived=False,
                is_private=False,
                default_branch="main",
                topics=["python", "testing"],
                license_name="MIT",
                homepage=None
            )
            
            mock_contributors.return_value = [
                ContributorInfo(
                    login="testuser",
                    id=12345,
                    type="User",
                    contributions=50,
                    avatar_url="https://github.com/images/testuser",
                    profile_url="https://github.com/testuser"
                )
            ]
            
            mock_languages.return_value = {"Python": 75.0, "JavaScript": 25.0}
            
            # Perform analysis
            result = await analyzer.analyze(
                "https://github.com/testuser/test-repo",
                depth="basic"
            )
            
            # Verify results
            assert result["repository_url"] == "https://github.com/testuser/test-repo"
            assert result["platform"] == "github.com"
            assert result["analysis_depth"] == "basic"
            assert result["basic_info"]["name"] == "test-repo"
            assert len(result["contributors"]) == 1
            assert result["languages"]["Python"] == 75.0
    
    @pytest.mark.asyncio
    async def test_analyze_blocked_domain(self, test_config):
        """Test analysis with blocked domain."""
        test_config.security.allowed_domains = ["github.com"]  # Only allow GitHub
        analyzer = RepositoryAnalyzer(test_config)
        
        with pytest.raises(ValueError, match="is not allowed by configuration"):
            await analyzer.analyze("https://malicious.com/user/repo")
    
    def test_repository_info_dataclass(self):
        """Test RepositoryInfo dataclass."""
        repo_info = RepositoryInfo(
            name="test",
            owner="user",
            full_name="user/test",
            description="Test repo",
            primary_language="Python",
            languages={"Python": 100.0},
            stars=10,
            forks=2,
            watchers=8,
            size_kb=512,
            created_at="2020-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            pushed_at="2024-01-01T00:00:00Z",
            is_fork=False,
            is_archived=False,
            is_private=False,
            default_branch="main",
            topics=["python"],
            license_name="MIT",
            homepage="https://example.com"
        )
        
        assert repo_info.name == "test"
        assert repo_info.primary_language == "Python"
        assert repo_info.stars == 10
    
    def test_contributor_info_dataclass(self):
        """Test ContributorInfo dataclass."""
        contributor = ContributorInfo(
            login="testuser",
            id=12345,
            type="User",
            contributions=25,
            avatar_url="https://avatar.url",
            profile_url="https://profile.url",
            name="Test User",
            email="test@example.com"
        )
        
        assert contributor.login == "testuser"
        assert contributor.contributions == 25
        assert contributor.name == "Test User"
        assert contributor.email == "test@example.com"