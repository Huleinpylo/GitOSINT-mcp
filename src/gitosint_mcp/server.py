#!/usr/bin/env python3
"""
GitOSINT-MCP: MCP Server for OSINT intelligence gathering from Git repositories
Author: Huleinpylo
License: MIT
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
import json
import httpx
from urllib.parse import urlparse, unquote
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gitosint-mcp")

@dataclass
class UserIntelligence:
    """Structure for user intelligence data"""
    username: str
    email_addresses: List[str]
    repositories: List[Dict[str, Any]]
    commit_count: int
    languages: List[str]
    activity_pattern: Dict[str, Any]
    social_connections: List[str]
    profile_data: Dict[str, Any]

@dataclass
class RepositoryIntel:
    """Structure for repository intelligence"""
    name: str
    description: str
    stars: int
    forks: int
    language: str
    topics: List[str]
    contributors: List[Dict[str, Any]]
    commit_activity: Dict[str, Any]
    security_issues: List[str]
    dependencies: List[str]

class GitOSINTAnalyzer:
    """Core OSINT analyzer for Git repositories"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "GitOSINT-MCP/1.0.0 (+https://github.com/Huleinpylo/GitOSINT-mcp)"
            }
        )
        self.rate_limit_delay = 1.0  # Rate limiting
        
    async def analyze_repository(self, repo_url: str) -> RepositoryIntel:
        """Analyze a repository for intelligence"""
        try:
            parsed_url = urlparse(repo_url)
            path_parts = parsed_url.path.strip('/').split('/')
            
            if len(path_parts) < 2:
                raise ValueError("Invalid repository URL format")
                
            owner, repo = path_parts[0], path_parts[1]
            
            # Determine platform and API endpoint
            if parsed_url.netloc == "github.com" or parsed_url.netloc.endswith(".github.com"):
                return await self._analyze_github_repo(owner, repo)
            elif parsed_url.netloc == "gitlab.com" or parsed_url.netloc.endswith(".gitlab.com"):
                return await self._analyze_gitlab_repo(owner, repo)
            else:
                raise ValueError(f"Unsupported platform: {parsed_url.netloc}")
                
        except Exception as e:
            logger.error(f"Repository analysis failed: {str(e)}")
            raise
    
    async def _analyze_github_repo(self, owner: str, repo: str) -> RepositoryIntel:
        """Analyze GitHub repository"""
        base_url = "https://api.github.com"
        
        # Get repository information
        repo_response = await self.client.get(f"{base_url}/repos/{owner}/{repo}")
        repo_response.raise_for_status()
        repo_data = repo_response.json()
        
        # Get contributors
        contributors_response = await self.client.get(f"{base_url}/repos/{owner}/{repo}/contributors")
        contributors_data = contributors_response.json() if contributors_response.status_code == 200 else []
        
        # Get languages
        languages_response = await self.client.get(f"{base_url}/repos/{owner}/{repo}/languages")
        languages_data = languages_response.json() if languages_response.status_code == 200 else {}
        
        # Analyze commit activity (last 52 weeks)
        activity_response = await self.client.get(f"{base_url}/repos/{owner}/{repo}/stats/commit_activity")
        activity_data = activity_response.json() if activity_response.status_code == 200 else []
        
        await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
        
        return RepositoryIntel(
            name=f"{owner}/{repo}",
            description=repo_data.get('description', ''),
            stars=repo_data.get('stargazers_count', 0),
            forks=repo_data.get('forks_count', 0),
            language=repo_data.get('language', 'Unknown'),
            topics=repo_data.get('topics', []),
            contributors=contributors_data[:10],  # Top 10 contributors
            commit_activity=self._process_commit_activity(activity_data),
            security_issues=await self._check_security_indicators(repo_data),
            dependencies=list(languages_data.keys())
        )
    
    async def _analyze_gitlab_repo(self, owner: str, repo: str) -> RepositoryIntel:
        """Analyze GitLab repository"""
        project_path = f"{owner}/{repo}"
        encoded_path = unquote(project_path).replace('/', '%2F')
        base_url = "https://gitlab.com/api/v4"
        
        # Get project information
        project_response = await self.client.get(f"{base_url}/projects/{encoded_path}")
        project_response.raise_for_status()
        project_data = project_response.json()
        
        # Get contributors
        contributors_response = await self.client.get(f"{base_url}/projects/{project_data['id']}/repository/contributors")
        contributors_data = contributors_response.json() if contributors_response.status_code == 200 else []
        
        await asyncio.sleep(self.rate_limit_delay)
        
        return RepositoryIntel(
            name=project_data.get('path_with_namespace', ''),
            description=project_data.get('description', ''),
            stars=project_data.get('star_count', 0),
            forks=project_data.get('forks_count', 0),
            language='Unknown',  # GitLab API doesn't provide primary language easily
            topics=project_data.get('topics', []),
            contributors=contributors_data[:10],
            commit_activity={},
            security_issues=[],
            dependencies=[]
        )
    
    async def discover_user_info(self, username: str, platform: str = "github") -> UserIntelligence:
        """Discover user information across platforms"""
        if platform.lower() == "github":
            return await self._discover_github_user(username)
        elif platform.lower() == "gitlab":
            return await self._discover_gitlab_user(username)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    async def _discover_github_user(self, username: str) -> UserIntelligence:
        """Discover GitHub user information"""
        base_url = "https://api.github.com"
        
        # Get user profile
        user_response = await self.client.get(f"{base_url}/users/{username}")
        user_response.raise_for_status()
        user_data = user_response.json()
        
        # Get user repositories
        repos_response = await self.client.get(f"{base_url}/users/{username}/repos?per_page=100")
        repos_data = repos_response.json() if repos_response.status_code == 200 else []
        
        # Extract email addresses from commits (public repos only)
        email_addresses = await self._extract_emails_from_repos(username, repos_data[:5])  # Limit to 5 repos
        
        await asyncio.sleep(self.rate_limit_delay)
        
        return UserIntelligence(
            username=username,
            email_addresses=list(set(email_addresses)),  # Remove duplicates
            repositories=[{
                'name': repo['name'],
                'stars': repo['stargazers_count'],
                'language': repo['language'],
                'updated': repo['updated_at']
            } for repo in repos_data],
            commit_count=len(repos_data),  # Approximate
            languages=self._extract_languages(repos_data),
            activity_pattern=self._analyze_activity_pattern(repos_data),
            social_connections=await self._find_social_connections(username),
            profile_data={
                'name': user_data.get('name'),
                'bio': user_data.get('bio'),
                'location': user_data.get('location'),
                'company': user_data.get('company'),
                'blog': user_data.get('blog'),
                'twitter': user_data.get('twitter_username'),
                'public_repos': user_data.get('public_repos'),
                'followers': user_data.get('followers'),
                'following': user_data.get('following'),
                'created_at': user_data.get('created_at')
            }
        )
    
    async def _discover_gitlab_user(self, username: str) -> UserIntelligence:
        """Discover GitLab user information"""
        base_url = "https://gitlab.com/api/v4"
        
        # Search for user
        search_response = await self.client.get(f"{base_url}/users?username={username}")
        search_data = search_response.json()
        
        if not search_data:
            raise ValueError(f"User {username} not found on GitLab")
        
        user_data = search_data[0]
        user_id = user_data['id']
        
        # Get user projects
        projects_response = await self.client.get(f"{base_url}/users/{user_id}/projects?per_page=100")
        projects_data = projects_response.json() if projects_response.status_code == 200 else []
        
        await asyncio.sleep(self.rate_limit_delay)
        
        return UserIntelligence(
            username=username,
            email_addresses=[user_data.get('public_email')] if user_data.get('public_email') else [],
            repositories=[{
                'name': proj['name'],
                'stars': proj['star_count'],
                'language': 'Unknown',
                'updated': proj['last_activity_at']
            } for proj in projects_data],
            commit_count=len(projects_data),
            languages=[],
            activity_pattern={},
            social_connections=[],
            profile_data={
                'name': user_data.get('name'),
                'bio': user_data.get('bio'),
                'location': user_data.get('location'),
                'website': user_data.get('website_url'),
                'created_at': user_data.get('created_at')
            }
        )
    
    async def find_emails(self, target: str, search_type: str = "user") -> List[str]:
        """Find email addresses associated with a user or repository"""
        emails = set()
        
        if search_type == "user":
            # Search user across multiple platforms
            for platform in ["github", "gitlab"]:
                try:
                    user_intel = await self.discover_user_info(target, platform)
                    emails.update(user_intel.email_addresses)
                except:
                    continue
        elif search_type == "repo":
            # Extract emails from repository commits
            try:
                repo_intel = await self.analyze_repository(target)
                for contributor in repo_intel.contributors:
                    if 'email' in contributor:
                        emails.add(contributor['email'])
            except:
                pass
        
        return list(emails)
    
    async def map_social_network(self, username: str, depth: int = 2) -> Dict[str, Any]:
        """Map social network connections for a user"""
        network = {
            'center': username,
            'connections': {},
            'depth': depth,
            'total_connections': 0
        }
        
        try:
            # Get user's repositories and find collaborators
            user_intel = await self.discover_user_info(username, "github")
            
            # Analyze top repositories for collaborators
            for repo in user_intel.repositories[:5]:  # Limit to top 5 repos
                try:
                    repo_url = f"https://github.com/{username}/{repo['name']}"
                    repo_intel = await self.analyze_repository(repo_url)
                    
                    repo_connections = []
                    for contributor in repo_intel.contributors:
                        if contributor.get('login') != username:
                            repo_connections.append({
                                'username': contributor.get('login'),
                                'contributions': contributor.get('contributions', 0),
                                'type': 'collaborator'
                            })
                    
                    network['connections'][repo['name']] = repo_connections
                    network['total_connections'] += len(repo_connections)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze repo {repo['name']}: {str(e)}")
                    continue
                    
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.error(f"Network mapping failed: {str(e)}")
        
        return network
    
    async def scan_security_issues(self, repo_url: str) -> List[Dict[str, Any]]:
        """Scan repository for potential security issues"""
        issues = []
        
        try:
            repo_intel = await self.analyze_repository(repo_url)
            
            # Check for common security indicators
            if any(keyword in repo_intel.description.lower() for keyword in ['password', 'key', 'secret', 'token']):
                issues.append({
                    'type': 'potential_secret_exposure',
                    'severity': 'medium',
                    'description': 'Repository description mentions sensitive terms'
                })
            
            # Check for suspicious dependencies
            suspicious_deps = ['crypto-mining', 'bitcoin-miner', 'ethereum-miner']
            for dep in repo_intel.dependencies:
                if any(sus in dep.lower() for sus in suspicious_deps):
                    issues.append({
                        'type': 'suspicious_dependency',
                        'severity': 'high',
                        'description': f'Potentially malicious dependency: {dep}'
                    })
            
            # Check repository age and activity
            if repo_intel.commit_activity.get('recent_activity', 0) == 0:
                issues.append({
                    'type': 'inactive_repository',
                    'severity': 'low',
                    'description': 'Repository appears to be inactive'
                })
            
        except Exception as e:
            logger.error(f"Security scan failed: {str(e)}")
            issues.append({
                'type': 'scan_error',
                'severity': 'info',
                'description': f'Could not complete security scan: {str(e)}'
            })
        
        return issues
    
    # Helper methods
    def _process_commit_activity(self, activity_data: List[Dict]) -> Dict[str, Any]:
        """Process commit activity data"""
        if not activity_data:
            return {'recent_activity': 0, 'peak_week': 0, 'total_commits': 0}
        
        total_commits = sum(week.get('total', 0) for week in activity_data)
        recent_activity = sum(week.get('total', 0) for week in activity_data[-4:])  # Last 4 weeks
        peak_week = max(week.get('total', 0) for week in activity_data)
        
        return {
            'recent_activity': recent_activity,
            'peak_week': peak_week,
            'total_commits': total_commits
        }
    
    async def _check_security_indicators(self, repo_data: Dict) -> List[str]:
        """Check for security indicators in repository"""
        indicators = []
        
        # Check for security-related topics
        topics = repo_data.get('topics', [])
        security_topics = ['security', 'vulnerability', 'exploit', 'malware', 'ransomware']
        
        for topic in topics:
            if topic.lower() in security_topics:
                indicators.append(f"Security-related topic: {topic}")
        
        # Check if repository has security policy
        if repo_data.get('has_security_policy'):
            indicators.append("Has security policy")
        
        return indicators
    
    async def _extract_emails_from_repos(self, username: str, repos: List[Dict]) -> List[str]:
        """Extract email addresses from repository commits"""
        emails = []
        
        for repo in repos[:3]:  # Limit to 3 repos to avoid rate limiting
            try:
                repo_name = repo['name']
                commits_url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
                
                commits_response = await self.client.get(f"{commits_url}?per_page=10")
                if commits_response.status_code == 200:
                    commits_data = commits_response.json()
                    
                    for commit in commits_data:
                        author_email = commit.get('commit', {}).get('author', {}).get('email')
                        if author_email and '@' in author_email:
                            emails.append(author_email)
                
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.warning(f"Failed to extract emails from {repo['name']}: {str(e)}")
                continue
        
        return emails
    
    def _extract_languages(self, repos_data: List[Dict]) -> List[str]:
        """Extract programming languages from repositories"""
        languages = set()
        for repo in repos_data:
            lang = repo.get('language')
            if lang:
                languages.add(lang)
        return list(languages)
    
    def _analyze_activity_pattern(self, repos_data: List[Dict]) -> Dict[str, Any]:
        """Analyze user activity patterns"""
        if not repos_data:
            return {}
        
        # Analyze repository creation dates
        creation_dates = []
        for repo in repos_data:
            created_at = repo.get('created_at')
            if created_at:
                creation_dates.append(created_at)
        
        # Analyze update patterns
        update_dates = []
        for repo in repos_data:
            updated_at = repo.get('updated_at')
            if updated_at:
                update_dates.append(updated_at)
        
        return {
            'total_repositories': len(repos_data),
            'creation_span': f"{min(creation_dates)} to {max(creation_dates)}" if creation_dates else "Unknown",
            'last_activity': max(update_dates) if update_dates else "Unknown",
            'active_repositories': len([r for r in repos_data if r.get('updated_at')])
        }
    
    async def _find_social_connections(self, username: str) -> List[str]:
        """Find social connections for a user"""
        connections = []
        
        try:
            # Get user's following list (limited)
            following_response = await self.client.get(f"https://api.github.com/users/{username}/following?per_page=50")
            if following_response.status_code == 200:
                following_data = following_response.json()
                connections.extend([user['login'] for user in following_data])
            
            await asyncio.sleep(self.rate_limit_delay)
            
        except Exception as e:
            logger.warning(f"Failed to find social connections: {str(e)}")
        
        return connections[:20]  # Limit to 20 connections
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

# Initialize the MCP server
server = Server("gitosint-mcp")
analyzer = GitOSINTAnalyzer()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="analyze_repository",
            description="Analyze a Git repository for intelligence gathering",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {
                        "type": "string",
                        "description": "URL of the Git repository to analyze"
                    }
                },
                "required": ["repo_url"]
            },
        ),
        Tool(
            name="discover_user_info",
            description="Discover comprehensive user information across Git platforms",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Username to investigate"
                    },
                    "platform": {
                        "type": "string",
                        "description": "Git platform (github, gitlab)",
                        "enum": ["github", "gitlab"],
                        "default": "github"
                    }
                },
                "required": ["username"]
            },
        ),
        Tool(
            name="find_emails",
            description="Find email addresses associated with a user or repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Username or repository URL to search for emails"
                    },
                    "search_type": {
                        "type": "string",
                        "description": "Type of search (user or repo)",
                        "enum": ["user", "repo"],
                        "default": "user"
                    }
                },
                "required": ["target"]
            },
        ),
        Tool(
            name="map_social_network",
            description="Map social network connections for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Username to map social network for"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Depth of network mapping (1-3)",
                        "minimum": 1,
                        "maximum": 3,
                        "default": 2
                    }
                },
                "required": ["username"]
            },
        ),
        Tool(
            name="scan_security_issues",
            description="Scan repository for potential security issues and suspicious patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {
                        "type": "string",
                        "description": "URL of the repository to scan for security issues"
                    }
                },
                "required": ["repo_url"]
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    try:
        if name == "analyze_repository":
            repo_url = arguments.get("repo_url")
            if not repo_url:
                raise ValueError("Repository URL is required")
            
            result = await analyzer.analyze_repository(repo_url)
            return [types.TextContent(
                type="text",
                text=json.dumps(asdict(result), indent=2, default=str)
            )]
        
        elif name == "discover_user_info":
            username = arguments.get("username")
            platform = arguments.get("platform", "github")
            
            if not username:
                raise ValueError("Username is required")
            
            result = await analyzer.discover_user_info(username, platform)
            return [types.TextContent(
                type="text",
                text=json.dumps(asdict(result), indent=2, default=str)
            )]
        
        elif name == "find_emails":
            target = arguments.get("target")
            search_type = arguments.get("search_type", "user")
            
            if not target:
                raise ValueError("Target is required")
            
            result = await analyzer.find_emails(target, search_type)
            return [types.TextContent(
                type="text",
                text=json.dumps({"emails": result, "count": len(result)}, indent=2)
            )]
        
        elif name == "map_social_network":
            username = arguments.get("username")
            depth = arguments.get("depth", 2)
            
            if not username:
                raise ValueError("Username is required")
            
            result = await analyzer.map_social_network(username, depth)
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
        
        elif name == "scan_security_issues":
            repo_url = arguments.get("repo_url")
            
            if not repo_url:
                raise ValueError("Repository URL is required")
            
            result = await analyzer.scan_security_issues(repo_url)
            return [types.TextContent(
                type="text",
                text=json.dumps({"security_issues": result, "count": len(result)}, indent=2)
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Tool execution failed: {str(e)}")
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]

async def main():
    """Main entry point"""
    # Import here to avoid issues with event loop
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gitosint-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
