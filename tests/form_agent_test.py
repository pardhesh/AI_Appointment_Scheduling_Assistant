"""
Test script for form_agent.py
-----------------------------
- Tests the two main scenarios for the form agent.
- Requires your .env file to be set up with SendGrid credentials.
- Requires the 'New Patient Intake Form.pdf' to be in the correct location.
"""

# Make sure the agent can be imported
from src.agents.form_agent import form_agent

# --- Test Case 1: Appointment was Confirmed ---
print("--- 1. TESTING 'APPOINTMENT CONFIRMED' SCENARIO ---")

# This simulates the state after a patient has successfully confirmed their booking.
confirmed_state = {
    "confirmation_status": "appointment_confirmed",
    "patient_record": {
        "Name": "pardhesh maddala",
        # IMPORTANT: Replace this with your own email address to receive the test email.
        "Email": "pardheshmaddala24@gmail.com", 
    }
}

print(f"Attempting to send intake form to: {confirmed_state['patient_record']['Email']}")
result_confirmed = form_agent(confirmed_state)
print("Agent returned:", result_confirmed)
print("CHECK: You should receive an email with a PDF attachment.")
print("-" * 50)


# --- Test Case 2: Appointment was NOT Confirmed ---
print("\n--- 2. TESTING 'SKIPPED' SCENARIO ---")

# This simulates a state where the patient cancelled or the booking failed.
skipped_state = {
    "confirmation_status": "appointment_cancelled", # Could be any status other than "appointment_confirmed"
    "patient_record": {
        "Name": "Test name",
        "Email": "pardheshmaddala24@gmail.com",
    }
}

print("Attempting to run agent on a non-confirmed appointment...")
result_skipped = form_agent(skipped_state)
print("Agent returned:", result_skipped)
print("CHECK: The agent should return 'skipped_not_confirmed' and no email should be sent.")
print("-" * 50)
