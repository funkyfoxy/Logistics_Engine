import streamlit as st
import pdfplumber
import json
import os
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI
from extractor import extract_data_from_pdf

# Load the secret vault
load_dotenv()

# Initialize the AI Brain using the vault key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure the web page
st.set_page_config(page_title="Logistics Engine", page_icon="📦")

# Initialize the Database
def init_db():
    # This creates the physical file if it doesn't exist
    conn = sqlite3.connect('logistics_ledger.db')
    c = conn.cursor()
    
    # This builds the rigid columns for our data
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            destination TEXT,
            cargo_weight TEXT,
            total_amount_due TEXT,
            source_file TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Run the initialization every time the app boots
init_db()

# Inject data into the permanent SQL ledger
def save_invoice_to_db(invoice_data, filename):
    conn = sqlite3.connect('logistics_ledger.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO invoices (invoice_number, destination, cargo_weight, total_amount_due, source_file)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        invoice_data.get('invoice_number', 'N/A'),
        invoice_data.get('destination', 'N/A'),
        invoice_data.get('cargo_weight', 'N/A'),
        invoice_data.get('total_amount_due', 'N/A'),
        filename
    ))
    
    conn.commit()
    conn.close()

# Fetch all saved data from the permanent ledger
def get_all_invoices():
    conn = sqlite3.connect('logistics_ledger.db')
    c = conn.cursor()
    # SQL Command to select specific columns from our table
    c.execute('SELECT invoice_number, destination, cargo_weight, total_amount_due, source_file FROM invoices')
    rows = c.fetchall()
    conn.close()
    return rows

st.title("📦 AI Logistics Dashboard")
st.write("Upload your freight invoices below. The AI will extract the data and build your spreadsheet instantly.")

# 2. The Visual Drop Zone
# This creates a drag-and-drop box that accepts multiple PDFs
uploaded_files = st.file_uploader("Drop PDF Invoices Here", type="pdf", accept_multiple_files=True)

# 3. The Execution Button
if st.button("Process Invoices"):
        all_extracted_data = []

        for uploaded_file in uploaded_files:
            # 1. Save the uploaded file temporarily
            temp_file_path = f"temp_{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 2. Run the AI Extractor on the temporary file
            raw_json = extract_data_from_pdf(temp_file_path)
            
            # 3. Convert the AI's text into a structured Python dictionary
            extracted_data = json.loads(raw_json)
            
            # --- NEW: Inject the data into the permanent SQL database ---
            save_invoice_to_db(extracted_data, uploaded_file.name)
            
            # 4. Add the data to the list so Streamlit can display it
            all_extracted_data.append(extracted_data)
            
            # 5. Clean up the temporary file
            os.remove(temp_file_path)

        # 6. Display the success message and the data table
        st.success("Extraction Complete & Saved to Database!")
        st.table(all_extracted_data)

# --- THE PERMANENT LEDGER DISPLAY ---
st.divider() # Draws a neat horizontal line on the web page
st.subheader("🗄️ Historical Invoice Database")

# Fetch the data using the function we just built
historical_data = get_all_invoices()

# If the database has data in it, display it!
if historical_data:
    import pandas as pd
    # Convert the raw SQL data into a clean, interactive dataframe
    df = pd.DataFrame(historical_data, columns=["Invoice Number", "Destination", "Cargo Weight", "Total Amount Due", "Source File"])
    st.dataframe(df, use_container_width=True)
else:
    st.info("The database is currently empty. Upload an invoice to begin logging data.")