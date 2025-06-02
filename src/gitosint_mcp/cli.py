#!/usr/bin/env python3
"""
GitOSINT-MCP Command Line Interface
Author: Huleinpylo
License: MIT
"""

import asyncio
import argparse
import json
import sys
from typing import Dict, Any
from pathlib import Path

from .server import GitOSINTAnalyzer


class GitOSINTCLI:
    """Command line interface for GitOSINT-MCP"""
    
    def __init__(self):
        self.analyzer = GitOSINTAnalyzer()
    
    async def analyze_repository(self, repo_url: str) -> Dict[str, Any]:
        """Analyze a repository and return results"""
        try:
            result = await self.analyzer.analyze_repository(repo_url)
            return {
                "success": True,
                "data": {
                    "name": result.name,
                    "description": result.description,
                    "stars": result.stars,
                    "forks": result.forks,
                    "language": result.language,
                    "topics": result.topics,
                    "contributors_count": len(result.contributors),
                    "security_issues_count": len(result.security_issues),
                    "commit_activity": result.commit_activity
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def discover_user(self, username: str, platform: str = "github") -> Dict[str, Any]:
        """Discover user information"""
        try:
            result = await self.analyzer.discover_user_info(username, platform)
            return {
                "success": True,
                "data": {
                    "username": result.username,
                    "email_addresses": result.email_addresses,
                    "repository_count": len(result.repositories),
                    "commit_count": result.commit_count,
                    "languages": result.languages,
                    "social_connections": result.social_connections[:10],  # Limit output
                    "profile_data": result.profile_data
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def find_emails(self, target: str, search_type: str = "user") -> Dict[str, Any]:
        """Find email addresses"""
        try:
            result = await self.analyzer.find_emails(target, search_type)
            return {
                "success": True,
                "data": {
                    "target": target,
                    "search_type": search_type,
                    "emails": result,
                    "count": len(result)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def map_network(self, username: str, depth: int = 2) -> Dict[str, Any]:
        """Map social network"""
        try:
            result = await self.analyzer.map_social_network(username, depth)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def scan_security(self, repo_url: str) -> Dict[str, Any]:
        """Scan for security issues"""
        try:
            result = await self.analyzer.scan_security_issues(repo_url)
            return {
                "success": True,
                "data": {
                    "repository": repo_url,
                    "issues": result,
                    "total_issues": len(result),
                    "high_severity": len([i for i in result if i.get('severity') == 'high']),
                    "medium_severity": len([i for i in result if i.get('severity') == 'medium']),
                    "low_severity": len([i for i in result if i.get('severity') == 'low'])
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Clean up resources"""
        await self.analyzer.close()


def print_json_result(result: Dict[str, Any], pretty: bool = True):
    """Print results in JSON format"""
    if pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))


def print_formatted_result(result: Dict[str, Any], command: str):
    """Print results in human-readable format"""
    if not result.get("success"):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        return
    
    data = result.get("data", {})
    
    if command == "analyze-repo":
        print(f"📊 Repository Analysis: {data.get('name', 'Unknown')}")
        print(f"📝 Description: {data.get('description', 'No description')}")
        print(f"⭐ Stars: {data.get('stars', 0)}")
        print(f"🍴 Forks: {data.get('forks', 0)}")
        print(f"💻 Language: {data.get('language', 'Unknown')}")
        print(f"🏷️  Topics: {', '.join(data.get('topics', []))}")
        print(f"👥 Contributors: {data.get('contributors_count', 0)}")
        print(f"🔒 Security Issues: {data.get('security_issues_count', 0)}")
    
    elif command == "discover-user":
        print(f"👤 User Profile: {data.get('username', 'Unknown')}")
        print(f"📧 Email Addresses: {len(data.get('email_addresses', []))}")
        print(f"📂 Repositories: {data.get('repository_count', 0)}")
        print(f"💻 Languages: {', '.join(data.get('languages', []))}")
        print(f"🌐 Social Connections: {len(data.get('social_connections', []))}")
        
        profile = data.get('profile_data', {})
        if profile.get('name'):
            print(f"🏷️  Name: {profile['name']}")
        if profile.get('company'):
            print(f"🏢 Company: {profile['company']}")
        if profile.get('location'):
            print(f"📍 Location: {profile['location']}")
    
    elif command == "find-emails":
        print(f"📧 Email Discovery for: {data.get('target', 'Unknown')}")
        print(f"🔍 Search Type: {data.get('search_type', 'Unknown')}")
        print(f"📊 Found {data.get('count', 0)} email(s):")
        for email in data.get('emails', []):
            print(f"  • {email}")
    
    elif command == "map-network":
        print(f"🕸️  Social Network Map for: {data.get('center', 'Unknown')}")
        print(f"📊 Total Connections: {data.get('total_connections', 0)}")
        print(f"📏 Depth: {data.get('depth', 0)}")
        
        connections = data.get('connections', {})
        for repo, collaborators in connections.items():
            print(f"  📂 {repo}: {len(collaborators)} collaborators")
    
    elif command == "scan-security":
        total = data.get('total_issues', 0)
        high = data.get('high_severity', 0)
        medium = data.get('medium_severity', 0)
        low = data.get('low_severity', 0)
        
        print(f"🔒 Security Scan: {data.get('repository', 'Unknown')}")
        print(f"📊 Total Issues: {total}")
        print(f"🔴 High Severity: {high}")
        print(f"🟡 Medium Severity: {medium}")
        print(f"🟢 Low Severity: {low}")
        
        if total > 0:
            print("\n📋 Issues Found:")
            for issue in data.get('issues', []):
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.get('severity'), "ℹ️")
                print(f"  {severity_emoji} {issue.get('type', 'Unknown')}: {issue.get('description', 'No description')}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="GitOSINT-MCP: OSINT intelligence gathering from Git repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gitosint-mcp analyze-repo https://github.com/torvalds/linux
  gitosint-mcp discover-user octocat
  gitosint-mcp find-emails octocat --type user
  gitosint-mcp map-network octocat --depth 2
  gitosint-mcp scan-security https://github.com/user/repo

For more information, visit: https://github.com/Huleinpylo/GitOSINT-mcp
        """
    )
    
    parser.add_argument("--version", action="version", version="GitOSINT-MCP 1.0.0")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--pretty", action="store_true", default=True, help="Pretty print JSON output")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze repository command
    analyze_parser = subparsers.add_parser("analyze-repo", help="Analyze a Git repository")
    analyze_parser.add_argument("repo_url", help="URL of the repository to analyze")
    
    # Discover user command
    discover_parser = subparsers.add_parser("discover-user", help="Discover user information")
    discover_parser.add_argument("username", help="Username to investigate")
    discover_parser.add_argument("--platform", choices=["github", "gitlab"], default="github",
                               help="Git platform (default: github)")
    
    # Find emails command
    emails_parser = subparsers.add_parser("find-emails", help="Find email addresses")
    emails_parser.add_argument("target", help="Username or repository URL")
    emails_parser.add_argument("--type", choices=["user", "repo"], default="user",
                              help="Search type (default: user)")
    
    # Map network command
    network_parser = subparsers.add_parser("map-network", help="Map social network connections")
    network_parser.add_argument("username", help="Username to map network for")
    network_parser.add_argument("--depth", type=int, choices=[1, 2, 3], default=2,
                               help="Network mapping depth (default: 2)")
    
    # Scan security command
    security_parser = subparsers.add_parser("scan-security", help="Scan for security issues")
    security_parser.add_argument("repo_url", help="URL of the repository to scan")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = GitOSINTCLI()
    
    try:
        # Execute the appropriate command
        if args.command == "analyze-repo":
            result = await cli.analyze_repository(args.repo_url)
        elif args.command == "discover-user":
            result = await cli.discover_user(args.username, args.platform)
        elif args.command == "find-emails":
            result = await cli.find_emails(args.target, args.type)
        elif args.command == "map-network":
            result = await cli.map_network(args.username, args.depth)
        elif args.command == "scan-security":
            result = await cli.scan_security(args.repo_url)
        else:
            print(f"Unknown command: {args.command}")
            return
        
        # Output results
        if args.json:
            print_json_result(result, args.pretty)
        else:
            print_formatted_result(result, args.command)
        
        # Set exit code based on success
        if not result.get("success"):
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        await cli.close()


if __name__ == "__main__":
    asyncio.run(main())