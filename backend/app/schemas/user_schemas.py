from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr  # change from username
    password: str

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str
