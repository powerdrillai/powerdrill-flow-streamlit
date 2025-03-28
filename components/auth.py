import streamlit as st
from typing import Tuple, Optional

class AuthComponent:
    def __init__(self):
        """Authentication component for PowerDrill API"""
        pass
    
    def render(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Render the authentication form
        
        Returns:
            Tuple of (user_id, api_key) if provided, (None, None) otherwise
        """
        st.header("Authentication")
        
        with st.form("auth_form"):
            user_id = st.text_input(
                "User ID", 
                key="user_id",
                help="Your PowerDrill User ID"
            )
            
            api_key = st.text_input(
                "API Key", 
                type="password", 
                key="api_key",
                help="Your PowerDrill API Key"
            )
            
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if not user_id or not api_key:
                    st.error("Please provide both User ID and API Key")
                    return None, None
                
                return user_id, api_key
        
        # Display help information
        with st.expander("Need help finding your credentials?"):
            st.markdown("""
            ### How to get your PowerDrill credentials:
            
            1. Log in to your PowerDrill account
            2. Navigate to the API settings page
            3. Copy your User ID and API Key
            
            If you don't have an account yet, sign up at [PowerDrill](https://powerdrill.ai)
            """)
        
        return None, None 