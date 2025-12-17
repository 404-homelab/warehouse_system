#!/bin/bash
#
# WAREHOUSE RESTART SCRIPT
# ========================
# Automatisk restart av Warehouse System efter update
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🔄 Restarting Warehouse System..."

# Method 1: Try systemd service
if command -v systemctl &> /dev/null; then
    if systemctl list-units --type=service | grep -q warehouse; then
        echo "📌 Using systemd..."
        sudo systemctl restart warehouse
        if [ $? -eq 0 ]; then
            echo "✅ Service restarted via systemd"
            exit 0
        fi
    fi
fi

# Method 2: Try supervisord
if command -v supervisorctl &> /dev/null; then
    if supervisorctl status | grep -q warehouse; then
        echo "📌 Using supervisord..."
        sudo supervisorctl restart warehouse
        if [ $? -eq 0 ]; then
            echo "✅ Service restarted via supervisord"
            exit 0
        fi
    fi
fi

# Method 3: Kill and restart manually
echo "📌 Using pkill method..."

# Find and kill existing processes
pkill -f "python.*app.py"
sleep 2

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Start in background
echo "🚀 Starting app.py..."
nohup python3 app.py > warehouse.log 2>&1 &

sleep 3

# Verify it started
if pgrep -f "python.*app.py" > /dev/null; then
    echo "✅ Warehouse System restarted successfully!"
    echo "📋 Log: tail -f warehouse.log"
    echo "🌐 Access: http://localhost:5000"
else
    echo "❌ Failed to start. Check warehouse.log for errors."
    exit 1
fi
