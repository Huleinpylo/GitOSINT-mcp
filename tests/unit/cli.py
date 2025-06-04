"""
Test suite for GitOSINT-MCP CLI module
"""

import pytest
import asyncio
import json
import sys
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from io import StringIO

from src.gitosint_mcp.cli import GitOSINTCLI, main, print_json_result, print_formatted_result
from src.gitosint_mcp.server import UserIntelligence, RepositoryIntel


class TestGitOSINTCLI:
    """Test GitOSINT CLI class"""
    
    @pytest.fixture
    async def cli(self):
        """Create CLI instance for testing"""
        cli = GitOSINTCLI()
        # Mock the analyzer to avoid actual HTTP calls
        cli.analyzer = AsyncMock()
        yield cli
        await cli.close()
    
    @pytest.mark.asyncio
    async def test_cli_initialization(self):
        """Test CLI initialization"""
        cli = GitOSINTCLI()
        assert cli.analyzer is not None
        await cli.close()
    
    @pytest.mark.asyncio
    async def test_analyze_repository_success(self, cli):
        """Test successful repository analysis via CLI"""
        mock_result = RepositoryIntel(
            name="test/repo",
            description="Test repository",
            stars=100,
            forks=25,
            language="Python",
            topics=["test", "automation"],
            contributors=[
                {"login": "user1", "contributions": 50},
                {"login": "user2", "contributions": 30}
            ],
            commit_activity={"recent_activity": 10, "peak_week": 15},
            security_issues=["issue1", "issue2"],
            dependencies={"Python": 1000}
        )
        
        cli.analyzer.analyze_repository.return_value = mock_result
        
        result = await cli.analyze_repository("https://github.com/test/repo")
        
        assert result["success"] is True
        assert result["data"]["name"] == "test/repo"
        assert result["data"]["stars"] == 100
        assert result["data"]["contributors_count"] == 2
        assert result["data"]["security_issues_count"] == 2
    
    @pytest.mark.asyncio
    async def test_analyze_repository_failure(self, cli):
        """Test repository analysis failure via CLI"""
        cli.analyzer.analyze_repository.side_effect = Exception("Repository not found")
        
        result = await cli.analyze_repository("https://github.com/invalid/repo")
        
        assert result["success"] is False
        assert "Repository not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_repository_missing_url(self, cli):
        """Test repository analysis with missing URL"""
        result = await cli.analyze_repository("")
        
        assert result["success"] is False
        assert "required" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_discover_user_success(self, cli):
        """Test successful user discovery via CLI"""
        mock_result = UserIntelligence(
            username="testuser",
            email_addresses=["test@example.com", "work@company.com"],
            repositories=[
                {"name": "repo1", "stars": 10},
                {"name": "repo2", "stars": 5}
            ],
            commit_count=25,
            languages=["Python", "JavaScript"],
            activity_pattern={"total_repos": 2},
            social_connections=["friend1", "friend2"],
            profile_data={
                "name": "Test User",
                "company": "Test Corp",
                "location": "San Francisco"
            }
        )
        
        cli.analyzer.discover_user_info.return_value = mock_result
        
        result = await cli.discover_user("testuser", "github")
        
        assert result["success"] is True
        assert result["data"]["username"] == "testuser"
        assert result["data"]["repository_count"] == 2
        assert result["data"]["commit_count"] == 25
        assert len(result["data"]["languages"]) == 2
        assert len(result["data"]["social_connections"]) == 2
    
    @pytest.mark.asyncio
    async def test_discover_user_failure(self, cli):
        """Test user discovery failure via CLI"""
        cli.analyzer.discover_user_info.side_effect = Exception("User not found")
        
        result = await cli.discover_user("nonexistent", "github")
        
        assert result["success"] is False
        assert "User not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_discover_user_missing_username(self, cli):
        """Test user discovery with missing username"""
        result = await cli.discover_user("", "github")
        
        assert result["success"] is False
        assert "required" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_find_emails_success(self, cli):
        """Test successful email discovery via CLI"""
        mock_emails = [
            "user@example.com",
            "user@company.com", 
            "personal@gmail.com"
        ]
        
        cli.analyzer.find_emails.return_value = mock_emails
        
        result = await cli.find_emails("testuser", "user")
        
        assert result["success"] is True
        assert result["data"]["target"] == "testuser"
        assert result["data"]["search_type"] == "user"
        assert result["data"]["emails"] == mock_emails
        assert result["data"]["count"] == 3
    
    @pytest.mark.asyncio
    async def test_find_emails_empty_result(self, cli):
        """Test email discovery with no results"""
        cli.analyzer.find_emails.return_value = []
        
        result = await cli.find_emails("testuser", "user")
        
        assert result["success"] is True
        assert result["data"]["count"] == 0
        assert result["data"]["emails"] == []
    
    @pytest.mark.asyncio
    async def test_find_emails_failure(self, cli):
        """Test email discovery failure via CLI"""
        cli.analyzer.find_emails.side_effect = Exception("API error")
        
        result = await cli.find_emails("testuser", "user")
        
        assert result["success"] is False
        assert "API error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_map_network_success(self, cli):
        """Test successful network mapping via CLI"""
        mock_network = {
            "center": "testuser",
            "depth": 2,
            "total_connections": 8,
            "connections": {
                "repo1": [
                    {"username": "collaborator1", "contributions": 15},
                    {"username": "collaborator2", "contributions": 8}
                ],
                "repo2": [
                    {"username": "collaborator3", "contributions": 12}
                ]
            }
        }
        
        cli.analyzer.map_social_network.return_value = mock_network
        
        result = await cli.map_network("testuser", 2)
        
        assert result["success"] is True
        assert result["data"]["center"] == "testuser"
        assert result["data"]["depth"] == 2
        assert result["data"]["total_connections"] == 8
        assert "repo1" in result["data"]["connections"]
    
    @pytest.mark.asyncio
    async def test_map_network_failure(self, cli):
        """Test network mapping failure via CLI"""
        cli.analyzer.map_social_network.side_effect = Exception("Network error")
        
        result = await cli.map_network("testuser", 2)
        
        assert result["success"] is False
        assert "Network error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_scan_security_success(self, cli):
        """Test successful security scanning via CLI"""
        mock_issues = [
            {"type": "potential_secret_exposure", "severity": "high", "description": "API key found"},
            {"type": "suspicious_dependency", "severity": "medium", "description": "Crypto miner"},
            {"type": "inactive_repository", "severity": "low", "description": "No recent commits"},
            {"type": "weak_authentication", "severity": "high", "description": "No 2FA"}
        ]
        
        cli.analyzer.scan_security_issues.return_value = mock_issues
        
        result = await cli.scan_security("https://github.com/test/repo")
        
        assert result["success"] is True
        assert result["data"]["repository"] == "https://github.com/test/repo"
        assert result["data"]["total_issues"] == 4
        assert result["data"]["high_severity"] == 2
        assert result["data"]["medium_severity"] == 1
        assert result["data"]["low_severity"] == 1
        assert len(result["data"]["issues"]) == 4
    
    @pytest.mark.asyncio
    async def test_scan_security_no_issues(self, cli):
        """Test security scanning with no issues found"""
        cli.analyzer.scan_security_issues.return_value = []
        
        result = await cli.scan_security("https://github.com/test/repo")
        
        assert result["success"] is True
        assert result["data"]["total_issues"] == 0
        assert result["data"]["high_severity"] == 0
        assert result["data"]["medium_severity"] == 0
        assert result["data"]["low_severity"] == 0
    
    @pytest.mark.asyncio
    async def test_scan_security_failure(self, cli):
        """Test security scanning failure via CLI"""
        cli.analyzer.scan_security_issues.side_effect = Exception("Scan failed")
        
        result = await cli.scan_security("https://github.com/test/repo")
        
        assert result["success"] is False
        assert "Scan failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_cli_close(self, cli):
        """Test CLI cleanup"""
        cli.analyzer.close = AsyncMock()
        
        await cli.close()
        cli.analyzer.close.assert_called_once()


class TestCLIOutputFormatting:
    """Test CLI output formatting functions"""
    
    def test_print_json_result_pretty(self):
        """Test pretty JSON output formatting"""
        result = {
            "success": True,
            "data": {
                "name": "test/repo",
                "stars": 100
            }
        }
        
        with patch('builtins.print') as mock_print:
            print_json_result(result, pretty=False)
            
            mock_print.assert_called_once()
            printed_text = mock_print.call_args[0][0]
            assert '{"success":true,"data":{"name":"test/repo"}}' in printed_text.replace(' ', '')
    
    def test_print_formatted_result_analyze_repo(self):
        """Test formatted output for repository analysis"""
        result = {
            "success": True,
            "data": {
                "name": "test/awesome-repo",
                "description": "An awesome test repository",
                "stars": 250,
                "forks": 45,
                "language": "Python",
                "topics": ["python", "testing", "automation"],
                "contributors_count": 8,
                "security_issues_count": 2
            }
        }
        
        with patch('builtins.print') as mock_print:
            print_formatted_result(result, "analyze-repo")
            
            # Check that multiple print calls were made with expected content
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            combined_output = ' '.join(print_calls)
            
            assert "📊 Repository Analysis: test/awesome-repo" in combined_output
            assert "📝 Description: An awesome test repository" in combined_output
            assert "⭐ Stars: 250" in combined_output
            assert "🍴 Forks: 45" in combined_output
            assert "💻 Language: Python" in combined_output
            assert "🏷️  Topics: python, testing, automation" in combined_output
            assert "👥 Contributors: 8" in combined_output
            assert "🔒 Security Issues: 2" in combined_output
    
    def test_print_formatted_result_discover_user(self):
        """Test formatted output for user discovery"""
        result = {
            "success": True,
            "data": {
                "username": "testuser",
                "email_addresses": ["test@example.com", "work@company.com"],
                "repository_count": 15,
                "languages": ["Python", "JavaScript", "Go"],
                "social_connections": ["friend1", "friend2", "colleague"],
                "profile_data": {
                    "name": "Test User",
                    "company": "Test Corp",
                    "location": "San Francisco, CA"
                }
            }
        }
        
        with patch('builtins.print') as mock_print:
            print_formatted_result(result, "discover-user")
            
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            combined_output = ' '.join(print_calls)
            
            assert "👤 User Profile: testuser" in combined_output
            assert "📧 Email Addresses: 2" in combined_output
            assert "📂 Repositories: 15" in combined_output
            assert "💻 Languages: Python, JavaScript, Go" in combined_output
            assert "🌐 Social Connections: 3" in combined_output
            assert "🏷️  Name: Test User" in combined_output
            assert "🏢 Company: Test Corp" in combined_output
            assert "📍 Location: San Francisco, CA" in combined_output
    
    def test_print_formatted_result_find_emails(self):
        """Test formatted output for email discovery"""
        result = {
            "success": True,
            "data": {
                "target": "testuser",
                "search_type": "user",
                "count": 3,
                "emails": ["user@example.com", "user@company.com", "personal@gmail.com"]
            }
        }
        
        with patch('builtins.print') as mock_print:
            print_formatted_result(result, "find-emails")
            
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            combined_output = ' '.join(print_calls)
            
            assert "📧 Email Discovery for: testuser" in combined_output
            assert "🔍 Search Type: user" in combined_output
            assert "📊 Found 3 email(s):" in combined_output
            assert "• user@example.com" in combined_output
            assert "• user@company.com" in combined_output
            assert "• personal@gmail.com" in combined_output
    
    def test_print_formatted_result_map_network(self):
        """Test formatted output for network mapping"""
        result = {
            "success": True,
            "data": {
                "center": "testuser",
                "total_connections": 12,
                "depth": 2,
                "connections": {
                    "repo1": [{"username": "friend1"}, {"username": "friend2"}],
                    "repo2": [{"username": "colleague1"}]
                }
            }
        }
        
        with patch('builtins.print') as mock_print:
            print_formatted_result(result, "map-network")
            
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            combined_output = ' '.join(print_calls)
            
            assert "🕸️  Social Network Map for: testuser" in combined_output
            assert "📊 Total Connections: 12" in combined_output
            assert "📏 Depth: 2" in combined_output
            assert "📂 repo1: 2 collaborators" in combined_output
            assert "📂 repo2: 1 collaborators" in combined_output
    
    def test_print_formatted_result_scan_security(self):
        """Test formatted output for security scanning"""
        result = {
            "success": True,
            "data": {
                "repository": "https://github.com/test/repo",
                "total_issues": 4,
                "high_severity": 2,
                "medium_severity": 1,
                "low_severity": 1,
                "issues": [
                    {"type": "potential_secret_exposure", "severity": "high", "description": "API key found"},
                    {"type": "weak_authentication", "severity": "high", "description": "No 2FA enabled"},
                    {"type": "suspicious_dependency", "severity": "medium", "description": "Crypto mining lib"},
                    {"type": "inactive_repository", "severity": "low", "description": "No recent activity"}
                ]
            }
        }
        
        with patch('builtins.print') as mock_print:
            print_formatted_result(result, "scan-security")
            
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            combined_output = ' '.join(print_calls)
            
            assert "🔒 Security Scan: https://github.com/test/repo" in combined_output
            assert "📊 Total Issues: 4" in combined_output
            assert "🔴 High Severity: 2" in combined_output
            assert "🟡 Medium Severity: 1" in combined_output
            assert "🟢 Low Severity: 1" in combined_output
            assert "🔴 potential_secret_exposure: API key found" in combined_output
            assert "🔴 weak_authentication: No 2FA enabled" in combined_output
            assert "🟡 suspicious_dependency: Crypto mining lib" in combined_output
            assert "🟢 inactive_repository: No recent activity" in combined_output
    
    def test_print_formatted_result_error(self):
        """Test formatted output for error results"""
        result = {
            "success": False,
            "error": "Repository not found"
        }
        
        with patch('builtins.print') as mock_print:
            print_formatted_result(result, "analyze-repo")
            
            mock_print.assert_called_once_with("❌ Error: Repository not found")


class TestCLIMainFunction:
    """Test CLI main function and argument parsing"""
    
    @pytest.mark.asyncio
    async def test_main_analyze_repo_command(self):
        """Test main function with analyze-repo command"""
        test_args = ["gitosint-mcp", "analyze-repo", "https://github.com/test/repo"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('src.gitosint_mcp.cli.GitOSINTCLI') as mock_cli_class:
                mock_cli = AsyncMock()
                mock_cli.analyze_repository.return_value = {"success": True, "data": {"name": "test/repo"}}
                mock_cli_class.return_value = mock_cli
                
                with patch('src.gitosint_mcp.cli.print_formatted_result') as mock_print:
                    await main()
                    
                    mock_cli.analyze_repository.assert_called_once_with("https://github.com/test/repo")
                    mock_print.assert_called_once()
                    mock_cli.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_discover_user_command(self):
        """Test main function with discover-user command"""
        test_args = ["gitosint-mcp", "discover-user", "testuser", "--platform", "github"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('src.gitosint_mcp.cli.GitOSINTCLI') as mock_cli_class:
                mock_cli = AsyncMock()
                mock_cli.discover_user.return_value = {"success": True, "data": {"username": "testuser"}}
                mock_cli_class.return_value = mock_cli
                
                with patch('src.gitosint_mcp.cli.print_formatted_result') as mock_print:
                    await main()
                    
                    mock_cli.discover_user.assert_called_once_with("testuser", "github")
                    mock_print.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_json_output(self):
        """Test main function with JSON output"""
        test_args = ["gitosint-mcp", "analyze-repo", "https://github.com/test/repo", "--json"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('src.gitosint_mcp.cli.GitOSINTCLI') as mock_cli_class:
                mock_cli = AsyncMock()
                mock_cli.analyze_repository.return_value = {"success": True, "data": {"name": "test/repo"}}
                mock_cli_class.return_value = mock_cli
                
                with patch('src.gitosint_mcp.cli.print_json_result') as mock_print:
                    await main()
                    
                    mock_print.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_no_command(self):
        """Test main function with no command"""
        test_args = ["gitosint-mcp"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('argparse.ArgumentParser.print_help') as mock_help:
                await main()
                mock_help.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self):
        """Test main function handling keyboard interrupt"""
        test_args = ["gitosint-mcp", "analyze-repo", "https://github.com/test/repo"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('src.gitosint_mcp.cli.GitOSINTCLI') as mock_cli_class:
                mock_cli = AsyncMock()
                mock_cli.analyze_repository.side_effect = KeyboardInterrupt()
                mock_cli_class.return_value = mock_cli
                
                with patch('builtins.print') as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        await main()
                    
                    assert exc_info.value.code == 1
                    mock_print.assert_called_with("\n❌ Operation cancelled by user")
    
    @pytest.mark.asyncio
    async def test_main_unexpected_error(self):
        """Test main function handling unexpected errors"""
        test_args = ["gitosint-mcp", "analyze-repo", "https://github.com/test/repo"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('src.gitosint_mcp.cli.GitOSINTCLI') as mock_cli_class:
                mock_cli = AsyncMock()
                mock_cli.analyze_repository.side_effect = Exception("Unexpected error")
                mock_cli_class.return_value = mock_cli
                
                with patch('builtins.print') as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        await main()
                    
                    assert exc_info.value.code == 1
                    mock_print.assert_called_with("❌ Unexpected error: Unexpected error")
    
    @pytest.mark.asyncio
    async def test_main_failed_operation_exit_code(self):
        """Test main function exit code for failed operations"""
        test_args = ["gitosint-mcp", "analyze-repo", "https://github.com/test/repo"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('src.gitosint_mcp.cli.GitOSINTCLI') as mock_cli_class:
                mock_cli = AsyncMock()
                mock_cli.analyze_repository.return_value = {"success": False, "error": "Failed"}
                mock_cli_class.return_value = mock_cli
                
                with patch('src.gitosint_mcp.cli.print_formatted_result'):
                    with pytest.raises(SystemExit) as exc_info:
                        await main()
                    
                    assert exc_info.value.code == 1


class TestCLIEdgeCases:
    """Test CLI edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_all_commands_with_defaults(self):
        """Test that all commands work with default parameters"""
        commands = [
            (["discover-user", "testuser"], "discover_user"),
            (["find-emails", "testuser"], "find_emails"),
            (["map-network", "testuser"], "map_network"),
        ]
        
        for args, method_name in commands:
            test_args = ["gitosint-mcp"] + args
            
            with patch.object(sys, 'argv', test_args):
                with patch('src.gitosint_mcp.cli.GitOSINTCLI') as mock_cli_class:
                    mock_cli = AsyncMock()
                    getattr(mock_cli, method_name).return_value = {"success": True, "data": {}}
                    mock_cli_class.return_value = mock_cli
                    
                    with patch('src.gitosint_mcp.cli.print_formatted_result'):
                        await main()
                        
                        # Verify the method was called
                        assert getattr(mock_cli, method_name).called
    
    @pytest.mark.asyncio
    async def test_version_argument(self):
        """Test --version argument"""
        test_args = ["gitosint-mcp", "--version"]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                await main()
            
            # argparse exits with code 0 for --version
            assert exc_info.value.code == 0
    
    @pytest.mark.asyncio
    async def test_help_argument(self):
        """Test --help argument"""
        test_args = ["gitosint-mcp", "--help"]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                await main()
            
            # argparse exits with code 0 for --help
            assert exc_info.value.code == 0
    
    @pytest.mark.asyncio
    async def test_invalid_command(self):
        """Test invalid command handling"""
        test_args = ["gitosint-mcp", "invalid-command"]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                await main()
            
            # argparse exits with code 2 for invalid arguments
            assert exc_info.value.code == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])result(result, pretty=True)
            
            mock_print.assert_called_once()
            printed_text = mock_print.call_args[0][0]
            assert '"success": true' in printed_text
            assert '"name": "test/repo"' in printed_text
            assert '"stars": 100' in printed_text
    
    def test_print_json_result_compact(self):
        """Test compact JSON output formatting"""
        result = {"success": True, "data": {"name": "test/repo"}}
        
        with patch('builtins.print') as mock_print:
            print_json_