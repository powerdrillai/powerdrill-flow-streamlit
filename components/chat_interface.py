import streamlit as st
import json
import time
import tempfile
import os
from typing import List, Dict, Any, Optional

class ChatInterface:
    def __init__(self, api_client, dataset_id: str):
        """
        Chat interface component for Powerdrill
        
        Args:
            api_client: The Powerdrill API client
            dataset_id: The current dataset ID
        """
        self.api_client = api_client
        self.dataset_id = dataset_id
        
        # Initialize chat history if not in session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Get dataset overview if not already loaded
        if st.session_state.get("exploration_questions") is None or st.session_state.get("current_dataset_id") != dataset_id:
            self._load_dataset_overview()
    
    def render(self):
        """Render the chat interface component"""
        st.header("AI Data Analysis")
        
        # Display dataset info
        self._display_dataset_info()
        
        # Check if we're processing files
        processing_files = st.session_state.get("processing_files", False)
        if processing_files:
            self._process_files_in_chat()
            
            # Even if we're processing files, still show the chat history and input area
            # if the processing was completed in a previous run but the UI hasn't refreshed yet
            if not st.session_state.get("processing_files", False):
                self._display_chat_history()
                self._display_suggested_questions()
                self._display_input_area()
            return
            
        # Display chat history
        self._display_chat_history()
        
        # Display suggested questions
        self._display_suggested_questions()
        
        # Input area
        self._display_input_area()
    
    def _process_files_in_chat(self):
        """Handle file processing in the chat area"""
        # Get file processing info from session state
        dataset_name = st.session_state.get("processing_dataset_name", "")
        dataset_description = st.session_state.get("processing_dataset_description", "")
        uploaded_files = st.session_state.get("processing_uploaded_files", [])
        
        # Create a chat-like container for processing messages
        chat_container = st.container()
        
        with chat_container:
            # Display user's upload action as a message
            with st.chat_message("user"):
                st.write(f"I'm uploading {len(uploaded_files)} files to create dataset: '{dataset_name}'")
                
            # Display assistant's response
            with st.chat_message("assistant"):
                status_container = st.empty()
                
                with status_container:
                    try:
                        # Create dataset
                        with st.spinner("Creating dataset..."):
                            response = self.api_client.create_dataset(dataset_name, dataset_description)
                            dataset_id = response['data']['id']
                            st.success(f"Dataset '{dataset_name}' created successfully!")
                        
                        # Upload progress
                        st.write("Uploading and processing files...")
                        total_files = len(uploaded_files)
                        progress_bar = st.progress(0)
                        
                        for i, file in enumerate(uploaded_files):
                            # Create a temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
                                temp_file.write(file.getbuffer())
                                temp_path = temp_file.name
                            
                            # Upload the file
                            try:
                                st.write(f"Uploading {file.name}...")
                                self.api_client.create_data_source(dataset_id, temp_path, file.name)
                                progress_bar.progress((i + 1) / total_files)
                            finally:
                                # Clean up temporary file
                                if os.path.exists(temp_path):
                                    os.unlink(temp_path)
                        
                        # Wait for processing to complete
                        st.write("Processing data... This may take a while.")
                        if self.api_client.wait_for_dataset_ready(dataset_id):
                            st.success("All files processed successfully!")
                            
                            # Load dataset overview to get exploration questions
                            st.write("Preparing AI exploration suggestions...")
                            self.dataset_id = dataset_id
                            self._load_dataset_overview()
                            
                            # Display exploration questions
                            if st.session_state.get("exploration_questions"):
                                st.write("Here are some questions you can ask about your data:")
                                questions = st.session_state.get("exploration_questions", [])
                                for q in questions:
                                    st.write(f"- {q}")
                        else:
                            st.warning("Dataset processing timed out. You can check the status later.")
                        
                        # Update session state
                        st.session_state.current_dataset_id = dataset_id
                        st.session_state.processing_files = False
                        
                        # Add file processing to chat history
                        st.session_state.chat_history.append({
                            'is_user': True,
                            'content': f"I'm uploading {len(uploaded_files)} files to create dataset: '{dataset_name}'"
                        })
                        
                        # Prepare the assistant's message with all the processing information
                        assistant_message = f"Dataset '{dataset_name}' created successfully!\n\n"
                        assistant_message += "Uploading and processing files...\n"
                        for file in uploaded_files:
                            assistant_message += f"Uploaded {file.name}\n"
                        assistant_message += "\nAll files processed successfully!\n\n"
                        
                        if st.session_state.get("exploration_questions"):
                            assistant_message += "Here are some questions you can ask about your data:\n"
                            for q in st.session_state.get("exploration_questions", []):
                                assistant_message += f"- {q}\n"
                        
                        assistant_message += "\nYou can now ask questions about your data!"
                        
                        # Add assistant's response to chat history
                        st.session_state.chat_history.append({
                            'is_user': False,
                            'content': assistant_message
                        })
                        
                        # Trigger a rerun to switch to normal chat mode
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error processing files: {str(e)}")
                        st.session_state.processing_files = False
    
    def _load_dataset_overview(self):
        """Load dataset overview and exploration questions"""
        try:
            with st.spinner("Loading dataset information..."):
                response = self.api_client.get_dataset_overview(self.dataset_id)
                
                if 'data' in response:
                    data = response['data']
                    st.session_state.dataset_name = data.get('name', 'Unnamed Dataset')
                    st.session_state.dataset_description = data.get('description', '')
                    st.session_state.dataset_summary = data.get('summary', '')
                    st.session_state.exploration_questions = data.get('exploration_questions', [])
                    st.session_state.dataset_keywords = data.get('keywords', [])
                    st.session_state.current_dataset_id = self.dataset_id
                else:
                    st.warning("Dataset overview information not available")
                    # Set minimal default values
                    st.session_state.dataset_name = st.session_state.get("dataset_name", "Dataset")
                    st.session_state.exploration_questions = []
        except Exception as e:
            st.error(f"Error loading dataset information: {str(e)}")
            # Set minimal default values even on error
            st.session_state.dataset_name = st.session_state.get("dataset_name", "Dataset")
            st.session_state.exploration_questions = []
            st.session_state.current_dataset_id = self.dataset_id
    
    def _display_dataset_info(self):
        """Display dataset information"""
        st.subheader(st.session_state.get("dataset_name", "Dataset"))
        
        if st.session_state.get("dataset_description"):
            st.write(st.session_state.get("dataset_description"))
        
        if st.session_state.get("dataset_summary"):
            with st.expander("Dataset Summary"):
                st.write(st.session_state.get("dataset_summary"))
        
        if st.session_state.get("dataset_keywords"):
            st.write("Keywords: " + ", ".join(st.session_state.get("dataset_keywords")))
    
    def _display_chat_history(self):
        """Display chat history"""
        # Create chat container with auto scroll
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history:
                self._render_message(message)
    
    def _render_message(self, message: Dict[str, Any]):
        """
        Render a chat message
        
        Args:
            message: The message to render
        """
        is_user = message.get('is_user', False)
        content = message.get('content', '')
        
        if is_user:
            st.chat_message("user").write(content)
        else:
            with st.chat_message("assistant"):
                st.write(content)
    
    def _display_suggested_questions(self):
        """Display suggested questions"""
        if st.session_state.get("exploration_questions"):
            with st.expander("Suggested Questions", expanded=True):
                for question in st.session_state.get("exploration_questions"):
                    if st.button(question, key=f"q_{hash(question)}"):
                        self._ask_question(question)
    
    def _display_input_area(self):
        """Display input area for user questions"""
        user_input = st.chat_input("Ask a question about your data...")
        
        if user_input:
            self._ask_question(user_input)
    
    def _ask_question(self, question: str):
        """
        Ask a question and process the response
        
        Args:
            question: The question to ask
        """
        # Add user message to chat history
        st.session_state.chat_history.append({
            'is_user': True,
            'content': question
        })
        
        # Create a placeholder for the assistant's response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            response_content = ""
            
            try:
                # Call API with streaming enabled
                stream = self.api_client.create_job(self.dataset_id, question, stream=True)
                
                # Process streaming response
                for line in stream:
                    if not line:
                        continue
                    
                    try:
                        # Try to decode the line as JSON
                        data = json.loads(line.decode('utf-8'))
                        
                        # Process different message types
                        if 'data' in data and 'messages' in data['data']:
                            for msg in data['data']['messages']:
                                msg_type = msg.get('type')
                                content = msg.get('content')
                                
                                if msg_type == 'TEXT' and content:
                                    # For text messages, append to response
                                    if isinstance(content, list) and len(content) > 0:
                                        text = content[0]
                                        response_content += text
                                        message_placeholder.markdown(response_content)
                                    elif isinstance(content, str):
                                        response_content += content
                                        message_placeholder.markdown(response_content)
                    except json.JSONDecodeError:
                        # If not valid JSON, skip
                        continue
            except Exception as e:
                error_msg = f"Error processing question: {str(e)}"
                message_placeholder.error(error_msg)
                response_content = error_msg
            
            # Add assistant message to chat history
            st.session_state.chat_history.append({
                'is_user': False,
                'content': response_content
            }) 