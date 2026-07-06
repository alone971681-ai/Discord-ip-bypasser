"""
WSGI entry point for the Flask web application
This file is used by Gunicorn to run the application in production mode
"""

import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Import the Flask application
from app import app as application

# Log application startup
logging.info("Perfect Selfbot — Web Interface starting via WSGI")

# Check if TOKEN is set
if not os.environ.get('TOKEN'):
    logging.warning("⚠️ WARNING: Discord TOKEN environment variable is not set!")
    logging.warning("The Discord bot cannot be started without a valid token.")
    logging.warning("Use the web interface to add your token as an environment variable.")
else:
    logging.info("Discord TOKEN is configured")

# Export the application for Gunicorn
__all__ = ['application']