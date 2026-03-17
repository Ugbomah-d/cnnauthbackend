import os
import urllib.parse

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change_this_to_a_long_random_secret_key")
    
    db_path = os.path.join(basedir, 'database', 'users.db').replace("\\", "/")
    SQLALCHEMY_DATABASE_URI = "sqlite:///users.db"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60