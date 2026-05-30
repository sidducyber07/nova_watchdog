import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

from ..core.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from ..db import get_db
from .. import models, schemas

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    q = await db.execute(models.sa.select(models.User).where(models.User.id == user_id))
    user = q.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=schemas.UserOut, status_code=201)
async def register(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        q = await db.execute(models.sa.select(models.User).where(models.User.email == user_in.email))
        existing = q.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user = models.User(id=str(uuid.uuid4()), email=user_in.email, hashed_password=hash_password(user_in.password), full_name=user_in.full_name)
        db.add(user)
    await db.commit()
    return user


@router.post("/login", response_model=schemas.Token)
async def login(form: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.User).where(models.User.email == form.email))
    user = q.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id)
    return {"access_token": token}


@router.get("/me", response_model=schemas.UserOut)
async def me(current_user: models.User = Depends(get_current_user)):
    return current_user
