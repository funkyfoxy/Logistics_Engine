import os
import pdfplumber
import json
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load the secret vault
load_dotenv()

# 2. Initialize the AI Brain using the vault key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 3. The Core Extraction Engine
def extract_data_from_pdf(pdf_path, target_fields):
    extracted_text = ""
    
    # ARMOR: Catch broken PDFs
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
    except Exception as e:
        print(f"PDF Read Error: {e}")
        return {"error": "Failed to read PDF file."}, "N/A"

    # TRUNCATION MOAT: Restrict text to roughly the first 3-4 pages to protect your wallet
    if len(extracted_text) > 15000:
        extracted_text = extracted_text[:15000] + "\n...[Text truncated for length safety]..."
    
    # Format the dynamic fields clearly into the instructions for the AI
    fields_list_str = "\n".join([f"- {field}" for field in target_fields])
    
    # Step B: Strict System Prompt (Now Dynamic)
    prompt = f"""
    You are a highly precise logistics data extractor. Analyze the following invoice text and extract these exact fields:
    {fields_list_str}
    
    Return the exact data as a raw JSON dictionary where the keys are the exact field names requested above.
    If a field is missing from the text, return "N/A" for that key.
    
    Invoice Text:
    {extracted_text}
    """
    
    # Step C: The AI Call with JSON Lock
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={ "type": "json_object" } # Forces strict JSON
        )
        
        raw_json = response.choices[0].message.content
        
        # Parse the JSON and return it along with the raw text for preview
        return json.loads(raw_json), extracted_text
        
    except json.JSONDecodeError:
        # ARMOR: Dynamic Fallback if the AI hallucinates
        fallback_data = {field: "PARSE_ERROR" for field in target_fields}
        return fallback_data, extracted_text
        
    except Exception as e:
        # NEW LINE: This prints the exact rejection reason to your cloud terminal
        print(f"🚨 OPENAI REJECTION REASON: {str(e)}")

        # ARMOR: Dynamic Fallback if the API crashes
        fallback_data = {field: "API_ERROR" for field in target_fields}
        return fallback_data, extracted_text