import requests
import json
import time
from typing import Dict, List, Optional, Union, Any, Iterator
import os

class PowerdrillClient:
    def __init__(self, api_endpoint: str, user_id: str, api_key: str, debug: bool = True):
        """
        Initialize the Powerdrill API client
        
        Args:
            api_endpoint: The base API endpoint
            user_id: The user ID for authentication
            api_key: The API key for authentication
            debug: Whether to print debug information for API calls
        """
        # Make sure the api_endpoint doesn't end with a slash
        self.api_endpoint = api_endpoint.rstrip('/')
        self.user_id = user_id
        self.api_key = api_key
        self.debug = debug
        self.headers = {
            "x-pd-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, path: str, params: Dict = None, json_data: Dict = None, stream: bool = False) -> Union[Dict, Iterator]:
        """
        Make an HTTP request to the Powerdrill API
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            path: API path to append to the base endpoint
            params: Query parameters
            json_data: JSON data for POST requests
            stream: Whether to stream the response
            
        Returns:
            Response data as dictionary or iterator if streaming
        """
        # Ensure path starts with a slash
        if not path.startswith('/'):
            path = '/' + path
            
        url = f"{self.api_endpoint}{path}"
        
        # Add user_id to query params if not present
        params = params or {}
        if 'user_id' not in params:
            params['user_id'] = self.user_id
        
        # Debug print request information
        if self.debug:
            print("\n" + "="*80)
            print(f"POWERDRILL API REQUEST - {method} {url}")
            print("-"*80)
            print(f"Headers: {self._sanitize_headers(self.headers)}")
            print(f"Params: {params}")
            if json_data:
                print(f"Body: {json.dumps(json_data, indent=2)}")
            print("-"*80)
            
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                stream=stream
            )
            
            # Debug print response information
            if self.debug:
                print(f"POWERDRILL API RESPONSE - Status: {response.status_code}")
                print("-"*80)
                if not stream:
                    try:
                        resp_json = response.json()
                        print(f"Response: {json.dumps(resp_json, indent=2)}")
                    except:
                        print(f"Response (text): {response.text[:1000]}...")
                else:
                    print("Streaming response (content not shown)")
                print("="*80 + "\n")
            
            # Raise exception for HTTP errors - this will raise HTTPError for 401, 403, etc.
            response.raise_for_status()
            
            if stream:
                return response.iter_lines()
            
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Debug print error information for HTTP errors (including auth failures)
            if self.debug and hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"POWERDRILL API ERROR - Status: {e.response.status_code}")
                    print("-"*80)
                    print(f"Error: {json.dumps(error_data, indent=2)}")
                    print("="*80 + "\n")
                except:
                    pass
            
            # Re-raise the HTTPError for authentication failures
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code in (401, 403):
                    # Authentication error
                    raise
            
            # For other HTTP errors, convert to a generic exception with details
            error_msg = str(e)
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_data = e.response.json()
                    if 'message' in error_data:
                        error_msg = error_data['message']
            except:
                pass
            
            raise Exception(f"API request failed: {error_msg}")
            
        except requests.exceptions.RequestException as e:
            # Handle other request errors
            error_msg = str(e)
            if self.debug:
                print(f"POWERDRILL API ERROR - {error_msg}")
                print("="*80 + "\n")
            
            raise Exception(f"API request failed: {error_msg}")
    
    def _upload_file(self, file_path: str, file_name: str) -> str:
        """
        Upload a file to Powerdrill and get the file_object_key
        
        Args:
            file_path: Path to the file to upload
            file_name: Name of the file
            
        Returns:
            The file_object_key of the uploaded file
        """
        url = f"{self.api_endpoint}/file/upload-datasource"
        
        # Prepare the multipart/form-data payload
        payload = {'user_id': self.user_id}
        
        # Determine content type based on file extension
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext == '.csv':
            content_type = 'text/csv'
        elif file_ext == '.pdf':
            content_type = 'application/pdf'
        elif file_ext == '.json':
            content_type = 'application/json'
        elif file_ext == '.txt':
            content_type = 'text/plain'
        elif file_ext == '.md' or file_ext == '.mdx':
            content_type = 'text/markdown'
        elif file_ext == '.xlsx' or file_ext == '.xls':
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif file_ext == '.docx' or file_ext == '.doc':
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif file_ext == '.pptx' or file_ext == '.ppt':
            content_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        elif file_ext == '.tsv':
            content_type = 'text/tab-separated-values'
        else:
            content_type = 'application/octet-stream'
        
        # Create files parameter for the multipart request
        files = [
            ('file', (file_name, open(file_path, 'rb'), content_type))
        ]
        
        # Modify headers for multipart/form-data (remove Content-Type as it will be set automatically)
        upload_headers = {
            "x-pd-api-key": self.api_key
        }
        
        # Debug information
        if self.debug:
            print("\n" + "="*80)
            print(f"POWERDRILL FILE UPLOAD - POST {url}")
            print("-"*80)
            print(f"Headers: {self._sanitize_headers(upload_headers)}")
            print(f"File: {file_path} ({file_name})")
            print(f"Content-Type: {content_type}")
            print("-"*80)
        
        try:
            response = requests.request("POST", url, headers=upload_headers, data=payload, files=files)
            
            # Debug print response information
            if self.debug:
                print(f"POWERDRILL FILE UPLOAD RESPONSE - Status: {response.status_code}")
                print("-"*80)
                try:
                    resp_json = response.json()
                    print(f"Response: {json.dumps(resp_json, indent=2)}")
                except:
                    print(f"Response (text): {response.text[:1000]}...")
                print("="*80 + "\n")
            
            response.raise_for_status()
            upload_response = response.json()
            
            if 'data' not in upload_response or 'file_object_key' not in upload_response['data']:
                raise Exception("Failed to upload file: Invalid response format")
            
            return upload_response['data']['file_object_key']
            
        except Exception as e:
            error_msg = str(e)
            if self.debug:
                print(f"POWERDRILL FILE UPLOAD ERROR - {error_msg}")
                print("="*80 + "\n")
            raise Exception(f"File upload failed: {error_msg}")
        finally:
            # Close the file
            files[0][1][1].close()
    
    def _sanitize_headers(self, headers: Dict) -> Dict:
        """Sanitize headers to hide sensitive information"""
        sanitized = headers.copy()
        if 'x-pd-api-key' in sanitized:
            api_key = sanitized['x-pd-api-key']
            if api_key and len(api_key) > 8:
                sanitized['x-pd-api-key'] = api_key[:4] + '****' + api_key[-4:]
            else:
                sanitized['x-pd-api-key'] = '********'
        return sanitized
    
    # Dataset operations
    
    def create_dataset(self, name: str, description: str = "") -> Dict:
        """Create a new dataset"""
        return self._make_request(
            "POST", 
            "/datasets",
            json_data={
                "name": name,
                "description": description,
                "user_id": self.user_id
            }
        )
    
    def list_datasets(self) -> Dict:
        """List all available datasets"""
        # Following the exact format shown in the example:
        # https://ai.data.cloud/api/v2/team/datasets?user_id=tmm-dafasdfasdfasdf
        return self._make_request("GET", "/datasets")
    
    def get_dataset_overview(self, dataset_id: str) -> Dict:
        """Get dataset overview including recommended questions"""
        return self._make_request("GET", f"/datasets/{dataset_id}/overview")
    
    def get_dataset_status(self, dataset_id: str) -> Dict:
        """Get status summary of data sources in dataset"""
        return self._make_request("GET", f"/datasets/{dataset_id}/status")
    
    def delete_dataset(self, dataset_id: str) -> Dict:
        """Delete a dataset"""
        return self._make_request(
            "DELETE", 
            f"/datasets/{dataset_id}", 
            json_data={"user_id": self.user_id}
        )
    
    # Data source operations
    
    def list_data_sources(self, dataset_id: Optional[str] = None) -> Dict:
        """
        List data sources in the specified dataset
        
        Args:
            dataset_id: The dataset ID to list data sources from
            
        Returns:
            Dict containing the list of data sources
        """
        if not dataset_id:
            raise ValueError("Dataset ID is required to list data sources")
            
        # The correct endpoint should be /datasets/{id}/datasources
        return self._make_request("GET", f"/datasets/{dataset_id}/datasources")
    
    def create_data_source(self, dataset_id: str, file_path: str, file_name: str) -> Dict:
        """
        Create a data source by uploading a file
        
        This is a two-step process:
        1. Upload the file using multipart/form-data to get file_object_key
        2. Create a data source using the file_object_key
        
        Args:
            dataset_id: The dataset ID to create the data source in
            file_path: Path to the file to upload
            file_name: Name of the file
            
        Returns:
            The created data source information
        """
        # Step 1: Upload the file to get file_object_key
        file_object_key = self._upload_file(file_path, file_name)
        
        # Step 2: Create a data source using the file_object_key
        return self._make_request(
            "POST",
            f"/datasets/{dataset_id}/datasources",
            json_data={
                "name": file_name,
                "type": "FILE",
                "user_id": self.user_id,
                "file_object_key": file_object_key
            }
        )
    
    def delete_data_source(self, data_source_id: str, dataset_id: str) -> Dict:
        """
        Delete a data source
        
        Args:
            data_source_id: The ID of the data source to delete
            dataset_id: The ID of the dataset that contains the data source
            
        Returns:
            Response from the API
        """
        return self._make_request("DEL", f"/datasets/{dataset_id}/datasources/{data_source_id}")
    
    # Session operations
    
    def create_session(self, session_name: str, output_language: str = "AUTO", job_mode: str = "AUTO", max_contextual_job_history: int = 10) -> Dict:
        """
        Create a session for continuous interaction
        
        Args:
            session_name: Name for the session
            output_language: Language for the output (e.g., AUTO, EN, FR)
            job_mode: Job mode (AUTO or DATA_ANALYTICS)
            max_contextual_job_history: Max number of recent jobs retained as context
            
        Returns:
            Dict containing the session ID
        """
        return self._make_request(
            "POST",
            "/sessions",
            json_data={
                "name": session_name,
                "user_id": self.user_id,
                "output_language": output_language,
                "job_mode": job_mode,
                "max_contextual_job_history": max_contextual_job_history,
                "agent_id": "DATA_ANALYSIS_AGENT"
            }
        )
    
    def get_session(self, session_id: str) -> Dict:
        """
        Get session details
        
        Args:
            session_id: The session ID
            
        Returns:
            Dict containing session details
        """
        return self._make_request("GET", f"/sessions/{session_id}")
    
    def list_sessions(self) -> Dict:
        """
        List all sessions
        
        Returns:
            Dict containing the list of sessions
        """
        return self._make_request("GET", "/sessions")
    
    # Job operations
    
    def create_job(self, dataset_id: str, prompt: str, stream: bool = True, session_id: str = None, datasource_ids: List[str] = None) -> Union[Dict, Iterator]:
        """
        Create a job to analyze data based on prompt/question
        
        Args:
            dataset_id: The dataset ID
            prompt: The question or prompt to analyze data
            stream: Whether to stream the response
            session_id: Session ID (required for API v2)
            datasource_ids: Optional list of specific data source IDs to use
            
        Returns:
            Response from the API or a stream iterator
        """
        # If no session_id provided, create a new session
        if not session_id:
            session_name = f"Session_{int(time.time())}"
            session_response = self.create_session(session_name)
            session_id = session_response['data']['id']
            if self.debug:
                print(f"Created new session: {session_id}")
        
        # Prepare the request payload
        json_data = {
            "dataset_id": dataset_id,
            "question": prompt,  # API expects 'question' rather than 'prompt'
            "session_id": session_id,  # Session ID is required
            "stream": stream,
            "user_id": self.user_id,
            "output_language": "AUTO",
            "job_mode": "AUTO"
        }
        
        # Add optional parameters if provided
        if datasource_ids:
            json_data["datasource_ids"] = datasource_ids
            
        return self._make_request(
            "POST",
            "/jobs",
            json_data=json_data,
            stream=stream
        )
    
    # Data source status polling
    
    def wait_for_dataset_ready(self, dataset_id: str, timeout: int = 300, interval: int = 5) -> bool:
        """
        Poll dataset status until all data sources are synchronized or timeout
        
        Args:
            dataset_id: The dataset ID to check
            timeout: Maximum time to wait in seconds
            interval: Polling interval in seconds
            
        Returns:
            True if all data sources are synchronized, False if timeout
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            status = self.get_dataset_status(dataset_id)
            
            if 'data' in status:
                data = status['data']
                if data.get('invalid_count', 0) == 0 and data.get('synching_count', 0) == 0:
                    return True
            
            time.sleep(interval)
        
        return False 