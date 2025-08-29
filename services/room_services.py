from models.models import Room
from database.db import Session

def create_room(room_no: str, price: float, db: Session, capacity: int = 4) -> Room:
    existing = db.query(Room).filter_by(room_no=room_no).first()
    if existing:
        raise ValueError(f"Room {room_no} already exists")
    room = Room(room_no=room_no, price=price, capacity=capacity)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

def delete_room(room_no: str, db: Session):
    room = db.query(Room).filter_by(room_no=room_no).first()
    if not room:
        raise ValueError(f"Room {room_no} does not exist")
    db.delete(room)
    db.commit()
    return {"message": "Room deleted successfully", "deleted_room": {"room_no": room_no}}
