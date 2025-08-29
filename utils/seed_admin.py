#services/seed_admin.py
from models.models import User, UserRole
from passlib.hash import bcrypt
from database.db import Session

def seed_admin():
    db = Session()
    if not db.query(User).filter(User.role == UserRole.admin).first():
        admin = User(
            username="admin",
            role=UserRole.admin,
            password_hash=bcrypt.hash("admin123")
        )
        db.add(admin)
        db.commit()
        print("Default admin created: username=admin, password=admin123")
    db.close()
