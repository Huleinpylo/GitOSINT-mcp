#!/bin/bash
# GitOSINT-MCP Easy Installation Script
# Author: Huleinpylo
# License: MIT

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/Huleinpylo/GitOSINT-mcp.git"
INSTALL_DIR="$HOME/.local/share/gitosint-mcp"
PYTHON_MIN_VERSION="3.9"

# Helper functions
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════╗"
    echo "║           GitOSINT-MCP Installer             ║"
    echo "║     OSINT Intelligence from Git Repos        ║"
    echo "╚══════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_python() {
    print_step "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.9+ first."
        echo "Visit: https://python.org/downloads"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
        print_success "Python $PYTHON_VERSION is compatible"
    else
        print_error "Python $PYTHON_VERSION found, but Python 3.9+ is required"
        exit 1
    fi
}

check_git() {
    print_step "Checking Git installation..."
    
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install Git first."
        echo "Visit: https://git-scm.com/downloads"
        exit 1
    fi
    
    print_success "Git is available"
}

install_method_pip() {
    print_step "Installing GitOSINT-MCP via pip..."
    
    # Install from PyPI (when available)
    if pip3 show gitosint-mcp &> /dev/null; then
        print_warning "GitOSINT-MCP is already installed. Upgrading..."
        pip3 install --upgrade gitosint-mcp
    else
        pip3 install gitosint-mcp
    fi
    
    print_success "GitOSINT-MCP installed via pip"
}

install_method_source() {
    print_step "Installing GitOSINT-MCP from source..."
    
    # Create install directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Clone repository
    if [ -d ".git" ]; then
        print_warning "Repository already exists. Updating..."
        git pull origin feat-mcp
    else
        git clone -b feat-mcp "$REPO_URL" .
    fi
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
    
    print_success "GitOSINT-MCP installed from source"
}

install_method_docker() {
    print_step "Installing GitOSINT-MCP via Docker..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Create directory for Docker setup
    mkdir -p "$INSTALL_DIR/docker"
    cd "$INSTALL_DIR/docker"
    
    # Download Docker Compose file
    curl -s https://raw.githubusercontent.com/Huleinpylo/GitOSINT-mcp/feat-mcp/docker-compose.yml -o docker-compose.yml
    
    # Pull and run
    docker-compose pull
    docker-compose up -d
    
    print_success "GitOSINT-MCP Docker container is running"
}

configure_claude_desktop() {
    print_step "Configuring Claude Desktop integration..."
    
    local config_dir
    case "$(uname -s)" in
        Darwin*)
            config_dir="$HOME/Library/Application Support/Claude"
            ;;
        Linux*)
            config_dir="$HOME/.config/claude"
            ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*)
            config_dir="$APPDATA/Claude"
            ;;
        *)
            print_warning "Unknown OS. Please configure Claude Desktop manually."
            return
            ;;
    esac
    
    mkdir -p "$config_dir"
    
    local config_file="$config_dir/claude_desktop_config.json"
    
    if [ -f "$config_file" ]; then
        print_warning "Claude Desktop config exists. Backing up..."
        cp "$config_file" "$config_file.backup.$(date +%s)"
    fi
    
    # Create or update config
    cat > "$config_file" << EOF
{
  "mcpServers": {
    "gitosint-mcp": {
      "command": "python",
      "args": ["-m", "src.gitosint_mcp.server"],
      "cwd": "$INSTALL_DIR"
    }
  }
}
EOF
    
    print_success "Claude Desktop configured"
    print_warning "Please restart Claude Desktop to apply changes"
}

configure_cursor() {
    print_step "Configuring Cursor IDE integration..."
    
    local cursor_config="$HOME/.cursor/mcp_servers.json"
    mkdir -p "$(dirname "$cursor_config")"
    
    cat > "$cursor_config" << EOF
{
  "gitosint-mcp": {
    "command": "python",
    "args": ["-m", "src.gitosint_mcp.server"],
    "cwd": "$INSTALL_DIR"
  }
}
EOF
    
    print_success "Cursor IDE configured"
}

show_usage() {
    echo
    print_step "Usage Examples:"
    echo
    echo "📋 Available Commands:"
    echo "  gitosint-mcp analyze-repo https://github.com/user/repo"
    echo "  gitosint-mcp discover-user username"
    echo "  gitosint-mcp find-emails username"
    echo "  gitosint-mcp map-network username"
    echo "  gitosint-mcp scan-security https://github.com/user/repo"
    echo
    echo "🔧 MCP Integration:"
    echo "  - Restart Claude Desktop to use GitOSINT tools"
    echo "  - In Claude, you can now ask for Git repository analysis"
    echo "  - Example: 'Analyze the security of https://github.com/user/repo'"
    echo
    echo "📚 Documentation:"
    echo "  - GitHub: https://github.com/Huleinpylo/GitOSINT-mcp"
    echo "  - Config: $INSTALL_DIR/README.md"
    echo
}

main() {
    print_header
    
    # Parse arguments
    INSTALL_METHOD="auto"
    CONFIGURE_CLAUDE=true
    CONFIGURE_CURSOR=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --method)
                INSTALL_METHOD="$2"
                shift 2
                ;;
            --no-claude)
                CONFIGURE_CLAUDE=false
                shift
                ;;
            --cursor)
                CONFIGURE_CURSOR=true
                shift
                ;;
            --help)
                echo "GitOSINT-MCP Installer"
                echo
                echo "Options:"
                echo "  --method [pip|source|docker]  Installation method (default: auto)"
                echo "  --no-claude                   Skip Claude Desktop configuration"
                echo "  --cursor                       Configure Cursor IDE"
                echo "  --help                         Show this help"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # System checks
    check_python
    check_git
    
    # Choose installation method
    case $INSTALL_METHOD in
        auto)
            # Try pip first, fall back to source
            if command -v pip3 &> /dev/null; then
                print_step "Auto-detected: Installing via pip..."
                install_method_pip || {
                    print_warning "Pip installation failed. Trying source installation..."
                    install_method_source
                }
            else
                install_method_source
            fi
            ;;
        pip)
            install_method_pip
            ;;
        source)
            install_method_source
            ;;
        docker)
            install_method_docker
            ;;
        *)
            print_error "Invalid installation method: $INSTALL_METHOD"
            exit 1
            ;;
    esac
    
    # Configure integrations
    if [ "$CONFIGURE_CLAUDE" = true ]; then
        configure_claude_desktop
    fi
    
    if [ "$CONFIGURE_CURSOR" = true ]; then
        configure_cursor
    fi
    
    # Show usage
    show_usage
    
    print_success "GitOSINT-MCP installation completed successfully! 🎉"
    echo
    print_warning "Next steps:"
    echo "1. Restart Claude Desktop (if configured)"
    echo "2. Try: gitosint-mcp --help"
    echo "3. In Claude: 'Analyze the repository https://github.com/torvalds/linux'"
}

# Run main function
main "$@"