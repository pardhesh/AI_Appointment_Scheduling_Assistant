# src/agents/generate_reply_agent.py

"""
GenerateReplyAgent
------------------
Uses Groq LLM to rephrase static assistant responses into more natural,
varied conversational text. The data placeholders must be preserved exactly.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

# --- Load Env ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API")

# --- Initialize LLM ---
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7, groq_api_key=GROQ_API_KEY)

# --- Prompt Template ---
prompt_template = PromptTemplate(
    input_variables=["text"],
    template=(
        "You are a friendly medical scheduling assistant.\n\n"
        "Rephrase the following response to sound natural, warm, and slightly varied each time.\n"
        "Only rephrase the surrounding words, keep all placeholders intact.\n\n"
        "The meaning of the response generated should always be same of what recieved."
        "Keep the vocabulary to simple."
        "Response:\n{text}"
    ),
)

def generate_reply(text: str) -> str:
    """
    Generate a rephrased response while keeping placeholders intact.
    Falls back to original text if Groq API fails.
    """
    try:
        chain = prompt_template | llm
        result = chain.invoke({"text": text})
        return result.content.strip()
    except Exception as e:
        print(f"[GenerateReplyAgent Error] {e}")
        return text
