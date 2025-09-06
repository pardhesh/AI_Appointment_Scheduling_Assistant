"""
FormAgent
-----------------
- Sends the new patient intake form as a PDF attachment via email.
- Uses Twilio SendGrid for sending emails.
- Securely loads credentials from a .env file.
"""

import os
import base64
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition
)

# --- Load Environment Variables for SendGrid ---
load_dotenv()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL") # The email address you verified with SendGrid

# --- File Path for the Intake Form ---
FORM_PDF_PATH = "data/New_Patient_Intake_Form.pdf"


def form_agent(state: Dict) -> Dict:
    """
    Main entry point for the form distribution agent.
    
    If the appointment was confirmed, this agent sends an email with the
    patient intake form as a PDF attachment.
    """
    # 1. Check if the appointment was actually confirmed in the previous step
    if state.get("confirmation_status") != "appointment_confirmed":
        return {"form_sent_status": "skipped_not_confirmed"}

    # 2. Verify that we have the necessary credentials and patient info
    if not SENDGRID_API_KEY or not SENDER_EMAIL:
        print("--- WARNING: SendGrid API Key or Sender Email not found. Email will be simulated. ---")
        return {"form_sent_status": "simulated_missing_credentials"}
        
    patient_record = state.get("patient_record", {})
    recipient_email = patient_record.get("Email")
    patient_name = patient_record.get("Name", "Valued Patient")

    if not recipient_email:
        return {"form_sent_status": "error_no_email_found"}

    # 3. Prepare the email content
    subject = "Your New Patient Intake Form"
    html_content = (
        f"Dear {patient_name},<br><br>"
        "Thank you for scheduling your appointment with us. Please find the New Patient Intake Form attached to this email.<br><br>"
        "To help us prepare for your visit, please complete this form and either email it back to us or bring a printed copy to your appointment.<br><br>"
        "We look forward to seeing you soon.<br><br>"
        "Sincerely,<br>"
        "The Scheduling Team"
    )
    
    # 4. Prepare the PDF attachment
    try:
        form_path = Path(FORM_PDF_PATH)
        with open(form_path, 'rb') as f:
            pdf_data = f.read()
        
        # Encode the PDF data in base64
        encoded_file = base64.b64encode(pdf_data).decode()
        
        attachment = Attachment(
            FileContent(encoded_file),
            FileName(form_path.name),
            FileType('application/pdf'),
            Disposition('attachment')
        )
    except FileNotFoundError:
        print(f"--- ERROR: Intake form not found at {FORM_PDF_PATH} ---")
        return {"form_sent_status": f"error_pdf_not_found_at_{FORM_PDF_PATH}"}
    except Exception as e:
        print(f"--- ERROR: Could not read or encode the PDF file. Details: {e} ---")
        return {"form_sent_status": f"error_processing_pdf:_{e}"}

    # 5. Create the SendGrid mail object and send the email
    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=recipient_email,
        subject=subject,
        html_content=html_content
    )
    message.attachment = attachment

    try:
        sendgrid_client = SendGridAPIClient(SENDGRID_API_KEY)
        response = sendgrid_client.send(message)
        
        # Check the response status code to confirm it was sent
        if 200 <= response.status_code < 300:
            print(f"\n--- Intake form successfully sent to {recipient_email} (Status: {response.status_code}) ---\n")
            return {"form_sent_status": "sent_successfully"}
        else:
            print(f"\n--- ERROR: Failed to send email via SendGrid. Status: {response.status_code}, Body: {response.body} ---\n")
            return {"form_sent_status": f"error_sendgrid_api_{response.status_code}"}
            
    except Exception as e:
        print(f"\n--- ERROR: An exception occurred while sending the email. Details: {e} ---\n")
        return {"form_sent_status": f"error_exception_{e}"}
