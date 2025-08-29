# test_db.py
from database.db import Session
from models.models import User, UserRole
from utils.security import hash_password

# create a session
db = Session()

hashed_password = hash_password("admin123")
new_user = User(username="admin", password_hash=hashed_password, role=UserRole.admin)
db.add(new_user)
db.commit() 
db.refresh(new_user)

print("Created user:", new_user.username, new_user.role)