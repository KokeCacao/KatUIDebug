import random
from fastapi import Request

from backend import variable
from backend.app import app
from backend.utils import SafeJSONResponse


@app.get('/ping')
async def ping(request: Request):
    """Ping the server."""
    if variable.node_loader is None:
        return SafeJSONResponse(status_code=500, content={"error": "Server failed to load nodes."})

    ret = {
        "pong": random.choice(["Ping!", "Pong!", "Pang!", "Pung!"]),
    }
    return SafeJSONResponse(status_code=200, content=ret)
