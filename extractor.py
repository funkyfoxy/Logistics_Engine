import os
import pdfplumber
import json
import csv
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load the secret vault
load_dotenv()

# 2. Initialize the AI Brain using the vault key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 3. The Core Extraction Engine
def extract_data_from_pdf(pdf_path):
    # Step A: Read the PDF text
    extracted_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
    
    # Step B: Give the AI strict instructions
    prompt = f"""
    You are a highly precise logistics data extractor. Analyze the following invoice text and extract these exact fields:
    - invoice_number
    - destination
    - cargo_weight
    - total_amount_due
    
    Return the exact data as a raw JSON dictionary. Do NOT include markdown formatting or backticks.
    
    Invoice Text:
    {extracted_text}
    """
    
    # Step C: Send the text to the AI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    # Step D: Return the raw JSON back to the app
    return response.choices[0].message.content