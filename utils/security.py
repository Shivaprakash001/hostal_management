from passlib.hash import bcrypt

def hash_password(password: str) -> str:
    from passlib.hash import bcrypt
    return bcrypt.hash(password)