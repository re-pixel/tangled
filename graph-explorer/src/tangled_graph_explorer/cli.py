"""
CLI entry point for running the Flask application.
"""

import sys


def main():
    """Run the Flask development server."""
    from tangled_graph_explorer.app import create_app
    
    app = create_app()
    
    # Default to debug mode for development
    debug = "--no-debug" not in sys.argv
    port = 5000
    
    # Simple arg parsing for port
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg == "--port" and i < len(sys.argv) - 1:
            port = int(sys.argv[i + 1])
    
    print(f"Starting Tangled Graph Explorer on http://localhost:{port}")
    app.run(debug=debug, port=port)


if __name__ == "__main__":
    main()
