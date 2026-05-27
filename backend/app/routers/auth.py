from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserCreate, UserResponse, Token
from app.security import get_password_hash, verify_password, create_access_token, timedelta, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем, есть ли уже такой юзер
    result = await db.execute(select(User).filter(User.username == user_data.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
        
    # Создаем нового пользователя
    hashed_pw = get_password_hash(user_data.password)
    # Защита: роль admin можно выдать только если это указано, по умолчанию будет viewer/service
    try:
        role_enum = UserRole(user_data.role)
    except ValueError:
        role_enum = UserRole.viewer

    new_user = User(
        username=user_data.username,
        hashed_password=hashed_pw,
        role=role_enum
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}