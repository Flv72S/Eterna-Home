from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    print(f"DEBUG VERIFY_PASSWORD: plain={plain_password}, hashed={hashed_password}")
    return pwd_context.verify(plain_password, hashed_password) 