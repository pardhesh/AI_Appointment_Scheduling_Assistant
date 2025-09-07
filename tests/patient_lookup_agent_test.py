import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import os
from pathlib import Path
from src.agents.patient_lookup_agent import lookup_patient

# Adjust this path to wherever your synthetic CSV lives
CSV_PATH = Path("C:/Users/pardh/Downloads/RAGAAI/data/synthetic_patients_final.csv")  # e.g., data/patients.csv

def show(result):
    print("STATUS:", result["status"])
    print("SCORE :", result["match_score"])
    print("REASON:", result["reason"])
    print("PATIENT:", result["patient"])
    print("DUPLICATES:", result["duplicates"])
    print("---")

def main():
    print("== Returning (exact) ==")
    r1 = lookup_patient(CSV_PATH, "Kishore Kumar K", "1990-03-12")
    show(r1)

    print("== Returning (fuzzy) ==")
    r2 = lookup_patient(CSV_PATH, "Kishore Kumar", "12-03-1990")  # slight misspelling
    show(r2)

    print("== New Patient ==")
    r3 = lookup_patient(CSV_PATH, "Random Person", "01-01-1980")
    show(r3)

    print("== Insufficient Info (missing dob) ==")
    r4 = lookup_patient(CSV_PATH, "Ravi Varma", None)
    show(r4)

if __name__ == "__main__":
    if not CSV_PATH.exists():
        print(f"CSV file not found at {CSV_PATH}. Please set CSV_PATH to your synthetic patients.csv.")
    else:
        main()
