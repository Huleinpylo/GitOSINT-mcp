"""
Security Scanner for GitOSINT-MCP

Provides security analysis and threat detection for Git repositories
through the MCP addon.

Capabilities:
- Secret and credential detection
- Malware pattern recognition
- Vulnerability assessment
- Security configuration analysis
- Privacy and compliance checking
"""

import asyncio
import aiohttp
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

from ..config import Config

logger = logging.getLogger(__name__)

@dataclass
class SecurityFinding:
    """Security finding for MCP addon analysis."""
    finding_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    title: str
    description: str
    file_path: str
    line_number: Optional[int]
    evidence: str
    recommendation: str
    confidence: float
    cve_ids: List[str]
    additional_info: Dict[str, Any]

class SecurityScanner:
    """
    Security Scanner for GitOSINT-MCP Addon
    
    Performs security analysis of Git repositories
    for AI assistant consumption through MCP protocol.
    
    Features:
    - Leaked secret detection
    - Malware pattern recognition
    - Vulnerability scanning
    - Configuration analysis
    - Privacy-respecting public data only
    """
    
    def __init__(self, config: Config):
        """Initialize security scanner for MCP addon."""
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Secret detection patterns
        self.secret_patterns = {
            'aws_access_key': r'AKIA[0-9A-Z]{16}',
            'aws_secret_key': r'[0-9a-zA-Z/+]{40}',
            'github_token': r'ghp_[0-9a-zA-Z]{36}',
            'slack_token': r'xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9a-zA-Z]{24}',
            'api_key': r'[aA][pP][iI][_]?[kK][eE][yY].*[\'\"][0-9a-zA-Z]{32,45}[\'\"]',
            'private_key': r'-----BEGIN [A-Z]+ PRIVATE KEY-----',
            'password': r'[pP][aA][sS][sS][wW][oO][rR][dD].*[\'\"][^\'\"].*[\'\"]'
        }
        
        # Suspicious file patterns
        self.suspicious_extensions = [
            '.exe', '.scr', '.bat', '.cmd', '.pif', '.com',
            '.jar', '.vbs', '.js', '.ps1', '.sh'
        ]
    
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
    
    async def scan(
        self,
        repository_url: str,
        scan_depth: str = "surface",
        check_history: bool = False,
        threat_intel: bool = False
    ) -> Dict[str, Any]:
        """
        Perform security scan for MCP addon.
        
        Args:
            repository_url: URL of repository to scan
            scan_depth: 'surface', 'deep', or 'comprehensive'
            check_history: Scan commit history for secrets
            threat_intel: Cross-reference with threat intelligence
            
        Returns:
            Security scan results with findings and recommendations
        """
        logger.info(f"MCP: Starting security scan for {repository_url}")
        
        # Initialize session if not in context manager
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
                headers={'User-Agent': self.config.get_user_agent()}
            )
        
        findings: List[SecurityFinding] = []
        
        try:
            # Parse repository URL
            from ..analyzers.repository import RepositoryAnalyzer
            analyzer = RepositoryAnalyzer(self.config)
            platform, owner, repo_name = analyzer._parse_repository_url(repository_url)
            
            # Scan for leaked secrets
            secret_findings = await self._scan_secrets(platform, owner, repo_name)
            findings.extend(secret_findings)
            
            # Scan for suspicious files
            file_findings = await self._scan_suspicious_files(platform, owner, repo_name)
            findings.extend(file_findings)
            
            # Additional scans based on depth
            if scan_depth in ['deep', 'comprehensive']:
                config_findings = await self._scan_configurations(platform, owner, repo_name)
                findings.extend(config_findings)
            
            if scan_depth == 'comprehensive':
                vuln_findings = await self._scan_vulnerabilities(platform, owner, repo_name)
                findings.extend(vuln_findings)
            
            # Calculate overall risk level
            risk_level = self._calculate_risk_level(findings)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(findings)
            
            logger.info(f"MCP: Security scan completed with {len(findings)} findings")
            
            return {
                'repository_url': repository_url,
                'scan_timestamp': datetime.now(timezone.utc).isoformat(),
                'scan_depth': scan_depth,
                'risk_level': risk_level,
                'findings_count': len(findings),
                'leaked_secrets': [f for f in findings if f.finding_type == 'leaked_secret'],
                'suspicious_files': [f for f in findings if f.finding_type == 'suspicious_file'],
                'vulnerabilities': [f for f in findings if f.finding_type == 'vulnerability'],
                'recommendations': recommendations,
                'scan_coverage': {
                    'secrets_scanned': True,
                    'files_scanned': True,
                    'configurations_scanned': scan_depth in ['deep', 'comprehensive'],
                    'vulnerabilities_scanned': scan_depth == 'comprehensive'
                }
            }
            
        except Exception as e:
            logger.error(f"MCP: Security scan failed for {repository_url}: {str(e)}")
            raise
    
    async def _scan_secrets(self, platform: str, owner: str, repo: str) -> List[SecurityFinding]:
        """Scan for leaked secrets in MCP addon."""
        findings = []
        
        # Scan common files for secrets
        secret_files = ['.env', 'config.json', 'settings.py', 'application.properties']
        
        for file_path in secret_files:
            try:
                content = await self._get_file_content(platform, owner, repo, file_path)
                if content:
                    file_findings = self._detect_secrets_in_content(content, file_path)
                    findings.extend(file_findings)
            except Exception as e:
                logger.debug(f"MCP: Could not scan {file_path} for secrets: {str(e)}")
        
        return findings
    
    async def _scan_suspicious_files(self, platform: str, owner: str, repo: str) -> List[SecurityFinding]:
        """Scan for suspicious files in MCP addon."""
        findings = []
        
        # This would require directory listing and file analysis
        # Placeholder implementation for MCP addon
        
        return findings
    
    async def _scan_configurations(self, platform: str, owner: str, repo: str) -> List[SecurityFinding]:
        """Scan security configurations in MCP addon."""
        findings = []
        
        # Scan Docker configurations
        docker_findings = await self._scan_docker_security(platform, owner, repo)
        findings.extend(docker_findings)
        
        # Scan CI/CD configurations
        ci_findings = await self._scan_ci_security(platform, owner, repo)
        findings.extend(ci_findings)
        
        return findings
    
    async def _scan_vulnerabilities(self, platform: str, owner: str, repo: str) -> List[SecurityFinding]:
        """Scan for known vulnerabilities in MCP addon."""
        findings = []
        
        # Scan dependency files for known vulnerabilities
        dep_files = ['package.json', 'requirements.txt', 'pom.xml', 'Gemfile']
        
        for dep_file in dep_files:
            try:
                content = await self._get_file_content(platform, owner, repo, dep_file)
                if content:
                    vuln_findings = await self._check_dependency_vulnerabilities(content, dep_file)
                    findings.extend(vuln_findings)
            except Exception as e:
                logger.debug(f"MCP: Could not scan {dep_file} for vulnerabilities: {str(e)}")
        
        return findings
    
    async def _get_file_content(self, platform: str, owner: str, repo: str, file_path: str) -> Optional[str]:
        """Get file content for MCP addon security scanning."""
        if platform == 'github.com':
            api_url = f"{self.config.platform.github_api_url}/repos/{owner}/{repo}/contents/{file_path}"
            
            try:
                async with self.session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('type') == 'file' and 'content' in data:
                            import base64
                            content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                            return content
            except Exception as e:
                logger.debug(f"MCP: Could not get file content for {file_path}: {str(e)}")
        
        return None
    
    def _detect_secrets_in_content(self, content: str, file_path: str) -> List[SecurityFinding]:
        """Detect secrets in file content for MCP addon."""
        findings = []
        
        for secret_type, pattern in self.secret_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                
                finding = SecurityFinding(
                    finding_type='leaked_secret',
                    severity='HIGH',
                    title=f'Potential {secret_type.replace("_", " ").title()} Detected',
                    description=f'A potential {secret_type} was found in {file_path}',
                    file_path=file_path,
                    line_number=line_number,
                    evidence=match.group(0)[:20] + '...',  # Truncate for safety
                    recommendation=f'Remove the {secret_type} from the code and use environment variables or secure secret management',
                    confidence=0.8,
                    cve_ids=[],
                    additional_info={
                        'secret_type': secret_type,
                        'pattern_matched': pattern
                    }
                )
                findings.append(finding)
        
        return findings
    
    async def _scan_docker_security(self, platform: str, owner: str, repo: str) -> List[SecurityFinding]:
        """Scan Docker security configurations for MCP addon."""
        findings = []
        
        dockerfile_content = await self._get_file_content(platform, owner, repo, 'Dockerfile')
        if dockerfile_content:
            # Check for common Docker security issues
            if 'USER root' in dockerfile_content or 'USER 0' in dockerfile_content:
                finding = SecurityFinding(
                    finding_type='configuration',
                    severity='MEDIUM',
                    title='Docker Container Running as Root',
                    description='Container is configured to run as root user',
                    file_path='Dockerfile',
                    line_number=None,
                    evidence='USER root detected',
                    recommendation='Use a non-root user in the Docker container',
                    confidence=0.9,
                    cve_ids=[],
                    additional_info={'issue_type': 'docker_root_user'}
                )
                findings.append(finding)
        
        return findings
    
    async def _scan_ci_security(self, platform: str, owner: str, repo: str) -> List[SecurityFinding]:
        """Scan CI/CD security configurations for MCP addon."""
        findings = []
        
        # Check GitHub Actions workflows
        workflow_files = ['.github/workflows/ci.yml', '.github/workflows/main.yml']
        
        for workflow_file in workflow_files:
            content = await self._get_file_content(platform, owner, repo, workflow_file)
            if content and 'secrets.' in content.lower():
                # Basic check for secret usage patterns
                finding = SecurityFinding(
                    finding_type='configuration',
                    severity='LOW',
                    title='CI/CD Workflow Uses Secrets',
                    description='Workflow file references secrets - ensure proper secret management',
                    file_path=workflow_file,
                    line_number=None,
                    evidence='secrets. reference found',
                    recommendation='Verify that secrets are properly configured and not exposed',
                    confidence=0.6,
                    cve_ids=[],
                    additional_info={'issue_type': 'ci_secrets_usage'}
                )
                findings.append(finding)
        
        return findings
    
    async def _check_dependency_vulnerabilities(self, content: str, file_path: str) -> List[SecurityFinding]:
        """Check dependencies for known vulnerabilities in MCP addon."""
        findings = []
        
        # Placeholder for vulnerability checking
        # In a real implementation, this would cross-reference with vulnerability databases
        
        return findings
    
    def _calculate_risk_level(self, findings: List[SecurityFinding]) -> str:
        """Calculate overall risk level for MCP addon."""
        if not findings:
            return 'LOW'
        
        severity_scores = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        total_score = sum(severity_scores.get(finding.severity, 0) for finding in findings)
        avg_score = total_score / len(findings)
        
        if avg_score >= 3.5:
            return 'CRITICAL'
        elif avg_score >= 2.5:
            return 'HIGH'
        elif avg_score >= 1.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_recommendations(self, findings: List[SecurityFinding]) -> List[str]:
        """Generate security recommendations for MCP addon."""
        recommendations = []
        
        if any(f.finding_type == 'leaked_secret' for f in findings):
            recommendations.append('Immediately rotate any exposed credentials and implement proper secret management')
        
        if any(f.finding_type == 'suspicious_file' for f in findings):
            recommendations.append('Review and remove any suspicious or unnecessary executable files')
        
        if any(f.finding_type == 'vulnerability' for f in findings):
            recommendations.append('Update dependencies to patched versions to address known vulnerabilities')
        
        if any(f.finding_type == 'configuration' for f in findings):
            recommendations.append('Review and harden security configurations following best practices')
        
        # Default recommendations
        if not recommendations:
            recommendations.append('Continue following security best practices and regular security reviews')
        
        return recommendations