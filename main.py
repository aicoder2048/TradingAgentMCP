#!/usr/bin/env python3
"""MCP Server - Model Context Protocol Server."""

from src.mcp_server.server import create_server

def main():
    """Main entry point."""
    server = create_server()
    server.run()

if __name__ == "__main__":
    main()
