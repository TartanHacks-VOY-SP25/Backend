"""
Authentication module for FastAPI application.
"""

from typing import List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from passlib.context import CryptContext
from database import database
from jose import JWTError, jwt
from typing import List
import xrpledger.smart_contracts as xrp
from database import database

# Constants
# TODO: REPLACE WITH ENV VARS
SECRET_KEY = "testkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

# Convenience helpers

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Creates an access token with an expiration time and
    associates it with the http response object.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def check_and_renew_access_token(request: Request, response: Response):
    """
    Checks access token for validity, and renews if it is within timeout.
    Otherwise, raises an exception.
    Should run first on all protected routes.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if datetime.now(timezone.utc) < datetime.fromtimestamp(
            payload["exp"], timezone.utc
        ):
            # renew token within timeout
            access_token = create_access_token({"sub": payload["sub"]})
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="Lax",
            )
        if datetime.now(timezone.utc) > datetime.fromtimestamp(
            payload["exp"], timezone.utc
        ):
            # token expired
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access Token has expired",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    return payload


def get_current_user(request: Request):
    """Retrieves the current user from the request."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


# Routes
@router.post("/register", tags=["Authentication"])
async def register(username: str, password: str):
    """Registers a new user."""
    async with database.AsyncSessionLocalFactory() as session:
        user_ids = await session.execute(select(database.User.user_id))
        user_ids: List[database.User] = user_ids.scalars().all()
        if username in user_ids:
            raise HTTPException(status_code=400, detail="User already exists")
        else:
            # TODO: XRP INTEGRATION HERE
            xrp_wallet = await xrp.create_account()
            xrp_acc_num  = xrp_wallet[0]
            xrp_acc_addr = xrp_wallet[1]
            new_user = database.User(
                user_id=username,
                hashed_password=hash_password(password),
                wallet_number=xrp_acc_num,
                wallet_address=xrp_acc_addr,
            )
            session.add(new_user)
            await session.commit()
    return {
        "message": "User registered successfully",
        "XRP Wallet Address": xrp_acc_addr,
        "XRP Account Seed (Only available once)": xrp_acc_num
    }


@router.post("/login", tags=["Authentication"])
async def login(user: str, password: str, response: Response):
    """
    Logs in a user and sets a cookie with the access token.
    No HTTP request data to read.
    """
    async with database.AsyncSessionLocalFactory() as session:
        user = await session.execute(
            select(database.User).where(database.User.user_id == user)
        )
        user: database.User = user.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

    if not user.hashed_password or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token({"sub": user.user_id})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return {"message": "Login successful"}


@router.post("/logout", tags=["Authentication"])
async def logout(response: Response):
    """
    Logs out a user by deleting the access token cookie.
    No HTTP request data to read.
    """
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", tags=["Authentication"])
async def get_me(request: Request, response: Response):
    """
    Returns the current user's information.
    Checks and renews the access token if necessary.
    """

    # debug
    print(f"Request Headers: {dict(request.headers)}")
    print(f"Request Query Parameters: {dict(request.query_params)}")
    try:
        print(f"Request JSON Body: {await request.json()}")
    except Exception:
        print(f"Request Text Body: {await request.body()}")
    print(f"Request Method: {request.method}")
    print(f"Request URL: {request.url}")

    check_and_renew_access_token(request, response)
    user = get_current_user(request)["sub"]
    async with database.AsyncSessionLocalFactory() as session:
        user_details = await session.execute(
            select(database.User).where(
                database.User.user_id == user
            )
        )
        user_entry:database.User = user_details.scalars().first()
        balance = await xrp.check_balance(
            user_entry.wallet_address
        )
        print(balance)

        return {
            "username": user,
            "account_balance": balance
        }
