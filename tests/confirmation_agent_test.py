import sys
from pathlib import Path
from unittest.mock import patch
import pandas as pd

# --- Add the project root to the Python path ---
# This allows us to import from the 'src' folder
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agents.confirmation_agent import confirmation_agent

# ==============================================================================
# IMPORTANT: SETUP INSTRUCTIONS BEFORE RUNNING
# ==============================================================================
# To ensure these tests run correctly, please do the following:
#
# 1. Create/replace 'data/doctor_schedule.xlsx' with this exact content:
#
#    Doctor Name,Date,Time Slot,Status
#    Dr. Evelyn Reed,2025-09-08,10:00-10:30,Booked
#    Dr. Evelyn Reed,2025-09-08,10:30-11:00,Booked
#    Dr. Evelyn Reed,2025-09-08,11:00-11:30,Available
#
# 2. Create/replace 'data/synthetic_patients.csv' with this exact content:
#
#    Name,DOB,Location,Insurance Carrier,Member ID,Group Number,Email,Phone
#    Existing Patient,01-01-1990,Old Town,Old Insurance,E123,G99,existing@test.com,9876543210
#
# 3. Delete 'data/patient_status.xlsx' if it exists.
#
# ==============================================================================

def run_tests():
    """Runs a series of manual test cases."""

    # --- Test Case 1: New Patient Confirms Appointment ---
    # We use '@patch' to automatically provide the required inputs.
    print("\n--- 1. TESTING NEW PATIENT (CONFIRM) ---")
    new_patient_state_confirm = {
        "status": "new",
        "extracted_info": {"name": "New Patient Alice", "dob": "02-02-2000"},
        "insurance_carrier": "HealthFirst", "member_id": "N123", "group_number": "G1",
        "scheduled_slot": {
            "status": "confirmed", "doctor": "Dr. Arjun Reddy", 
            "date": "08-09-2025", "time": "10:30-11:00 & 11:00-11:30"
        }
    }
    # side_effect provides inputs in order: email, phone, confirm/cancel
    with patch('builtins.input', side_effect=['alice@email.com', '9032278543', 'CONFIRM']):
        result = confirmation_agent(new_patient_state_confirm)
    print("Final State Update:", result)
    print("CHECK: 'synthetic_patients.csv' should now have 'New Patient Alice'.")
    print("CHECK: 'patient_status.xlsx' should be created with Alice's confirmed appointment.")
    print("-" * 50)


    # --- Test Case 2: New Patient Cancels Appointment ---
    print("\n--- 2. TESTING NEW PATIENT (CANCEL) ---")
    new_patient_state_cancel = {
        "status": "new",
        "extracted_info": {"name": "New Patient Bob", "dob": "03-03-2001"},
        "insurance_carrier": "WellCare", "member_id": "N456", "group_number": "G2",
        "scheduled_slot": {
            "status": "confirmed", "doctor": "Dr. Arjun Reddy", 
            "date": "08-09-2025", "time": "10:00-10:30"
        }
    }
    with patch('builtins.input', side_effect=['bob@email.com', '9032278543', 'CANCEL']):
        result = confirmation_agent(new_patient_state_cancel)
    print("Final State Update:", result)
    print("CHECK: 'New Patient Bob' should NOT be in 'synthetic_patients.csv'.")
    print("CHECK: 'doctor_schedule.xlsx' slot at 10:00 should be 'Available' again.")
    print("-" * 50)


    # --- Test Case 3: Returning Patient Confirms Appointment ---
    print("\n--- 3. TESTING RETURNING PATIENT (CONFIRM) ---")
    returning_patient_state = {
        "status": "returning",
        "lookup_result": {
            "patient": {
                "name": "pardhesh maddala", "dob": "01-08-2005", 
                "email": "pardheshmaddala24@gmail.com", "phone": "9032278543"
            }
        },
        "scheduled_slot": {
            "status": "confirmed", "doctor": "Dr. Arjun Reddy", 
            "date": "08-09-2025", "time": "11:00-11:30"
        }
    }
    with patch('builtins.input', return_value='CONFIRM'):
        result = confirmation_agent(returning_patient_state)
    print("Final State Update:", result)
    print("CHECK: 'patient_status.xlsx' should now have a second entry for 'Existing Patient'.")
    print("CHECK: 'synthetic_patients.csv' should be unchanged.")
    print("-" * 50)


if __name__ == "__main__":
    run_tests()

