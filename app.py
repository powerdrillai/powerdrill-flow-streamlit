import streamlit as st
import os
from dotenv import load_dotenv
import time

from utils.api_client import PowerdrillClient
from utils.file_uploader import FileUploader
from components.auth import AuthComponent
from components.data_manager import DataManager
from components.chat_interface import ChatInterface

# Load environment variables
load_dotenv()

# App configuration
st.set_page_config(
    page_title="PowerDrill AI Data Analysis",
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
        background-color: #3182CE !important;
        color: white !important;
        border-radius: 0.375rem !important;
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
        background-color: #3182CE;
        color: white;
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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "exploration_questions" not in st.session_state:
    st.session_state.exploration_questions = []

# App header
st.title("PowerDrill AI Data Analysis")
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
                client.list_datasets()
                st.session_state.authenticated = True
                st.session_state.api_client = client
                st.success("Authentication successful!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")
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
        file_uploader = FileUploader(client)
        uploaded = file_uploader.render()
        
        if uploaded:
            st.success("Files uploaded successfully!")
            st.session_state.current_dataset_id = uploaded
            st.rerun()
    
    # Main content area
    if st.session_state.current_dataset_id:
        # Chat interface
        chat = ChatInterface(client, st.session_state.current_dataset_id)
        chat.render()
    else:
        st.info("Please select or upload a dataset to begin analysis") 