# Authentication utilities

import jwt
from datetime import UTC, timedelta, datetime
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer # Handles token-based authentication

from config import settings

password_hasher = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl="/api/users/token" # Indicates where to send username and password to fetch access token
        )

def hash_password(password: str) -> str: # creates the hashed password
    return password_hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool: # Verifies what we just received against what we have (usually user input vs. password hash in or db)
    return password_hasher.verify(plain_password, hashed_password)

def create_access_token(data: dict, expire_time: timedelta | None = None) -> str:
    to_encode = data.copy()

    if expire_time:
        expire = datetime.now(UTC) + expire_time
    else:
        expire = datetime.now(UTC) + timedelta(settings.access_token_expire_minutes)

    to_encode["exp"] = expire
    jwt_token = jwt.encode(
                        payload=to_encode,
                        key=settings.secret_key.get_secret_value(), 
                        algorithm=settings.algorithm
                               )
    return jwt_token

def verify_access_token(token: str) -> str | None:
    """ Verify a JWT Token and return the subject (user ID) if the token is valid"""
    try:
        decoded_token = jwt.decode(
            jwt=token,
            key=settings.secret_key.get_secret_value(),
            algorithms=settings.algorithm,
            options={"require": ["exp", "sub"]}
        )
    except jwt.InvalidTokenError:
        return None
    else:
        
        return decoded_token.get("sub")