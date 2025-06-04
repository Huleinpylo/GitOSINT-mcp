"""
GitOSINT-MCP Security Package

Security analysis modules for the MCP addon including:
- Secret and credential scanning
- Malware and threat detection
- Security vulnerability assessment
- Privacy and compliance checking

These modules provide security intelligence capabilities
for AI assistants through the MCP protocol.
"""

from .scanner import SecurityScanner

__all__ = [
    "SecurityScanner"
]