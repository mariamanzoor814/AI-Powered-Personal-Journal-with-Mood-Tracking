from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.models import User
from app.db.database import get_db
from app.auth.auth import get_password_hash, verify_password, create_access_token
import random, string
from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema
from app.schemas.user_schemas import UserRegister, UserLogin, VerifyOTP
from app.core.config import mail_conf  # 👈 import shared mail config

router = APIRouter(prefix="/users", tags=["users"])


# ---- Utility ----
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


# ---- Verify OTP ----
@router.post("/verify")
def verify_user(data: VerifyOTP, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        return {"msg": "User already verified"}
    if user.otp_code != data.otp or user.otp_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user.is_verified = True
    user.otp_code = None
    user.otp_expiry = None
    db.commit()
    return {"msg": "Account verified successfully"}


# ---- Register ----
@router.post("/register", status_code=201)
async def register(data: UserRegister, db: Session = Depends(get_db)):
    # Check if username/email exists
    existing = db.query(User).filter(
        (User.username == data.username) | (User.email == data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    hashed_password = get_password_hash(data.password)
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=10)

    # Create user object but do NOT commit yet
    new_user = User(
        username=data.username,
        email=data.email,
        hashed_password=hashed_password,
        created_at=datetime.utcnow(),
        otp_code=otp,
        otp_expiry=expiry
    )

    # Send OTP email first
    fm = FastMail(mail_conf)
    message = MessageSchema(
        subject="Your OTP Code",
        recipients=[data.email],
        body=f"Your verification code is {otp}. It expires in 10 minutes.",
        subtype="plain"
    )

    try:
        await fm.send_message(message)
    except Exception as e:
        # Fail gracefully if email sending fails
        raise HTTPException(status_code=500, detail=f"Could not send email: {str(e)}")

    # Only now add to DB if email succeeded
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"msg": "User registered successfully. Check your email for OTP."}


# ---- Login ----
@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()  # use email
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Account not verified. Please check your email.")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

