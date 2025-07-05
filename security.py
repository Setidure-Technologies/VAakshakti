from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt # PyJWT library
import os
import logging # Add logging
import uuid # For generating JTI

# --- Configuration ---
# For JWT, generate a strong secret key. You can use:
# import os; os.urandom(32).hex()
# Store this in an environment variable in production.
SECRET_KEY = os.getenv("SECRET_KEY", "your-fallback-secret-key-for-development") # CHANGE THIS!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)) # Default 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)) # Default 7 days

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- JWT Token Handling ---
# Get a logger instance
logger = logging.getLogger(__name__)
# Configure basic logging if no handlers are set (sends to stderr by default)
# This is a simple setup; in a larger app, you'd configure logging more centrally.
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add 'iat' (issued at) and 'jti' (JWT ID) claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token decoding failed: ExpiredSignatureError")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token decoding failed: InvalidTokenError - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during token decoding: {str(e)}")
        return None

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()), # Unique ID for the refresh token as well
        "token_type": "refresh" # Explicitly mark as refresh token
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# You would typically add more functions here, e.g., for getting current user from token,
# and FastAPI dependencies for requiring authentication.