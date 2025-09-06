"""
ConfirmationAgent (Streamlit-Compatible Version)
------------------------------------------------
- Keeps all existing functionality (Twilio, file writes, schedule revert).
- Removes interactive `input()` calls.
- Accepts `email`, `phone`, and `decision` ("CONFIRM" or "CANCEL") as function arguments.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Union
import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# --- Load Environment Variables for Twilio ---
load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# --- Initialize Twilio Client ---
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    print("--- WARNING: Twilio credentials not found. SMS will be simulated. ---")

# --- File Paths and Columns ---
PATIENT_DB_FILE = "data/synthetic_patients.csv"
APPOINTMENT_STATUS_FILE = "data/patient_status.xlsx"
DOCTOR_SCHEDULE_FILE = "data/doctor_schedule.xlsx"
PATIENT_DB_COLUMNS = [
    "Name", "DOB", "Location", "Insurance Carrier",
    "Member ID", "Group Number", "Email", "Phone"
]
APPOINTMENT_STATUS_COLUMNS = [
    "Patient_Name", "Patient_DOB", "Doctor_Name", "DOA", "Time_Slot",
    "Email", "Phone_Number", "Status", "Form_Filled", "Cancellation_Reason"
]

# --- Helper Functions (unchanged) ---
def _format_phone_number(phone: str) -> Union[str, None]:
    if not phone or not isinstance(phone, str): 
        return None
    phone = phone.strip()
    if not phone.startswith('+'): 
        return f"+91{phone}"
    return phone

def _send_twilio_confirmation_sms(phone: str, details: Dict):
    if not phone:
        print("\n--- WARNING: Cannot send confirmation SMS, no phone number provided. ---\n")
        return
    doctor_name = details.get('doctor', '[Doctor Name]')
    appointment_date = details.get('date', '[Date]')
    time_slot = details.get('time', '[Time]')

    message_body = (
        f"Hi. Thank you for using the scheduling AI. "
        f"Your appointment with {doctor_name} on {appointment_date} is confirmed. "
        f"Your time slot is {time_slot}. "
        f"Please make sure to complete all necessary requirements and arrive 15 minutes early."
    )

    if not twilio_client:
        print(f"\n[Twilio Simulation] SMS to {phone}: {message_body}\n")
        return
    try:
        to_number = _format_phone_number(phone)
        message = twilio_client.messages.create(body=message_body, from_=TWILIO_PHONE_NUMBER, to=to_number)
        print(f"\n--- Confirmation SMS sent successfully to {to_number} (SID: {message.sid}) ---\n")
    except TwilioRestException as e:
        print(f"\n--- ERROR: Failed to send Twilio SMS. Details: {e} ---\n")

def _send_twilio_cancellation_sms(phone: str):
    if not phone:
        print("\n--- WARNING: Cannot send cancellation SMS, no phone number provided. ---\n")
        return
    message_body = "Your medical appointment has been successfully cancelled as requested."
    if not twilio_client:
        print(f"\n[Twilio Simulation] SMS to {phone}: {message_body}\n")
        return
    try:
        to_number = _format_phone_number(phone)
        message = twilio_client.messages.create(body=message_body, from_=TWILIO_PHONE_NUMBER, to=to_number)
        print(f"\n--- Cancellation SMS sent successfully to {to_number} (SID: {message.sid}) ---\n")
    except TwilioRestException as e:
        print(f"\n--- ERROR: Failed to send Twilio SMS. Details: {e} ---\n")

def _resolve_schedule_columns(df: pd.DataFrame) -> Union[Dict, None]:
    col_map = {"doctor": ["doctor name", "doctor", "dr"], "date": ["date"], "time": ["time slot", "time", "slot"], "status": ["status", "availability"]}
    resolved, normalized_cols = {}, {c.strip().lower(): c for c in df.columns}
    for key, aliases in col_map.items():
        for alias in aliases:
            if alias in normalized_cols:
                resolved[key] = normalized_cols[alias]
                break
    return resolved if len(resolved) == len(col_map) else None

def _revert_doctor_schedule(state: Dict):
    try:
        path = Path(DOCTOR_SCHEDULE_FILE)
        if not path.exists(): return
        df = pd.read_excel(path)
        resolved_cols = _resolve_schedule_columns(df)
        if not resolved_cols: return
        slot_info = state.get("scheduled_slot", {})
        doctor, date, times = slot_info.get("doctor"), pd.to_datetime(slot_info.get("date"), format="%d-%m-%Y").date(), [t.strip() for t in str(slot_info.get("time", "")).split('&')]
        condition = ((df[resolved_cols['doctor']].str.strip().str.lower() == doctor.lower()) & (pd.to_datetime(df[resolved_cols['date']]).dt.date == date) & (df[resolved_cols['time']].isin(times)))
        indices = df[condition].index
        if not indices.empty:
            df.loc[indices, resolved_cols['status']] = "Available"
            df.to_excel(path, index=False)
            print(f"--- Schedule updated for {doctor} on {date}. ---")
    except Exception as e:
        print(f"Error reverting doctor schedule: {e}")

def _remove_new_patient_record(patient_record: Dict):
    try:
        path = Path(PATIENT_DB_FILE)
        if not path.exists(): return
        df = pd.read_csv(path)
        condition = ((df['Name'].str.strip().str.lower() == str(patient_record.get("Name")).lower()) & (df['DOB'].str.strip() == str(patient_record.get("DOB"))))
        matches = df[condition]
        if not matches.empty:
            df.drop(matches.index[-1], inplace=True)
            df.to_csv(path, index=False)
            print(f"--- New patient record for {patient_record.get('Name')} removed. ---")
    except Exception as e:
        print(f"Error removing new patient record: {e}")

# --- Main Agent Logic (UPDATED) ---
def confirmation_agent(state: Dict, email: str = None, phone: str = None, decision: str = "CONFIRM") -> Dict:
    """
    Finalizes booking. Works for both NEW and RETURNING patients.
    Args:
        state: Conversation state (must include scheduled_slot + extracted_info).
        email: Patient email (from UI).
        phone: Patient phone (from UI).
        decision: "CONFIRM" or "CANCEL".
    """
    if not state.get("scheduled_slot") or state["scheduled_slot"].get("status") != "confirmed":
        return {"confirmation_status": "skipped_no_booking", "patient_record": None}

    # --- NEW Patient ---
    if state.get("status") == "new":
        info = state.get("extracted_info", {})
        patient_record = {
            "Name": info.get("name"), "DOB": info.get("dob"), "Location": info.get("location"),
            "Insurance Carrier": state.get("insurance_carrier"), "Member ID": state.get("member_id"),
            "Group Number": state.get("group_number"),
            "Email": (email or "").strip(), "Phone": (phone or "").strip()
        }

        # Save new patient
        try:
            path = Path(PATIENT_DB_FILE)
            df = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=PATIENT_DB_COLUMNS)
            pd.concat([df, pd.DataFrame([patient_record])])[PATIENT_DB_COLUMNS].to_csv(path, index=False)
        except Exception as e:
            return {"confirmation_status": f"error_writing_to_csv: {e}"}

        return _finalize_confirmation(state, patient_record, decision)

    # --- RETURNING Patient ---
    elif state.get("status") == "returning":
        pr_raw = state.get("lookup_result", {}).get("patient", {})
        transactional_record = {
            "Name": pr_raw.get("name"), "DOB": pr_raw.get("dob"),
            "Location": pr_raw.get("location"), "Insurance Carrier": pr_raw.get("insurance_carrier"),
            "Member ID": pr_raw.get("member_id"), "Group Number": pr_raw.get("group"),
            "Email": (email or "").strip(), "Phone": (phone or "").strip()
        }
        return _finalize_confirmation(state, transactional_record, decision)

    return {"confirmation_status": "error_unknown_patient_status", "patient_record": None}


def _finalize_confirmation(state: Dict, patient_record: Dict, decision: str) -> Dict:
    """Handles CONFIRM or CANCEL (no input calls)."""
    decision = (decision or "").strip().upper()
    if decision == "CONFIRM":
        slot = state.get("scheduled_slot", {})
        status_data = {
            "Patient_Name": patient_record.get("Name"), "Patient_DOB": patient_record.get("DOB"),
            "Doctor_Name": slot.get("doctor"), "DOA": slot.get("date"), "Time_Slot": slot.get("time"),
            "Email": patient_record.get("Email"), "Phone_Number": patient_record.get("Phone"),
            "Status": "Confirmed", "Form_Filled": "No", "Cancellation_Reason": ""
        }
        try:
            path = Path(APPOINTMENT_STATUS_FILE)
            df = pd.read_excel(path) if path.exists() else pd.DataFrame(columns=APPOINTMENT_STATUS_COLUMNS)
            pd.concat([df, pd.DataFrame([status_data])]).to_excel(path, index=False)
        except Exception as e:
            print(f"Error writing to {APPOINTMENT_STATUS_FILE}: {e}")

        _send_twilio_confirmation_sms(patient_record.get("Phone"), slot)
        return {"confirmation_status": "appointment_confirmed", "patient_record": patient_record}

    elif decision == "CANCEL":
        _revert_doctor_schedule(state)
        if state.get("status") == "new": _remove_new_patient_record(patient_record)
        _send_twilio_cancellation_sms(patient_record.get("Phone"))
        return {"confirmation_status": "appointment_cancelled", "patient_record": patient_record}

    return {"confirmation_status": "invalid_decision", "patient_record": patient_record}
