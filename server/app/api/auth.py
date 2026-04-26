from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from app.database import get_db
from app.models.user import User

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

_bearer_scheme = HTTPBearer(auto_error=False)


class TokenRequest(BaseModel):
    credential: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/auth/google", response_model=TokenResponse)
def google_auth(request: TokenRequest, db: Session = Depends(get_db)):
    try:
        # Verify the Google JWT token
        idinfo = id_token.verify_oauth2_token(
            request.credential,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")

        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        # Check if user exists in DB
        db_user = db.query(User).filter(User.email == email).first()
        if not db_user:
            db_user = User(email=email, name=name, picture=picture)
            db.add(db_user)
        else:
            db_user.last_login = datetime.utcnow()
            db_user.name = name
            db_user.picture = picture

        db.commit()
        db.refresh(db_user)

        # Issue our own application token
        access_token = create_access_token(data={"sub": email, "user_id": db_user.id})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": db_user.id,
                "email": db_user.email,
                "name": db_user.name,
                "picture": db_user.picture
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")


# ---------------------------------------------------------------------------
# Reusable JWT dependency — use as Depends(get_current_user)
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
    db: Session = Depends(get_db),
):
    """
    Validate the Bearer JWT token and return the User ORM object.
    Raises HTTP 401 if token is missing, expired, or invalid.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload.")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user
