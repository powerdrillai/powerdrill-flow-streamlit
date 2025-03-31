import streamlit as st
import os
from dotenv import load_dotenv
import time
import requests

from utils.api_client import PowerdrillClient
from utils.file_uploader import FileUploader
from components.auth import AuthComponent
from components.data_manager import DataManager
from components.chat_interface import ChatInterface

# Load environment variables
load_dotenv()

# App configuration
st.set_page_config(
    page_title="Powerdrill AI Data Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Optimize sidebar as the only leftmost element
st.markdown("""
<style>
    /* Main content styling */
    .main {
        background-color: #f8f9fa;
    }

    /* Sidebar styling to match design */
    [data-testid="stSidebar"] {
        background-color: #2D3748 !important;
        color: white !important;
        width: 400px !important;
        flex-shrink: 0 !important;
        padding: 1.5rem !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: white !important;
    }

    [data-testid="stSidebar"] .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        border-bottom-color: #4A5568 !important;
    }

    [data-testid="stSidebar"] .stTabs [role="tab"] {
        background-color: transparent !important;
        color: #A0AEC0 !important;
        border-radius: 0 !important;
        padding: 0.5rem 1rem !important;
    }

    [data-testid="stSidebar"] .stTabs [role="tab"][aria-selected="true"] {
        background-color: transparent !important;
        color: white !important;
        border-bottom: 2px solid #F56565 !important;
    }

    [data-testid="stSidebar"] .stButton button {
        background-color: #4A90E2 !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        border-radius: 0.375rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }

    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stTextArea textarea {
        background-color: #1A202C !important;
        color: white !important;
        border: 1px solid #4A5568 !important;
        border-radius: 0.375rem !important;
    }

    /* Remove the sidebar collapse button */
    button[kind="header"] {
        display: none !important;
    }

    /* Force 2-column layout: sidebar and main content */
    .appview-container {
        width: 100% !important;
        display: flex !important;
        flex-direction: row !important;
    }

    /* Fix main content */
    [data-testid="stAppViewContainer"] > .main {
        flex-grow: 1 !important;
        max-width: calc(100% - 400px) !important;
    }

    /* Remove extra spacing */
    .block-container {
        max-width: 100% !important;
        padding: 2rem !important;
    }

    /* Remove all extra columns and padding */
    div:has(> [data-testid="stSidebar"]) {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Button styling */
    .stButton button {
        background-color: #4A90E2 !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        border-radius: 0.375rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }

    .stButton button:hover {
        background-color: #357ABD !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        transform: translateY(-1px) !important;
    }

    .stButton button:active {
        transform: translateY(0px) !important;
    }

    /* Sidebar button specific styling */
    [data-testid="stSidebar"] .stButton button {
        background-color: #4A90E2 !important;
        color: white !important;
        width: 100% !important;
        margin: 0.25rem 0 !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }

    /* Question button specific styling */
    button[kind="secondary"] {
        background-color: #F0F2F6 !important;
        color: #1E1E1E !important;
        border: 1px solid #E0E3E7 !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }

    button[kind="secondary"]:hover {
        background-color: #E8EAF0 !important;
        color: #000000 !important;
    }

    /* Progress bar */
    .stProgress .st-bo {
        background-color: #3182CE;
    }

    /* Info message styling */
    .element-container div[data-testid="stVerticalBlock"] div[data-baseweb="notification"] {
        background-color: #2C5282 !important;
        color: white !important;
        border-radius: 0.375rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "api_client" not in st.session_state:
    st.session_state.api_client = None
if "current_dataset_id" not in st.session_state:
    st.session_state.current_dataset_id = None
if "current_dataset_name" not in st.session_state:
    st.session_state.current_dataset_name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "exploration_questions" not in st.session_state:
    st.session_state.exploration_questions = []

# App header
st.title("Powerdrill AI Data Analysis")
st.markdown("Upload your data files and get AI-powered insights instantly")

# Authentication
if not st.session_state.authenticated:
    auth = AuthComponent()
    user_id, api_key = auth.render()

    if user_id and api_key:
        with st.spinner("Authenticating..."):
            # Initialize API client
            api_endpoint = os.getenv("POWERDRILL_API_ENDPOINT", "https://ai.data.cloud/api/v2/team")
            client = PowerdrillClient(api_endpoint, user_id, api_key)

            # Test authentication by listing datasets
            try:
                # Attempt to list datasets to validate credentials
                response = client.list_datasets()

                # If we reached here, the request was successful (200 OK)
                st.session_state.authenticated = True
                st.session_state.api_client = client
                st.success("Authentication successful!")
                time.sleep(1)
                st.rerun()
            except requests.exceptions.HTTPError as e:
                # Handle specific HTTP errors
                if e.response.status_code == 401 or e.response.status_code == 403:
                    st.error("Authentication failed: Invalid User ID or API Key")
                else:
                    st.error(f"Authentication failed: {str(e)}")
            except Exception as e:
                # Handle any other errors
                error_msg = str(e)
                if "API request failed" in error_msg:
                    st.error("Authentication failed: Invalid User ID or API Key")
                else:
                    st.error(f"Authentication failed: {error_msg}")
else:
    # Main app interface after authentication
    client = st.session_state.api_client

    # Sidebar with data management
    with st.sidebar:
        st.header("Data Management")
        data_manager = DataManager(client)
        data_manager.render()

        # File uploader component
        st.header("Upload New Files")

        # Get the selected dataset name from session state if available
        dataset_name = st.session_state.get("current_dataset_name")

        file_uploader = FileUploader(client, initial_dataset_name=dataset_name)
        files_ready = file_uploader.render()

        if files_ready:
            # We'll handle processing in the chat interface
            st.rerun()

    # Main content area
    if st.session_state.get("processing_files", False):
        # If we're processing files, show a chat interface with a temporary dataset id
        # This will be updated once processing is complete
        chat = ChatInterface(client, st.session_state.get("current_dataset_id", "temp-processing"))
        chat.render()
    elif st.session_state.current_dataset_id:
        # Chat interface with selected dataset
        chat = ChatInterface(client, st.session_state.current_dataset_id)
        chat.render()
    else:
        st.info("Please select or upload a dataset to begin analysis") 