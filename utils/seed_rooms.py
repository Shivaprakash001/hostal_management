# services/seed_rooms.py
from database.db import Session
from models.models import Room

def seed_rooms():
    session = Session()

    # Predefined room IDs/numbers
    room_numbers = [
        "G1", "G2", "G3", "G4", "G5",
        "101", "102", "103", "104", "105",
        "201", "202", "203", "204", "205",
        "301", "302", "303", "304", "305",
        "401", "402", "403", "404", "405"
    ]

    for rn in room_numbers:
        # Add only if not already in DB
        if not session.query(Room).filter_by(room_no=rn).first():
            session.add(Room(room_no=rn))

    session.commit()
    session.close()
    print("Rooms seeded successfully!")

def init_rooms():
    try:
        seed_rooms()
    except Exception as e:
        print(f"Error seeding rooms: {e}")

if __name__ == "__main__":
    seed_rooms()
