import os
import urllib.parse


basedir = os.path.abspath(os.path.dirname(__file__))
key = os.getenv("key")
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", key)
    
    db_path = os.path.join(basedir, 'database', 'users.db').replace("\\", "/")
    SQLALCHEMY_DATABASE_URI = "sqlite:///users.db"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60