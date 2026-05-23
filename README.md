# 📦 AI-Powered Logistics Extraction Engine

A full-stack web application designed to automate the extraction of critical freight data from unstructured PDF invoices using Large Language Models (LLMs).

## 🏗️ Architecture Overview

This project was built to demonstrate end-to-end data pipeline engineering, featuring:
*   **Frontend:** A responsive web dashboard built with `Streamlit` for seamless PDF drag-and-drop uploads.
*   **Processing Engine:** `pdfplumber` to parse raw text from PDF documents.
*   **AI Brain:** Integration with the `OpenAI API` (gpt-4o-mini) to intelligently extract and structure specific data points (Invoice Number, Destination, Weight, Total).
*   **Database:** A permanent `SQLite` database acting as a historical ledger to store and display all processed invoices.
*   **Security:** Full implementation of `python-dotenv` to isolate and secure API credentials outside of the source code.

## 🚀 How to Run Locally

1. Clone this repository to your local machine.
2. Install the required dependencies: `pip install streamlit pdfplumber openai python-dotenv pandas`
3. Create a `.env` file in the root directory and add your OpenAI API key: `OPENAI_API_KEY=your_key_here`
4. Run the application: `streamlit run app.py`

## 📊 Features
* Instantly converts raw PDF invoices into clean JSON data.
* Automatically injects extracted data into a permanent SQLite database.
* Renders a historical database UI that persists across server reboots.