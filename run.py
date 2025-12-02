#!/usr/bin/env python3
"""
NeonMind - Cyberpunk FiSi Quiz Platform
Main entry point for running the application
"""

import os
from app import create_app
from app.extensions import socketio

# Get configuration from environment
config_name = os.getenv('FLASK_ENV', 'development')

# Create Flask app
app = create_app(config_name)

if __name__ == '__main__':
    # Run with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=(config_name == 'development'),
        use_reloader=True,
        log_output=True
    )
