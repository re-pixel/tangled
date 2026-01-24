"""
Flask application factory.
"""

from flask import Flask
from tangled_platform import Platform


def create_app(config=None):
    """
    Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Default configuration
    app.config.update(
        SECRET_KEY="dev-secret-key-change-in-production",
        DEBUG=True,
    )
    
    # Override with provided config
    if config:
        app.config.update(config)
    
    # Initialize platform (discovers all plugins)
    platform = Platform()
    app.config["PLATFORM"] = platform
    
    # Register blueprints
    from tangled_graph_explorer.routes import main_bp
    from tangled_graph_explorer.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    
    return app
