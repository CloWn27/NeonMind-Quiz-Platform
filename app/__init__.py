from flask import Flask
from config import config
from app.extensions import db, socketio, babel, redis_client, csrf


def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(
        app,
        message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'],
        async_mode=app.config['SOCKETIO_ASYNC_MODE'],
        cors_allowed_origins="*"
    )
    
    # Initialize Redis
    redis_client.init_app(app)
    
    # Initialize CSRF Protection
    csrf.init_app(app)
    
    # Register blueprints
    from app.routes import main_bp, game_bp, admin_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(game_bp, url_prefix='/game')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register SocketIO events
    from app.services import socket_events
    socket_events.register_handlers(socketio)
    
    # Babel locale selector
    def get_locale():
        from flask import request, session
        # Check if user has set a language preference
        if 'language' in session:
            return session['language']
        # Otherwise, try to match browser language
        return request.accept_languages.best_match(app.config['LANGUAGES'])
    
    babel.init_app(app, locale_selector=get_locale)
    
    # Add Content Security Policy headers for development
    @app.after_request
    def add_security_headers(response):
        # Allow eval() for SocketIO and dynamic JS (development only)
        if app.config.get('ENV') == 'development' or app.config.get('DEBUG'):
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.socket.io https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:;"
            )
        return response
    
    return app
