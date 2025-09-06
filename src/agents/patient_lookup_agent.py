"""
PatientLookupAgent
------------------
Classifies a patient as Returning vs New by looking up in a CSV "DB".
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import pandas as pd
import re
import string
from difflib import SequenceMatcher


# ---- column aliasing (case-insensitive) --------------------------------------
ALIASES = {
    "name": ["name", "patient_name", "full_name"],
    "dob": ["dob", "date_of_birth", "birthdate"],
    "location": ["location", "city"],
    "insurance_carrier": ["insurance_carrier", "carrier", "insurance"],
    "member_id": ["member_id", "memberid", "policy_number", "policy_no"],
    "group": ["group", "group_id", "group_number"],
}

def _find_col(df: pd.DataFrame, key: str) -> Optional[str]:
    lower_cols = {c.lower(): c for c in df.columns}
    for alias in ALIASES.get(key, []):
        if alias in lower_cols:
            return lower_cols[alias]
    return None


# ---- normalization helpers ---------------------------------------------------
PUNCT_TABLE = str.maketrans("", "", string.punctuation)

def normalize_name(name: str) -> str:
    if not name:
        return ""
    n = name.strip()
    # drop titles like dr, mr, mrs (prefix only)
    n = re.sub(r"^\b(dr|mr|mrs|ms)\.?\s+", "", n, flags=re.IGNORECASE)
    # remove punctuation/dots in initials
    n = n.translate(PUNCT_TABLE)
    # collapse whitespace
    n = re.sub(r"\s+", " ", n)
    return n.strip().lower()

def token_sort_key(name: str) -> str:
    toks = normalize_name(name).split()
    toks_sorted = sorted(toks)
    return " ".join(toks_sorted)

def name_similarity(a: str, b: str) -> float:
    ta = token_sort_key(a)
    tb = token_sort_key(b)
    return SequenceMatcher(None, ta, tb).ratio()

def _parse_dob_any(dob: str) -> Optional[datetime]:
    if not dob or not str(dob).strip():
        return None
    s = str(dob).strip().replace("/", "-")
    fmts = ["%d-%m-%Y", "%Y-%m-%d", "%d-%m-%y"]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.year < 100:
                year = dt.year + (1900 if dt.year >= 20 else 2000)
                dt = dt.replace(year=year)
            return dt
        except Exception:
            continue
    return None

def _dob_equal(a: str, b: str) -> bool:
    da = _parse_dob_any(a)
    db = _parse_dob_any(b)
    if not da or not db:
        return False
    return da.date() == db.date()

def _dob_to_str(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y")


# ---- core API ----------------------------------------------------------------
def lookup_patient(csv_path: str | Path, name: Optional[str], dob: Optional[str],
                   location: Optional[str] = None, fuzzy_threshold: float = 0.87) -> Dict[str, object]:
    """
    Lookup patient in CSV by Name+DOB. Returns status and matched record (if any).
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        return {"status": "new", "reason": f"CSV not found at {csv_path}",
                "match_score": None, "patient": None, "duplicates": 0}

    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(csv_path)

    # resolve columns
    col_name = _find_col(df, "name")
    col_dob = _find_col(df, "dob")
    col_loc = _find_col(df, "location")
    col_carrier = _find_col(df, "insurance_carrier")
    col_member = _find_col(df, "member_id")
    col_group = _find_col(df, "group")

    if not col_name or not col_dob:
        return {"status": "new", "reason": "CSV missing required columns for name/dob",
                "match_score": None, "patient": None, "duplicates": 0}

    name_in = normalize_name(name or "")
    dob_in = dob or ""
    if not name_in or not _parse_dob_any(dob_in):
        return {"status": "new", "reason": "Insufficient info for lookup (need name + valid dob)",
                "match_score": None, "patient": None, "duplicates": 0}

    # 1) Exact match
    matches_exact: List[Tuple[int, float]] = []
    for idx, row in df.iterrows():
        if _dob_equal(dob_in, row[col_dob]) and normalize_name(row[col_name]) == name_in:
            matches_exact.append((idx, 1.0))

    if matches_exact:
        idx, score = matches_exact[0]
        dup_count = len(matches_exact) - 1
        row = df.loc[idx]
        return {
            "status": "returning",
            "match_score": score,
            "patient": {
                "name": str(row[col_name]),
                "dob": _dob_to_str(_parse_dob_any(str(row[col_dob]))),
                "location": (str(row[col_loc]) if col_loc else None),
                "insurance_carrier": (str(row[col_carrier]) if col_carrier else None),
                "member_id": (str(row[col_member]) if col_member else None),
                "group": (str(row[col_group]) if col_group else None),
            },
            "duplicates": dup_count,
            "reason": "Exact name+dob match."
        }

    # 2) Fuzzy name + exact dob
    best_idx = None
    best_score = 0.0
    for idx, row in df.iterrows():
        if _dob_equal(dob_in, row[col_dob]):
            score = name_similarity(name_in, str(row[col_name]))
            if score > best_score:
                best_score = score
                best_idx = idx

    if best_idx is not None and best_score >= fuzzy_threshold:
        row = df.loc[best_idx]
        return {
            "status": "returning",
            "match_score": round(best_score, 3),
            "patient": {
                "name": str(row[col_name]),
                "dob": _dob_to_str(_parse_dob_any(str(row[col_dob]))),
                "location": (str(row[col_loc]) if col_loc else None),
                "insurance_carrier": (str(row[col_carrier]) if col_carrier else None),
                "member_id": (str(row[col_member]) if col_member else None),
                "group": (str(row[col_group]) if col_group else None),
            },
            "duplicates": 0,
            "reason": "Fuzzy name match with exact dob."
        }

    # New patient
    return {"status": "new", "reason": "No match found for name+dob",
            "match_score": None, "patient": None, "duplicates": 0}


# ---- Wrapper for LangGraph ---------------------------------------------------
DEFAULT_CSV = "data/synthetic_patients.csv"

def patient_lookup_agent(extracted_info: dict) -> dict:
    """
    Wrapper to integrate with LangGraph.
    Expects extracted_info = {"name": ..., "dob": ..., "location": ...}
    """
    return lookup_patient(
        csv_path=DEFAULT_CSV,
        name=extracted_info.get("name"),
        dob=extracted_info.get("dob"),
        location=extracted_info.get("location")
    )
