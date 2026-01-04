"""
Supabase REST API Client Helper
Handles bucket operations and signed URL generation using REST API.
"""

import os
import requests
import time
from typing import Optional, Tuple
from pathlib import Path


class SupabaseClient:
    """Client for Supabase Storage operations using REST API."""
    
    def __init__(self, url: str, service_key: str):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase project URL (e.g., https://xxxx.supabase.co)
            service_key: Supabase service role key
        """
        self.url = url.rstrip('/')
        self.service_key = service_key
        self.headers = {
            'apikey': service_key,
            'Authorization': f'Bearer {service_key}',
            'Content-Type': 'application/json'
        }
        self.storage_url = f"{self.url}/storage/v1"
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if a bucket exists.
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            True if bucket exists, False otherwise
        """
        try:
            response = requests.get(
                f"{self.storage_url}/bucket/{bucket_name}",
                headers=self.headers
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error checking bucket existence: {e}")
            return False
    
    def create_bucket(self, bucket_name: str, public: bool = False) -> Tuple[bool, str]:
        """
        Create a bucket if it doesn't exist.
        
        Args:
            bucket_name: Name of the bucket
            public: Whether the bucket should be public
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.bucket_exists(bucket_name):
            return True, f"Bucket '{bucket_name}' already exists"
        
        try:
            payload = {
                'name': bucket_name,
                'public': public
            }
            response = requests.post(
                f"{self.storage_url}/bucket",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code in [200, 201]:
                return True, f"Bucket '{bucket_name}' created successfully"
            else:
                error_msg = response.json().get('message', response.text)
                return False, f"Failed to create bucket: {error_msg}"
        except Exception as e:
            return False, f"Error creating bucket: {str(e)}"
    
    def upload_file(self, bucket_name: str, file_path: str, object_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Upload a file to Supabase storage.
        
        Args:
            bucket_name: Name of the bucket
            file_path: Local path to the file
            object_name: Object name in bucket (defaults to filename)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        # Ensure object_name uses forward slashes
        object_name = object_name.replace('\\', '/')
        
        try:
            # Read file in binary mode
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload headers
            upload_headers = {
                'apikey': self.service_key,
                'Authorization': f'Bearer {self.service_key}',
                'Content-Type': 'application/octet-stream',
                'x-upsert': 'true'  # Overwrite if exists
            }
            
            response = requests.post(
                f"{self.storage_url}/object/{bucket_name}/{object_name}",
                headers=upload_headers,
                data=file_data
            )
            
            if response.status_code in [200, 201]:
                return True, f"File uploaded successfully: {object_name}"
            else:
                error_msg = response.json().get('message', response.text) if response.text else "Unknown error"
                return False, f"Upload failed: {error_msg}"
        except Exception as e:
            return False, f"Error uploading file: {str(e)}"
    
    def create_signed_url(self, bucket_name: str, object_name: str, expires_in: int = 7200) -> Tuple[bool, Optional[str], str]:
        """
        Create a signed URL for an object.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            expires_in: Expiration time in seconds (default 7200 = 2 hours)
            
        Returns:
            Tuple of (success: bool, signed_url: Optional[str], message: str)
        """
        # Ensure object_name uses forward slashes
        object_name = object_name.replace('\\', '/')
        
        try:
            # Create signed URL using Supabase REST API
            # Endpoint: POST /storage/v1/object/sign/{bucket}/{path}
            response = requests.post(
                f"{self.storage_url}/object/sign/{bucket_name}/{object_name}",
                headers=self.headers,
                json={'expiresIn': expires_in}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Try different possible response formats
                signed_url = data.get('signedURL') or data.get('signed_url') or data.get('url')
                
                if signed_url:
                    # If signed_url is already a full URL, use it directly
                    # Otherwise, prepend the base URL
                    if signed_url.startswith('http'):
                        full_url = signed_url
                    else:
                        # Ensure signed_url starts with /
                        if not signed_url.startswith('/'):
                            signed_url = '/' + signed_url
                        full_url = f"{self.url}{signed_url}"
                    
                    return True, full_url, "Signed URL created successfully"
                else:
                    return False, None, f"Signed URL not found in response: {data}"
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message') or error_data.get('error') or str(error_data)
                except:
                    error_msg = response.text or f"HTTP {response.status_code}"
                return False, None, f"Failed to create signed URL: {error_msg}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Network error creating signed URL: {str(e)}"
        except Exception as e:
            return False, None, f"Error creating signed URL: {str(e)}"
    
    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        """
        Check if a file exists in the bucket.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            
        Returns:
            True if file exists, False otherwise
        """
        object_name = object_name.replace('\\', '/')
        try:
            response = requests.head(
                f"{self.storage_url}/object/{bucket_name}/{object_name}",
                headers=self.headers
            )
            return response.status_code == 200
        except Exception:
            return False

