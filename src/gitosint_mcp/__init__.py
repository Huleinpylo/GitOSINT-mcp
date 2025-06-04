"""
GitOSINT-MCP: OSINT intelligence gathering from Git repositories via MCP
Author: Huleinpylo
License: MIT

This package provides MCP (Model Context Protocol) tools for gathering
Open Source Intelligence (OSINT) from public Git repositories without
requiring authentication.
"""

__version__ = "1.0.0"
__author__ = "Huleinpylo"
__license__ = "MIT"
__description__ = "OSINT intelligence gathering from Git repositories via MCP"

# Import main classes for easy access
try:
    from .server import GitOSINTAnalyzer, UserIntelligence, RepositoryIntel
    from .config import GitOSINTConfig, get_config
    from .cli import GitOSINTCLI
except ImportError:
    # Handle import errors gracefully during package installation
    pass

# Package metadata
__all__ = [
    "GitOSINTAnalyzer",
    "UserIntelligence", 
    "RepositoryIntel",
    "GitOSINTConfig",
    "get_config",
    "GitOSINTCLI",
    "__version__",
    "__author__",
    "__license__",
    "__description__"
]