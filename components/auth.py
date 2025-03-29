import streamlit as st
from typing import Tuple, Optional

class AuthComponent:
    def __init__(self):
        """Authentication component for Powerdrill API"""
        pass
    
    def render(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Render the authentication form
        
        Returns:
            Tuple of (user_id, api_key) if provided, (None, None) otherwise
        """
        st.header("Authentication")
        
        st.info("""
        Please enter your Powerdrill API Key and User ID.
        """)
        
        with st.form("auth_form"):
            user_id = st.text_input(
                "User ID", 
                key="user_id",
                help="Your Powerdrill User ID (looks like: tmm-xxxxxxxxxxxx)"
            )

            api_key = st.text_input(
                "API Key", 
                type="password", 
                key="api_key",
                help="Your Powerdrill API Key (starts with 'proj-')"
            )
            
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if not user_id:
                    st.error("Please provide a User ID")
                    return None, None
                
                if not api_key:
                    st.error("Please provide an API Key")
                    return None, None
                
                return user_id, api_key
        
        # Display help information
        with st.expander("Need help finding your credentials?"):
            st.markdown("""
            ### How to get your Powerdrill credentials:
            
            1. Log in to your Powerdrill account
            2. Navigate to the API settings page
            3. Copy your User ID and API Key
            
            Your User ID typically starts with 'tmm-' followed by a unique identifier.
            Your API Key typically starts with 'proj-' followed by a unique identifier.
            
            Both credentials are required for authentication. If you enter them correctly,
            the system will verify them by attempting to list your datasets.
            
            If you don't have an account yet, sign up at [Powerdrill](https://powerdrill.ai)
            """)
        
        return None, None 