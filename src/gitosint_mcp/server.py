# src/gitosint_mcp/server.py
from mcp.server import Server
from mcp.types import Tool, TextContent, EmbeddedResource
import asyncio
import logging

class GitOSINTMCPServer:
    def __init__(self):
        self.server = Server("gitosint-mcp")
        self.setup_tools()
        self.setup_resources()
    
    def setup_tools(self):
        """Register MCP tools"""
        
        @self.server.call_tool()
        async def analyze_repository(arguments: dict) -> list[TextContent]:
            """Analyze a Git repository for OSINT intelligence"""
            repo_url = arguments.get("repository_url")
            depth = arguments.get("depth", "basic")
            
            analyzer = RepositoryAnalyzer()
            results = await analyzer.analyze(repo_url, depth)
            
            return [TextContent(
                type="text",
                text=f"Repository Analysis for {repo_url}:\n{results}"
            )]
        
        @self.server.call_tool()
        async def discover_user_info(arguments: dict) -> list[TextContent]:
            """Discover information about a Git user"""
            username = arguments.get("username")
            platform = arguments.get("platform", "github")
            
            user_intel = UserIntelligence()
            info = await user_intel.gather(username, platform)
            
            return [TextContent(
                type="text", 
                text=f"User Intelligence for {username}:\n{info}"
            )]
        
        @self.server.call_tool()
        async def find_emails(arguments: dict) -> list[TextContent]:
            """Find email addresses associated with repositories or users"""
            target = arguments.get("target")
            target_type = arguments.get("type", "repository")
            
            email_finder = EmailDiscovery()
            emails = await email_finder.find(target, target_type)
            
            return [TextContent(
                type="text",
                text=f"Email Discovery Results:\n{emails}"
            )]

    def setup_resources(self):
        """Register MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> list[EmbeddedResource]:
            return [
                EmbeddedResource(
                    type="resource",
                    resource={"uri": "gitosint://help", "name": "GitOSINT Help"}
                ),
                EmbeddedResource(
                    type="resource", 
                    resource={"uri": "gitosint://techniques", "name": "OSINT Techniques"}
                )
            ]

async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    
    server = GitOSINTMCPServer()
    
    # Start the MCP server
    async with server.server.create_session() as session:
        await session.run()

if __name__ == "__main__":
    asyncio.run(main())