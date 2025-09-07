# services/seed_rooms.py
from database.db import Session
from models.models import Room

def seed_rooms():
    session = Session()

    # Predefined room IDs/numbers with rent prices
    room_data = [
        # Ground floor rooms (cheaper)
        {"room_no": "G1", "price": 3500},
        {"room_no": "G2", "price": 3500},
        {"room_no": "G3", "price": 3500},
        {"room_no": "G4", "price": 3500},
        {"room_no": "G5", "price": 3500},

        # First floor rooms
        {"room_no": "101", "price": 4000},
        {"room_no": "102", "price": 4000},
        {"room_no": "103", "price": 4000},
        {"room_no": "104", "price": 4000},
        {"room_no": "105", "price": 4000},

        # Second floor rooms
        {"room_no": "201", "price": 4500},
        {"room_no": "202", "price": 4500},
        {"room_no": "203", "price": 4500},
        {"room_no": "204", "price": 4500},
        {"room_no": "205", "price": 4500},

        # Third floor rooms
        {"room_no": "301", "price": 5000},
        {"room_no": "302", "price": 5000},
        {"room_no": "303", "price": 5000},
        {"room_no": "304", "price": 5000},
        {"room_no": "305", "price": 5000},

        # Fourth floor rooms (most expensive)
        {"room_no": "401", "price": 5500},
        {"room_no": "402", "price": 5500},
        {"room_no": "403", "price": 5500},
        {"room_no": "404", "price": 5500},
        {"room_no": "405", "price": 5500}
    ]

    for room_info in room_data:
        # Add only if not already in DB
        if not session.query(Room).filter_by(room_no=room_info["room_no"]).first():
            session.add(Room(
                room_no=room_info["room_no"],
                price=room_info["price"]
            ))

    session.commit()
    session.close()
    print("Rooms seeded successfully with rent prices!")

def init_rooms():
    try:
        seed_rooms()
    except Exception as e:
        print(f"Error seeding rooms: {e}")

if __name__ == "__main__":
    seed_rooms()
