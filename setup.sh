#!/usr/bin/env bash

# Exit script on error
set -e

# Create virtual environment (if using Python 3)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Set up the database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

echo "Setup complete!"
