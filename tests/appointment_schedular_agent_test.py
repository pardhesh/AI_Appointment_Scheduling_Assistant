import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.agents.appointment_scheduler_agent import schedule_appointment

def test_returning():
    state = {
        "status": "returning",
        "extracted_info": {"name": "Ravi Varma", "doctor": "Dr. Arjun Reddy", "location": "Bengaluru"}
    }
    updated = schedule_appointment(state, "09-09-2025")
    print("Returning:", updated["scheduled_slot"])

def test_new():
    state = {
        "status": "new",
        "extracted_info": {"name": "Anita Sharma", "doctor": "Dr. Arjun Reddy", "location": "Bengaluru"}
    }
    updated = schedule_appointment(state, "09-09-2025")
    print("New:", updated["scheduled_slot"])

if __name__ == "__main__":
    test_returning()
    test_new()
