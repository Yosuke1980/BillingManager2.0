#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Python is not installed or not found in PATH"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if PyQt5 is installed
$PYTHON_CMD -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "PyQt5 is not installed"
    echo "Please install PyQt5 using: pip install PyQt5"
    exit 1
fi

# Run the application
echo "Starting Billing Manager..."
$PYTHON_CMD app.py