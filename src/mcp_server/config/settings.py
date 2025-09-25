import os
from typing import Optional

class Settings:
    """Application settings."""

    def __init__(self):
        # Server identification - can be overridden by environment variables
        self.server_name = os.getenv("MCP_SERVER_NAME", "TradingAgentMCP")
        self.version = os.getenv("MCP_VERSION", "1.0.0")

        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"

        # Extended configuration for future features
        self.max_prompt_calls = int(os.getenv("MAX_PROMPT_CALLS", "10"))
        self.enable_metrics = os.getenv("ENABLE_METRICS", "false").lower() == "true"

# Singleton instance
settings = Settings()
