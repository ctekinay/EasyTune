import os

class Config:
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    REDIRECT_URI = os.getenv('REDIRECT_URI')
    AUTH_URL = os.getenv('AUTH_URL', 'https://accounts.spotify.com/authorize')
    TOKEN_URL = os.getenv('TOKEN_URL', 'https://accounts.spotify.com/api/token')
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://api.spotify.com/v1/')
    SECRET_KEY = os.urandom(24)  # Unique key for Flask sessions
