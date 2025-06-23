import streamlit as st
import pandas as pd
import pdfplumber
import re
import tempfile
import os
import io

st.set_page_config(page_title="PDF to Excel Converter", layout="centered")

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


HEADER = ["Domain name", "Customer ID", "Amount(US$)"]
ROW_REGEX = re.compile(r"^([\w\-.]+)\s+(C\w+)\s+([\d,]+\.\d{2})$")

def extract_table_from_text(pdf_path):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.splitlines()
            in_table = False
            for i, line in enumerate(lines):
                if "Summary of costs by domain" in line:
                    in_table = True
                    continue
                if in_table:
                    if re.match(r"\d{1,2} \w+ \d{4} - \d{1,2} \w+ \d{4}", line):
                        continue
                    if all(h in line for h in ["Domain name", "Customer ID", "Amount"]):
                        continue
                    m = ROW_REGEX.match(line.strip())
                    if m:
                        domain, customer_id, amount = m.groups()
                        rows.append([domain, customer_id, amount])
                    elif line.strip() == '' or 'Subtotal' in line:
                        in_table = False
    return rows

st.title("PDF Table to Excel Converter")
st.write("Upload one or more PDFs containing a 'Summary of costs by domain' table. The app will extract the table from each and let you download each as Excel.")

uploaded_files = st.file_uploader("Choose PDF files", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_pdf_path = tmp_file.name
        rows = extract_table_from_text(tmp_pdf_path)
        os.unlink(tmp_pdf_path)
        st.markdown(f"### File: {uploaded_file.name}")
        if not rows:
            st.error("No table rows found in the PDF text.")
        else:
            df = pd.DataFrame(rows, columns=HEADER)
            st.success(f"Extracted {len(df)} rows. Your file is ready!")
            st.dataframe(df)
            st.info("Click the button below to download your Excel file.")
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            st.markdown("## 📥 Download your Excel file below:")
            st.download_button(
                label=f"⬇️ Download Excel for {uploaded_file.name}",
                data=output,
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_summary_of_costs_by_domain.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ) 