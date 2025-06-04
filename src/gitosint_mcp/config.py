"""
Configuration module for GitOSINT-MCP
Author: Huleinpylo
License: MIT
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class MCPConfig:
    """MCP server configuration"""
    def __init__(self):
        self.server_name: str = "gitosint-mcp"
        self.server_version: str = "1.0.0"
        self.log_level: str = "INFO"
        self.rate_limit_delay: float = 1.0
        self.max_repositories_per_user: int = 100
        self.max_contributors_per_repo: int = 50
        self.max_network_depth: int = 3
        self.max_social_connections: int = 20
        self.timeout_seconds: int = 30
        self.user_agent: str = "GitOSINT-MCP/1.0.0 (+https://github.com/Huleinpylo/GitOSINT-mcp)"
        self.platform: PlatformConfig = PlatformConfig(
                github_api_url="https://api.github.com",
                timeout_seconds=30
            )

    def get_user_agent(self) -> str:
        # UA personnalisé
        return self.user_agent

    def is_domain_allowed(self, domain: str) -> bool:
        # N’autorise que GitHub, GitLab, Bitbucket
        return domain in {"github.com", "gitlab.com", "bitbucket.org"}

@dataclass
class PlatformConfig:
    """Platform-specific configuration"""
    def __init__(self, github_api_url: str, timeout_seconds: int, max_contributors_per_repo: int = 100):
        self.github_api_url = github_api_url
        self.timeout_seconds = timeout_seconds
        self.max_contributors_per_repo = max_contributors_per_repo
        self.bitbucket_api_url: str = "https://api.bitbucket.org/2.0"
        
        self.gitlab_api_url: str = "https://gitlab.com/api/v4"
        self.enable_github: bool = True
        self.enable_gitlab: bool = True
        self.enable_bitbucket: bool = True


@dataclass
class SecurityConfig:
    """Security and privacy configuration"""
    respect_rate_limits: bool = True
    log_requests: bool = False
    anonymize_results: bool = False
    max_email_extraction: int = 10
    enable_security_scanning: bool = True
    scan_timeout: int = 60


@dataclass
class GitOSINTConfig:
    """Main configuration class"""
    mcp: MCPConfig
    platforms: PlatformConfig
    security: SecurityConfig
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitOSINTConfig':
        """Create config from dictionary"""
        return cls(
            mcp=MCPConfig(**data.get('mcp', {})),
            platforms=PlatformConfig(**data.get('platforms', {})),
            security=SecurityConfig(**data.get('security', {}))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'mcp': asdict(self.mcp),
            'platforms': asdict(self.platforms),
            'security': asdict(self.security)
        }
    
    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> 'GitOSINTConfig':
        """Load configuration from file"""
        if config_path is None:
            # Try multiple default locations
            possible_paths = [
                Path.cwd() / "gitosint_config.json",
                Path.home() / ".config" / "gitosint-mcp" / "config.json",
                Path.home() / ".gitosint-mcp.json"
            ]
            
            config_path = None
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                return cls.from_dict(data)
            except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                print(f"Warning: Could not load config from {config_path}: {e}")
        
        # Return default configuration
        return cls.default()
    
    @classmethod
    def default(cls) -> 'GitOSINTConfig':
        """Create default configuration"""
        return cls(
            mcp=MCPConfig(),
            platforms=PlatformConfig(
                github_api_url="https://api.github.com",
                timeout_seconds=30
            ),
            security=SecurityConfig()
        )
    
    def save_to_file(self, config_path: Path):
        """Save configuration to file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def update_from_env(self):
        """Update configuration from environment variables"""
        # MCP settings
        if env_val := os.getenv('GITOSINT_LOG_LEVEL'):
            self.mcp.log_level = env_val
        
        if env_val := os.getenv('GITOSINT_RATE_LIMIT_DELAY'):
            try:
                self.mcp.rate_limit_delay = float(env_val)
            except ValueError:
                pass
        
        if env_val := os.getenv('GITOSINT_TIMEOUT'):
            try:
                self.mcp.timeout_seconds = int(env_val)
            except ValueError:
                pass
        
        # Platform settings
        if env_val := os.getenv('GITOSINT_GITHUB_API_URL'):
            self.platforms.github_api_url = env_val
        
        if env_val := os.getenv('GITOSINT_GITLAB_API_URL'):
            self.platforms.gitlab_api_url = env_val
        
        if env_val := os.getenv('GITOSINT_ENABLE_GITHUB'):
            self.platforms.enable_github = env_val.lower() in ('true', '1', 'yes')
        
        if env_val := os.getenv('GITOSINT_ENABLE_GITLAB'):
            self.platforms.enable_gitlab = env_val.lower() in ('true', '1', 'yes')
        
        # Security settings
        if env_val := os.getenv('GITOSINT_RESPECT_RATE_LIMITS'):
            self.security.respect_rate_limits = env_val.lower() in ('true', '1', 'yes')
        
        if env_val := os.getenv('GITOSINT_LOG_REQUESTS'):
            self.security.log_requests = env_val.lower() in ('true', '1', 'yes')
        
        if env_val := os.getenv('GITOSINT_ANONYMIZE_RESULTS'):
            self.security.anonymize_results = env_val.lower() in ('true', '1', 'yes')


# Global configuration instance
_config: Optional[GitOSINTConfig] = None


def get_config() -> GitOSINTConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = GitOSINTConfig.load_from_file()
        _config.update_from_env()
    return _config


def reload_config(config_path: Optional[Path] = None) -> GitOSINTConfig:
    """Reload configuration from file"""
    global _config
    _config = GitOSINTConfig.load_from_file(config_path)
    _config.update_from_env()
    return _config


def create_default_config_file(config_path: Path) -> None:
    """Create a default configuration file"""
    config = GitOSINTConfig.default()
    config.save_to_file(config_path)
    print(f"Created default configuration file: {config_path}")


# Configuration validation
def validate_config(config: GitOSINTConfig) -> bool:
    """Validate configuration settings"""
    issues = []
    
    # Validate MCP settings
    if config.mcp.rate_limit_delay < 0:
        issues.append("Rate limit delay cannot be negative")
    
    if config.mcp.timeout_seconds <= 0:
        issues.append("Timeout must be positive")
    
    if config.mcp.max_repositories_per_user <= 0:
        issues.append("Max repositories per user must be positive")
    
    # Validate platform URLs
    if not config.platforms.github_api_url.startswith('https://'):
        issues.append("GitHub API URL must use HTTPS")
    
    if not config.platforms.gitlab_api_url.startswith('https://'):
        issues.append("GitLab API URL must use HTTPS")
    
    # Validate security settings
    if config.security.max_email_extraction <= 0:
        issues.append("Max email extraction must be positive")
    
    if config.security.scan_timeout <= 0:
        issues.append("Scan timeout must be positive")
    
    if issues:
        print("Configuration validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    return True


# Example configuration file content
EXAMPLE_CONFIG = """
{
  "mcp": {
    "server_name": "gitosint-mcp",
    "server_version": "1.0.0",
    "log_level": "INFO",
    "rate_limit_delay": 1.0,
    "max_repositories_per_user": 100,
    "max_contributors_per_repo": 50,
    "max_network_depth": 3,
    "max_social_connections": 20,
    "timeout_seconds": 30,
    "user_agent": "GitOSINT-MCP/1.0.0 (+https://github.com/Huleinpylo/GitOSINT-mcp)"
  },
  "platforms": {
    "github_api_url": "https://api.github.com",
    "gitlab_api_url": "https://gitlab.com/api/v4",
    "enable_github": true,
    "enable_gitlab": true,
    "enable_bitbucket": false
  },
  "security": {
    "respect_rate_limits": true,
    "log_requests": false,
    "anonymize_results": false,
    "max_email_extraction": 10,
    "enable_security_scanning": true,
    "scan_timeout": 60
  }
}
"""


def print_config_help():
    """Print configuration help"""
    print("""
GitOSINT-MCP Configuration Help
===============================

Configuration File Locations (checked in order):
1. ./gitosint_config.json (current directory)
2. ~/.config/gitosint-mcp/config.json (user config)
3. ~/.gitosint-mcp.json (user home)

Environment Variables:
- GITOSINT_LOG_LEVEL: Set logging level (DEBUG, INFO, WARNING, ERROR)
- GITOSINT_RATE_LIMIT_DELAY: Rate limiting delay in seconds (default: 1.0)
- GITOSINT_TIMEOUT: HTTP request timeout in seconds (default: 30)
- GITOSINT_GITHUB_API_URL: GitHub API base URL
- GITOSINT_GITLAB_API_URL: GitLab API base URL
- GITOSINT_ENABLE_GITHUB: Enable GitHub support (true/false)
- GITOSINT_ENABLE_GITLAB: Enable GitLab support (true/false)
- GITOSINT_RESPECT_RATE_LIMITS: Respect API rate limits (true/false)
- GITOSINT_LOG_REQUESTS: Log HTTP requests (true/false)
- GITOSINT_ANONYMIZE_RESULTS: Anonymize sensitive data (true/false)

Example Configuration File:
""")
    print(EXAMPLE_CONFIG)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GitOSINT-MCP Configuration Manager")
    parser.add_argument("--create-default", metavar="PATH", 
                       help="Create default configuration file at specified path")
    parser.add_argument("--validate", metavar="PATH", 
                       help="Validate configuration file")
    parser.add_argument("--show-current", action="store_true",
                       help="Show current configuration")
    parser.add_argument("--help-config", action="store_true",
                       help="Show configuration help")
    
    args = parser.parse_args()
    
    if args.help_config:
        print_config_help()
    elif args.create_default:
        create_default_config_file(Path(args.create_default))
    elif args.validate:
        config = GitOSINTConfig.load_from_file(Path(args.validate))
        if validate_config(config):
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration has issues")
    elif args.show_current:
        config = get_config()
        print("Current Configuration:")
        print(json.dumps(config.to_dict(), indent=2))
    else:
        parser.print_help()