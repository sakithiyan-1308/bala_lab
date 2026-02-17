import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid
import bcrypt

# Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "balalab_db")

async def seed():
    print(f"Connecting to {MONGO_URL}...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Clean up
    print("Clearing existing users and reports...")
    await db.users.delete_many({})
    await db.reports.delete_many({})
    
    # Create Admin
    admin_id = str(uuid.uuid4())
    admin_data = {
        "id": admin_id,
        "email": "admin@balalab.demo",
        "password_hash": bcrypt.hashpw("demo".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "admin",
        "created_at": datetime.utcnow().isoformat()
    }
    await db.users.insert_one(admin_data)
    print(f"Created Admin: {admin_data['email']} / demo")
    
    # Create Patient
    patient_id = str(uuid.uuid4())
    patient_data = {
        "id": patient_id,
        "email": "patient@balalab.demo",
        "password_hash": bcrypt.hashpw("demo".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "user",
        "created_at": datetime.utcnow().isoformat()
    }
    await db.users.insert_one(patient_data)
    print(f"Created Patient: {patient_data['email']} / demo")
    
    print("Seeding complete!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed())
