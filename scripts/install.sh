#!/bin/bash
# Maxwell Installation Script for Unix/macOS/Linux
# Usage: curl -fsSL https://raw.githubusercontent.com/your-repo/maxwell/main/scripts/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ASCII Art Banner
print_banner() {
    echo -e "${BLUE}"
    echo "  __  __                        _ _ "
    echo " |  \/  | __ ___  ____      _____| | |"
    echo " | |\/| |/ _\` \ \/ /\ \ /\ / / _ \ | |"
    echo " | |  | | (_| |>  <  \ V  V /  __/ | |"
    echo " |_|  |_|\__,_/_/\_\  \_/\_/ \___|_|_|"
    echo ""
    echo " Local-First Fiction Writing IDE"
    echo -e "${NC}"
}

# Print colored message
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."

    # Check Docker
    if ! command_exists docker; then
        error "Docker is not installed. Please install Docker first: https://docs.docker.com/get-docker/"
    fi

    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        error "Docker Compose is not installed. Please install Docker Compose: https://docs.docker.com/compose/install/"
    fi

    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        error "Docker daemon is not running. Please start Docker and try again."
    fi

    success "All prerequisites met!"
}

# Get installation directory
get_install_dir() {
    DEFAULT_DIR="$HOME/maxwell"

    echo ""
    read -p "Installation directory [$DEFAULT_DIR]: " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_DIR}

    # Expand tilde
    INSTALL_DIR="${INSTALL_DIR/#\~/$HOME}"

    echo "$INSTALL_DIR"
}

# Clone or download Maxwell
download_maxwell() {
    local dir="$1"

    info "Downloading Maxwell to $dir..."

    if [ -d "$dir" ]; then
        warn "Directory $dir already exists."
        read -p "Do you want to update it? [y/N]: " UPDATE
        if [[ "$UPDATE" =~ ^[Yy]$ ]]; then
            cd "$dir"
            if [ -d ".git" ]; then
                git pull origin main
            else
                error "Cannot update: not a git repository. Please remove the directory and try again."
            fi
        else
            info "Using existing installation."
        fi
    else
        if command_exists git; then
            git clone https://github.com/your-repo/maxwell.git "$dir"
        else
            warn "Git not found, downloading as zip..."
            mkdir -p "$dir"
            curl -L "https://github.com/your-repo/maxwell/archive/main.zip" -o /tmp/maxwell.zip
            unzip -q /tmp/maxwell.zip -d /tmp
            mv /tmp/maxwell-main/* "$dir/"
            rm -rf /tmp/maxwell.zip /tmp/maxwell-main
        fi
    fi

    success "Maxwell downloaded successfully!"
}

# Build and start containers
start_maxwell() {
    local dir="$1"

    info "Building and starting Maxwell..."
    cd "$dir"

    # Use docker compose (v2) or docker-compose (v1)
    if docker compose version >/dev/null 2>&1; then
        docker compose up -d --build
    else
        docker-compose up -d --build
    fi

    success "Maxwell is starting..."
}

# Wait for services to be ready
wait_for_ready() {
    info "Waiting for services to be ready..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            success "Maxwell is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    warn "Maxwell may still be starting. Check with: docker-compose logs -f"
}

# Print success message
print_success() {
    local dir="$1"

    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Maxwell installed successfully!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "  Open Maxwell: http://localhost:3000"
    echo ""
    echo "  Useful commands:"
    echo "    cd $dir"
    echo "    docker-compose logs -f     # View logs"
    echo "    docker-compose stop        # Stop Maxwell"
    echo "    docker-compose start       # Start Maxwell"
    echo "    docker-compose down        # Stop and remove containers"
    echo ""
    echo "  Your data is stored in a Docker volume and persists"
    echo "  across restarts. To backup your data:"
    echo "    docker cp maxwell_backend:/app/data ./maxwell-backup"
    echo ""
    echo -e "${BLUE}Happy writing!${NC}"
    echo ""
}

# Main installation flow
main() {
    print_banner

    echo "This script will install Maxwell on your system using Docker."
    echo "All your writing data will be stored locally on your machine."
    echo ""

    check_prerequisites

    INSTALL_DIR=$(get_install_dir)

    download_maxwell "$INSTALL_DIR"
    start_maxwell "$INSTALL_DIR"
    wait_for_ready
    print_success "$INSTALL_DIR"

    # Try to open browser
    if command_exists open; then
        open http://localhost:3000
    elif command_exists xdg-open; then
        xdg-open http://localhost:3000
    fi
}

# Run main function
main "$@"
