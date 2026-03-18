import jwt
from datetime import datetime, timedelta, timezone
from flask import request, jsonify, current_app
from functools import wraps
from passlib.context import CryptContext
from models import User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(email: str):
    expiry = datetime.now(timezone.utc) + timedelta(minutes=current_app.config['ACCESS_TOKEN_EXPIRE_MINUTES'])
    payload = {"sub": email, "exp": expiry}
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm=current_app.config['ALGORITHM'])

# Decorator to protect routes (Replacement for FastAPI's Depends)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            # Expecting "Bearer <token>"
            auth_header = request.headers["Authorization"].split(" ")
            if len(auth_header) == 2:
                token = auth_header[1]

        if not token:
            return jsonify({"detail": "Token is missing"}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=[current_app.config['ALGORITHM']])
            current_user = User.query.filter_by(email=data["sub"]).first()
            if not current_user:
                raise Exception("User not found")
        except Exception as e:
            return jsonify({"detail": "Token is invalid or expired"}), 401

        return f(*args, current_user=current_user, **kwargs)
    return decorated