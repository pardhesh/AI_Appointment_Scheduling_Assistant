"""
Streamlit Web Interface for the AI Scheduling Assistant
-------------------------------------------------------
This script creates an interactive chat interface that connects to the
backend agentic workflow defined in `patient_flow_graph.py`.

To Run:
1. Make sure all dependencies are installed (`pip install -r requirements.txt`).
2. Place this file in the root directory of your project.
3. Run from the terminal: `streamlit run app.py`
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# --- Import Agent Functions ---
import sys
sys.path.append('src')

from src.agents.patient_info_agent import parse_patient_info
from src.agents.patient_lookup_agent import patient_lookup_agent
from src.agents.appointment_scheduler_agent import schedule_appointment
from src.agents.confirmation_agent import confirmation_agent
from src.agents.form_agent import form_agent
from src.agents.insurance_agent import insurance_agent
from src.agents.generate_reply_agent import generate_reply

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Scheduling Assistant",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Helper Functions ---
@st.cache_data
def get_available_doctors():
    """Reads the doctor schedule to get a unique list of available doctors."""
    schedule_path = Path("data/doctor_schedule.xlsx")
    if not schedule_path.exists():
        return ["Dr. Arjun Reddy", "Dr. Meena Iyer", "Dr. Ravi Varma"]  # Fallback
    try:
        df = pd.read_excel(schedule_path)
        doctor_col = next((col for col in df.columns if col.strip().lower() in ["doctor name", "doctor", "dr"]), None)
        if doctor_col:
            return df[doctor_col].unique().tolist()
        return ["Dr. Arjun Reddy", "Dr. Meena Iyer", "Dr. Ravi Varma"]
    except Exception:
        return ["Dr. Arjun Reddy", "Dr. Meena Iyer", "Dr. Ravi Varma"]

# --- Session State Initialization ---
def initialize_session_state():
    if "stage" not in st.session_state:
        st.session_state.stage = "GREETING"
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hey there! I'm Cura. Say the word, and I'll get your health check lined up. 🩺"}]
    if "agent_state" not in st.session_state:
        st.session_state.agent_state = {}
    if "temp_email" not in st.session_state:
        st.session_state.temp_email = None
    if "temp_phone" not in st.session_state:
        st.session_state.temp_phone = None

initialize_session_state()

# --- Main App UI ---
st.title("CURA AI 🩺")
st.write("Your personal assistant for booking appointments hassle-free.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Main Interactive Logic ---
if prompt := st.chat_input("Your response..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- GREETING STAGE ---
    if st.session_state.stage == "GREETING":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                doctors = get_available_doctors()
                doctor_list_md = "- " + "\n- ".join(doctors)
                response = (
                    "Let me help you out! I'm here to help you book a medical appointment.\n\n"
                    f"Our available doctors are:\n{doctor_list_md}\n\n"
                    "To get started, could you please provide your **full name, date of birth (DD-MM-YYYY), preferred doctor, and city**?"
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.stage = "COLLECTING_INFO"

    # --- COLLECTING INFO STAGE ---
    elif st.session_state.stage == "COLLECTING_INFO":
        with st.chat_message("assistant"):
            with st.spinner("Checking our records..."):
                st.session_state.agent_state['raw_text'] = prompt
                info = parse_patient_info(prompt)
                st.session_state.agent_state['extracted_info'] = info

                lookup = patient_lookup_agent(info)
                st.session_state.agent_state['lookup_result'] = lookup
                st.session_state.agent_state['status'] = lookup.get('status')

                if lookup.get('status') == 'new':
                    response = (
                        f"Thank you, {info.get('name', 'patient')}. It looks like you're a new patient.\n\n"
                        "To proceed, let’s collect your insurance details step by step.\n\n"
                        "First, could you please provide your **Insurance Carrier**?"
                    )
                    st.session_state.stage = "COLLECTING_INSURANCE_CARRIER"
                else:
                    patient_name = lookup.get('patient', {}).get('name', info.get('name'))
                    response = (
                        f"Welcome back, {patient_name}! It's great to see you again.\n\n"
                        "What date (DD-MM-YYYY) would you like to book your appointment for?"
                    )
                    st.session_state.stage = "COLLECTING_DATE"

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # --- COLLECTING INSURANCE STAGES (New Patients) ---
    elif st.session_state.stage == "COLLECTING_INSURANCE_CARRIER":
        with st.chat_message("assistant"):
            st.session_state.agent_state['insurance_carrier'] = prompt.strip()
            response = "Thanks! Now, could you please provide your **Member ID**?"
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.stage = "COLLECTING_INSURANCE_MEMBER_ID"

    elif st.session_state.stage == "COLLECTING_INSURANCE_MEMBER_ID":
        with st.chat_message("assistant"):
            st.session_state.agent_state['member_id'] = prompt.strip()
            response = "Great! Finally, could you provide your **Group Number**?"
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.stage = "COLLECTING_INSURANCE_GROUP_NUMBER"

    elif st.session_state.stage == "COLLECTING_INSURANCE_GROUP_NUMBER":
        with st.chat_message("assistant"):
            st.session_state.agent_state['group_number'] = prompt.strip()

            # Call insurance_agent here
            insurance_details = insurance_agent(
                st.session_state.agent_state['insurance_carrier'],
                st.session_state.agent_state['member_id'],
                st.session_state.agent_state['group_number']
            )
            st.session_state.agent_state.update(insurance_details)

            response = "Thank you! Now, what date (DD-MM-YYYY) would you like to book your appointment for?"
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.stage = "COLLECTING_DATE"

    # --- COLLECTING DATE STAGE ---
    elif st.session_state.stage == "COLLECTING_DATE":
        with st.chat_message("assistant"):
            with st.spinner("Checking available slots..."):
                result_state = schedule_appointment(st.session_state.agent_state, prompt)
                slot = result_state.get('scheduled_slot', {})
                st.session_state.agent_state['scheduled_slot'] = slot

                if slot.get('status') == 'confirmed':
                    response = (
                        f"Great! I've provisionally booked you a slot with **{slot['doctor']}** "
                        f"on **{slot['date']}** at **{slot['time']}**.\n\n"
                        "To finalize, please provide your **email address**."
                    )
                    st.session_state.stage = "COLLECTING_EMAIL"
                else:
                    response = "I'm sorry, but it looks like there are no available slots on that day. \nPlease try another date (DD-MM-YYYY)."

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # --- COLLECTING EMAIL STAGE ---
    elif st.session_state.stage == "COLLECTING_EMAIL":
        with st.chat_message("assistant"):
            st.session_state.temp_email = prompt.strip()
            response = "Thanks! Now, could you please provide your **phone number**?"
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.stage = "COLLECTING_PHONE"

    # --- COLLECTING PHONE STAGE ---
    elif st.session_state.stage == "COLLECTING_PHONE":
        with st.chat_message("assistant"):
            st.session_state.temp_phone = prompt.strip()
            response = "Almost done! Please type **CONFIRM** to confirm your appointment or **CANCEL** to cancel it."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.stage = "COLLECTING_DECISION"

    # --- COLLECTING DECISION STAGE ---
    elif st.session_state.stage == "COLLECTING_DECISION":
        with st.chat_message("assistant"):
            decision = prompt.strip().upper()
            if decision not in ["CONFIRM", "CANCEL"]:
                response = "❌ Invalid input. Please type **CONFIRM** or **CANCEL**."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                # Call confirmation_agent with collected values
                st.session_state.agent_state = confirmation_agent(
                    st.session_state.agent_state,
                    email=st.session_state.temp_email,
                    phone=st.session_state.temp_phone,
                    decision=decision
                )

                if decision == "CONFIRM":
                    st.session_state.agent_state = form_agent(st.session_state.agent_state)
                    response = (
                        
                        "✅ Thank you! Your appointment is confirmed. "
                        "You will receive an SMS and an email with the intake form shortly. "
                        "You will be reminded when the appointment date is getting near. No need to worry."
                        "Don't have a good day. Have a great day!"
                    )
                else:
                    response = (
                        
                        "❌ Your appointment has been cancelled. "
                        "If you'd like to rebook, just start over!")
                    

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.stage = "DONE"

    # --- DONE STAGE ---
    else:
        with st.chat_message("assistant"):
            response = "I'm ready to help with a new booking. Just let me know!"
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.stage = "GREETING"
            st.session_state.agent_state = {}
            st.session_state.temp_email = None
            st.session_state.temp_phone = None

# --- Sidebar with Progress Steps ---
with st.sidebar:
    # Progress Header
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <span style="font-size: 20px; margin-right: 8px;">📋</span>
        <h2 style="margin: 0; color: white;">Progress</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Define progress steps
    progress_steps = [
        " Patient Info",
        " Patient Lookup", 
        " Scheduling",
        " Insurance",
        " Confirmation",
        " Send Confirmation"
    ]
    
    # Determine current step based on stage
    def get_current_step():
        stage = st.session_state.stage
        if stage == "GREETING":
            return 0
        elif stage == "COLLECTING_INFO":
            return 0
        elif stage in ["COLLECTING_INSURANCE_CARRIER", "COLLECTING_INSURANCE_MEMBER_ID", "COLLECTING_INSURANCE_GROUP_NUMBER"]:
            return 3
        elif stage == "COLLECTING_DATE":
            return 2
        elif stage in ["COLLECTING_EMAIL", "COLLECTING_PHONE", "COLLECTING_DECISION"]:
            return 4
        elif stage == "DONE":
            return 5
        else:
            return 1
    
    current_step = get_current_step()
    
    # Display progress steps
    for i, step in enumerate(progress_steps):
        if i == current_step:
            # Active step styling
            st.markdown(f"""
            <div style="background-color: #1f4e79; padding: 8px 12px; border-radius: 6px; margin-bottom: 4px;">
                <span style="color: white; font-weight: 500;">{step}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Inactive step styling
            st.markdown(f"""
            <div style="padding: 8px 12px; margin-bottom: 4px;">
                <span style="color: #9ca3af;">{step}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Enhanced booking details section
    if st.session_state.agent_state:
        st.markdown("### 📋 Booking Details")
        
        info = st.session_state.agent_state.get('extracted_info', {})
        if info.get('name'):
            st.markdown(f"**👤 Patient:** {info.get('name', '...')}")
        if info.get('dob'):
            st.markdown(f"**📅 DOB:** {info.get('dob', '...')}")
        if info.get('doctor'):
            st.markdown(f"**👨‍⚕️ Doctor:** {info.get('doctor', '...')}")

        status = st.session_state.agent_state.get('status')
        if status:
            color = '#3b82f6' if status == 'new' else '#10b981'
            st.markdown(f"**📊 Status:** <span style='color: {color}; font-weight: 500;'>{status.capitalize()}</span>", unsafe_allow_html=True)

        slot = st.session_state.agent_state.get('scheduled_slot', {})
        if slot.get('status') == 'confirmed':
            st.markdown("### ✅ Confirmed Slot")
            st.markdown(f"**📅 Date:** {slot['date']}")
            st.markdown(f"**🕐 Time:** {slot['time']}")
            st.markdown(f"**👨‍⚕️ Doctor:** {slot['doctor']}")

        if st.session_state.stage == "DONE":
            st.markdown("### 🎉 Process Completed!")
            st.success("Thank you for using CURAAI")

    else:
        st.markdown("### 📝 No Active Booking")
        st.info("Start a new booking to see progress here.")

    st.markdown("---")
    
    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.clear()
        st.rerun()
