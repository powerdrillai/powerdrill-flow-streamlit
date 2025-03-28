import streamlit as st
import os
import tempfile
import uuid
from datetime import datetime
from typing import List, Optional

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
    
    def render(self) -> Optional[str]:
        """
        Render the file uploader component
        
        Returns:
            Dataset ID if files were uploaded and processed, None otherwise
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
            return self._process_files(dataset_name, dataset_description, uploaded_files)
        
        return None
    
    def _process_files(self, dataset_name: str, dataset_description: str, uploaded_files: List) -> Optional[str]:
        """
        Process uploaded files and create a dataset
        
        Args:
            dataset_name: Name of the dataset
            dataset_description: Description of the dataset
            uploaded_files: List of uploaded files
            
        Returns:
            Dataset ID if successful, None otherwise
        """
        if not uploaded_files:
            st.error("No files uploaded")
            return None
            
        with st.spinner("Creating dataset..."):
            try:
                # Create a new dataset
                response = self.api_client.create_dataset(dataset_name, dataset_description)
                dataset_id = response['data']['id']
                
                total_files = len(uploaded_files)
                progress_bar = st.progress(0)
                
                # Upload each file as a data source
                for i, file in enumerate(uploaded_files):
                    # Create a temporary file to store the uploaded content
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
                        temp_file.write(file.getbuffer())
                        temp_path = temp_file.name
                    
                    # Upload the file as a data source
                    try:
                        st.text(f"Uploading {file.name}...")
                        self.api_client.create_data_source(dataset_id, temp_path, file.name)
                        
                        # Update progress bar
                        progress_bar.progress((i + 1) / total_files)
                    finally:
                        # Clean up temporary file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                
                # Wait for dataset to be ready
                st.text("Processing data... This may take a while.")
                if self.api_client.wait_for_dataset_ready(dataset_id):
                    st.success(f"All files processed successfully!")
                    return dataset_id
                else:
                    st.warning("Dataset processing timed out. You can check the status later.")
                    return dataset_id
                    
            except Exception as e:
                st.error(f"Error processing files: {str(e)}")
                return None 