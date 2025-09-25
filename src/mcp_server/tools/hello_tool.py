from datetime import datetime, UTC
from typing import Dict, Any
from ..config.settings import settings

async def hello(name: str) -> Dict[str, Any]:
    """
    Say hello to someone with a structured response.

    Args:
        name: The name of the person to greet

    Returns:
        dict: Structured response with status, message, and metadata
    """
    try:
        if not name or not name.strip():
            message = f"Hello! Welcome to {settings.server_name}."
            name = "Guest"
        else:
            name = name.strip()
            message = f"Hello, {name}! Welcome to {settings.server_name}."

        return {
            "status": "success",
            "message": message,
            "name": name,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": {
                "server": settings.server_name,
                "tool": "hello",
                "version": settings.version
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to process greeting: {str(e)}",
            "timestamp": datetime.now(UTC).isoformat()
        }
