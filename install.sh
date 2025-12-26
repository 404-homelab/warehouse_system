#!/bin/bash
#
# WAREHOUSE MANAGEMENT SYSTEM - INSTALLER
# ========================================
# Easy installation script for Ubuntu/Debian servers
#
# GitHub: https://github.com/404-homelab/warehouse_system
#
# Quick Install:
#   curl -sSL https://raw.githubusercontent.com/404-homelab/warehouse_system/master/install.sh | sudo bash
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/warehouse"
SERVICE_USER="warehouse"
APP_PORT="5000"
GIT_REPO="https://github.com/404-homelab/warehouse_system.git"
GIT_BRANCH="master"
UPDATE_MODE="false"

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║    WAREHOUSE MANAGEMENT SYSTEM - INSTALLER                ║"
    echo "║    GitHub: 404-homelab/warehouse_system                   ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() { echo -e "${GREEN}▶ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root (use sudo)"
        exit 1
    fi
}

detect_os() {
    print_step "Detecting operating system..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        print_success "Detected: $PRETTY_NAME"
    else
        print_error "Cannot detect OS"
        exit 1
    fi
}

install_dependencies() {
    print_step "Installing system dependencies..."
    apt-get update -qq
    
    # Install Python build dependencies for Pillow and other packages
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        git \
        sqlite3 \
        curl \
        wget \
        supervisor \
        libjpeg-dev \
        zlib1g-dev \
        libtiff-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libwebp-dev \
        libopenjp2-7-dev \
        || {
        print_error "Failed to install dependencies"
        exit 1
    }
    print_success "Dependencies installed"
}

create_user() {
    print_step "Creating service user..."
    if id "$SERVICE_USER" &>/dev/null; then
        print_info "User $SERVICE_USER already exists"
    else
        useradd -r -m -d /home/$SERVICE_USER -s /bin/bash $SERVICE_USER
        print_success "User $SERVICE_USER created"
    fi
}

download_application() {
    print_step "Downloading application from GitHub..."
    
    if [ -d "$INSTALL_DIR" ] && [ "$UPDATE_MODE" = "true" ]; then
        print_info "Backing up existing installation..."
        mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    mkdir -p "$INSTALL_DIR"
    
    if [ ! -z "$GIT_REPO" ]; then
        git clone -b "$GIT_BRANCH" "$GIT_REPO" "$INSTALL_DIR" || {
            print_error "Failed to clone from GitHub"
            print_info "Trying local copy..."
            if [ -f "./app.py" ]; then
                cp -r ./* "$INSTALL_DIR/"
            else
                print_error "No source available"
                exit 1
            fi
        }
    fi
    
    print_success "Application downloaded"
}

setup_python_environment() {
    print_step "Setting up Python virtual environment..."
    cd "$INSTALL_DIR"
    
    # Check Python version
    PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_info "Python version: $PYTHON_VER"
    
    # Warn if Python 3.13+
    if [[ $(echo "$PYTHON_VER >= 3.13" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        print_warning "Python 3.13+ detected. Some packages may have issues."
        print_info "Installing with pip --use-pep517..."
    fi
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip and setuptools
    pip install --upgrade pip setuptools wheel -q
    
    # Install requirements with better error handling
    if [ -f requirements.txt ]; then
        print_info "Installing Python packages (this may take a few minutes)..."
        
        # Try normal install first
        if ! pip install -r requirements.txt -q 2>/dev/null; then
            print_warning "Normal install failed, trying with --use-pep517..."
            pip install --use-pep517 -r requirements.txt || {
                print_error "Failed to install requirements"
                print_info "Try manually: cd $INSTALL_DIR && source venv/bin/activate && pip install -r requirements.txt"
                exit 1
            }
        fi
        
        print_success "Python packages installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    deactivate
}

setup_database() {
    print_step "Setting up database..."
    cd "$INSTALL_DIR"
    if [ ! -f warehouse.db ]; then
        print_info "Initializing database..."
        source venv/bin/activate
        python3 -c "from database import init_db; init_db()" || print_warning "Database init failed, will retry on first run"
        deactivate
        print_success "Database initialized"
    else
        print_info "Database already exists"
    fi
}

configure_systemd() {
    print_step "Configuring systemd service..."
    cat > /etc/systemd/system/warehouse.service << EOF
[Unit]
Description=Warehouse Management System
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable warehouse
    systemctl start warehouse
    print_success "Systemd service configured"
}

set_permissions() {
    print_step "Setting permissions..."
    chown -R $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/restart.sh" 2>/dev/null || true
    print_success "Permissions set"
}

setup_git_permissions() {
    print_step "Configuring Git for auto-updates..."
    cd "$INSTALL_DIR"
    
    if [ -d ".git" ]; then
        # Ensure git directory is owned by service user
        chown -R $SERVICE_USER:$SERVICE_USER .git
        
        # Mark directory as safe for git operations
        sudo -u $SERVICE_USER git config --global --add safe.directory "$INSTALL_DIR"
        
        # Verify remote is set
        REMOTE=$(sudo -u $SERVICE_USER git config --get remote.origin.url 2>/dev/null || echo "")
        if [ -z "$REMOTE" ]; then
            print_warning "Setting git remote..."
            sudo -u $SERVICE_USER git remote add origin "$GIT_REPO"
        fi
        
        # Set branch tracking
        sudo -u $SERVICE_USER git branch --set-upstream-to=origin/$GIT_BRANCH $GIT_BRANCH 2>/dev/null || true
        
        print_success "Git configured for auto-updates"
        print_info "Remote: $(sudo -u $SERVICE_USER git config --get remote.origin.url)"
        print_info "Branch: $(sudo -u $SERVICE_USER git branch --show-current)"
    else
        print_warning "Not a git repository - auto-updates will not work"
        print_info "Install using: curl -sSL https://raw.githubusercontent.com/404-homelab/warehouse_system/master/install.sh | sudo bash"
    fi
}

create_update_config() {
    print_step "Creating update configuration..."
    cd "$INSTALL_DIR"
    if [ ! -f update_config.json ]; then
        cat > update_config.json << 'EOF'
{
  "update_server": "http://your-computer.local:8080",
  "channel": "stable",
  "auto_update": false,
  "auto_restart": true,
  "check_interval": 3600,
  "backup_before_update": true
}
EOF
        chown $SERVICE_USER:$SERVICE_USER update_config.json
        print_success "Update config created"
    else
        print_info "Update config already exists"
    fi
}

print_summary() {
    local IP=$(hostname -I | awk '{print $1}')
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}║           INSTALLATION COMPLETED SUCCESSFULLY! ✓           ║${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    print_success "Warehouse Management System is now running!"
    echo ""
    echo -e "${BLUE}Access Information:${NC}"
    echo "  • URL: http://$IP:$APP_PORT"
    echo "  • Local: http://localhost:$APP_PORT"
    echo ""
    echo -e "${BLUE}Service Management:${NC}"
    echo "  • Status:  sudo systemctl status warehouse"
    echo "  • Restart: sudo systemctl restart warehouse"
    echo "  • Logs:    sudo journalctl -u warehouse -f"
    echo ""
    echo -e "${BLUE}Files:${NC}"
    echo "  • Install: $INSTALL_DIR"
    echo "  • Database: $INSTALL_DIR/warehouse.db"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Open http://$IP:$APP_PORT"
    echo "  2. Go to Admin → Updates (Git auto-update enabled!)"
    echo "  3. Go to Admin → Locations"
    echo "  4. Create locations & print barcodes"
    echo "  5. Start registering products!"
    echo ""
    echo -e "${BLUE}GitHub:${NC} https://github.com/404-homelab/warehouse_system"
    echo ""
}

uninstall() {
    print_warning "Uninstalling Warehouse Management System..."
    read -p "This will remove ALL data. Are you sure? (yes/NO) " -r
    if [[ ! $REPLY == "yes" ]]; then
        echo "Cancelled"
        exit 0
    fi
    
    systemctl stop warehouse 2>/dev/null || true
    systemctl disable warehouse 2>/dev/null || true
    rm -rf "$INSTALL_DIR"
    rm -f /etc/systemd/system/warehouse.service
    rm -rf /var/log/warehouse
    userdel -r $SERVICE_USER 2>/dev/null || true
    systemctl daemon-reload
    print_success "Uninstallation complete"
}

update_installation() {
    print_step "Updating from GitHub..."
    
    if [ ! -d "$INSTALL_DIR" ]; then
        print_error "No existing installation found"
        exit 1
    fi
    
    cd "$INSTALL_DIR"
    
    # Check if it's a git repo
    if [ ! -d ".git" ]; then
        print_error "Not a git repository. Reinstall to enable git updates."
        exit 1
    fi
    
    print_info "Stopping service..."
    systemctl stop warehouse
    
    print_info "Backing up current version..."
    cp warehouse.db warehouse.db.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    
    print_info "Pulling latest changes..."
    sudo -u $SERVICE_USER git pull origin "$GIT_BRANCH" || {
        print_error "Git pull failed"
        systemctl start warehouse
        exit 1
    }
    
    print_info "Updating dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt -q
    deactivate
    
    print_info "Starting service..."
    systemctl start warehouse
    
    print_success "Update complete!"
    print_info "Check status: sudo systemctl status warehouse"
}

show_help() {
    echo "Warehouse Management System - Installer"
    echo ""
    echo "Usage: sudo ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help       Show this help"
    echo "  --uninstall  Remove completely"
    echo "  --update     Update existing installation"
    echo "  --port PORT  Set port (default: 5000)"
    echo "  --dir DIR    Set directory (default: /opt/warehouse)"
    echo ""
    echo "Quick install:"
    echo "  curl -sSL https://raw.githubusercontent.com/404-homelab/warehouse_system/master/install.sh | sudo bash"
    echo ""
}

main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help) show_help; exit 0 ;;
            --uninstall) check_root; uninstall; exit 0 ;;
            --update) check_root; update_installation; exit 0 ;;
            --port) APP_PORT="$2"; shift 2 ;;
            --dir) INSTALL_DIR="$2"; shift 2 ;;
            *) print_error "Unknown option: $1"; show_help; exit 1 ;;
        esac
    done
    
    print_header
    check_root
    detect_os
    
    echo ""
    print_info "Settings:"
    echo "  • Directory: $INSTALL_DIR"
    echo "  • User: $SERVICE_USER"
    echo "  • Port: $APP_PORT"
    echo "  • Source: GitHub (404-homelab/warehouse_system)"
    echo ""
    
    read -p "Continue? (Y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_warning "Cancelled"
        exit 0
    fi
    
    echo ""
    install_dependencies
    create_user
    download_application
    setup_python_environment
    setup_database
    configure_systemd
    set_permissions
    setup_git_permissions
    create_update_config
    echo ""
    print_summary
}

main "$@"