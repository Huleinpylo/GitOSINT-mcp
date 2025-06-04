# GitOSINT-MCP: OSINT Intelligence via Model Context Protocol

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

> **? Powerful OSINT for Git repositories through the Model Context Protocol**

GitOSINT-MCP bridges Open Source Intelligence (OSINT) techniques with modern AI agent frameworks via the Model Context Protocol (MCP). This addon enables AI assistants to gather intelligence from public Git repositories without requiring authentication or API tokens.

## ? Features

### Core OSINT Capabilities
- **? Repository Analysis**: Extract metadata, contributors, and project intelligence
- **? Email Discovery**: Find email addresses from commits, issues, and documentation
- **? User Profiling**: Gather intelligence on developers across platforms
- **?? Social Mapping**: Identify connections between users and organizations
- **? Cross-Reference**: Link information across multiple repositories and platforms

### MCP Integration Benefits
- **? AI Agent Ready**: Works with Claude Desktop, Cursor, VS Code, and other MCP clients
- **? Plug & Play**: Standard MCP protocol for seamless integration
- **? Real-time**: Live intelligence gathering during AI conversations
- **? Privacy First**: No authentication required, public data only
- **? Composable**: Combine with other MCP servers for powerful workflows

## ?? Quick Start

### Option 1: Docker (Recommended)
```bash
# Pull and run the container
docker run -d --name gitosint-mcp -p 8080:8080 huleinpylo/gitosint-mcp:latest

# Configure your AI assistant to use: http://localhost:8080
```

### Option 2: Python Installation
```bash
# Install from PyPI
pip install gitosint-mcp

# Start the MCP server
gitosint-mcp serve
```

### Option 3: Development Setup
```bash
# Clone this repository
git clone https://github.com/Huleinpylo/GitOSINT-mcp.git
cd GitOSINT-mcp

# Switch to feature branch
git checkout feat-mcp

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest tests/ -v
```

## ? AI Assistant Configuration

### Claude Desktop
```json
{
  "mcpServers": {
    "gitosint": {
      "command": "gitosint-mcp",
      "args": ["serve"]
    }
  }
}
```

### VS Code (with MCP extension)
```json
{
  "servers": {
    "gitosint": {
      "type": "sse",
      "url": "http://localhost:8080/sse"
    }
  }
}
```

### Cursor IDE
```json
{
  "mcpServers": {
    "gitosint": {
      "url": "http://localhost:8080"
    }
  }
}
```

## ? Usage Examples

Once configured, your AI assistant can perform OSINT tasks:

```
? "Analyze the repository https://github.com/microsoft/vscode and find the key contributors"

? "Find email addresses associated with the user 'octocat' on GitHub"

? "Map the social connections between contributors to the Linux kernel project"

? "Check if there are any leaked secrets in the repository https://github.com/example/project"
```

## ?? Architecture

```
GitOSINT-MCP Architecture
??? MCP Server Core
?   ??? Repository Analyzer
?   ??? User Intelligence Module
?   ??? Email Discovery Engine
?   ??? Social Graph Mapper
??? Intelligence Gathering
?   ??? Commit Analysis
?   ??? Contributor Mapping
?   ??? Organization Detection
?   ??? Cross-Platform Correlation
??? AI Integration
    ??? Claude Desktop
    ??? VS Code Agents
    ??? Cursor IDE
    ??? Custom MCP Clients
```

## ? Development

### Branch Structure
- `main` - Stable release branch
- `feat-mcp` - **Current development branch for MCP addon features**
- `test` - Testing and validation branch

### Contributing to MCP Addon
```bash
# Work on the MCP addon features
git checkout feat-mcp

# Make your changes
# ...

# Commit with MCP-focused messages
git commit -m "feat(mcp): add email discovery tool for MCP integration"
git commit -m "fix(mcp): improve repository analysis tool response format"
git commit -m "docs(mcp): update MCP server configuration examples"
```

### Testing MCP Integration
```bash
# Run MCP-specific tests
pytest tests/mcp/ -v

# Test with real MCP clients
python -m gitosint_mcp.server --transport stdio

# Integration testing
docker-compose -f docker-compose.test.yml up
```

## ? Project Status

### Current Phase: MCP Addon Development
- [x] ? Repository structure and documentation
- [ ] ? Core MCP server implementation
- [ ] ? Repository analysis tools
- [ ] ? Email discovery engine
- [ ] ? User intelligence gathering
- [ ] ? Docker containerization
- [ ] ? CI/CD pipeline setup
- [ ] ? Documentation and examples

### Upcoming Features
- [ ] Social network mapping
- [ ] Machine learning insights
- [ ] Threat intelligence integration
- [ ] Multi-platform support (GitLab, Bitbucket)
- [ ] Advanced analytics dashboard

## ? Documentation

- [Installation Guide](docs/installation.md)
- [MCP Integration Guide](docs/mcp-integration.md)
- [API Reference](docs/api-reference.md)
- [Configuration Options](docs/configuration.md)
- [Security Considerations](docs/security.md)
- [Development Guide](docs/development.md)

## ?? Security & Privacy

- **Public Data Only**: No authentication required, operates on publicly available information
- **Rate Limited**: Built-in rate limiting to respect platform APIs
- **Privacy Focused**: No personal data storage or tracking
- **Secure by Design**: Input validation and sanitization
- **Compliance Ready**: Respects robots.txt and platform terms of service

## ? Contributing

We welcome contributions to the GitOSINT-MCP project! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch from `feat-mcp`
3. Make your changes with proper MCP-focused commit messages
4. Add tests for new functionality
5. Submit a pull request to `feat-mcp` branch

## ? License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ? Acknowledgments

- [Anthropic](https://anthropic.com) for the Model Context Protocol specification
- [OSINT Community](https://github.com/topics/osint) for inspiration and techniques
- [Git OSINT Tools](https://github.com/topics/git-osint) contributors

## ? Support

- ? [Report Bugs](https://github.com/Huleinpylo/GitOSINT-mcp/issues)
- ? [Request Features](https://github.com/Huleinpylo/GitOSINT-mcp/issues)
- ? [Discussions](https://github.com/Huleinpylo/GitOSINT-mcp/discussions)
- ? [Documentation](https://github.com/Huleinpylo/GitOSINT-mcp/wiki)

---

**? Star this repository if you find GitOSINT-MCP useful for your OSINT and AI agent workflows!**