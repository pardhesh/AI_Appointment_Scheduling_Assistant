import pandas as pd
import random

# Load the existing CSV
df = pd.read_csv("C:/Users/pardh/Downloads/RAGAAI/data/synthetic_patients.csv")

# Function to generate an email from the name
def generate_email(name):
    clean_name = name.lower().replace(" ", ".").replace("..", ".")
    domain = "gmail.com"
    return f"{clean_name}@{domain}"

# Function to generate Indian-style phone number (+91)
def generate_phone():
    return f"{random.randint(6000000000, 9999999999)}"

# Add email and phone columns
df["Email"] = df["Name"].apply(generate_email)
df["Phone"] = [generate_phone() for _ in range(len(df))]

# Save updated CSV
df.to_csv("synthetic_patients_final.csv", index=False)

print("✅ Extended CSV saved as synthetic_patients_final.csv")
