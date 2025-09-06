from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from dotenv import load_dotenv 
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API")
from typing import Optional
from pydantic import BaseModel, Field

class PatientInfo(BaseModel):
    name: Optional[str] = Field(description="Patient's full name")
    dob: Optional[str] = Field(description="Date of Birth in DD-MM-YYYY format")
    doctor: Optional[str] = Field(description="Doctor's full name")
    location: Optional[str] = Field(description="City or location name")


from datetime import datetime

def normalize_output(data: dict) -> dict:
    # Normalize DOB formats
    if data.get("dob"):
        token = data["dob"].replace("/", "-")
        for fmt in ["%d-%m-%Y", "%Y-%m-%d", "%d-%m-%y"]:
            try:
                dt = datetime.strptime(token, fmt)
                if dt.year < 100:  # fix 2-digit years
                    dt = dt.replace(year=dt.year + 1900)
                data["dob"] = dt.strftime("%d-%m-%Y")
                break
            except:
                continue
    
    # Normalize "null" strings → None
    for k, v in data.items():
        if isinstance(v, str) and v.strip().lower() in {"null", "none", ""}:
            data[k] = None
    
    return data



def parse_patient_info(text: str) -> dict:
    chain = prompt | llm | parser
    try:
        result = chain.invoke({"text": text})
        return normalize_output(result.dict())
    except Exception as e:
        return {"error": str(e), "raw_text": text}

parser = PydanticOutputParser(pydantic_object=PatientInfo)

template = """
You are an information extraction system.

Extract the patient's information from the input text.

Return output ONLY in JSON format, with NO code, NO markdown, NO explanation.
Strictly follow this schema:
{format_instructions}

When there is related information matching in the text note the value for that column as "None".
Input:
{text}
"""

prompt = PromptTemplate(
    template=template,
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, groq_api_key=GROQ_API_KEY)
