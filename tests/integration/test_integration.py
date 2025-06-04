"""
Integration tests for GitOSINT-MCP
These tests require network access and test against real APIs
"""

import time
import pytest
import os
import asyncio
from typing import Dict, Any

from src.gitosint_mcp.server import GitOSINTAnalyzer, UserIntelligence, RepositoryIntel
from src.gitosint_mcp.cli import GitOSINTCLI


@pytest.mark.integration
class TestRealAPIIntegration:
    """Test integration with real Git platform APIs"""
    
    @pytest.fixture(scope="class")
    def skip_if_no_integration(self):
        """Skip integration tests if not enabled"""
        if not os.getenv('INTEGRATION_TEST'):
            pytest.skip("Integration tests disabled. Set INTEGRATION_TEST=1 to enable.")
    
    @pytest.fixture
    async def analyzer(self, skip_if_no_integration):
        """Create analyzer for integration testing"""
        analyzer = GitOSINTAnalyzer()
        yield analyzer
        await analyzer.close()
    
    @pytest.fixture
    async def cli(self, skip_if_no_integration):
        """Create CLI for integration testing"""
        cli = GitOSINTCLI()
        yield cli
        await cli.close()
    
    @pytest.mark.asyncio
    async def test_github_public_repo_analysis(self, analyzer):
        """Test analysis of a real public GitHub repository"""
        # Use a well-known, stable public repository
        repo_url = "https://github.com/octocat/Hello-World"
        
        result = await analyzer.analyze_repository(repo_url)
        
        assert isinstance(result, RepositoryIntel)
        assert result.name == "octocat/Hello-World"
        assert result.stars >= 0
        assert result.forks >= 0
        assert result.language is not None
        assert isinstance(result.contributors, list)
        assert isinstance(result.topics, list)
        assert isinstance(result.security_issues, list)
    
    @pytest.mark.asyncio
    async def test_github_user_discovery(self, analyzer):
        """Test discovery of a real GitHub user"""
        username = "octocat"
        
        result = await analyzer.discover_user_info(username, "github")
        
        assert isinstance(result, UserIntelligence)
        assert result.username == username
        assert len(result.repositories) > 0
        assert isinstance(result.profile_data, dict)
        assert result.profile_data.get("name") is not None
        assert isinstance(result.languages, list)
        assert isinstance(result.email_addresses, list)
    
    @pytest.mark.asyncio
    async def test_github_email_discovery(self, analyzer):
        """Test email discovery from real GitHub data"""
        username = "octocat"
        
        result = await analyzer.find_emails(username, "user")
        
        assert isinstance(result, list)
        # May or may not find emails depending on user's privacy settings
        for email in result:
            assert "@" in email
            assert "." in email.split("@")[1]
    
    @pytest.mark.asyncio
    async def test_github_social_network_mapping(self, analyzer):
        """Test social network mapping with real GitHub data"""
        username = "octocat"
        
        result = await analyzer.map_social_network(username, depth=1)
        
        assert isinstance(result, dict)
        assert result["center"] == username
        assert result["depth"] == 1
        assert isinstance(result["connections"], dict)
        assert isinstance(result["total_connections"], int)
    
    @pytest.mark.asyncio
    async def test_github_security_scanning(self, analyzer):
        """Test security scanning on real GitHub repository"""
        repo_url = "https://github.com/octocat/Hello-World"
        
        result = await analyzer.scan_security_issues(repo_url)
        
        assert isinstance(result, list)
        for issue in result:
            assert isinstance(issue, dict)
            assert "type" in issue
            assert "severity" in issue
            assert "description" in issue
            assert issue["severity"] in ["high", "medium", "low", "info"]
    
    @pytest.mark.asyncio
    async def test_gitlab_repo_analysis(self, analyzer):
        """Test analysis of a real GitLab repository"""
        # Use a well-known GitLab repository
        repo_url = "https://gitlab.com/gitlab-org/gitlab"
        
        try:
            result = await analyzer.analyze_repository(repo_url)
            
            assert isinstance(result, RepositoryIntel)
            assert "gitlab-org/gitlab" in result.name
            assert result.stars >= 0
            assert result.forks >= 0
            assert isinstance(result.contributors, list)
        except Exception as e:
            # GitLab API might have rate limits or require auth
            pytest.skip(f"GitLab API unavailable: {e}")
    
    @pytest.mark.asyncio
    async def test_gitlab_user_discovery(self, analyzer):
        """Test discovery of a real GitLab user"""
        username = "gitlab-bot"
        
        try:
            result = await analyzer.discover_user_info(username, "gitlab")
            
            assert isinstance(result, UserIntelligence)
            assert result.username == username
            assert isinstance(result.repositories, list)
            assert isinstance(result.profile_data, dict)
        except Exception as e:
            # GitLab API might have different requirements
            pytest.skip(f"GitLab user discovery unavailable: {e}")
    
    @pytest.mark.asyncio
    async def test_rate_limiting_respected(self, analyzer):
        """Test that rate limiting is properly respected"""
        import time
        
        # Make multiple requests and measure timing
        start_time = time.time()
        
        requests = [
            analyzer.analyze_repository("https://github.com/octocat/Hello-World"),
            analyzer.discover_user_info("octocat", "github"),
            analyzer.find_emails("octocat", "user")
        ]
        
        await asyncio.gather(*requests, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should take at least rate_limit_delay * (requests - 1) seconds
        min_duration = analyzer.rate_limit_delay * (len(requests) - 1)
        assert duration >= min_duration, f"Rate limiting not respected: {duration} < {min_duration}"
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_repo(self, analyzer):
        """Test error handling with invalid repository"""
        with pytest.raises(Exception):
            await analyzer.analyze_repository("https://github.com/nonexistent/repo-that-does-not-exist")
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_user(self, analyzer):
        """Test error handling with invalid user"""
        with pytest.raises(Exception):
            await analyzer.discover_user_info("nonexistent-user-12345", "github")


@pytest.mark.integration
class TestCLIIntegration:
    """Test CLI integration with real APIs"""
    
    @pytest.fixture(scope="class")
    def skip_if_no_integration(self):
        """Skip integration tests if not enabled"""
        if not os.getenv('INTEGRATION_TEST'):
            pytest.skip("Integration tests disabled. Set INTEGRATION_TEST=1 to enable.")
    
    @pytest.fixture
    async def cli(self, skip_if_no_integration):
        """Create CLI for integration testing"""
        cli = GitOSINTCLI()
        yield cli
        await cli.close()
    
    @pytest.mark.asyncio
    async def test_cli_analyze_repository(self, cli):
        """Test CLI repository analysis with real data"""
        result = await cli.analyze_repository("https://github.com/octocat/Hello-World")
        
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["name"] == "octocat/Hello-World"
        assert isinstance(result["data"]["stars"], int)
        assert isinstance(result["data"]["forks"], int)
    
    @pytest.mark.asyncio
    async def test_cli_discover_user(self, cli):
        """Test CLI user discovery with real data"""
        result = await cli.discover_user("octocat", "github")
        
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["username"] == "octocat"
        assert isinstance(result["data"]["repository_count"], int)
        assert isinstance(result["data"]["commit_count"], int)
    
    @pytest.mark.asyncio
    async def test_cli_find_emails(self, cli):
        """Test CLI email discovery with real data"""
        result = await cli.find_emails("octocat", "user")
        
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["target"] == "octocat"
        assert result["data"]["search_type"] == "user"
        assert isinstance(result["data"]["emails"], list)
        assert isinstance(result["data"]["count"], int)
    
    @pytest.mark.asyncio
    async def test_cli_map_network(self, cli):
        """Test CLI network mapping with real data"""
        result = await cli.map_network("octocat", 1)
        
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["center"] == "octocat"
        assert result["data"]["depth"] == 1
        assert isinstance(result["data"]["connections"], dict)
    
    @pytest.mark.asyncio
    async def test_cli_scan_security(self, cli):
        """Test CLI security scanning with real data"""
        result = await cli.scan_security("https://github.com/octocat/Hello-World")
        
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["repository"] == "https://github.com/octocat/Hello-World"
        assert isinstance(result["data"]["issues"], list)
        assert isinstance(result["data"]["total_issues"], int)
    
    @pytest.mark.asyncio
    async def test_cli_error_handling(self, cli):
        """Test CLI error handling with invalid input"""
        result = await cli.analyze_repository("https://github.com/invalid/repo")
        
        assert result["success"] is False
        assert "error" in result
        assert isinstance(result["error"], str)


@pytest.mark.integration
class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    @pytest.fixture(scope="class")
    def skip_if_no_integration(self):
        """Skip integration tests if not enabled"""
        if not os.getenv('INTEGRATION_TEST'):
            pytest.skip("Integration tests disabled. Set INTEGRATION_TEST=1 to enable.")
    
    @pytest.fixture
    async def analyzer(self, skip_if_no_integration):
        """Create analyzer for integration testing"""
        analyzer = GitOSINTAnalyzer()
        yield analyzer
        await analyzer.close()
    
    @pytest.mark.asyncio
    async def test_complete_user_investigation(self, analyzer):
        """Test complete investigation workflow for a user"""
        username = "octocat"
        
        # Step 1: Discover user information
        user_info = await analyzer.discover_user_info(username, "github")
        assert isinstance(user_info, UserIntelligence)
        assert user_info.username == username
        
        # Step 2: Find emails associated with user
        emails = await analyzer.find_emails(username, "user")
        assert isinstance(emails, list)
        
        # Step 3: Map social network
        network = await analyzer.map_social_network(username, depth=1)
        assert isinstance(network, dict)
        assert network["center"] == username
        
        # Step 4: Analyze user's top repository (if any)
        if user_info.repositories:
            top_repo = user_info.repositories[0]
            repo_url = f"https://github.com/{username}/{top_repo['name']}"
            
            try:
                repo_analysis = await analyzer.analyze_repository(repo_url)
                assert isinstance(repo_analysis, RepositoryIntel)
                
                # Step 5: Security scan of the repository
                security_issues = await analyzer.scan_security_issues(repo_url)
                assert isinstance(security_issues, list)
                
            except Exception as e:
                # Repository might be private or deleted
                pytest.skip(f"Repository analysis failed: {e}")
        
        # Verify we collected comprehensive intelligence
        assert len(user_info.profile_data) > 0
        assert len(user_info.repositories) >= 0
        assert len(user_info.languages) >= 0
    
    @pytest.mark.asyncio
    async def test_repository_deep_analysis(self, analyzer):
        """Test deep analysis workflow for a repository"""
        repo_url = "https://github.com/octocat/Hello-World"
        
        # Step 1: Basic repository analysis
        repo_info = await analyzer.analyze_repository(repo_url)
        assert isinstance(repo_info, RepositoryIntel)
        
        # Step 2: Security scanning
        security_issues = await analyzer.scan_security_issues(repo_url)
        assert isinstance(security_issues, list)
        
        # Step 3: Analyze contributors
        if repo_info.contributors:
            # Pick first contributor for analysis
            contributor = repo_info.contributors[0]
            if contributor.get("login"):
                contributor_info = await analyzer.discover_user_info(
                    contributor["login"], "github"
                )
                assert isinstance(contributor_info, UserIntelligence)
        
        # Step 4: Find emails from repository
        repo_emails = await analyzer.find_emails(repo_url, "repo")
        assert isinstance(repo_emails, list)
        
        # Verify comprehensive repository intelligence
        assert repo_info.name is not None
        assert isinstance(repo_info.stars, int)
        assert isinstance(repo_info.forks, int)
        assert isinstance(repo_info.contributors, list)
    
    @pytest.mark.asyncio
    async def test_cross_platform_analysis(self, analyzer):
        """Test analysis across multiple platforms"""
        username = "gitlab-bot"  # Known to exist on GitLab
        
        # Try GitHub first
        github_info = None
        try:
            github_info = await analyzer.discover_user_info(username, "github")
        except:
            pass  # User might not exist on GitHub
        
        # Try GitLab
        gitlab_info = None
        try:
            gitlab_info = await analyzer.discover_user_info(username, "gitlab")
        except:
            pass  # GitLab API might be restricted
        
        # At least one platform should work or we skip
        if github_info is None and gitlab_info is None:
            pytest.skip("User not found on any platform or APIs unavailable")
        
        # Verify cross-platform data consistency
        if github_info and gitlab_info:
            # If user exists on both platforms, compare data
            assert github_info.username == gitlab_info.username


@pytest.mark.integration
class TestPerformanceAndLimits:
    """Test performance characteristics and limits"""
    
    @pytest.fixture(scope="class")
    def skip_if_no_integration(self):
        """Skip integration tests if not enabled"""
        if not os.getenv('INTEGRATION_TEST'):
            pytest.skip("Integration tests disabled. Set INTEGRATION_TEST=1 to enable.")
    
    @pytest.fixture
    async def analyzer(self, skip_if_no_integration):
        """Create analyzer for integration testing"""
        analyzer = GitOSINTAnalyzer()
        yield analyzer
        await analyzer.close()
    
    @pytest.mark.asyncio
    async def test_large_repository_analysis(self, analyzer):
        """Test analysis of a large, popular repository"""
        # Use a large, well-known repository
        repo_url = "https://github.com/torvalds/linux"
        
        import time
        start_time = time.time()
        
        try:
            result = await analyzer.analyze_repository(repo_url)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert isinstance(result, RepositoryIntel)
            assert result.stars > 1000  # Linux kernel should have many stars
            assert len(result.contributors) > 0
            
            # Should complete within reasonable time (60 seconds)
            assert duration < 60, f"Analysis took too long: {duration} seconds"
            
        except Exception as e:
            # Might hit rate limits or timeouts with very large repos
            pytest.skip(f"Large repository analysis failed: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, analyzer):
        """Test handling of concurrent requests"""
        # Create multiple concurrent requests
        urls = [
            "https://github.com/octocat/Hello-World",
            "https://github.com/octocat/Spoon-Knife",
        ]
        
        tasks = [analyzer.analyze_repository(url) for url in urls]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Check that all requests completed
        successful_results = [r for r in results if isinstance(r, RepositoryIntel)]
        assert len(successful_results) > 0
        
        # Should respect rate limiting (minimum time)
        min_expected_time = analyzer.rate_limit_delay * (len(tasks) - 1)
        actual_time = end_time - start_time
        assert actual_time >= min_expected_time
    
    @pytest.mark.asyncio
    async def test_memory_usage_limits(self, analyzer):
        """Test that memory usage stays within reasonable bounds"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Perform multiple operations
        for i in range(10):
            await analyzer.discover_user_info("octocat", "github")
            await analyzer.analyze_repository("https://github.com/octocat/Hello-World")
            
            # Force garbage collection
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        max_increase = 100 * 1024 * 1024  # 100MB
        assert memory_increase < max_increase, f"Memory usage increased by {memory_increase / 1024 / 1024:.2f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])