from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback
import sys

# Create the Vercel entry point app IMMEDIATELY
app = FastAPI()

# Allow CORS globally for the entry point
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to cache the real app
real_app = None
startup_error = None

@app.get("/health")
async def health_check():
    global real_app, startup_error
    
    db_status = "unknown"
    db_latency = None
    db_error = None

    # Try to load if not loaded
    if real_app is None and startup_error is None:
        try:
            from backend.app.main import app as loaded_app
            real_app = loaded_app
            status = "ok"
            message = "Backend loaded successfully (lazy loaded)."
        except Exception as e:
            startup_error = traceback.format_exc()
            status = "error"
            message = "Backend failed to load."

    if startup_error:
        return {
            "status": "critical_startup_error",
            "message": message,
            "error": str(startup_error).splitlines()[-1],
            "traceback": startup_error.splitlines()
        }
    
    # Verify DB Connection
    try:
        from backend.app.database.mongo import client
        import time
        start = time.time()
        await client.admin.command('ping')
        db_latency = round((time.time() - start) * 1000, 2)
        db_status = "connected"
    except Exception as e:
        db_status = "disconnected"
        db_error = str(e)
    
    return {
        "status": "ok",
        "message": message,
        "mode": "lazy_loaded",
        "database": {
            "status": db_status,
            "latency_ms": db_latency,
            "error": db_error
        }
    }

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def catch_all(path_name: str, request: Request):
    global real_app, startup_error
    
    # lazy load
    if real_app is None and startup_error is None:
        try:
            from backend.app.main import app as loaded_app
            real_app = loaded_app
        except Exception as e:
            startup_error = traceback.format_exc()
            
    if startup_error:
        return JSONResponse(
            status_code=500,
            content={
                "status": "critical_startup_error",
                "message": "The backend failed to start.",
                "traceback": startup_error.splitlines()
            }
        )
    
    # Forward request to the real app
    # This is a bit hacky for serverless, but effectively we want to delegate.
    # Since we can't easily 'delegate' in FastAPI without mounting, we will assume
    # Vercel calls this function. ideally we should import 'app' at top level.
    # BUT since top level crashes, we are stuck.
    
    # ACTUALLY: The best way to lazy load in Vercel is to return the app instance if loaded.
    # But current Vercel python builder expects 'app' to be the ASGI app.
    # So we act as a proxy.
    
    scope = request.scope
    receive = request.receive
    send = request._send
    
    await real_app(scope, receive, send)
    return

