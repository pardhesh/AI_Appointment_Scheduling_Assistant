# src/agents/insurance_agent.py

"""
InsuranceAgent
Collects insurance details for new patients.
"""

def insurance_agent(carrier: str, member_id: str, group_num: str) -> dict:
    """
    Collect insurance details (Streamlit-friendly version).
    Args:
        carrier: Insurance Carrier (string)
        member_id: Insurance Member ID (string)
        group_num: Insurance Group Number (string)
    Returns:
        dict with normalized insurance info
    """
    return {
        "insurance_carrier": carrier.strip(),
        "member_id": member_id.strip(),
        "group_number": group_num.strip()
    }
