"""
Repository Analyzer for GitOSINT-MCP

Provides comprehensive analysis of Git repositories for OSINT intelligence
including metadata extraction, contributor analysis, and development patterns.

This analyzer is specifically designed for MCP addon integration,
formatting results for consumption by AI assistants.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import re

from ..config import Config

logger = logging.getLogger(__name__)

@dataclass
class RepositoryInfo:
    """Repository information structure for MCP addon."""
    name: str
    owner: str
    full_name: str
    description: Optional[str]
    primary_language: Optional[str]
    languages: Dict[str, float]
    stars: int
    forks: int
    watchers: int
    size_kb: int
    created_at: str
    updated_at: str
    pushed_at: str
    is_fork: bool
    is_archived: bool
    is_private: bool
    default_branch: str
    topics: List[str]
    license_name: Optional[str]
    homepage: Optional[str]

@dataclass
class ContributorInfo:
    """Contributor information for MCP analysis."""
    login: str
    id: int
    type: str  # User or Organization
    contributions: int
    avatar_url: str
    profile_url: str
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None

class RepositoryAnalyzer:
    """
    Repository Analyzer for GitOSINT-MCP Addon
    
    Provides comprehensive OSINT analysis of Git repositories
    with focus on intelligence gathering for AI assistants.
    
    Features:
    - Multi-platform support (GitHub, GitLab, Bitbucket)
    - Async operation for performance
    - Rate limiting and security controls
    - Structured output for MCP integration
    """
    
    def __init__(self, config: Config):
        """Initialize repository analyzer for MCP addon."""
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._platform_parsers = {
            'github.com': self._parse_github_url,
            'gitlab.com': self._parse_gitlab_url,
            'bitbucket.org': self._parse_bitbucket_url
        }
    
    async def __aenter__(self):
        """Async context manager entry for MCP addon."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            headers={'User-Agent': self.config.get_user_agent()}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit for MCP addon."""
        if self.session:
            await self.session.close()
    
    async def analyze(
        self, 
        repository_url: str, 
        depth: str = "basic",
        include_contributors: bool = True,
        include_commits: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze repository for OSINT intelligence via MCP addon.
        
        Args:
            repository_url: URL of the repository to analyze
            depth: Analysis depth ('basic' or 'detailed')
            include_contributors: Include contributor analysis
            include_commits: Include commit pattern analysis
            
        Returns:
            Comprehensive repository analysis results
        """
        logger.info(f"MCP: Starting repository analysis for {repository_url}")
        
        # Parse repository URL
        platform, owner, repo_name = self._parse_repository_url(repository_url)
        
        if not self.config.is_domain_allowed(platform):
            raise ValueError(f"Platform {platform} is not allowed by configuration")
        
        # Initialize session if not in context manager
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
                headers={'User-Agent': self.config.get_user_agent()}
            )
        
        results = {
            'repository_url': repository_url,
            'platform': platform,
            'analysis_depth': depth,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        try:
            # Get basic repository information
            basic_info = await self._get_repository_info(platform, owner, repo_name)
            results['basic_info'] = basic_info.__dict__ if basic_info else None
            
            # Get contributors if requested
            if include_contributors:
                contributors = await self._get_contributors(platform, owner, repo_name)
                results['contributors'] = [c.__dict__ for c in contributors]
            
            # Get language statistics
            languages = await self._get_languages(platform, owner, repo_name)
            results['languages'] = languages
            
            # Detailed analysis for MCP addon
            if depth == 'detailed':
                # Get repository topics and metadata
                topics = await self._get_repository_topics(platform, owner, repo_name)
                results['topics'] = topics
                
                # Get branch information
                branches = await self._get_branches(platform, owner, repo_name)
                results['branches'] = branches
                
                # Get recent releases
                releases = await self._get_releases(platform, owner, repo_name)
                results['releases'] = releases
                
                # Commit analysis if requested
                if include_commits:
                    commit_stats = await self._analyze_commits(platform, owner, repo_name)
                    results['commit_analysis'] = commit_stats
            
            logger.info(f"MCP: Repository analysis completed for {repository_url}")
            return results
            
        except Exception as e:
            logger.error(f"MCP: Repository analysis failed for {repository_url}: {str(e)}")
            raise
    
    def _parse_repository_url(self, url: str) -> tuple[str, str, str]:
        """Parse repository URL for MCP addon processing."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Parse path to extract owner and repository
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError(f"Invalid repository URL format: {url}")
        
        owner = path_parts[0]
        repo_name = path_parts[1]
        
        # Remove .git suffix if present
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        # Validate platform support for MCP addon
        if domain not in self._platform_parsers:
            raise ValueError(f"Unsupported platform: {domain}")
        
        return domain, owner, repo_name
    
    def _parse_github_url(self, url: str) -> tuple[str, str]:
        """Parse GitHub repository URL for MCP addon."""
        # Implementation specific to GitHub
        return self._parse_repository_url(url)[1:]
    
    def _parse_gitlab_url(self, url: str) -> tuple[str, str]:
        """Parse GitLab repository URL for MCP addon."""
        # Implementation specific to GitLab
        return self._parse_repository_url(url)[1:]
    
    def _parse_bitbucket_url(self, url: str) -> tuple[str, str]:
        """Parse Bitbucket repository URL for MCP addon."""
        # Implementation specific to Bitbucket
        return self._parse_repository_url(url)[1:]
    
    async def _get_repository_info(self, platform: str, owner: str, repo: str) -> Optional[RepositoryInfo]:
        """Get basic repository information for MCP addon."""
        if platform == 'github.com':
            return await self._get_github_repo_info(owner, repo)
        elif platform == 'gitlab.com':
            return await self._get_gitlab_repo_info(owner, repo)
        elif platform == 'bitbucket.org':
            return await self._get_bitbucket_repo_info(owner, repo)
        else:
            logger.warning(f"MCP: Unsupported platform for repo info: {platform}")
            return None
    
    async def _get_github_repo_info(self, owner: str, repo: str) -> Optional[RepositoryInfo]:
        """Get GitHub repository information for MCP addon."""
        api_url = f"{self.config.platform.github_api_url}/repos/{owner}/{repo}"
        
        try:
            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return RepositoryInfo(
                        name=data.get('name', ''),
                        owner=data.get('owner', {}).get('login', ''),
                        full_name=data.get('full_name', ''),
                        description=data.get('description'),
                        primary_language=data.get('language'),
                        languages={},  # Will be filled separately
                        stars=data.get('stargazers_count', 0),
                        forks=data.get('forks_count', 0),
                        watchers=data.get('watchers_count', 0),
                        size_kb=data.get('size', 0),
                        created_at=data.get('created_at', ''),
                        updated_at=data.get('updated_at', ''),
                        pushed_at=data.get('pushed_at', ''),
                        is_fork=data.get('fork', False),
                        is_archived=data.get('archived', False),
                        is_private=data.get('private', False),
                        default_branch=data.get('default_branch', 'main'),
                        topics=data.get('topics', []),
                        license_name=data.get('license', {}).get('name') if data.get('license') else None,
                        homepage=data.get('homepage')
                    )
                else:
                    logger.warning(f"MCP: GitHub API returned {response.status} for {owner}/{repo}")
                    return None
        except Exception as e:
            logger.error(f"MCP: Failed to get GitHub repo info for {owner}/{repo}: {str(e)}")
            return None
    
    async def _get_gitlab_repo_info(self, owner: str, repo: str) -> Optional[RepositoryInfo]:
        """Get GitLab repository information for MCP addon."""
        # Placeholder for GitLab implementation
        logger.info(f"MCP: GitLab support not yet implemented for {owner}/{repo}")
        return None
    
    async def _get_bitbucket_repo_info(self, owner: str, repo: str) -> Optional[RepositoryInfo]:
        """Get Bitbucket repository information for MCP addon."""
        # Placeholder for Bitbucket implementation
        logger.info(f"MCP: Bitbucket support not yet implemented for {owner}/{repo}")
        return None
    
    async def _get_contributors(self, platform: str, owner: str, repo: str) -> List[ContributorInfo]:
        """Get repository contributors for MCP addon analysis."""
        if platform == 'github.com':
            return await self._get_github_contributors(owner, repo)
        else:
            logger.warning(f"MCP: Contributors not yet supported for {platform}")
            return []
    
    async def _get_github_contributors(self, owner: str, repo: str) -> List[ContributorInfo]:
        """Get GitHub contributors for MCP addon."""
        api_url = f"{self.config.platform.github_api_url}/repos/{owner}/{repo}/contributors"
        contributors = []
        
        try:
            params = {'per_page': min(100, self.config.platform.max_contributors_per_repo)}
            async with self.session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    for contributor_data in data:
                        contributor = ContributorInfo(
                            login=contributor_data.get('login', ''),
                            id=contributor_data.get('id', 0),
                            type=contributor_data.get('type', 'User'),
                            contributions=contributor_data.get('contributions', 0),
                            avatar_url=contributor_data.get('avatar_url', ''),
                            profile_url=contributor_data.get('html_url', '')
                        )
                        contributors.append(contributor)
                else:
                    logger.warning(f"MCP: GitHub contributors API returned {response.status} for {owner}/{repo}")
        except Exception as e:
            logger.error(f"MCP: Failed to get GitHub contributors for {owner}/{repo}: {str(e)}")
        
        return contributors
    
    async def _get_languages(self, platform: str, owner: str, repo: str) -> Dict[str, float]:
        """Get programming language statistics for MCP addon."""
        if platform == 'github.com':
            return await self._get_github_languages(owner, repo)
        else:
            logger.warning(f"MCP: Languages not yet supported for {platform}")
            return {}
    
    async def _get_github_languages(self, owner: str, repo: str) -> Dict[str, float]:
        """Get GitHub language statistics for MCP addon."""
        api_url = f"{self.config.platform.github_api_url}/repos/{owner}/{repo}/languages"
        
        try:
            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Convert bytes to percentages
                    total_bytes = sum(data.values())
                    if total_bytes > 0:
                        return {lang: (bytes_count / total_bytes) * 100 
                               for lang, bytes_count in data.items()}
                    else:
                        return data
                else:
                    logger.warning(f"MCP: GitHub languages API returned {response.status} for {owner}/{repo}")
                    return {}
        except Exception as e:
            logger.error(f"MCP: Failed to get GitHub languages for {owner}/{repo}: {str(e)}")
            return {}
    
    async def _get_repository_topics(self, platform: str, owner: str, repo: str) -> List[str]:
        """Get repository topics for MCP addon analysis."""
        # This is often included in basic repo info, but can be separate API call
        return []
    
    async def _get_branches(self, platform: str, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get repository branches for MCP addon."""
        # Placeholder for branch analysis
        return []
    
    async def _get_releases(self, platform: str, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get repository releases for MCP addon."""
        # Placeholder for release analysis
        return []
    
    async def _analyze_commits(self, platform: str, owner: str, repo: str) -> Dict[str, Any]:
        """Analyze commit patterns for MCP addon."""
        # Placeholder for commit analysis
        return {
            'total_commits': 0,
            'recent_activity': {},
            'commit_frequency': {},
            'author_statistics': {}
        }