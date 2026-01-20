import os
import sys
import traceback
from fastapi import FastAPI, Response

# Add the project root to sys.path to ensure 'backend' module is found
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    # Import the FastAPI app directly
    from backend.app.main import app
except Exception as e:
    # Catch ANY import error or startup error and return it as JSON
    error_msg = traceback.format_exc()
    print(f"CRITICAL STARTUP ERROR: {error_msg}")
    
    # Create a dummy app to serve the error
    app = FastAPI()
    
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    def catch_all_error(path: str):
        return Response(
            content=f'{{"status": "critical_error", "message": "Backend failed to start", "details": "{str(e)}", "traceback": {error_msg.splitlines()}}}',
            status_code=500,
            media_type="application/json"
        )

