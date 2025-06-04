"""
Test suite for GitOSINT-MCP configuration module
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from dataclasses import dataclass

# Import the actual classes from our config module
from src.gitosint_mcp.config import (
    GitOSINTConfig,
    MCPConfig,
    SecurityConfig,
    PlatformConfig,
    get_config,
    reload_config,
    validate_config,
    create_default_config_file
)



class TestMCPConfig:
    """Test MCP configuration dataclass"""
    
    def test_default_mcp_config(self):
        """Test default MCP configuration values"""
        config = MCPConfig()
        
        assert config.server_name == "gitosint-mcp"
        assert config.server_version == "1.0.0"
        assert config.log_level == "INFO"
        assert config.rate_limit_delay == 1.0
        assert config.max_repositories_per_user == 100
        assert config.max_contributors_per_repo == 50
        assert config.max_network_depth == 3
        assert config.max_social_connections == 20
        assert config.timeout_seconds == 30
        assert "GitOSINT-MCP/1.0.0" in config.user_agent
    
    def test_custom_mcp_config(self):
        """Test custom MCP configuration values"""
        config = MCPConfig()
        config.server_name = "custom-server"
        config.server_version = "1.0.0"
        config.log_level = "DEBUG"
        config.rate_limit_delay = 2.5
        config.max_repositories_per_user = 100
        config.max_contributors_per_repo = 50
        config.max_network_depth = 3
        config.max_social_connections = 20
        config.timeout_seconds = 60
        config.user_agent = "test"
        
        assert config.server_name == "custom-server"
        assert config.log_level == "DEBUG"
        assert config.rate_limit_delay == 2.5
        assert config.timeout_seconds == 60


class TestPlatformConfig:
    """Test platform configuration dataclass"""
    
    def test_default_platform_config(self):
        """Test default platform configuration"""
        config = PlatformConfig(
            github_api_url="https://api.github.com",
            timeout_seconds=30
        )
        
        assert config.github_api_url == "https://api.github.com"
        assert config.gitlab_api_url == "https://gitlab.com/api/v4"
        assert config.enable_github is True

    def test_custom_platform_config(self):
        """Test custom platform configuration"""
        config = PlatformConfig(
            github_api_url="https://api.github.enterprise.com",
            timeout_seconds=30, # Custom timeout
            max_contributors_per_repo=100
        )
        config.enable_github = False
        config.enable_gitlab = False
        config.enable_bitbucket = True
        assert config.github_api_url == "https://api.github.enterprise.com"
        assert config.enable_github is False
        assert config.enable_gitlab is False
        assert config.enable_bitbucket is True


class TestSecurityConfig:
    """Test security configuration dataclass"""
    
    def test_default_security_config(self):
        """Test default security configuration"""
        config = SecurityConfig()
        
        assert config.respect_rate_limits is True
        assert config.log_requests is False
        assert config.anonymize_results is False
        assert config.max_email_extraction == 10
        assert config.enable_security_scanning is True
        assert config.scan_timeout == 60
    
    def test_custom_security_config(self):
        """Test custom security configuration"""
        config = SecurityConfig(
            respect_rate_limits=False,
            log_requests=True,
            anonymize_results=True,
            max_email_extraction=5,
            scan_timeout=120
        )
        
        assert config.respect_rate_limits is False
        assert config.log_requests is True
        assert config.anonymize_results is True
        assert config.max_email_extraction == 5
        assert config.scan_timeout == 120


class TestGitOSINTConfig:
    """Test main GitOSINT configuration class"""
    
    def test_default_config_creation(self):
        """Test creating default configuration"""
        config = GitOSINTConfig.default()
        
        assert isinstance(config.mcp, MCPConfig)
        assert isinstance(config.platforms, PlatformConfig)
        assert isinstance(config.security, SecurityConfig)
        
        assert config.mcp.server_name == "gitosint-mcp"
        assert config.platforms.enable_github is True
        assert config.security.respect_rate_limits is True
    
    def test_config_from_dict(self):
        """Test creating configuration from dictionary"""
        data = {
            "mcp": {
                "server_name": "test-server",
                "log_level": "DEBUG",
                "rate_limit_delay": 2.0
            },
            "platforms": {
                "enable_github": False,
                "enable_gitlab": True
            },
            "security": {
                "anonymize_results": True,
                "max_email_extraction": 5
            }
        }
        
        config = GitOSINTConfig.from_dict(data)
        
        assert config.mcp.server_name == "test-server"
        assert config.mcp.log_level == "DEBUG"
        assert config.mcp.rate_limit_delay == 2.0
        assert config.platforms.enable_github is False
        assert config.platforms.enable_gitlab is True
        assert config.security.anonymize_results is True
        assert config.security.max_email_extraction == 5
    
    def test_config_to_dict(self):
        """Test converting configuration to dictionary"""
        config = GitOSINTConfig.default()
        data = config.to_dict()
        
        assert "mcp" in data
        assert "platforms" in data
        assert "security" in data
        
        assert data["mcp"]["server_name"] == "gitosint-mcp"
        assert data["platforms"]["enable_github"] is True
        assert data["security"]["respect_rate_limits"] is True
    
    def test_config_load_from_file_not_exists(self):
        """Test loading config when file doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_path = Path(tmpdir) / "non_existent.json"
            config = GitOSINTConfig.load_from_file(non_existent_path)
            
            # Should return default config when file doesn't exist
            assert isinstance(config, GitOSINTConfig)
            assert config.mcp.server_name == "gitosint-mcp"
    
    def test_config_load_from_file_exists(self):
        """Test loading config from existing file"""
        config_data = {
            "mcp": {
                "server_name": "loaded-server",
                "log_level": "DEBUG"
            },
            "platforms": {
                "enable_github": False
            },
            "security": {
                "anonymize_results": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            config = GitOSINTConfig.load_from_file(config_path)
            
            assert config.mcp.server_name == "loaded-server"
            assert config.mcp.log_level == "DEBUG"
            assert config.platforms.enable_github is False
            assert config.security.anonymize_results is True
        finally:
            config_path.unlink()
    
    def test_config_save_to_file(self):
        """Test saving configuration to file"""
        config = GitOSINTConfig.default()
        config.mcp.server_name = "saved-server"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            config.save_to_file(config_path)
            
            assert config_path.exists()
            
            # Load and verify
            with open(config_path) as f:
                data = json.load(f)
            
            assert data["mcp"]["server_name"] == "saved-server"
    
    def test_config_update_from_env(self):
        """Test updating configuration from environment variables"""
        config = GitOSINTConfig.default()
        
        env_vars = {
            'GITOSINT_LOG_LEVEL': 'DEBUG',
            'GITOSINT_RATE_LIMIT_DELAY': '2.5',
            'GITOSINT_TIMEOUT': '60',
            'GITOSINT_GITHUB_API_URL': 'https://custom.github.com/api',
            'GITOSINT_ENABLE_GITHUB': 'false',
            'GITOSINT_ENABLE_GITLAB': 'true',
            'GITOSINT_RESPECT_RATE_LIMITS': 'false',
            'GITOSINT_LOG_REQUESTS': 'true',
            'GITOSINT_ANONYMIZE_RESULTS': 'true'
        }
        
        with patch.dict(os.environ, env_vars):
            config.update_from_env()
        
        assert config.mcp.log_level == 'DEBUG'
        assert config.mcp.rate_limit_delay == 2.5
        assert config.mcp.timeout_seconds == 60
        assert config.platforms.github_api_url == 'https://custom.github.com/api'
        assert config.platforms.enable_github is False
        assert config.platforms.enable_gitlab is True
        assert config.security.respect_rate_limits is False
        assert config.security.log_requests is True
        assert config.security.anonymize_results is True
    
    def test_config_update_from_env_invalid_values(self):
        """Test handling invalid environment variable values"""
        config = GitOSINTConfig.default()
        original_delay = config.mcp.rate_limit_delay
        original_timeout = config.mcp.timeout_seconds
        
        env_vars = {
            'GITOSINT_RATE_LIMIT_DELAY': 'invalid_float',
            'GITOSINT_TIMEOUT': 'invalid_int',
        }
        
        with patch.dict(os.environ, env_vars):
            config.update_from_env()
        
        # Should keep original values when env vars are invalid
        assert config.mcp.rate_limit_delay == original_delay
        assert config.mcp.timeout_seconds == original_timeout


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_valid_config(self):
        """Test validation of valid configuration"""
        config = GitOSINTConfig.default()
        assert validate_config(config) is True
    
    def test_invalid_rate_limit_delay(self):
        """Test validation with invalid rate limit delay"""
        config = GitOSINTConfig.default()
        config.mcp.rate_limit_delay = -1.0
        
        with patch('builtins.print') as mock_print:
            result = validate_config(config)
            assert result is False
            mock_print.assert_called()
    
    def test_invalid_timeout(self):
        """Test validation with invalid timeout"""
        config = GitOSINTConfig.default()
        config.mcp.timeout_seconds = 0
        
        with patch('builtins.print') as mock_print:
            result = validate_config(config)
            assert result is False
            mock_print.assert_called()
    
    def test_invalid_max_repositories(self):
        """Test validation with invalid max repositories"""
        config = GitOSINTConfig.default()
        config.mcp.max_repositories_per_user = 0
        
        with patch('builtins.print') as mock_print:
            result = validate_config(config)
            assert result is False
            mock_print.assert_called()
    
    def test_invalid_api_urls(self):
        """Test validation with invalid API URLs"""
        config = GitOSINTConfig.default()
        config.platforms.github_api_url = "http://insecure.com"
        
        with patch('builtins.print') as mock_print:
            result = validate_config(config)
            assert result is False
            mock_print.assert_called()
    
    def test_invalid_email_extraction(self):
        """Test validation with invalid email extraction limit"""
        config = GitOSINTConfig.default()
        config.security.max_email_extraction = 0
        
        with patch('builtins.print') as mock_print:
            result = validate_config(config)
            assert result is False
            mock_print.assert_called()


class TestGlobalConfigFunctions:
    """Test global configuration functions"""
    
    def test_get_config_singleton(self):
        """Test that get_config returns singleton instance"""
        # Reset global config
        import src.gitosint_mcp.config
        src.gitosint_mcp.config._config = None
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
        assert isinstance(config1, GitOSINTConfig)
    
    def test_reload_config(self):
        """Test reloading configuration"""
        # Create a test config file
        config_data = {
            "mcp": {"server_name": "reloaded-server"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            config = reload_config(config_path)
            assert config.mcp.server_name == "reloaded-server"
        finally:
            config_path.unlink()
    
    def test_create_default_config_file(self):
        """Test creating default configuration file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "default_config.json"
            
            with patch('builtins.print') as mock_print:
                create_default_config_file(config_path)
            
            assert config_path.exists()
            mock_print.assert_called_with(f"Created default configuration file: {config_path}")
            
            # Verify the file contains valid config
            with open(config_path) as f:
                data = json.load(f)
            
            assert "mcp" in data
            assert "platforms" in data
            assert "security" in data


class TestConfigEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_config_from_empty_dict(self):
        """Test creating config from empty dictionary"""
        config = GitOSINTConfig.from_dict({})
        
        # Should use defaults for missing sections
        assert config.mcp.server_name == "gitosint-mcp"
        assert config.platforms.enable_github is True
        assert config.security.respect_rate_limits is True
    
    def test_config_from_partial_dict(self):
        """Test creating config from partial dictionary"""
        data = {
            "mcp": {"server_name": "partial-server"}
            # Missing platforms and security sections
        }
        
        config = GitOSINTConfig.from_dict(data)
        
        assert config.mcp.server_name == "partial-server"
        assert config.mcp.log_level == "INFO"  # Default value
        assert config.platforms.enable_github is True  # Default value
        assert config.security.respect_rate_limits is True  # Default value
    
    def test_config_load_invalid_json(self):
        """Test loading configuration from invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            config_path = Path(f.name)
        
        try:
            with patch('builtins.print') as mock_print:
                config = GitOSINTConfig.load_from_file(config_path)
            
            # Should return default config and print warning
            assert isinstance(config, GitOSINTConfig)
            assert config.mcp.server_name == "gitosint-mcp"
            mock_print.assert_called()
        finally:
            config_path.unlink()
    
    def test_env_var_boolean_parsing(self):
        """Test various boolean value parsing from environment"""
        config = GitOSINTConfig.default()
        
        # Test various true values
        for true_val in ['true', '1', 'yes', 'TRUE', 'Yes']:
            with patch.dict(os.environ, {'GITOSINT_ENABLE_GITHUB': true_val}):
                config.update_from_env()
                assert config.platforms.enable_github is True
        
        # Test various false values
        for false_val in ['false', '0', 'no', 'FALSE', 'No', 'anything_else']:
            with patch.dict(os.environ, {'GITOSINT_ENABLE_GITHUB': false_val}):
                config.update_from_env()
                assert config.platforms.enable_github is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])