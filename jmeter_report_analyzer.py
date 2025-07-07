import zipfile
import tempfile
import os
import uuid
import streamlit as st
from fastapi import UploadedFile

def extract_zip_file(zip_path: str, extract_path: str) -> str:
    """Extract all files from a zip file to a specified directory."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract all files
            zip_ref.extractall(extract_path)
            # Return the path to the extracted directory
            return extract_path
    except Exception as e:
        raise Exception(f"Error extracting zip file: {str(e)}")

def process_uploaded_file(uploaded_file: UploadedFile) -> str:
    """Process uploaded file and return the path to the extracted report."""
    try:
        # Create a temporary file to save the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # Create a unique directory for this report
        report_dir = os.path.join('temp_jmeter_reports', str(uuid.uuid4()))
        os.makedirs(report_dir, exist_ok=True)

        # Extract all files from the zip
        extract_zip_file(tmp_file_path, report_dir)

        # Clean up the temporary file
        os.unlink(tmp_file_path)

        return report_dir
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None 