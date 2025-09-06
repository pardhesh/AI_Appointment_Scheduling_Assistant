import pandas as pd
from datetime import datetime
from typing import Dict

SCHEDULE_FILE = "data/doctor_schedule.xlsx"  # adjust path


def _validate_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        raise ValueError("Invalid date format. Use DD-MM-YYYY.")


def _find_consecutive_slots(slots):
    for i in range(len(slots) - 1):
        t1, s1 = slots[i]
        t2, s2 = slots[i + 1]
        if s1.lower() == "available" and s2.lower() == "available":
            # Check both in same session (morning or afternoon)
            if (("10" in t1 or "11" in t1) and ("10" in t2 or "11" in t2)) or \
               (("2" in t1 or "3" in t1 or "4" in t1 or "5" in t1) and ("2" in t2 or "3" in t2 or "4" in t2 or "5" in t2)):
                return [i, i + 1]
    return None


def schedule_appointment(state: Dict, preferred_date: str) -> Dict:
    doctor = state.get("extracted_info", {}).get("doctor")
    patient_name = state.get("extracted_info", {}).get("name")
    location = state.get("extracted_info", {}).get("location")
    status = state.get("status")

    try:
        dt = _validate_date(preferred_date)
    except ValueError as e:
        state["scheduled_slot"] = {"status": "error", "message": str(e)}
        return state

    df = pd.read_excel(SCHEDULE_FILE)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Map aliases
    col_map = {
        "doctor": ["doctor", "doctor name", "dr"],
        "date": ["date"],
        "time": ["time", "time slot", "slot"],
        "status": ["status", "availability"]
    }

    resolved = {}
    for key, aliases in col_map.items():
        for alias in aliases:
            if alias in df.columns:
                resolved[key] = alias
                break

    missing = [k for k in col_map if k not in resolved]
    if missing:
        state["scheduled_slot"] = {
            "status": "error",
            "message": f"Schedule file missing columns: {missing}. Found: {list(df.columns)}"
        }
        return state

    # Parse dates
    df[resolved["date"]] = pd.to_datetime(df[resolved["date"]], errors="coerce")

    # Filter doctor + date
    date_match = df[
        (df[resolved["doctor"]].str.lower() == doctor.lower())
        & (df[resolved["date"]].dt.date == dt.date())
    ]

    if date_match.empty:
        state["scheduled_slot"] = {
            "status": "error",
            "message": f"{doctor} not available on {preferred_date}."
        }
        return state

    # Returning patient
    if status == "returning":
        available = date_match[date_match[resolved["status"]].str.lower() == "available"]
        if not available.empty:
            idx = available.index[0]
            df.at[idx, resolved["status"]] = f"Booked by {patient_name}"
            slot_time = date_match.loc[idx, resolved["time"]]
            df.to_excel(SCHEDULE_FILE, index=False)
            state["scheduled_slot"] = {
                "doctor": doctor,
                "date": preferred_date,
                "time": slot_time,
                "location": location,
                "status": "confirmed"
            }
            return state
        else:
            state["scheduled_slot"] = {
                "status": "unavailable",
                "message": f"No slots available for {doctor} on {preferred_date}."
            }
            return state

    # New patient
    if status == "new":
        slots = list(zip(date_match[resolved["time"]], date_match[resolved["status"]]))
        indices = _find_consecutive_slots(slots)
        if indices:
            i1, i2 = indices
            idx1 = date_match.index[i1]
            idx2 = date_match.index[i2]
            df.at[idx1, resolved["status"]] = f"Booked by {patient_name}"
            df.at[idx2, resolved["status"]] = f"Booked by {patient_name}"
            slot_time = f"{date_match.loc[idx1, resolved['time']]} & {date_match.loc[idx2, resolved['time']]}"
            df.to_excel(SCHEDULE_FILE, index=False)
            state["scheduled_slot"] = {
                "doctor": doctor,
                "date": preferred_date,
                "time": slot_time,
                "location": location,
                "status": "confirmed"
            }
            return state
        else:
            state["scheduled_slot"] = {
                "status": "unavailable",
                "message": f"No 1 hour slots available for {doctor} on {preferred_date}."
            }
            return state

    state["scheduled_slot"] = {"status": "error", "message": "Unknown patient status"}
    return state
