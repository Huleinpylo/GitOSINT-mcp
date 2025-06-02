"""
Unit Tests for GitOSINT-MCP Configuration

Tests the configuration management system for the MCP addon.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path

from gitosint_mcp.config import (
    Config, 
    RateLimitConfig, 
    CacheConfig, 
    SecurityConfig,
    PlatformConfig,
    MCPConfig,
    validate_config,
    load_config_from_env
)

@pytest.mark.unit
class TestConfig:
    """Test configuration management for MCP addon."""
    
    def test_default_config_creation(self):
        """Test default configuration creation."""
        config = Config()
        
        assert config.log_level == "INFO"
        assert config.max_concurrent_requests == 10
        assert config.timeout_seconds == 30
        assert config.enable_email_discovery is True
        assert config.enable_security_scanning is True
        
        # Test nested configurations
        assert config.rate_limit.max_requests == 100
        assert config.security.max_repo_size_mb == 500
        assert config.platform.github_api_url == "https://api.github.com"
        assert config.mcp.server_name == "gitosint"
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = Config()
        errors = config.validate()
        assert len(errors) == 0
        
        # Should not raise exception
        validate_config(config)
    
    def test_config_validation_failure(self):
        """Test configuration validation with invalid values."""
        config = Config()
        config.rate_limit.max_requests = -1  # Invalid
        config.timeout_seconds = 0  # Invalid
        config.mcp.response_format = "invalid"  # Invalid
        
        errors = config.validate()
        assert len(errors) >= 3
        
        with pytest.raises(ValueError):
            validate_config(config)
    
    def test_config_save_and_load(self):
        """Test configuration save and load functionality."""
        original_config = Config()
        original_config.log_level = "DEBUG"
        original_config.rate_limit.max_requests = 200
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            # Save configuration
            original_config.save(config_path)
            
            # Load configuration
            loaded_config = Config.load(config_path)
            
            assert loaded_config.log_level == "DEBUG"
            assert loaded_config.rate_limit.max_requests == 200
            
        finally:
            os.unlink(config_path)
    
    def test_domain_allowed_check(self):
        """Test domain allowlist checking."""
        config = Config()
        
        assert config.is_domain_allowed("github.com") is True
        assert config.is_domain_allowed("gitlab.com") is True
        assert config.is_domain_allowed("malicious.com") is False
    
    def test_api_url_for_platform(self):
        """Test API URL retrieval for different platforms."""
        config = Config()
        
        assert config.get_api_url_for_platform("github") == "https://api.github.com"
        assert config.get_api_url_for_platform("gitlab") == "https://gitlab.com/api/v4"
        
        with pytest.raises(ValueError):
            config.get_api_url_for_platform("unsupported")
    
    def test_tool_rate_limit(self):
        """Test tool-specific rate limiting."""
        config = Config()
        
        assert config.get_tool_rate_limit("analyze_repository") == 20
        assert config.get_tool_rate_limit("discover_user_info") == 50
        assert config.get_tool_rate_limit("unknown_tool") == 100  # Default
    
    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        # Set environment variables
        os.environ["GITOSINT_MCP_LOG_LEVEL"] = "DEBUG"
        os.environ["GITOSINT_MCP_MAX_REQUESTS"] = "500"
        os.environ["GITOSINT_MCP_ENABLE_SECURITY_SCANNING"] = "false"
        
        try:
            config = load_config_from_env()
            
            assert config.log_level == "DEBUG"
            assert config.rate_limit.max_requests == 500
            assert config.enable_security_scanning is False
            
        finally:
            # Clean up environment variables
            for key in ["GITOSINT_MCP_LOG_LEVEL", "GITOSINT_MCP_MAX_REQUESTS", "GITOSINT_MCP_ENABLE_SECURITY_SCANNING"]:
                if key in os.environ:
                    del os.environ[key]