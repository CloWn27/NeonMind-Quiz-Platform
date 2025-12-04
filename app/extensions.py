from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
import redis


# Database
db = SQLAlchemy()

# SocketIO for real-time multiplayer
socketio = SocketIO()

# Babel for i18n
babel = Babel()

# CSRF Protection
csrf = CSRFProtect()


class RedisClient:
    """Redis client wrapper"""
    def __init__(self):
        self.client = None
    
    def init_app(self, app):
        """Initialize Redis client with app config"""
        try:
            redis_url = app.config.get('REDIS_URL')
            if redis_url:
                self.client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
                # Test connection
                self.client.ping()
                app.logger.info('✅ Redis connected successfully')
            else:
                app.logger.warning('⚠️  Redis URL not configured, running without Redis')
        except Exception as e:
            app.logger.warning(f'⚠️  Redis connection failed: {e}. Running without Redis.')
            self.client = None
    
    def get(self, key):
        """Get value from Redis"""
        return self.client.get(key) if self.client else None
    
    def set(self, key, value, ex=None):
        """Set value in Redis with optional expiration"""
        if self.client:
            return self.client.set(key, value, ex=ex)
        return None
    
    def delete(self, key):
        """Delete key from Redis"""
        if self.client:
            return self.client.delete(key)
        return None
    
    def hget(self, name, key):
        """Get hash field value"""
        if self.client:
            return self.client.hget(name, key)
        return None
    
    def hset(self, name, key, value):
        """Set hash field value"""
        if self.client:
            return self.client.hset(name, key, value)
        return None
    
    def hgetall(self, name):
        """Get all hash fields"""
        if self.client:
            return self.client.hgetall(name)
        return {}
    
    def hdel(self, name, *keys):
        """Delete hash fields"""
        if self.client:
            return self.client.hdel(name, *keys)
        return None
    
    def sadd(self, name, *values):
        """Add members to set"""
        if self.client:
            return self.client.sadd(name, *values)
        return None
    
    def srem(self, name, *values):
        """Remove members from set"""
        if self.client:
            return self.client.srem(name, *values)
        return None
    
    def smembers(self, name):
        """Get all set members"""
        if self.client:
            return self.client.smembers(name)
        return set()
    
    def exists(self, key):
        """Check if key exists"""
        if self.client:
            return self.client.exists(key)
        return False


redis_client = RedisClient()
