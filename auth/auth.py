import os
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from database import database

# Constants
# TODO: Replace with environment variables
SECRET_KEY = "testkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

# TODO: Fake in-memory user storage for now (replace with DB later)
db_users = {}

# Convenience helpers

def hash_password(password: str) -> str:
    '''Hashes a password using bcrypt.'''
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''Verifies a password against a hashed password.'''
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    '''
    Creates an access token with an expiration time and 
    associates it with the http response object.
    '''
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def check_and_renew_access_token(request: Request, response: Response):
    '''
    Checks access token for validity, and renews if it is within timeout.
    Otherwise, raises an exception.
    Should run first on all protected routes.
    '''
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if datetime.now(timezone.utc) < datetime.fromtimestamp(payload["exp"], timezone.utc):
            # renew token within timeout
            access_token = create_access_token({"sub": payload["sub"]})
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="Lax"
            )
        if (datetime.now(timezone.utc) > datetime.fromtimestamp(payload["exp"], timezone.utc)):
            # token expired
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access Token has expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload

def get_current_user(request: Request):
    '''Retrieves the current user from the request.'''
    check_and_renew_access_token(request, Response)
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) 
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Routes
@router.post("/register")
async def register(username: str, password: str):
    '''Registers a new user.'''

    # get all user entries from postgres db 
    user_ids = []
    async with database.AsyncSessionLocalFactory() as session:
        user_ids = await session.execute(select(database.User.userid))
        user_ids = user_ids.scalars().all()

    if username in user_ids:
        raise HTTPException(status_code=400, detail="User already exists")
    else:
        print("New user found against database!")
    db_users[username] = hash_password(password)
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(user: str, password: str, response: Response):
    '''
    Logs in a user and sets a cookie with the access token.
    No HTTP request data to read.
    '''
    stored_password = db_users.get(user.username)
    if not stored_password or not verify_password(user.password, stored_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.username})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    return {"message": "Login successful"}

@router.post("/logout")
async def logout(response: Response):
    '''
    Logs out a user by deleting the access token cookie.
    No HTTP request data to read.
    '''
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_me(request: Request, response: Response):
    '''
    Returns the current user's information.
    Checks and renews the access token if necessary.
    '''
    check_and_renew_access_token(request, response)
    user=get_current_user(request)
    return {"username": user["sub"]}
