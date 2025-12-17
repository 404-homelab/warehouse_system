#!/bin/bash
#
# WAREHOUSE MANAGEMENT SYSTEM - INSTALLER
# ========================================
# Easy installation script for Ubuntu/Debian servers
#
# Usage:
#   wget https://raw.githubusercontent.com/YOUR_REPO/install.sh
#   chmod +x install.sh
#   sudo ./install.sh
#
# Or one-liner:
#   curl -sSL https://raw.githubusercontent.com/YOUR_REPO/install.sh | sudo bash
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/warehouse"
SERVICE_USER="warehouse"
PYTHON_VERSION="3.10"
APP_PORT="5000"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║    WAREHOUSE MANAGEMENT SYSTEM - INSTALLER                ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

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
        VER=$VERSION_ID
        print_success "Detected: $PRETTY_NAME"
    else
        print_error "Cannot detect OS. This script requires Ubuntu or Debian."
        exit 1
    fi
    
    if [[ "$OS" != "ubuntu" ]] && [[ "$OS" != "debian" ]]; then
        print_warning "This script is optimized for Ubuntu/Debian"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

install_dependencies() {
    print_step "Installing system dependencies..."
    
    apt-get update -qq
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        git \
        sqlite3 \
        curl \
        wget \
        ufw \
        supervisor \
        || { print_error "Failed to install dependencies"; exit 1; }
    
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
    print_step "Downloading application..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    
    # Method 1: From git repository (if available)
    if [ ! -z "$GIT_REPO" ]; then
        print_info "Cloning from repository..."
        git clone "$GIT_REPO" "$INSTALL_DIR"
    else
        # Method 2: Copy from current directory
        if [ -f "./app.py" ]; then
            print_info "Copying from local directory..."
            cp -r ./* "$INSTALL_DIR"
        else
            print_error "No source found. Please provide GIT_REPO or run from parent directory."
            exit 1
        fi
    fi
    
    print_success "Application downloaded"
}

setup_python_environment() {
    print_step "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip -q
    
    # Install requirements
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt -q
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
        python3 -c "from database import init_db; init_db()"
        deactivate
        print_success "Database initialized"
    else
        print_info "Database already exists"
    fi
}

#configure_nginx() {
#    print_step "Configuring Nginx..."
#    
#    # Create Nginx config
#    cat > /etc/nginx/sites-available/warehouse << 'EOF'
#server {
#    listen 80;
#    server_name _;
#    
#    client_max_body_size 50M;
#    
#    location / {
#        proxy_pass http://127.0.0.1:5000;
#        proxy_set_header Host $host;
#        proxy_set_header X-Real-IP $remote_addr;
#        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#        proxy_set_header X-Forwarded-Proto $scheme;
#        
#        # WebSocket support
#        proxy_http_version 1.1;
#        proxy_set_header Upgrade $http_upgrade;
#        proxy_set_header Connection "upgrade";
#        
#        # Timeouts
#        proxy_connect_timeout 60s;
#        proxy_send_timeout 60s;
#        proxy_read_timeout 60s;
#    }
#    
#    location /static {
#        alias /opt/warehouse/static;
#        expires 30d;
#        add_header Cache-Control "public, immutable";
#    }
#}
#EOF
#    
#    # Enable site
#    ln -sf /etc/nginx/sites-available/warehouse /etc/nginx/sites-enabled/
#    rm -f /etc/nginx/sites-enabled/default
#    
#    # Test configuration
#    nginx -t || { print_error "Nginx configuration error"; exit 1; }
#    
#    # Restart Nginx
#    systemctl restart nginx
#    systemctl enable nginx
#    
#    print_success "Nginx configured"
#}

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
    
    # Reload systemd
    systemctl daemon-reload
    systemctl enable warehouse
    systemctl start warehouse
    
    print_success "Systemd service configured"
}

configure_supervisor() {
    print_step "Configuring Supervisor (alternative to systemd)..."
    
    cat > /etc/supervisor/conf.d/warehouse.conf << EOF
[program:warehouse]
command=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/app.py
directory=$INSTALL_DIR
user=$SERVICE_USER
autostart=true
autorestart=true
stderr_logfile=/var/log/warehouse/error.log
stdout_logfile=/var/log/warehouse/output.log
environment=PATH="$INSTALL_DIR/venv/bin"
EOF
    
    # Create log directory
    mkdir -p /var/log/warehouse
    chown $SERVICE_USER:$SERVICE_USER /var/log/warehouse
    
    # Reload supervisor
    supervisorctl reread
    supervisorctl update
    
    print_success "Supervisor configured"
}

#configure_firewall() {
#    print_step "Configuring firewall..."
#    
#    if command -v ufw &> /dev/null; then
#        ufw --force enable
#        ufw allow 22/tcp    # SSH
#        ufw allow 80/tcp    # HTTP
#        ufw allow 443/tcp   # HTTPS (future)
#        print_success "Firewall configured"
#    else
#        print_warning "UFW not available, skipping firewall setup"
#    fi
#}

set_permissions() {
    print_step "Setting permissions..."
    
    chown -R $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/restart.sh" 2>/dev/null || true
    
    print_success "Permissions set"
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
    echo "  • URL: http://$IP"
    echo "  • Local: http://localhost"
    echo ""
    echo -e "${BLUE}Service Management:${NC}"
    echo "  • Status:  sudo systemctl status warehouse"
    echo "  • Start:   sudo systemctl start warehouse"
    echo "  • Stop:    sudo systemctl stop warehouse"
    echo "  • Restart: sudo systemctl restart warehouse"
    echo "  • Logs:    sudo journalctl -u warehouse -f"
    echo ""
    echo -e "${BLUE}Files Location:${NC}"
    echo "  • Installation: $INSTALL_DIR"
    echo "  • Database: $INSTALL_DIR/warehouse.db"
    echo "  • Logs: /var/log/warehouse/"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Open http://$IP in your browser"
    echo "  2. Configure update server in Admin → Updates"
    echo "  3. Set up locations and start registering products!"
    echo ""
    echo -e "${YELLOW}Need help?${NC}"
    echo "  • Documentation: $INSTALL_DIR/README.md"
    echo "  • Run: sudo ./install.sh --help"
    echo ""
}

uninstall() {
    print_warning "Uninstalling Warehouse Management System..."
    
    read -p "This will remove ALL data. Are you sure? (yes/NO) " -r
    if [[ ! $REPLY == "yes" ]]; then
        echo "Uninstall cancelled"
        exit 0
    fi
    
    # Stop services
    systemctl stop warehouse 2>/dev/null || true
    systemctl disable warehouse 2>/dev/null || true
    supervisorctl stop warehouse 2>/dev/null || true
    
    # Remove files
    rm -rf "$INSTALL_DIR"
    rm -f /etc/systemd/system/warehouse.service
    rm -f /etc/supervisor/conf.d/warehouse.conf
#    rm -f /etc/nginx/sites-enabled/warehouse
#    rm -f /etc/nginx/sites-available/warehouse
    rm -rf /var/log/warehouse
    
    # Remove user
    userdel -r $SERVICE_USER 2>/dev/null || true
    
    # Reload services
    systemctl daemon-reload
    supervisorctl reread 2>/dev/null || true
    supervisorctl update 2>/dev/null || true
#    systemctl restart nginx
    
    print_success "Uninstallation complete"
}

show_help() {
    echo "Warehouse Management System - Installer"
    echo ""
    echo "Usage: sudo ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help              Show this help message"
    echo "  --uninstall         Remove the system completely"
    echo "  --update            Update existing installation"
    echo "  --port PORT         Set application port (default: 5000)"
    echo "  --dir DIR           Set installation directory (default: /opt/warehouse)"
    echo ""
    echo "Examples:"
    echo "  sudo ./install.sh"
    echo "  sudo ./install.sh --port 8080"
    echo "  sudo ./install.sh --uninstall"
    echo ""
}

# Main installation flow
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_help
                exit 0
                ;;
            --uninstall)
                check_root
                uninstall
                exit 0
                ;;
            --port)
                APP_PORT="$2"
                shift 2
                ;;
            --dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_header
    check_root
    detect_os
    
    echo ""
    print_info "Installation will proceed with these settings:"
    echo "  • Installation directory: $INSTALL_DIR"
    echo "  • Service user: $SERVICE_USER"
    echo "  • Application port: $APP_PORT"
    echo ""
    
    read -p "Continue? (Y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_warning "Installation cancelled"
        exit 0
    fi
    
    echo ""
    print_step "Starting installation..."
    echo ""
    
    install_dependencies
    create_user
    download_application
    setup_python_environment
    setup_database
#    configure_nginx
    configure_systemd
    # configure_supervisor  # Optional: uncomment if you prefer supervisor
    configure_firewall
    set_permissions
    create_update_config
    
    echo ""
    print_summary
}

# Run main installation
main "$@"
