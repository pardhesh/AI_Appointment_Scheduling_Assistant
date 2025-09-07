import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.agents.patient_info_agent import parse_patient_info

samples = [
    "Hi, I'm Ravi Varma, DOB 12/03/1990. I need appointment with Dr. Meena Iyer at Bengaluru clinic.",
    "This is Kishore Kumar K 1990-03-12 Dr. Arjun Reddy Bengaluru, IN",
    "Name: Anita Sharma, DOB: 5-7-1985, Doctor: Dr. Ravi Varma, Location: Bangalore",
    "I want to book with Dr. Meena, my name is Suresh Reddy and I'm born 01/01/1975",
    "No info here",
    "Hi. my name is pardhesh Maddala and i was born on 24/08/2005. i'm from bengaluru and i want to meet DR. Meera Iyer."
]

for s in samples:
    print("INPUT:", s)
    print("PARSED:", parse_patient_info(s))
    print("---")
