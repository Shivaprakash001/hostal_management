# utils/update_room_prices.py
from database.db import Session
from models.models import Room

def update_room_prices():
    session = Session()

    # Room price mapping
    room_prices = {
        # Ground floor rooms (cheaper)
        "G1": 3500, "G2": 3500, "G3": 3500, "G4": 3500, "G5": 3500,

        # First floor rooms
        "101": 4000, "102": 4000, "103": 4000, "104": 4000, "105": 4000,

        # Second floor rooms
        "201": 4500, "202": 4500, "203": 4500, "204": 4500, "205": 4500,

        # Third floor rooms
        "301": 5000, "302": 5000, "303": 5000, "304": 5000, "305": 5000,

        # Fourth floor rooms (most expensive)
        "401": 5500, "402": 5500, "403": 5500, "404": 5500, "405": 5500
    }

    updated_count = 0
    for room_no, price in room_prices.items():
        room = session.query(Room).filter_by(room_no=room_no).first()
        if room:
            room.price = price
            updated_count += 1
            print(f"Updated {room_no} with price ₹{price}")

    session.commit()
    session.close()
    print(f"Successfully updated {updated_count} rooms with rent prices!")

if __name__ == "__main__":
    update_room_prices()
