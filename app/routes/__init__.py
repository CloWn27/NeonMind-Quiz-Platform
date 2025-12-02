from flask import Blueprint

# Main routes (homepage, dashboard, etc.)
main_bp = Blueprint('main', __name__)

# Game routes (multiplayer, survival)
game_bp = Blueprint('game', __name__)

# Admin routes (god mode)
admin_bp = Blueprint('admin', __name__)

# API routes (REST endpoints)
api_bp = Blueprint('api', __name__)

# Import route handlers
from app.routes import main_routes, game_routes, admin_routes, api_routes
