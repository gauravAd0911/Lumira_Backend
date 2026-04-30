from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # FIXED: bcrypt 72-byte limit + encoding (KEEP AS IS)
    safe_password = password.encode('utf-8')[:72]
    return pwd_context.hash(safe_password)

def verify_password(plain: str, hashed: str) -> bool:
    safe_plain = plain.encode('utf-8')[:72]
    return pwd_context.verify(safe_plain, hashed)