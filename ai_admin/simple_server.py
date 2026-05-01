#!/usr/bin/env python3
"""Simple AI Admin MCP Server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import sys
import argparse
from pathlib import Path
import uvicorn
from mcp_proxy_adapter import create_app

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point for AI Admin server."""
    parser = argparse.ArgumentParser(description="AI Admin MCP Server")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--host", default="127.0.0.1", help="Server host address")
    parser.add_argument("--port", type=int, default=20000, help="Server port")

    args = parser.parse_args()

    # Simple configuration based on command line arguments
    config = {
        'server': {
            'host': args.host,
            'port': args.port
        },
        'ssl': {
            'enabled': False
        },
        'security': {
            'enabled': False
        },
        'registration': {
            'enabled': False
        },
        'protocols': {
            'enabled': True,
            'allowed_protocols': ['http']
        }
    }

    print(f"Creating AI Admin MCP server...")
    app = create_app(config)
    print(f"✅ App created successfully!")
    
    print(f"Starting server on {args.host}:{args.port}...")
    uvicorn.run(
        app, 
        host=args.host, 
        port=args.port, 
        log_level='debug' if args.debug else 'info'
    )


if __name__ == "__main__":
    main()
