from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback

try:
    # Attempt to import the real FastAPI app
    from backend.app.main import app
except Exception as e:
    # IF IMPORT FAILS: Create a Fallback App to report the error
    error_trace = traceback.format_exc()
    print(f"CRITICAL STARTUP ERROR: {e}")
    print(error_trace)
    
    app = FastAPI()

    # Allow CORS so we can see the error from frontend if needed
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "critical_startup_error",
            "message": "The backend failed to load.",
            "error": str(e),
            "traceback": error_trace.splitlines()
        }
    
    # Catch-all to prevent 405 on other routes
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def catch_all(path_name: str):
         return JSONResponse(
            status_code=500,
            content={
                "status": "critical_startup_error",
                "message": "The backend failed to start. Check /health for details.",
                "error": str(e)
            }
        )
