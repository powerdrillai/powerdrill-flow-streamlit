import streamlit as st
import os
import tempfile
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

class FileUploader:
    def __init__(self, api_client, initial_dataset_name: Optional[str] = None):
        """
        File uploader component for Powerdrill

        Args:
            api_client: The Powerdrill API client
            initial_dataset_name: Initial dataset name to use (when a dataset is selected)
        """
        self.api_client = api_client
        self.initial_dataset_name = initial_dataset_name
        self.supported_extensions = [
            ".csv", ".tsv", ".md", ".mdx", ".json", 
            ".txt", ".pdf", ".pptx", ".docx", ".xls", ".xlsx"
        ]

    def render(self) -> bool:
        """
        Render the file uploader component

        Returns:
            True if files are prepared for upload, False otherwise
        """
        # Use the initial dataset name if provided, otherwise generate a default name
        default_name = self.initial_dataset_name if self.initial_dataset_name else f"Dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        dataset_name = st.text_input(
            "Dataset Name", 
            value=default_name,
            help="Enter a name for your dataset"
        )

        dataset_description = st.text_area(
            "Description (optional)", 
            help="Enter a description for your dataset"
        )

        uploaded_files = st.file_uploader(
            "Upload Files", 
            accept_multiple_files=True,
            type=self.supported_extensions,
            help="Upload one or more files for analysis. Supported formats: CSV, TSV, MD, MDX, JSON, TXT, PDF, PPTX, DOCX, XLS, XLSX"
        )

        if uploaded_files and st.button("Process Files"):
            # Store upload information in session state for processing in the chat area
            st.session_state.processing_files = True
            st.session_state.processing_dataset_name = dataset_name
            st.session_state.processing_dataset_description = dataset_description
            st.session_state.processing_uploaded_files = uploaded_files

            return True

        return False 