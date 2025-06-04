"""
Email Discovery Module for GitOSINT-MCP

Provides email address discovery from Git repositories and user profiles
for the MCP addon using various OSINT techniques.

Capabilities:
- Git commit metadata extraction
- Documentation scanning
- Profile information correlation
- Cross-reference validation
- Confidence scoring
"""

import asyncio
import aiohttp
import logging
import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timezone

from ..config import Config

logger = logging.getLogger(__name__)

@dataclass
class EmailResult:
    """Email discovery result for MCP addon."""
    email: str
    source: str
    confidence: float
    associated_names: List[str]
    discovery_method: str
    first_seen: str
    last_seen: str
    validation_status: str  # valid, invalid, unknown
    additional_info: Dict[str, Any]

class EmailDiscovery:
    """
    Email Discovery Engine for GitOSINT-MCP Addon
    
    Discovers email addresses associated with Git repositories
    and users using multiple OSINT techniques.
    """
    
    def __init__(self, config: Config):
        """Initialize email discovery engine for MCP addon."""
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Email regex patterns for discovery
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\s*\[dot\]\s*[A-Z|a-z]{2,}\b',
            r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}\b'
        ]
        
        # Common obfuscation patterns
        self.obfuscation_replacements = {
            '[at]': '@',
            '[AT]': '@',
            '(at)': '@',
            ' at ': '@',
            '[dot]': '.',
            '[DOT]': '.',
            '(dot)': '.',
            ' dot ': '.'
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
    
    async def find(
        self,
        target: str,
        target_type: str,
        confidence_threshold: float = 0.5,
        validate: bool = True
    ) -> List[EmailResult]:
        """
        Find email addresses for MCP addon intelligence.
        
        Args:
            target: Repository URL or username
            target_type: 'repository' or 'user'
            confidence_threshold: Minimum confidence score (0.0-1.0)
            validate: Perform email validation checks
            
        Returns:
            List of discovered email addresses with metadata
        """
        logger.info(f"MCP: Starting email discovery for {target_type}: {target}")
        
        # Initialize session if not in context manager
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
                headers={'User-Agent': self.config.get_user_agent()}
            )
        
        discovered_emails = set()
        
        try:
            if target_type == 'repository':
                emails = await self._find_repository_emails(target)
                discovered_emails.update(emails)
            elif target_type == 'user':
                emails = await self._find_user_emails(target)
                discovered_emails.update(emails)
            else:
                raise ValueError(f"Unsupported target type: {target_type}")
            
            # Filter by confidence threshold
            filtered_emails = [
                email for email in discovered_emails 
                if email.confidence >= confidence_threshold
            ]
            
            # Validate emails if requested
            if validate:
                for email_result in filtered_emails:
                    email_result.validation_status = await self._validate_email(email_result.email)
            
            logger.info(f"MCP: Email discovery completed, found {len(filtered_emails)} emails")
            return filtered_emails
            
        except Exception as e:
            logger.error(f"MCP: Email discovery failed for {target}: {str(e)}")
            raise
    
    def _is_noreply_email(self, email: str) -> bool:
        """Check if email is a noreply/automated email for MCP addon."""
        noreply_patterns = [
            'noreply',
            'no-reply',
            'donotreply',
            'bot@',
            'action@',
            'github.com',
            'users.noreply.github.com'
        ]
        
        email_lower = email.lower()
        return any(pattern in email_lower for pattern in noreply_patterns)
    
    def _calculate_email_confidence(self, email: str, context: str) -> float:
        """Calculate confidence score for discovered email in MCP addon."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on context
        context_lower = context.lower()
        
        # Email appears in contact section
        if any(keyword in context_lower for keyword in ['contact', 'email', 'author', 'maintainer']):
            confidence += 0.2
        
        # Email domain matches repository domain
        if '@' in email:
            domain = email.split('@')[1]
            if domain in context_lower:
                confidence += 0.1
        
        # Email appears multiple times
        if context_lower.count(email.lower()) > 1:
            confidence += 0.1
        
        # Limit to maximum confidence
        return min(confidence, 1.0)
    
    async def _validate_email(self, email: str) -> str:
        """Validate email address for MCP addon."""
        # Basic format validation
        if not self._is_valid_email_format(email):
            return "invalid"
        
        # Additional validation could be added here
        # (DNS checks, SMTP checks, etc. - but respect privacy and rate limits)
        
        return "unknown"  # Conservative approach for MCP addon
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Check if email has valid format for MCP addon."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    # Placeholder methods for implementation
    async def _find_repository_emails(self, repo_url: str) -> Set[EmailResult]:
        """Find emails in repository for MCP addon."""
        return set()  # Placeholder implementation
    
    async def _find_user_emails(self, username: str) -> Set[EmailResult]:
        """Find emails for user for MCP addon."""
        return set()  # Placeholder implementation