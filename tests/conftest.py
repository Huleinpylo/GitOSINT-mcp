"""
Pytest configuration and fixtures for GitOSINT-MCP tests
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line(
        "markers", 
        "integration: mark test as integration test requiring network access"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers",
        "mcp: mark test as MCP protocol specific"
    )


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests that require network access"
    )
    parser.addoption(
        "--slow",
        action="store_true", 
        default=False,
        help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options"""
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(reason="need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
    
    if not config.getoption("--slow"):
        skip_slow = pytest.mark.skip(reason="need --slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing without network calls"""
    client = AsyncMock()
    
    # Default successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"default": "response"}
    mock_response.raise_for_status.return_value = None
    
    client.get.return_value = mock_response
    client.aclose = AsyncMock()
    
    return client


@pytest.fixture
def sample_github_repo_data():
    """Sample GitHub repository data for testing"""
    return {
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "description": "A test repository for OSINT analysis",
        "stargazers_count": 100,
        "forks_count": 25,
        "language": "Python",
        "topics": ["test", "osint", "python"],
        "has_security_policy": True,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "default_branch": "main",
        "size": 1024,
        "open_issues_count": 3,
        "subscribers_count": 15,
        "owner": {
            "login": "testuser",
            "id": 123456,
            "type": "User"
        }
    }


@pytest.fixture
def sample_github_user_data():
    """Sample GitHub user data for testing"""
    return {
        "login": "testuser",
        "id": 123456,
        "name": "Test User",
        "email": "test@example.com",
        "bio": "Software developer and security researcher",
        "location": "San Francisco, CA",
        "company": "Test Security Corp",
        "blog": "https://testuser.dev",
        "twitter_username": "testuser",
        "public_repos": 25,
        "public_gists": 5,
        "followers": 150,
        "following": 75,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "hireable": True,
        "avatar_url": "https://avatars.githubusercontent.com/u/123456?v=4",
        "html_url": "https://github.com/testuser"
    }


@pytest.fixture
def sample_contributors_data():
    """Sample contributors data for testing"""
    return [
        {
            "login": "contributor1",
            "id": 111111,
            "contributions": 50,
            "type": "User",
            "avatar_url": "https://avatars.githubusercontent.com/u/111111?v=4",
            "html_url": "https://github.com/contributor1"
        },
        {
            "login": "contributor2",
            "id": 222222,
            "contributions": 25,
            "type": "User",
            "avatar_url": "https://avatars.githubusercontent.com/u/222222?v=4",
            "html_url": "https://github.com/contributor2"
        },
        {
            "login": "testuser",
            "id": 123456,
            "contributions": 100,
            "type": "User",
            "avatar_url": "https://avatars.githubusercontent.com/u/123456?v=4",
            "html_url": "https://github.com/testuser"
        }
    ]


@pytest.fixture
def sample_commits_data():
    """Sample commits data for testing"""
    return [
        {
            "sha": "abc123def456",
            "commit": {
                "author": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "date": "2023-12-01T10:00:00Z"
                },
                "committer": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "date": "2023-12-01T10:00:00Z"
                },
                "message": "Add new OSINT feature",
                "tree": {
                    "sha": "tree123",
                    "url": "https://api.github.com/repos/testuser/test-repo/git/trees/tree123"
                }
            },
            "author": {
                "login": "testuser",
                "id": 123456,
                "avatar_url": "https://avatars.githubusercontent.com/u/123456?v=4"
            },
            "committer": {
                "login": "testuser",
                "id": 123456,
                "avatar_url": "https://avatars.githubusercontent.com/u/123456?v=4"
            },
            "html_url": "https://github.com/testuser/test-repo/commit/abc123def456"
        },
        {
            "sha": "def456ghi789",
            "commit": {
                "author": {
                    "name": "Contributor",
                    "email": "contrib@example.com",
                    "date": "2023-11-30T15:00:00Z"
                },
                "committer": {
                    "name": "Contributor",
                    "email": "contrib@example.com",
                    "date": "2023-11-30T15:00:00Z"
                },
                "message": "Fix security vulnerability in analyzer",
                "tree": {
                    "sha": "tree456",
                    "url": "https://api.github.com/repos/testuser/test-repo/git/trees/tree456"
                }
            },
            "author": {
                "login": "contributor1",
                "id": 111111,
                "avatar_url": "https://avatars.githubusercontent.com/u/111111?v=4"
            },
            "committer": {
                "login": "contributor1",
                "id": 111111,
                "avatar_url": "https://avatars.githubusercontent.com/u/111111?v=4"
            },
            "html_url": "https://github.com/testuser/test-repo/commit/def456ghi789"
        }
    ]


@pytest.fixture
def sample_activity_data():
    """Sample commit activity data for testing"""
    return [
        {"total": 5, "week": 1670000000, "days": [1, 0, 2, 1, 1, 0, 0]},
        {"total": 10, "week": 1670604800, "days": [2, 1, 3, 2, 2, 0, 0]},
        {"total": 3, "week": 1671209600, "days": [0, 1, 1, 0, 1, 0, 0]},
        {"total": 8, "week": 1671814400, "days": [1, 2, 2, 1, 2, 0, 0]}
    ]


@pytest.fixture
def sample_languages_data():
    """Sample languages data for testing"""
    return {
        "Python": 10000,
        "JavaScript": 3000,
        "HTML": 1500,
        "CSS": 800,
        "Shell": 200
    }


@pytest.fixture
def sample_gitlab_user_data():
    """Sample GitLab user data for testing"""
    return [
        {
            "id": 789123,
            "username": "testuser",
            "name": "Test User",
            "state": "active",
            "avatar_url": "https://secure.gravatar.com/avatar/123456?s=80&d=identicon",
            "web_url": "https://gitlab.com/testuser",
            "created_at": "2020-01-01T00:00:00.000Z",
            "bio": "Software developer",
            "location": "San Francisco",
            "public_email": "test@example.com",
            "skype": "",
            "linkedin": "",
            "twitter": "testuser",
            "website_url": "https://testuser.dev",
            "organization": "Test Corp"
        }
    ]


@pytest.fixture
def sample_gitlab_projects_data():
    """Sample GitLab projects data for testing"""
    return [
        {
            "id": 12345,
            "name": "test-project",
            "path": "test-project",
            "path_with_namespace": "testuser/test-project",
            "description": "A test project on GitLab",
            "default_branch": "main",
            "star_count": 15,
            "forks_count": 3,
            "last_activity_at": "2023-12-01T00:00:00.000Z",
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-12-01T00:00:00.000Z",
            "web_url": "https://gitlab.com/testuser/test-project",
            "topics": ["python", "testing"]
        }
    ]


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    from src.gitosint_mcp.config import GitOSINTConfig, MCPConfig, PlatformConfig, SecurityConfig
    
    return GitOSINTConfig(
        mcp=MCPConfig(
            server_name="test-gitosint-mcp",
            server_version="1.0.0-test",
            log_level="DEBUG",
            rate_limit_delay=0.1,  # Faster for testing
            timeout_seconds=10  # Shorter for testing
        ),
        platforms=PlatformConfig(
            enable_github=True,
            enable_gitlab=True,
            enable_bitbucket=False
        ),
        security=SecurityConfig(
            respect_rate_limits=False,  # Disabled for testing
            log_requests=True,
            max_email_extraction=5  # Limited for testing
        )
    )


@pytest.fixture
def temp_config_file(tmp_path, mock_config):
    """Create a temporary configuration file for testing"""
    import json
    
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(mock_config.to_dict(), f, indent=2)
    
    return config_file


@pytest.fixture
def mock_analyzer():
    """Mock GitOSINT analyzer for testing"""
    from src.gitosint_mcp.server import GitOSINTAnalyzer, UserIntelligence, RepositoryIntel
    
    analyzer = AsyncMock(spec=GitOSINTAnalyzer)
    
    # Set up default return values
    analyzer.analyze_repository.return_value = RepositoryIntel(
        name="test/repo",
        description="Test repository",
        stars=100,
        forks=25,
        language="Python",
        topics=["test"],
        contributors=[],
        commit_activity={},
        security_issues=[],
        dependencies=[]
    )
    
    analyzer.discover_user_info.return_value = UserIntelligence(
        username="testuser",
        email_addresses=["test@example.com"],
        repositories=[],
        commit_count=10,
        languages=["Python"],
        activity_pattern={},
        social_connections=[],
        profile_data={"name": "Test User"}
    )
    
    analyzer.find_emails.return_value = ["test@example.com"]
    
    analyzer.map_social_network.return_value = {
        "center": "testuser",
        "connections": {},
        "total_connections": 0
    }
    
    analyzer.scan_security_issues.return_value = []
    
    analyzer.close = AsyncMock()
    
    return analyzer


@pytest.fixture
def environment_variables():
    """Set up environment variables for testing"""
    env_vars = {
        'GITOSINT_LOG_LEVEL': 'DEBUG',
        'GITOSINT_RATE_LIMIT_DELAY': '0.1',
        'GITOSINT_TIMEOUT': '10',
        'GITOSINT_ENABLE_GITHUB': 'true',
        'GITOSINT_ENABLE_GITLAB': 'true',
        'GITOSINT_RESPECT_RATE_LIMITS': 'false'
    }
    
    # Store original values
    original_values = {}
    for key in env_vars:
        original_values[key] = os.environ.get(key)
        os.environ[key] = env_vars[key]
    
    yield env_vars
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def capture_logs(caplog):
    """Capture logs for testing"""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing"""
    try:
        from mcp.server import Server
        server = Mock(spec=Server)
        server.list_tools = AsyncMock()
        server.call_tool = AsyncMock()
        return server
    except ImportError:
        # MCP not available, return mock
        server = Mock()
        server.list_tools = AsyncMock()
        server.call_tool = AsyncMock()
        return server


# Custom assertions
def assert_valid_email(email):
    """Assert that a string is a valid email format"""
    assert isinstance(email, str)
    assert "@" in email
    assert "." in email.split("@")[1]
    assert len(email.split("@")) == 2


def assert_valid_url(url):
    """Assert that a string is a valid URL format"""
    assert isinstance(url, str)
    assert url.startswith(("http://", "https://"))
    assert "." in url


def assert_valid_github_url(url):
    """Assert that a string is a valid GitHub URL"""
    assert_valid_url(url)
    assert "github.com" in url


def assert_valid_gitlab_url(url):
    """Assert that a string is a valid GitLab URL"""
    assert_valid_url(url)
    assert "gitlab.com" in url


# Test data generators
def generate_mock_repository_data(name="test/repo", **kwargs):
    """Generate mock repository data with customizable fields"""
    default_data = {
        "name": name,
        "description": "Test repository",
        "stars": 100,
        "forks": 25,
        "language": "Python",
        "topics": ["test"],
        "contributors": [],
        "commit_activity": {},
        "security_issues": [],
        "dependencies": {}
    }
    default_data.update(kwargs)
    return default_data


def generate_mock_user_data(username="testuser", **kwargs):
    """Generate mock user data with customizable fields"""
    default_data = {
        "username": username,
        "email_addresses": ["test@example.com"],
        "repositories": [],
        "commit_count": 10,
        "languages": ["Python"],
        "activity_pattern": {},
        "social_connections": [],
        "profile_data": {"name": "Test User"}
    }
    default_data.update(kwargs)
    return default_data


# Pytest hooks for test reporting
def pytest_runtest_makereport(item, call):
    """Create test reports with additional information"""
    if "integration" in item.keywords:
        if call.excinfo is not None and "skip" not in str(call.excinfo.value):
            # Integration test failed - add network info
            item._network_test_failed = True


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add custom summary information to test results"""
    if hasattr(terminalreporter.config, 'getoption'):
        if not terminalreporter.config.getoption('--integration'):
            terminalreporter.write_line(
                "Integration tests skipped. Use --integration to run them.",
                yellow=True
            )
        
        if not terminalreporter.config.getoption('--slow'):
            terminalreporter.write_line(
                "Slow tests skipped. Use --slow to run them.",
                yellow=True
            )


# Async test utilities
async def wait_for_condition(condition, timeout=5.0, interval=0.1):
    """Wait for a condition to become true within a timeout"""
    import asyncio
    import time
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if await condition() if asyncio.iscoroutinefunction(condition) else condition():
            return True
        await asyncio.sleep(interval)
    return False


# Test data validation
def validate_repository_intel(repo_intel):
    """Validate RepositoryIntel data structure"""
    from src.gitosint_mcp.server import RepositoryIntel
    
    assert isinstance(repo_intel, RepositoryIntel)
    assert isinstance(repo_intel.name, str)
    assert isinstance(repo_intel.stars, int)
    assert isinstance(repo_intel.forks, int)
    assert isinstance(repo_intel.topics, list)
    assert isinstance(repo_intel.contributors, list)
    assert isinstance(repo_intel.security_issues, list)


def validate_user_intelligence(user_intel):
    """Validate UserIntelligence data structure"""
    from src.gitosint_mcp.server import UserIntelligence
    
    assert isinstance(user_intel, UserIntelligence)
    assert isinstance(user_intel.username, str)
    assert isinstance(user_intel.email_addresses, list)
    assert isinstance(user_intel.repositories, list)
    assert isinstance(user_intel.commit_count, int)
    assert isinstance(user_intel.languages, list)
    assert isinstance(user_intel.social_connections, list)
    assert isinstance(user_intel.profile_data, dict)


# Performance testing utilities
class PerformanceTimer:
    """Context manager for measuring execution time"""
    
    def __init__(self, name="operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, _, __, ___):
        import time
        self.end_time = time.time()
        self.duration = (self.end_time or 0) - (self.start_time or 0)
    
    def assert_duration_less_than(self, max_duration):
        """Assert that the operation completed within the specified time"""
        assert self.duration is not None, "Timer was not properly used"
        assert self.duration < max_duration, (
            f"{self.name} took {self.duration:.2f}s, "
            f"expected less than {max_duration}s"
        )


@pytest.fixture
def performance_timer():
    """Fixture providing performance timing utility"""
    return PerformanceTimer