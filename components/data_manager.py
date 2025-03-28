import streamlit as st
import pandas as pd
from typing import Dict, List, Optional

class DataManager:
    def __init__(self, api_client):
        """
        Data manager component for Powerdrill
        
        Args:
            api_client: The Powerdrill API client
        """
        self.api_client = api_client
    
    def render(self):
        """Render the data manager component"""
        tab1, tab2 = st.tabs(["Datasets", "Data Sources"])
        
        with tab1:
            self._render_datasets()
        
        with tab2:
            self._render_data_sources()
    
    def _render_datasets(self):
        """Render the datasets management section"""
        st.subheader("Your Datasets")
        
        # Add refresh button
        if st.button("Refresh Datasets", key="refresh_datasets"):
            st.rerun()
        
        try:
            # Get datasets
            response = self.api_client.list_datasets()
            
            if 'data' in response:
                # Check if there are no datasets (by checking total_items or missing records field)
                if response['data'].get('total_items', 0) == 0 or 'records' not in response['data']:
                    st.info("No datasets found. Upload files to create a new dataset.")
                    return
                
                datasets = response['data'].get('records', [])
                
                if not datasets:
                    st.info("No datasets found. Upload files to create a new dataset.")
                    return
                
                # Convert to DataFrame for display
                df = pd.DataFrame([
                    {
                        "ID": d.get('id', ''),
                        "Name": d.get('name', ''),
                        "Description": d.get('description', ''),
                        "Created": d.get('created_at', '')
                    }
                    for d in datasets
                ])
                
                # Display as table
                st.dataframe(df)
                
                # Dataset selection and actions
                selected_dataset = st.selectbox(
                    "Select a dataset", 
                    options=[d.get('id') for d in datasets],
                    format_func=lambda x: next((d.get('name', x) for d in datasets if d.get('id') == x), x)
                )
                
                if selected_dataset:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Use Selected Dataset", key="use_dataset"):
                            # Get the selected dataset name
                            selected_dataset_name = next((d.get('name', '') for d in datasets if d.get('id') == selected_dataset), '')
                            # Store both ID and name in session state
                            st.session_state.current_dataset_id = selected_dataset
                            st.session_state.current_dataset_name = selected_dataset_name
                            st.rerun()
                    
                    with col2:
                        if st.button("Delete Dataset", key="delete_dataset"):
                            self._delete_dataset(selected_dataset)
            else:
                st.error("Failed to retrieve datasets")
        
        except Exception as e:
            st.error(f"Error loading datasets: {str(e)}")
    
    def _render_data_sources(self):
        """Render the data sources management section"""
        st.subheader("Your Data Sources")
        
        # Add refresh button
        if st.button("Refresh Data Sources", key="refresh_sources"):
            st.rerun()
        
        # Get current dataset ID
        dataset_id = st.session_state.get("current_dataset_id")
        
        if not dataset_id:
            st.info("Select a dataset first to view its data sources")
            return
        
        try:
            # Get data sources for the current dataset
            response = self.api_client.list_data_sources(dataset_id)
            
            if 'data' in response and 'records' in response['data']:
                data_sources = response['data']['records']
                
                if not data_sources:
                    st.info("No data sources found in this dataset.")
                    return
                
                # Convert to DataFrame for display
                df = pd.DataFrame([
                    {
                        "ID": d.get('id', ''),
                        "Name": d.get('name', ''),
                        "Status": d.get('status', ''),
                        "Type": d.get('type', '')
                    }
                    for d in data_sources
                ])
                
                # Display as table
                st.dataframe(df)
                
                # Data source selection and actions
                selected_source = st.selectbox(
                    "Select a data source", 
                    options=[d.get('id') for d in data_sources],
                    format_func=lambda x: next((d.get('name', x) for d in data_sources if d.get('id') == x), x)
                )
                
                if selected_source:
                    if st.button("Delete Data Source", key="delete_source"):
                        self._delete_data_source(selected_source)
            else:
                st.error("Failed to retrieve data sources")
        
        except Exception as e:
            st.error(f"Error loading data sources: {str(e)}")
    
    def _delete_dataset(self, dataset_id: str):
        """Delete a dataset"""
        if st.session_state.get("current_dataset_id") == dataset_id:
            st.session_state.current_dataset_id = None
            st.session_state.current_dataset_name = None
        
        try:
            with st.spinner("Deleting dataset..."):
                self.api_client.delete_dataset(dataset_id)
                st.success("Dataset deleted successfully")
                st.rerun()
        except Exception as e:
            st.error(f"Error deleting dataset: {str(e)}")
    
    def _delete_data_source(self, data_source_id: str):
        """Delete a data source"""
        # Get current dataset ID
        dataset_id = st.session_state.get("current_dataset_id")
        if not dataset_id:
            st.error("Dataset ID is required to delete a data source")
            return
            
        try:
            with st.spinner("Deleting data source..."):
                self.api_client.delete_data_source(data_source_id, dataset_id)
                st.success("Data source deleted successfully")
                st.rerun()
        except Exception as e:
            st.error(f"Error deleting data source: {str(e)}") 