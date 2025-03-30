import streamlit as st
import json
import time
import tempfile
import os
from typing import List, Dict, Any, Optional
import pandas as pd

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

        # Initialize session_id for conversation if not in session state
        if "powerdrill_session_id" not in st.session_state or st.session_state.get("powerdrill_dataset_id") != dataset_id:
            # Create a new session for this dataset
            self._create_new_session()
            st.session_state.powerdrill_dataset_id = dataset_id

        # Get dataset overview if not already loaded
        if st.session_state.get("exploration_questions") is None or st.session_state.get("current_dataset_id") != dataset_id:
            self._load_dataset_overview()

        # Maintain dataset ID consistency
        st.session_state.current_dataset_id = dataset_id

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
            # Show spinner during loading
            with st.spinner("Loading dataset information..."):
                # Try up to 3 times with backoff
                max_retries = 3
                retry_delay = 1

                for attempt in range(max_retries):
                    try:
                        response = self.api_client.get_dataset_overview(self.dataset_id)

                        # If successful, process the response
                        if 'data' in response:
                            data = response['data']
                            st.session_state.dataset_name = data.get('name', 'Unnamed Dataset')
                            st.session_state.dataset_description = data.get('description', '')
                            st.session_state.dataset_summary = data.get('summary', '')
                            st.session_state.exploration_questions = data.get('exploration_questions', [])
                            st.session_state.dataset_keywords = data.get('keywords', [])
                            st.session_state.current_dataset_id = self.dataset_id

                            # Log success
                            print(f"Successfully loaded dataset overview. Found {len(st.session_state.exploration_questions)} exploration questions.")
                            return
                        else:
                            print(f"Dataset overview response missing 'data' field: {response}")
                            # Try again after delay
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff

                    except Exception as e:
                        if attempt < max_retries - 1:
                            print(f"Error loading dataset overview (attempt {attempt+1}/{max_retries}): {str(e)}")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            # On final attempt, re-raise
                            raise

                # If we got here, all retries failed but no exception was raised
                st.warning("Unable to load dataset information after multiple attempts")

        except Exception as e:
            st.error(f"Error loading dataset information: {str(e)}")
            print(f"Exception in _load_dataset_overview: {str(e)}")

        # Set minimal default values even on error
        if not st.session_state.get("dataset_name"):
            st.session_state.dataset_name = "Dataset"
        if not st.session_state.get("exploration_questions"):
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
        st.subheader("Ask AI about your data")

        # Display a more prominent UI for exploration questions
        if st.session_state.get("exploration_questions"):
            st.write("Select one of these AI-suggested questions or type your own:")

            # Display each question on its own line
            for question in st.session_state.get("exploration_questions"):
                if st.button(f"🔍 {question}", key=f"q_{hash(question)}", use_container_width=True):
                    self._ask_question(question)

            # Add a refresh button to get new questions
            if st.button("🔄 Refresh suggested questions", key="refresh_questions"):
                with st.spinner("Getting new question suggestions..."):
                    self._load_dataset_overview()
                    st.rerun()
        else:
            # If no exploration questions, show a message and refresh button
            st.info("No suggested questions available for this dataset.")
            if st.button("🔄 Get suggested questions", key="get_questions"):
                with st.spinner("Getting question suggestions..."):
                    self._load_dataset_overview()
                    st.rerun()

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

            # Display a placeholder message while waiting for the API response
            message_placeholder.markdown("Analyzing your data...")

            try:
                # Get the session ID for the conversation
                session_id = st.session_state.get("powerdrill_session_id")

                # If we don't have a session ID, create one
                if not session_id:
                    self._create_new_session()
                    session_id = st.session_state.get("powerdrill_session_id")

                # Call API with streaming enabled and passing the session ID
                stream = self.api_client.create_job(
                    dataset_id=self.dataset_id, 
                    prompt=question, 
                    stream=True,
                    session_id=session_id
                )

                # Track job completion status
                job_id = None
                images = []
                tables = []
                # Track seen image/table URLs to prevent duplicates
                seen_image_urls = set()
                seen_table_urls = set()

                # Helper function to strip query parameters from URLs
                def strip_url_params(url):
                    return url.split('?')[0] if '?' in url else url

                # Process streaming response
                event_type = None

                for line in stream:
                    if not line:
                        continue

                    try:
                        # Debug: Print raw line received from API
                        line_str = line.decode('utf-8')
                        print(f"DEBUG - Raw API response: {line}")

                        # Parse SSE format - extract event and data
                        if line_str.startswith('event:'):
                            event_type = line_str.replace('event:', '').strip()
                            continue
                        elif line_str.startswith('data:'):
                            # Extract the data part
                            data_str = line_str.replace('data:', '', 1).strip()

                            # Handle simple job ID response
                            if event_type == 'JOB_ID' and not data_str.startswith('{'):
                                job_id = data_str
                                print(f"DEBUG - Set job_id: {job_id}")
                                continue

                            # Try to decode the data as JSON
                            try:
                                data = json.loads(data_str)
                                print(f"DEBUG - Decoded {event_type} JSON data")

                                # Extract message content from MESSAGE events
                                if event_type == 'MESSAGE' and 'choices' in data:
                                    for choice in data.get('choices', []):
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            content = choice['delta']['content']
                                            if content and isinstance(content, str):
                                                response_content += content
                                                print(f"DEBUG - Extracted content from MESSAGE: '{content}'")
                                                message_placeholder.markdown(str(response_content))

                                # Handle IMAGE events
                                elif event_type == 'IMAGE' and 'choices' in data:
                                    for choice in data.get('choices', []):
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            img_content = choice['delta']['content']
                                            if isinstance(img_content, dict) and 'url' in img_content:
                                                image_url = img_content.get('url')
                                                image_name = img_content.get('name', 'Image')
                                                # Strip query params for comparison
                                                clean_url = strip_url_params(image_url)
                                                if clean_url and clean_url not in seen_image_urls:
                                                    print(f"DEBUG - Adding image: {image_name}, URL: {image_url}")
                                                    images.append({'url': image_url, 'name': image_name})
                                                    seen_image_urls.add(clean_url)
                                                    # Also update the response to indicate an image is available
                                                    image_text = f"\n\n![{image_name}]({image_url})\n\n"
                                                    response_content += image_text
                                                    message_placeholder.markdown(str(response_content))

                                # Handle TABLE events
                                elif event_type == 'TABLE' and 'choices' in data:
                                    for choice in data.get('choices', []):
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            table_content = choice['delta']['content']
                                            if isinstance(table_content, dict) and 'url' in table_content:
                                                table_url = table_content.get('url')
                                                table_name = table_content.get('name', 'Table')
                                                # Strip query params for comparison
                                                clean_url = strip_url_params(table_url)
                                                if clean_url and clean_url not in seen_table_urls:
                                                    print(f"DEBUG - Adding table: {table_name}, URL: {table_url}")
                                                    tables.append({'url': table_url, 'name': table_name})
                                                    seen_table_urls.add(clean_url)
                                                    # Also update the response to indicate a table is available
                                                    response_content += f"\n\n**Table: {table_name}** (will be displayed below)\n\n"
                                                    message_placeholder.markdown(str(response_content))

                                # Process blocks format (legacy)
                                if 'data' in data and 'blocks' in data['data']:
                                    for block in data['data']['blocks']:
                                        block_type = block.get('type')
                                        content = block.get('content')

                                        if block_type == 'MESSAGE' and content:
                                            # For text messages, append to response
                                            if content and isinstance(content, str):
                                                response_content += content
                                                # Debug: Print the current response content being displayed
                                                print(f"DEBUG - Updating UI with content: '{content}'")
                                                print(f"DEBUG - Current response_content: '{response_content}'")
                                                # Ensure we're calling markdown with a string
                                                message_placeholder.markdown(str(response_content))
                                            else:
                                                print(f"DEBUG - Skipping content of type {type(content)}: {content}")

                                        elif block_type == 'IMAGE' and isinstance(content, dict) and 'url' in content:
                                            # For image content
                                            image_url = content.get('url')
                                            image_name = content.get('name', 'Image')
                                            # Strip query params for comparison
                                            clean_url = strip_url_params(image_url)
                                            if clean_url and clean_url not in seen_image_urls:
                                                images.append({'url': image_url, 'name': image_name})
                                                seen_image_urls.add(clean_url)

                                        elif block_type == 'TABLE' and isinstance(content, dict) and 'url' in content:
                                            # For table content
                                            table_url = content.get('url')
                                            table_name = content.get('name', 'Table')
                                            # Strip query params for comparison
                                            clean_url = strip_url_params(table_url)
                                            if clean_url and clean_url not in seen_table_urls:
                                                tables.append({'url': table_url, 'name': table_name})
                                                seen_table_urls.add(clean_url)

                                # Legacy format support for backwards compatibility
                                elif 'data' in data and 'messages' in data['data']:
                                    for msg in data['data']['messages']:
                                        msg_type = msg.get('type')
                                        content = msg.get('content')

                                        if msg_type == 'TEXT' and content:
                                            # For text messages, append to response
                                            if isinstance(content, list) and len(content) > 0:
                                                text = content[0]
                                                response_content += text
                                                print(f"DEBUG - Legacy format - Updating UI with list content: '{text}'")
                                                message_placeholder.markdown(str(response_content))
                                            elif isinstance(content, str):
                                                response_content += content
                                                print(f"DEBUG - Legacy format - Updating UI with string content: '{content}'")
                                                message_placeholder.markdown(str(response_content))

                            except json.JSONDecodeError as e:
                                print(f"DEBUG - JSON decode error for data: {e}")
                        elif line_str.startswith('id:'):
                            # Skip ID lines
                            continue
                        else:
                            # Unknown line format
                            print(f"DEBUG - Unknown line format: {line_str}")

                    except Exception as e:
                        print(f"DEBUG - Exception processing line: {str(e)}")
                        continue

                # Display any images after the text response
                if images:
                    # Clear the placeholder to display the final content without the image markdown
                    # This prevents duplicate images since we've already included the markdown in the response
                    message_placeholder.markdown(str(response_content))

                    # Deduplicate images list before displaying
                    unique_images = []
                    unique_image_urls = set()
                    for image in images:
                        # Strip query params for final deduplication
                        clean_url = strip_url_params(image['url'])
                        if clean_url not in unique_image_urls:
                            unique_images.append(image)
                            unique_image_urls.add(clean_url)

                    # Display the actual images using st.image
                    for image in unique_images:
                        try:
                            st.image(image['url'], caption=image['name'])
                            print(f"DEBUG - Displaying image: {image['name']}")
                        except Exception as e:
                            print(f"DEBUG - Error displaying image: {str(e)}")
                            st.error(f"Failed to load image: {image['name']}")

                # Display any tables after the text response
                # Deduplicate tables list before displaying
                unique_tables = []
                unique_table_urls = set()
                for table in tables:
                    # Strip query params for final deduplication
                    clean_url = strip_url_params(table['url'])
                    if clean_url not in unique_table_urls:
                        unique_tables.append(table)
                        unique_table_urls.add(clean_url)

                for table in unique_tables:
                    st.write(f"**{table['name']}**")
                    try:
                        # Attempt to load the CSV from the URL and display as a table
                        table_data = pd.read_csv(table['url'])
                        st.dataframe(table_data)
                        print(f"DEBUG - Displaying table: {table['name']}")
                    except Exception as e:
                        print(f"DEBUG - Error displaying table: {str(e)}")
                        st.write(f"[View table]({table['url']})")

            except Exception as e:
                error_msg = f"Error processing question: {str(e)}"
                message_placeholder.error(error_msg)
                response_content = error_msg

            # Add assistant message to chat history (text content only)
            st.session_state.chat_history.append({
                'is_user': False,
                'content': response_content
            })

    def _create_new_session(self):
        """Create a new Powerdrill session"""
        try:
            session_name = f"Dataset_{self.dataset_id}_{int(time.time())}"
            response = self.api_client.create_session(session_name)
            if 'data' in response and 'id' in response['data']:
                st.session_state.powerdrill_session_id = response['data']['id']
                if st.session_state.get("debug", False):
                    st.info(f"Created new session: {st.session_state.powerdrill_session_id}")
            else:
                st.warning("Failed to create a session. Some features may not work correctly.")
        except Exception as e:
            st.error(f"Error creating session: {str(e)}")
            st.session_state.powerdrill_session_id = None 