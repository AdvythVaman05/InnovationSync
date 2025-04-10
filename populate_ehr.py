import random
from faker import Faker
from pymongo import MongoClient

fake = Faker()

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["synthetic_ehr"]

# Collections
patient_login = db["patient_login"]
doctor_login = db["doctor_login"]
patient_records = db["patient_records"]
patient_doctor_connections = db["patient_doctor_connections"]

# Clear existing data
patient_login.delete_many({})
doctor_login.delete_many({})
patient_records.delete_many({})
patient_doctor_connections.delete_many({})

# Configuration
NUM_PATIENTS = 50
NUM_DOCTORS = 10
DISEASES = ["diabetes", "blood_pressure", "arthritis", "asthma", "thyroid"]

# Generate doctors
doctor_ids = []
for i in range(NUM_DOCTORS):
    doctor_id = f"DOC{1000 + i}"
    password = fake.password()
    doctor_ids.append(doctor_id)
    doctor_login.insert_one({
        "doctor_id": doctor_id,
        "password": password
    })

# Generate patients
for i in range(NUM_PATIENTS):
    patient_id = f"PAT{1000 + i}"
    password = fake.password()
    patient_login.insert_one({
        "patient_id": patient_id,
        "password": password
    })

    # General patient info
    record = {
        "patient_id": patient_id,
        "name": fake.name(),
        "age": random.randint(18, 90),
        "gender": random.choice(["Male", "Female", "Other"]),
        "address": fake.address(),
        "contact": fake.phone_number(),
    }

    # Disease flags (yes/no)
    for disease in DISEASES:
        record[disease] = random.choice(["yes", "no"])

    patient_records.insert_one(record)

    # Assign patient to a random doctor for socket connection
    assigned_doc = random.choice(doctor_ids)
    room_id = f"room_{patient_id}_{assigned_doc}"
    patient_doctor_connections.insert_one({
        "patient_id": patient_id,
        "doctor_id": assigned_doc,
        "room_id": room_id
    })

print("✅ Synthetic EHR database populated successfully!")
