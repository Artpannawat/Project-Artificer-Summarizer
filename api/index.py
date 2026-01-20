import os
import sys

# Add the project root to sys.path to ensure 'backend' module is found
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import the FastAPI app directly
# This is the standard entry point for Vercel Python runtime
from backend.app.main import app

