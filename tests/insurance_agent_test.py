import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# tests/insurance_agent_test.py

from src.agents.insurance_agent import insurance_agent

if __name__ == "__main__":
    print("Simulating new patient insurance form...")
    details = insurance_agent()
    print("Collected Insurance Details:", details)
