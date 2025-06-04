# GitOSINT-MCP Quick Start Guide

? Get up and running with GitOSINT-MCP in under 5 minutes!

## What is GitOSINT-MCP?

GitOSINT-MCP is a Model Context Protocol (MCP) addon that enables AI assistants to perform Open Source Intelligence (OSINT) gathering from public Git repositories. It provides 5 powerful tools for repository analysis, user profiling, email discovery, social network mapping, and security scanning.

## Installation Options

### Option 1: Python Package (Recommended)

```bash
# Install from PyPI
pip install gitosint-mcp

# Verify installation
gitosint-mcp --version
```

### Option 2: Docker Container

```bash
# Pull the latest image
docker pull huleinpylo/gitosint-mcp:latest

# Run the container
docker run -p 8080:8080 huleinpylo/gitosint-mcp:latest
```

### Option 3: Development Installation

```bash
# Clone the repository
git clone https://github.com/Huleinpylo/GitOSINT-mcp.git
cd GitOSINT-mcp

# Switch to MCP addon branch
git checkout feat-mcp

# Install in development mode
pip install -e .[dev]
```

## AI Assistant Setup

### Claude Desktop (Easiest)

1. **Install Claude Desktop** from [claude.ai/desktop](https://claude.ai/desktop)

2. **Configure MCP Server**:
   - Open Claude Desktop
   - Go to Settings ? Developer ? Edit Config
   - Add this configuration:

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

3. **Restart Claude Desktop**

4. **Test the connection**:
   ```
   Can you analyze the repository https://github.com/microsoft/vscode?
   ```

### VS Code with MCP Extension

1. **Install MCP Extension** from VS Code marketplace

2. **Create configuration file** `.vscode/mcp.json`:

```json
{
  "servers": {
    "gitosint": {
      "type": "stdio",
      "command": "gitosint-mcp",
      "args": ["serve"]
    }
  }
}
```

3. **Reload VS Code** and activate MCP mode

### Other AI Assistants

See our [MCP Integration Guide](mcp-integration.md) for:
- Cursor IDE
- Windsurf
- Cline (Claude Dev)
- Custom MCP clients

## First Steps

### 1. Repository Analysis

Analyze any public Git repository:

```
Analyze the FastAPI repository and show me the top contributors
```

**Expected response:**
- Repository metadata (stars, forks, language)
- Contributor list with contribution counts
- Programming language distribution
- Project topics and license information

### 2. User Intelligence

Gather intelligence on Git users:

```
Who is the user 'gvanrossum' and what are their notable repositories?
```

**Expected response:**
- User profile information
- Activity statistics
- Repository ownership
- Account details and history

### 3. Email Discovery

Find email addresses in repositories:

```
Find email addresses associated with the Linux kernel repository
```

**Expected response:**
- Discovered email addresses
- Source information (commits, docs, etc.)
- Confidence scores
- Associated names

### 4. Social Network Mapping

Map developer relationships:

```
Map the social network of developers starting from 'torvalds' and 'gvanrossum'
```

**Expected response:**
- Network statistics
- Connection types and strengths
- Central/influential users
- Community clusters

### 5. Security Scanning

Scan repositories for security issues:

```
Perform a security scan of https://github.com/example/webapp
```

**Expected response:**
- Risk level assessment
- Leaked secrets detection
- Configuration issues
- Security recommendations

## Configuration

### Basic Configuration

Create `~/.config/gitosint-mcp/config.json`:

```json
{
  "log_level": "INFO",
  "rate_limit": {
    "max_requests": 100,
    "window_seconds": 3600
  },
  "security": {
    "allowed_domains": [
      "github.com",
      "gitlab.com",
      "bitbucket.org"
    ]
  }
}
```

### Environment Variables

```bash
# Set log level
export GITOSINT_MCP_LOG_LEVEL=DEBUG

# Configure rate limiting
export GITOSINT_MCP_MAX_REQUESTS=200

# Enable caching
export GITOSINT_MCP_ENABLE_CACHE=true
```

## Testing Your Setup

### 1. Test MCP Server

```bash
# Start server manually
gitosint-mcp serve --verbose

# Should see:
# "GitOSINT-MCP server initialized with 5 tools"
# "Starting GitOSINT-MCP server with STDIO transport"
```

### 2. Test Individual Tools

```bash
# Test repository analysis
gitosint-mcp analyze https://github.com/octocat/Hello-World

# Test user intelligence
gitosint-mcp user-intel octocat

# Test email discovery
gitosint-mcp find-emails octocat --type user
```

### 3. Test with AI Assistant

Try these example prompts:

```
1. "Analyze the repository https://github.com/python/cpython"
2. "Find information about the GitHub user 'octocat'"
3. "What emails can you find for the repository https://github.com/torvalds/linux?"
4. "Scan https://github.com/example/project for security issues"
5. "Map the social connections of developers starting from 'defunkt'"
```

## Troubleshooting

### Common Issues

**MCP server not found:**
```bash
# Check installation
which gitosint-mcp
pip show gitosint-mcp

# Reinstall if needed
pip install --upgrade gitosint-mcp
```

**Permission denied:**
```bash
# Fix permissions
chmod +x $(which gitosint-mcp)

# Or reinstall with user flag
pip install --user gitosint-mcp
```

**Rate limiting:**
```bash
# Increase rate limits
export GITOSINT_MCP_MAX_REQUESTS=500

# Or create config file with higher limits
```

**Connection issues:**
```bash
# Test server manually
gitosint-mcp serve --verbose

# Check logs
tail -f ~/.local/share/gitosint-mcp/logs/server.log
```

### Getting Help

- ? **Documentation**: [Full documentation](../README.md)
- ? **Issues**: [GitHub Issues](https://github.com/Huleinpylo/GitOSINT-mcp/issues)
- ? **Discussions**: [GitHub Discussions](https://github.com/Huleinpylo/GitOSINT-mcp/discussions)
- ? **Email**: contact@huleinpylo.dev

## Next Steps

### Learn More

1. **[MCP Integration Guide](mcp-integration.md)** - Detailed setup for all AI assistants
2. **[Configuration Guide](configuration.md)** - Advanced configuration options
3. **[API Reference](api-reference.md)** - Complete tool documentation
4. **[Security Guide](security.md)** - Security best practices

### Advanced Usage

1. **Custom Configurations** - Tailor GitOSINT-MCP for your use case
2. **Docker Deployment** - Run in containerized environments
3. **Development Setup** - Contribute to the project
4. **Enterprise Integration** - Deploy for team use

### Community

1. **? Star the repository** on [GitHub](https://github.com/Huleinpylo/GitOSINT-mcp)
2. **? Contribute** by following our [Contributing Guide](../CONTRIBUTING.md)
3. **? Share** your experience and use cases
4. **? Follow** for updates on new features

---

**? Congratulations!** You now have GitOSINT-MCP running and ready to enhance your AI assistant with powerful OSINT capabilities.

**Happy OSINT gathering! ?????**