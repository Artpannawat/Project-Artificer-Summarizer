try:
    from backend.app.main import app
except Exception as e:
    import traceback
    error_trace = traceback.format_exc()
    print(f"CRITICAL STARTUP ERROR: {e}")
    print(error_trace)
    
    # Fallback App to report error
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI()

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
            "status": "error",
            "startup_error": str(e),
            "traceback": error_trace.splitlines()
        }
    
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def catch_all(path_name: str, request: Request):
         return JSONResponse(
            status_code=500,
            content={
                "status": "critical_startup_error",
                "message": "The backend failed to start.",
                "error": str(e),
                "traceback": error_trace.splitlines(),
                 "debug_info": {
                    "received_path": request.url.path,
                    "received_method": request.method,
                    "path_name_arg": path_name
                }
            }
        )
