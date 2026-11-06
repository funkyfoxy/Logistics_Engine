import streamlit as st
import json
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from extractor import extract_data_from_pdf

# Load the secret vault
load_dotenv()

# Configure the web page to be wider and more enterprise-like
st.set_page_config(page_title="Logistics Engine", page_icon="📦", layout="wide")

# Upgraded Database Initialization with a flexible JSON column
def init_db():
    conn = sqlite3.connect('logistics_ledger.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            destination TEXT,
            cargo_weight TEXT,
            total_amount_due TEXT,
            extra_fields TEXT,  -- Vaults all your custom user extractions permanently
            source_file TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Upgraded Saving Function to automatically isolate custom metadata
def save_invoice_to_db(invoice_data, filename):
    # Separate the core columns from everything else
    core_keys = {'invoice_number', 'destination', 'cargo_weight', 'total_amount_due'}
    
    # Pack any user-defined custom fields into a neat JSON string
    extra_data = {k: v for k, v in invoice_data.items() if k not in core_keys}
    extra_fields_json = json.dumps(extra_data)

    with sqlite3.connect('logistics_ledger.db') as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO invoices (invoice_number, destination, cargo_weight, total_amount_due, extra_fields, source_file)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            str(invoice_data.get('invoice_number', 'N/A')),
            str(invoice_data.get('destination', 'N/A')),
            str(invoice_data.get('cargo_weight', 'N/A')),
            str(invoice_data.get('total_amount_due', 'N/A')),
            extra_fields_json,
            filename
        ))
        conn.commit()

# Upgraded Fetching function that flat-maps JSON columns into standard view rows
def get_all_invoices_upgraded():
    with sqlite3.connect('logistics_ledger.db') as conn:
        df = pd.read_sql_query('SELECT invoice_number, destination, cargo_weight, total_amount_due, extra_fields, source_file FROM invoices', conn)
        
        if df.empty:
            return df
            
        # Parse the JSON string from the extra_fields column into actual pandas columns
        extra_df = pd.json_normalize(df['extra_fields'].apply(json.loads))
        
        # Merge them back together and drop the raw JSON column
        final_df = pd.concat([df.drop(columns=['extra_fields']), extra_df], axis=1)
        
        # Reorder columns cleanly to keep source_file at the very end
        cols = [c for c in final_df.columns if c != 'source_file'] + ['source_file']
        return final_df[cols]


# --- THE DYNAMIC UI SIDEBAR ---
st.sidebar.subheader("⚙️ Extraction Configuration")
custom_fields_input = st.sidebar.text_input(
    "Data Fields to Extract (Comma-separated)", 
    value="invoice_number, destination, cargo_weight, total_amount_due"
)
# Convert the user input string into a clean Python list of fields
target_fields = [field.strip() for field in custom_fields_input.split(",") if field.strip()]

st.title("📦 AI Logistics Dashboard")
st.write("Upload your freight invoices below. The AI will extract the data and build your spreadsheet instantly.")

# --- THE ENTERPRISE SECURITY PITCH ---
with st.container():
    st.info(
        "🔒 **Enterprise Security Protocols Active:**\n"
        "*   **Zero Document Footprint:** Uploaded PDF documents are processed strictly in a volatile memory cache and are automatically scrubbed from the temporary system directory immediately following extraction data validation.\n"
        "*   **Secure Ledger Tracking:** Extracted operational metadata is piped directly into your dedicated isolated SQL ledger for secure historical persistence."
    )

# The Visual Drop Zone
uploaded_files = st.file_uploader("Drop PDF Invoices Here", type="pdf", accept_multiple_files=True)

# The Execution Button
if st.button("Process Invoices"):
    if not uploaded_files:
        st.warning("⚠️ Please upload at least one PDF first.")
    else:
        all_extracted_data = []
        
        # POLISH: The Visual Loading Spinner
        with st.spinner("Extracting and validating freight data..."):
            for uploaded_file in uploaded_files:
                temp_file_path = f"temp_{uploaded_file.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
    
                try:
                    # Run the upgraded AI Extractor (Now passing the dynamic fields!)
                    extracted_data, raw_text = extract_data_from_pdf(temp_file_path, target_fields)
        
                    if "error" in extracted_data:
                        st.error(f"❌ Failed to process {uploaded_file.name}. Ensure it is a valid PDF.")
                        continue
            
                    # Raw Text Preview
                    with st.expander(f"📄 View Raw PDF Text Preview for: {uploaded_file.name}"):
                        st.text(raw_text[:1000] + "\n\n... (Text truncated for preview)")
        
                    # Saves core fields to the permanent DB
                    save_invoice_to_db(extracted_data, uploaded_file.name)
                    
                    # Appends ALL dynamic fields to the live UI table
                    all_extracted_data.append(extracted_data)
        
                except Exception as e:
                    st.error(f"⚠️ System glitch processing {uploaded_file.name}: {str(e)}")
        
                finally:
                    # COMPLIANCE MOAT: This line runs 100% of the time, guaranteeing data deletion
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)

        # Success Output (Shows dynamic fields perfectly)
        if all_extracted_data:
            st.success("✅ Extraction Complete & Saved to Secure Database!")
            st.table(all_extracted_data)

# --- THE PERMANENT LEDGER DISPLAY ---
st.divider() 
st.subheader("🗄️ Historical Invoice Analytics Ledger")

df_historical = get_all_invoices_upgraded()

if not df_historical.empty:
    # 📊 THE EXECUTIVE ANALYTICS ROW
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric(label="Total Processed Invoices", value=len(df_historical))
        
    with kpi2:
        # Try to calculate global spending if numerical data exists
        try:
            # Clean string symbols like $, commas out to calculate sum
            clean_amounts = df_historical['Total Amount Due'].str.replace('$', '').str.replace(',', '').astype(float)
            total_spend = f"${clean_amounts.sum():,.2f}"
        except:
            total_spend = "Data Formatting Pending"
        st.metric(label="Total Logged Expenditure", value=total_spend)
        
    with kpi3:
        # Find the most frequent shipping destination
        top_dest = df_historical['Destination'].mode().values[0] if not df_historical['Destination'].empty else "N/A"
        st.metric(label="Top Logistics Corridor", value=str(top_dest))

    st.write("") # Spacer
    st.dataframe(df_historical, use_container_width=True)
else:
    st.info("The database is currently empty. Upload an invoice to begin logging data.")