from fastapi import FastAPI
from fastapi.responses import JSONResponse

# STANDALONE DEBUG MODE
# We are not importing backend.app.main yet to verify if Vercel can even run Python.

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "Vercel Python Runtime is Working!",
        "mode": "standalone_debug"
    }

@app.get("/api/test")
async def api_test():
    return {"message": "API Routing is working"}

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def catch_all(path_name: str):
    return {
        "status": "fallback",
        "message": "This is the standalone debug app catching your request.",
        "path": path_name
    }
