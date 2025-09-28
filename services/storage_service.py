"""
Storage Service for Google Cloud Storage operations
Handles file upload, download, and management in GCS
"""
import os
import logging
from typing import Optional
from google.cloud import storage
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing files in Google Cloud Storage"""
    
    def __init__(self, bucket_name: str, project_id: Optional[str] = None):
        """
        Initialize StorageService with GCS bucket
        
        Args:
            bucket_name: Name of the GCS bucket
            project_id: Google Cloud project ID (optional, will be inferred from credentials)
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self._client = None
        self._bucket = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Storage client"""
        try:
            # Get credentials file path
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not credentials_path:
                logger.error("GOOGLE_APPLICATION_CREDENTIALS not set")
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is required")
            
            if not os.path.exists(credentials_path):
                logger.error(f"Credentials file not found: {credentials_path}")
                raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
            
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            # Initialize Storage client
            self._client = storage.Client(credentials=credentials, project=self.project_id)
            self._bucket = self._client.bucket(self.bucket_name)
            
            logger.info(f"StorageService initialized successfully with bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize StorageService: {e}")
            raise
    
    async def upload_file(self, file_bytes: bytes, destination_path: str, content_type: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document") -> bool:
        """
        Upload file to Google Cloud Storage
        
        Args:
            file_bytes: File content as bytes
            destination_path: Path where to store the file in the bucket
            content_type: MIME type of the file
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            print(f"☁️ Загружаю в Cloud Storage: {destination_path}")
            
            if not self._bucket:
                print(f"❌ Bucket не инициализирован")
                logger.error("Storage bucket not initialized")
                return False
            
            # Create blob object
            blob = self._bucket.blob(destination_path)
            
            # Set content type
            blob.content_type = content_type
            
            # Upload file
            blob.upload_from_string(file_bytes, content_type=content_type)
            
            print(f"✅ Файл загружен: {destination_path}")
            logger.info(f"File uploaded successfully to: {destination_path}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            logger.error(f"Error uploading file to {destination_path}: {e}")
            return False
    
    async def download_file(self, source_path: str) -> Optional[bytes]:
        """
        Download file from Google Cloud Storage
        
        Args:
            source_path: Path to the file in the bucket
            
        Returns:
            File content as bytes, or None if error
        """
        try:
            if not self._bucket:
                logger.error("Storage bucket not initialized")
                return None
            
            # Get blob object
            blob = self._bucket.blob(source_path)
            
            # Check if blob exists
            if not blob.exists():
                logger.error(f"File not found: {source_path}")
                return None
            
            # Download file content
            file_bytes = blob.download_as_bytes()
            
            logger.info(f"File downloaded successfully from: {source_path}")
            return file_bytes
            
        except Exception as e:
            logger.error(f"Error downloading file from {source_path}: {e}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from Google Cloud Storage
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            if not self._bucket:
                logger.error("Storage bucket not initialized")
                return False
            
            # Get blob object
            blob = self._bucket.blob(file_path)
            
            # Delete file
            blob.delete()
            
            logger.info(f"File deleted successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in Google Cloud Storage
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            if not self._bucket:
                logger.error("Storage bucket not initialized")
                return False
            
            # Get blob object
            blob = self._bucket.blob(file_path)
            
            # Check if blob exists
            return blob.exists()
            
        except Exception as e:
            logger.error(f"Error checking file existence {file_path}: {e}")
            return False
    
    def get_public_url(self, file_path: str) -> Optional[str]:
        """
        Get public URL for a file in the bucket
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            Public URL or None if error
        """
        try:
            if not self._bucket:
                logger.error("Storage bucket not initialized")
                return None
            
            # Get blob object
            blob = self._bucket.blob(file_path)
            
            # Generate signed URL (valid for 1 hour)
            url = blob.generate_signed_url(expiration=3600)
            
            logger.info(f"Generated public URL for: {file_path}")
            return url
            
        except Exception as e:
            logger.error(f"Error generating public URL for {file_path}: {e}")
            return None
