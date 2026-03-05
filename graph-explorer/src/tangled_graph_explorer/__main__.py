"""
Entry point for the ``tangled`` console command.

Usage::

    tangled              # start on default port 5000
    tangled --port 8080  # start on port 8080
"""

import argparse

from tangled_graph_explorer.app import create_app


def main():
    parser = argparse.ArgumentParser(description="Tangled Graph Explorer")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    app = create_app()
    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
