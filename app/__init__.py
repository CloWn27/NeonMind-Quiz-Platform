from flask import Flask
from config import config
from app.extensions import db, socketio, babel, redis_client


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
    
    return app
