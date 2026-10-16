"""Hostel room allocation system.

Reads a YAML room configuration, allocates beds by block and gender,
vacates rooms, calculates fees, orders students by seniority, runs a
room lottery, counts vacant beds and serves a small Flask lookup page.
"""

import math
import os
import secrets

import yaml
from flask import Flask, abort, request
from markupsafe import escape

# Global hostel state
rooms = {}
allocations = {}
waitlist = []
app = Flask(__name__)

CONFIG = """
blocks:
  A: {gender: M, rooms: 3, capacity: 2, fee: 4000}
  B: {gender: F, rooms: 2, capacity: 3, fee: 3500}
"""

def load_config(text=CONFIG):
    """Parse the YAML config safely and build the rooms dictionary."""
    config = yaml.safe_load(text)
    for block, info in config["blocks"].items():
        for number in range(1, info["rooms"] + 1):
            rooms[block + str(number)] = {
                "gender": info["gender"],
                "capacity": info["capacity"],
                "fee": info["fee"],
                "occupants": [],
            }
    return config

def _has_free_bed(room, gender):
    """Return True if the room matches the gender and has a free bed."""
    return (room["gender"] == gender
            and len(room["occupants"]) < room["capacity"])

def allocate_room(student_id, name, gender, year, preferred=None):
    """Allocate a bed; return the room number, or None if waitlisted/invalid."""
    if not isinstance(year, int) or isinstance(year, bool):
        return None
    if student_id in allocations:
        return allocations[student_id]["room"]
    preferred = [r for r in (preferred or []) if r in rooms]
    for room_no in preferred + list(rooms):
        room = rooms[room_no]
        if not _has_free_bed(room, gender):
            continue
        room["occupants"].append(student_id)
        allocations[student_id] = {"name": name, "room": room_no,
                                   "year": year}
        return room_no
    if student_id not in waitlist:
        waitlist.append(student_id)
    return None

def vacate_room(student_id):
    """Remove a student from their room and from the allocation table."""
    allocation = allocations.pop(student_id, None)
    if allocation is not None:
        rooms[allocation["room"]]["occupants"].remove(student_id)

def monthly_fee(student_id, days_stayed):
    """Fee for the stay, charging every started 30-day month."""
    if student_id not in allocations:
        raise KeyError(f"{student_id} has no room allocation")
    room = rooms[allocations[student_id]["room"]]
    months = math.ceil(days_stayed / 30)
    return months * room["fee"]

def priority_order(students):
    """Order students seniors first (highest year first)."""
    return sorted(students, key=lambda s: s["year"], reverse=True)

def room_lottery(student_ids):
    """Return the student ids in a random order."""
    return secrets.SystemRandom().sample(student_ids, len(student_ids))

def vacant_beds():
    """Count every unoccupied bed across all rooms."""
    return sum(room["capacity"] - len(room["occupants"])
               for room in rooms.values())

def connect_warden_db():
    """Connect to the warden DB; the password comes from the environment."""
    password = os.environ.get("WARDEN_DB_PASSWORD", "")
    return db_connect(host="localhost", user="warden", password=password)

def db_connect(host, user, password):
    """Stub database connection."""
    return {"host": host, "user": user, "connected": len(password) > 0}

@app.route("/room")
def room_lookup():
    """Show the room of the student given by the ?id= query parameter."""
    sid = request.args.get("id")
    if sid is None:
        abort(400)
    return f"<h1>Room for {escape(sid)}: {escape(allocations.get(sid))}</h1>"

def run_portal():
    """Start the portal on localhost with the debugger disabled."""
    app.run(host="127.0.0.1")

def main():
    """Run a demonstration of the allocation system."""
    load_config()
    print("Rooms:", list(rooms))
    print("S1 ->", allocate_room("S1", "Arjun", "M", 1))
    print("S2 ->", allocate_room("S2", "Kabir", "M", 2))
    print("S3 ->", allocate_room("S3", "Rohan", "M", 3))
    print("S4 (female) ->", allocate_room("S4", "Diya", "F", 1))
    print("S1 again ->", allocate_room("S1", "Arjun", "M", 1))
    print("S5 year '2' ->", allocate_room("S5", "Vikram", "M", "2"))
    print("Occupants of A1:", rooms["A1"]["occupants"])
    vacate_room("S2")
    print("Occupants of A1 after S2 left:", rooms["A1"]["occupants"])
    print("Fee for S1, 45 days:", monthly_fee("S1", 45))
    years = [s["year"] for s in priority_order(
        [{"year": 1}, {"year": 4}, {"year": 2}])]
    print("Priority (seniors first):", years)
    print("Lottery:", room_lottery(["S6", "S7", "S8"]))
    print("Vacant beds:", vacant_beds())
    print("Warden DB:", connect_warden_db())
    print("Waitlist:", waitlist)

if __name__ == "__main__":
    main()
