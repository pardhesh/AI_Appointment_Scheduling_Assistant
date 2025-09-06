# src/agents/insurance_agent.py

"""
InsuranceAgent
Collects insurance details for new patients.
"""

def insurance_agent() -> dict:
    """
    Simulate collecting insurance details.
    In Streamlit → replace with form inputs.
    """
    # For now, just input() simulation (CLI)
    carrier = input("Enter Insurance Carrier: ")
    member_id = input("Enter Member ID: ")
    group_num = input("Enter Group Number: ")

    return {
        "insurance_carrier": carrier.strip(),
        "member_id": member_id.strip(),
        "group_number": group_num.strip()
    }
