from fastapi import APIRouter, HTTPException, Depends
from services.room_services import create_room, delete_room
from database.db import Session
from schemas.room import RoomCreate, DeleteRoom, RoomWithStudents, RoomOut, UpdateRoom
from schemas.payments import PaymentStatus
from models.models import Room, User, UserRole
from utils.auth import get_current_user, require_role
from typing import List
router = APIRouter(prefix="/rooms", tags=["rooms"])

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

# Create room
@router.post("/", response_model=RoomOut)
def add_room(room: RoomCreate, current_user: User = Depends(require_role([UserRole.admin])), db: Session = Depends(get_db)):
    return create_room(room.room_no, room.price, db, capacity=room.capacity)

# Delete room
@router.delete("/", response_model=dict)
def remove_room(room: DeleteRoom, current_user: User = Depends(require_role([UserRole.admin])), db: Session = Depends(get_db)):
    return delete_room(room.room_no, db)

# Get all rooms (with students)
@router.get("/", response_model=List[RoomWithStudents])
def get_rooms(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Only admins can see all rooms
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    rooms = db.query(Room).all()
    for room in rooms:
        total_paid = sum(payment.amount for payment in room.payments if payment.status == PaymentStatus.paid)
        room.total_payments = total_paid
        room.payment_status = PaymentStatus.paid if total_paid >= room.price else PaymentStatus.pending
    return rooms

# Get room by number
@router.get("/{room_no}", response_model=RoomWithStudents)
def get_room_by_no(room_no: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter_by(room_no=room_no).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

# Update room
@router.put("/{room_no}", response_model=RoomOut)
def update_room(room_no: str, update: UpdateRoom, db: Session = Depends(get_db)):
    room = db.query(Room).filter_by(room_no=room_no).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if update.new_room_no:
        room.room_no = update.new_room_no
    if update.price is not None:
        room.price = update.price
    if update.capacity is not None:
        room.capacity = update.capacity
    db.commit()
    db.refresh(room)
    return room
