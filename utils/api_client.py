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
        return self._make_request("DEL", f"/datasets/{dataset_id}")
    
    # Data source operations
    
    def list_data_sources(self, dataset_id: Optional[str] = None) -> Dict:
        """List data sources, optionally filtered by dataset"""
        params = {}
        if dataset_id:
            params["dataset_id"] = dataset_id
        return self._make_request("GET", "/datasources", params=params)
    
    def create_data_source(self, dataset_id: str, file_path: str, file_name: str) -> Dict:
        """Create a data source by uploading a file"""
        # First create a data source
        data_source = self._make_request(
            "POST",
            "/datasources",
            json_data={
                "dataset_id": dataset_id,
                "source_name": file_name,
                "description": f"Uploaded file: {file_name}",
                "user_id": self.user_id
            }
        )
        
        if 'data' not in data_source or 'id' not in data_source['data']:
            raise Exception("Failed to create data source")
        
        data_source_id = data_source['data']['id']
        
        # Then presign the data source for upload
        presign_response = self._make_request(
            "POST",
            f"/datasources/{data_source_id}/presign",
            json_data={
                "content_type": "application/octet-stream",
                "user_id": self.user_id
            }
        )
        
        if 'data' not in presign_response or 'presigned_url' not in presign_response['data']:
            raise Exception("Failed to get presigned URL")
        
        # Upload the file to the presigned URL
        presigned_url = presign_response['data']['presigned_url']
        
        if self.debug:
            print("\n" + "="*80)
            print(f"POWERDRILL FILE UPLOAD - PUT {presigned_url}")
            print("-"*80)
            print(f"File: {file_path} ({file_name})")
            print(f"Content-Type: application/octet-stream")
            print("-"*80)
        
        with open(file_path, 'rb') as f:
            upload_response = requests.put(
                presigned_url,
                data=f,
                headers={"Content-Type": "application/octet-stream"}
            )
            
            if self.debug:
                print(f"POWERDRILL FILE UPLOAD RESPONSE - Status: {upload_response.status_code}")
                print("="*80 + "\n")
                
            upload_response.raise_for_status()
        
        return data_source
    
    def delete_data_source(self, data_source_id: str) -> Dict:
        """Delete a data source"""
        return self._make_request("DEL", f"/datasources/{data_source_id}")
    
    # Job operations
    
    def create_job(self, dataset_id: str, prompt: str, stream: bool = True) -> Union[Dict, Iterator]:
        """Create a job to analyze data based on prompt"""
        return self._make_request(
            "POST",
            "/jobs",
            json_data={
                "dataset_id": dataset_id,
                "prompt": prompt,
                "stream": stream,
                "user_id": self.user_id
            },
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