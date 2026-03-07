"""
Azure Blob Storage service for file upload and retrieval.
"""
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import AzureError
import logging
from typing import Optional, BinaryIO
from app.config import settings

logger = logging.getLogger(__name__)

class AzureStorageService:
    """Service for Azure Blob Storage operations."""
    
    def __init__(self):
        self.blob_service_client: Optional[BlobServiceClient] = None
        self.container_name = settings.azure_storage_container_name
        
    def _get_client(self) -> Optional[BlobServiceClient]:
        """Get BlobServiceClient if Azure is configured."""
        if not settings.azure_storage_connection_string:
            logger.warning("Azure Storage connection string not configured")
            return None
            
        if not self.blob_service_client:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    settings.azure_storage_connection_string
                )
                logger.info("Azure Blob Storage client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Blob Storage client: {e}")
                return None
                
        return self.blob_service_client
    
    async def upload_file(self, file_data: BinaryIO, blob_name: str, content_type: str = None) -> Optional[str]:
        """
        Upload file to Azure Blob Storage.
        
        Args:
            file_data: File data to upload
            blob_name: Name for the blob in storage
            content_type: MIME type of the file
            
        Returns:
            Blob URL if successful, None if failed
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            # Get container client
            container_client = client.get_container_client(self.container_name)
            
            # Create container if it doesn't exist
            try:
                container_client.create_container()
                logger.info(f"Created Azure container: {self.container_name}")
            except AzureError as e:
                # Container might already exist
                if "ContainerAlreadyExists" not in str(e):
                    logger.error(f"Error creating container: {e}")
                    return None
            
            # Get blob client
            blob_client = container_client.get_blob_client(blob_name)
            
            # Upload file
            content_settings = None
            if content_type:
                from azure.storage.blob import ContentSettings
                content_settings = ContentSettings(content_type=content_type)
            
            blob_client.upload_blob(file_data, overwrite=True, content_settings=content_settings)
            
            # Return blob URL
            blob_url = f"https://{client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
            logger.info(f"Successfully uploaded file to Azure: {blob_url}")
            
            return blob_url
            
        except Exception as e:
            logger.error(f"Error uploading file to Azure: {e}")
            return None
    
    async def download_file(self, blob_name: str) -> Optional[bytes]:
        """
        Download file from Azure Blob Storage.
        
        Args:
            blob_name: Name of the blob to download
            
        Returns:
            File data as bytes if successful, None if failed
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            container_client = client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(blob_name)
            
            print(f"🔍 Azure: Getting blob client for {blob_name}")
            
            # Download blob
            blob_data = blob_client.download_blob()
            file_data = blob_data.readall()
            
            print(f"✅ Azure: Successfully downloaded {len(file_data)} bytes")
            logger.info(f"Successfully downloaded file from Azure: {blob_name}")
            return file_data
            
        except Exception as e:
            logger.error(f"Error downloading file from Azure: {e}")
            print(f"❌ Azure download error: {e}")
            import traceback
            print(f"❌ Azure download traceback: {traceback.format_exc()}")
            return None
    
    async def delete_file(self, blob_name: str) -> bool:
        """
        Delete file from Azure Blob Storage.
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            True if successful, False if failed
        """
        client = self._get_client()
        if not client:
            return False
            
        try:
            container_client = client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(blob_name)
            
            # Delete blob
            blob_client.delete_blob()
            
            logger.info(f"Successfully deleted file from Azure: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from Azure: {e}")
            return False
    
    def get_blob_url(self, blob_name: str) -> Optional[str]:
        """
        Get the URL for a blob.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            Blob URL if Azure is configured, None otherwise
        """
        client = self._get_client()
        if not client:
            return None
            
        return f"https://{client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"

# Global instance
azure_storage = AzureStorageService()
