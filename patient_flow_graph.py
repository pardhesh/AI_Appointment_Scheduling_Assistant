"""
LangGraph with Step 6: Final FormAgent integration.
This represents the complete backend logic for the scheduling AI.
"""

from langgraph.graph import StateGraph, END

# --- Import all agent functions ---
from src.agents.patient_info_agent import parse_patient_info
from src.agents.patient_lookup_agent import patient_lookup_agent
from src.agents.insurance_agent_for_graph import insurance_agent
from src.agents.appointment_scheduler_agent import schedule_appointment
from src.agents.confirmation_agent_for_graph import confirmation_agent
from src.agents.form_agent import form_agent

# ---- State Definition ----
from typing import TypedDict, Optional

class State(TypedDict):
    raw_text: str
    extracted_info: Optional[dict]
    lookup_result: Optional[dict]
    status: Optional[str]
    insurance_carrier: Optional[str]
    member_id: Optional[str]
    group_number: Optional[str]
    scheduled_slot: Optional[dict]
    confirmation_status: Optional[str]
    patient_record: Optional[dict]
    # New field for the form agent
    form_sent_status: Optional[str]
    error: Optional[str]


# ---- Agent Nodes ----

def patient_info_node(state: State) -> dict:
    """Node that calls the PatientInfoAgent to extract information."""
    print("---NODE: PATIENT INFO---")
    raw_text = state.get('raw_text', '')
    extracted_data = parse_patient_info(raw_text)
    if "error" in extracted_data:
        return {"error": "Failed to parse patient information."}
    return {"extracted_info": extracted_data}


def patient_lookup_node(state: State) -> dict:
    """Node that calls the PatientLookupAgent to check for an existing record."""
    print("---NODE: PATIENT LOOKUP---")
    info = state.get("extracted_info")
    if not info:
        return {"error": "Cannot perform lookup, patient info not extracted."}
    lookup_result = patient_lookup_agent(info)
    return {"lookup_result": lookup_result, "status": lookup_result.get("status")}


def insurance_node(state: State) -> dict:
    """Node that calls the InsuranceAgent to collect details for new patients."""
    print("---NODE: COLLECTING INSURANCE---")
    insurance_details = insurance_agent()
    return insurance_details


def appointment_scheduler_node(state: State) -> dict:
    """Node that calls the AppointmentSchedulerAgent to book a slot."""
    print("---NODE: SCHEDULING APPOINTMENT---")
    preferred_date = input("Enter preferred date for appointment (DD-MM-YYYY): ")
    updated_state = schedule_appointment(dict(state), preferred_date)
    return {"scheduled_slot": updated_state.get("scheduled_slot")}


def confirmation_node(state: State) -> dict:
    """Node that calls the ConfirmationAgent to handle final booking and SMS."""
    print("---NODE: CONFIRMATION---")
    confirmation_update = confirmation_agent(dict(state))
    return confirmation_update


def form_node(state: State) -> dict:
    """Node that calls the FormAgent to email the intake form if needed."""
    print("---NODE: FORM DISTRIBUTION---")
    form_update = form_agent(dict(state))
    return form_update


# ---- Conditional Routing Logic ----

def route_after_lookup(state: State) -> str:
    """Decides the next step after the patient lookup."""
    print("---ROUTING---")
    status = state.get("status")
    if status == "new":
        return "InsuranceAgent"
    elif status == "returning":
        return "AppointmentSchedulerAgent"
    else:
        return "END"

# ---- Graph Builder ----
def build_graph():
    graph = StateGraph(State)

    # Add all nodes to the graph
    graph.add_node("PatientInfoAgent", patient_info_node)
    graph.add_node("PatientLookupAgent", patient_lookup_node)
    graph.add_node("InsuranceAgent", insurance_node)
    graph.add_node("AppointmentSchedulerAgent", appointment_scheduler_node)
    graph.add_node("ConfirmationAgent", confirmation_node)
    graph.add_node("FormAgent", form_node)

    # Define the workflow edges
    graph.set_entry_point("PatientInfoAgent")
    graph.add_edge("PatientInfoAgent", "PatientLookupAgent")
    graph.add_conditional_edges(
        "PatientLookupAgent",
        route_after_lookup,
        {
            "InsuranceAgent": "InsuranceAgent",
            "AppointmentSchedulerAgent": "AppointmentSchedulerAgent",
            "END": END
        }
    )
    graph.add_edge("InsuranceAgent", "AppointmentSchedulerAgent")
    graph.add_edge("AppointmentSchedulerAgent", "ConfirmationAgent")
    
    # After confirmation, the form agent is called
    graph.add_edge("ConfirmationAgent", "FormAgent")
    
    # The form agent is the new final step
    graph.add_edge("FormAgent", END)

    return graph.compile()


# ---- Demo run ----
if __name__ == "__main__":
    graph = build_graph()
    
    # Example for a NEW patient to test the complete flow
    initial_state = {
        "raw_text": "Hi, my name is Priya Sharma, DOB is 15-05-1995. I want to see Dr. Meena Iyer in Bangalore.",
    }

    final_state = graph.invoke(initial_state)
    print("\n---FINAL STATE---")
    print(final_state)

