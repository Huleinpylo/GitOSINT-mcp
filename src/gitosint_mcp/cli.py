"""
GitOSINT-MCP Command Line Interface

Provides CLI commands for the MCP addon including:
- Starting the MCP server
- Running standalone analysis
- Configuration management
- Testing and validation
"""

import click
import asyncio
import logging
import json
import sys
from typing import Optional
from pathlib import Path

from .server import GitOSINTMCPServer
from .config import Config, load_config_from_env, validate_config
from . import __version__, __mcp_name__

# Configure logging for CLI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging for MCP addon')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--env-config', is_flag=True, help='Load configuration from environment variables')
@click.version_option(version=__version__, prog_name='GitOSINT-MCP')
@click.pass_context
def cli(ctx, verbose: bool, config: Optional[str], env_config: bool):
    """
    ? GitOSINT-MCP: OSINT intelligence via Model Context Protocol
    
    A powerful MCP addon that enables AI assistants to gather Open Source 
    Intelligence (OSINT) from public Git repositories without authentication.
    """
    ctx.ensure_object(dict)
    
    # Setup logging level
    level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger().setLevel(level)
    
    # Load configuration for MCP addon
    if env_config:
        ctx.obj['config'] = load_config_from_env()
    elif config:
        ctx.obj['config'] = Config.load(config)
    else:
        ctx.obj['config'] = Config.load()
    
    # Validate configuration
    try:
        validate_config(ctx.obj['config'])
    except ValueError as e:
        click.echo(f"? Configuration error: {e}", err=True)
        sys.exit(1)
    
    # Set log level from config
    logging.getLogger().setLevel(getattr(logging, ctx.obj['config'].log_level))
    
    if verbose:
        click.echo(f"? GitOSINT-MCP v{__version__} - MCP Server: {__mcp_name__}")
        click.echo(f"? Config: {ctx.obj['config'].log_level} logging, {len(ctx.obj['config'].security.allowed_domains)} allowed domains")

@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind MCP server to')
@click.option('--port', default=8080, type=int, help='Port to bind MCP server to')
@click.option('--transport', default='stdio', 
              type=click.Choice(['stdio', 'sse']), 
              help='MCP transport protocol')
@click.pass_context
def serve(ctx, host: str, port: int, transport: str):
    """
    ? Start the GitOSINT-MCP server for AI assistant integration.
    
    The server provides OSINT intelligence gathering capabilities through
    the Model Context Protocol, enabling AI assistants to analyze Git
    repositories, discover user information, and map social networks.
    """
    config: Config = ctx.obj['config']
    
    click.echo(f"? Starting GitOSINT-MCP server...")
    click.echo(f"? Transport: {transport}")
    click.echo(f"? Address: {host}:{port}")
    click.echo(f"? Security: {len(config.security.allowed_domains)} allowed domains")
    
    if transport == 'stdio':
        asyncio.run(start_stdio_server(config))
    elif transport == 'sse':
        asyncio.run(start_sse_server(config, host, port))
    else:
        click.echo(f"? Unsupported transport: {transport}", err=True)
        sys.exit(1)

# Helper functions for server startup
async def start_stdio_server(config: Config) -> None:
    """Start MCP server with STDIO transport for addon integration."""
    server = GitOSINTMCPServer(config)
    await server.run_stdio()

async def start_sse_server(config: Config, host: str, port: int) -> None:
    """Start MCP server with SSE transport for addon integration."""
    server = GitOSINTMCPServer(config)
    await server.run_sse(host, port)

def main() -> None:
    """Main entry point for GitOSINT-MCP CLI."""
    cli()

if __name__ == '__main__':
    main()