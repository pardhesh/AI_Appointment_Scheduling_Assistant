"""
Reminder Agent (Corrected Logic)
---------------------------------
- Fixes the bug where incorrect reminders were being sent by using independent 'if'
  statements for each reminder check instead of an 'if/elif' chain.
- Ensures every patient is evaluated for every due reminder on each run.
- Resolves the pandas FutureWarning by pre-defining column dtypes.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from apscheduler.schedulers.blocking import BlockingScheduler

# --- Configuration and Setup ---
load_dotenv()

# --- File Path ---
STATUS_FILE = "data/patient_status.xlsx"

# --- Twilio Credentials ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# --- Initialize API Client ---
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]) else None

# --- SMS Sending Helper Function ---

def normalize_phone(phone: str) -> str:
    """Ensure phone is in E.164 format (default: India +91)."""
    if not phone or str(phone).lower() == "nan":
        return None
    phone = str(phone).strip()
    if not phone.startswith("+"):
        phone = "+91" + phone
    return phone

def _send_sms(ph: str, body: str):
    """Sends a real or simulated SMS message."""
    phone = normalize_phone(ph)
    if not twilio_client:
        print(f"--- [SMS Simulation] To: {phone}, Body: {body} ---")
        return
        
    try:
        message = twilio_client.messages.create(body=body, from_=TWILIO_PHONE_NUMBER, to=phone)
        print(f"--- SMS sent successfully to {phone} (SID: {message.sid}) ---")
    except TwilioRestException as e:
        print(f"--- ERROR sending SMS to {phone}: {e} ---")


# --- Core Logic ---
def check_and_send_reminders():
    """
    The main function that is run by the scheduler.
    It reads the appointment status file and sends reminders based on the rules.
    """
    print(f"\n--- [{datetime.now():%Y-%m-%d %H:%M:%S}] Running Reminder Check ---")
    
    status_path = Path(STATUS_FILE)
    if not status_path.exists():
        print("--- Status file not found. Skipping. ---")
        return

    df = pd.read_excel(status_path)
    if df.empty:
        print("--- Status file is empty. Skipping. ---")
        return

    # --- Data Integrity: Ensure reminder tracking columns exist ---
    reminder_cols = ["Reminder1_Sent", "Reminder2_Sent", "Reminder3_Sent"]
    made_changes = False
    for col in reminder_cols:
        if col not in df.columns:
            # FIX: Initialize with a dtype that supports both None and strings
            df[col] = pd.Series(dtype='object')
            made_changes = True
            print(f"--- Added missing tracking column: '{col}' ---")

    today = datetime.now().date()
    # Use errors='coerce' to gracefully handle any malformed dates
    df['DOA'] = pd.to_datetime(df['DOA'], errors='coerce', format="%d-%m-%Y").dt.date

    # --- Loop through each confirmed, future appointment ---
    for index, row in df.iterrows():
        if row['Status'] != 'Confirmed' or pd.isnull(row['DOA']) or row['DOA'] < today:
            continue

        days_until = (row['DOA'] - today).days
        patient_name = row['Patient_Name']
        doctor_name = row['Doctor_Name']
        time_slot = row['Time_Slot']
        phone_number = row['Phone_Number']

        # *** FIX APPLIED HERE: Use separate 'if' statements instead of 'if/elif' ***
        # This ensures every reminder condition is checked for every patient on every run.

        # --- Reminder 1 Logic (3 days before) ---
        if days_until == 3 and pd.isnull(row['Reminder1_Sent']):
            print(f"-> Sending Reminder 1 for {patient_name}")
            msg = f"Hello {patient_name}, this is a reminder of your appointment with {doctor_name} on {row['DOA']:%d-%m-%Y} at {time_slot}."
            _send_sms(phone_number, msg)
            df.loc[index, 'Reminder1_Sent'] = "Yes"
            made_changes = True

        # --- Reminder 2 Logic (2 days before) ---
        if days_until == 2 and pd.isnull(row['Reminder2_Sent']):
            print(f"-> Sending Reminder 2 for {patient_name}")
            msg = f"Hi {patient_name}, have you completed your intake form? Reply YES or NO."
            _send_sms(phone_number, msg)
            df.loc[index, 'Reminder2_Sent'] = "Yes"
            made_changes = True

        # --- Reminder 3 Logic (1 day before) ---
        if days_until == 1 and pd.isnull(row['Reminder3_Sent']):
            print(f"-> Sending Reminder 3 for {patient_name}")
            msg = f"Remainder, {patient_name},your appointment is tomorrow. Reply CONFIRM if you are coming or CANCEL to cancel."
            _send_sms(phone_number, msg)
            df.loc[index, 'Reminder3_Sent'] = "Yes"
            made_changes = True
    
    # --- Save any changes back to the Excel file ---
    if made_changes:
        df['DOA'] = pd.to_datetime(df['DOA']).dt.strftime('%d-%m-%Y')
        df.to_excel(status_path, index=False)
        print("--- Status file updated with reminder tracking. ---")
    else:
        print("--- No new reminders to send. ---")


# --- Scheduler Execution ---
if __name__ == "__main__":
    try:
        import apscheduler
    except ImportError:
        print("APScheduler not found. Please run: pip install APScheduler")
        exit()

    check_and_send_reminders()

    scheduler = BlockingScheduler()
    scheduler.add_job(check_and_send_reminders, 'interval', hours=6)
    
    print("\n--- Reminder Agent is now running. It will check for reminders every 6 hours. ---")
    print("--- Press Ctrl+C to stop the agent. ---")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n--- Reminder Agent stopped. ---")

