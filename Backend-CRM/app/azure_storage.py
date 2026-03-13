"""
Azure Blob Storage service for file upload and retrieval.
"""
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
import asyncio
import logging
from typing import Optional, BinaryIO
from app.config import settings

logger = logging.getLogger(__name__)

class AzureStorageService:
    """Service for Azure Blob Storage operations."""
    
    def __init__(self):
        self._blob_service_client: Optional[BlobServiceClient] = None
        self.container_name = settings.azure_storage_container_name
        
    def get_client(self) -> Optional[BlobServiceClient]:
        """Public method to get or initialize the BlobServiceClient."""
        if not settings.azure_storage_connection_string:
            logger.warning("Azure Storage connection string not configured")
            return None
            
        if not self._blob_service_client:
            try:
                self._blob_service_client = BlobServiceClient.from_connection_string(
                    settings.azure_storage_connection_string
                )
                logger.info("Azure Blob Storage client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Blob Storage client: {e}")
                return None
                
        return self._blob_service_client

    async def _ensure_container_exists(self, client: BlobServiceClient):
        """Ensures the container exists; creates it if it doesn't."""
        container_client = client.get_container_client(self.container_name)
        try:
            # We run this in an executor because the azure-storage-blob SDK is synchronous
            await asyncio.get_event_loop().run_in_executor(None, container_client.get_container_properties)
        except ResourceNotFoundError:
            try:
                await asyncio.get_event_loop().run_in_executor(None, container_client.create_container)
                logger.info(f"Created Azure container: {self.container_name}")
            except ResourceExistsError:
                pass 
        except Exception as e:
            logger.error(f"Error verifying container: {e}")

    async def upload_file(self, file_data: BinaryIO, blob_name: str, content_type: str = None) -> Optional[str]:
        """Upload file to Azure Blob Storage."""
        client = self.get_client()
        if not client:
            return None
            
        try:
            await self._ensure_container_exists(client)
            container_client = client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(blob_name)
            
            content_settings = ContentSettings(content_type=content_type) if content_type else None

            # Ensure stream is at start
            if hasattr(file_data, 'seek'):
                file_data.seek(0)

            # Offload synchronous upload to a thread to keep FastAPI responsive
            await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: blob_client.upload_blob(file_data, overwrite=True, content_settings=content_settings)
            )
            
            # Construct the public URL (or use blob_client.url)
            blob_url = f"https://{client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
            logger.info(f"Successfully uploaded file to Azure: {blob_url}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Error uploading file to Azure: {e}")
            return None
    
    async def download_file(self, blob_name: str) -> Optional[bytes]:
        """Download file from Azure Blob Storage."""
        client = self.get_client()
        if not client:
            return None
            
        try:
            container_client = client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(blob_name)
            
            def _download():
                blob_data = blob_client.download_blob()
                return blob_data.readall()

            file_data = await asyncio.get_event_loop().run_in_executor(None, _download)
            logger.info(f"Successfully downloaded file from Azure: {blob_name}")
            return file_data
            
        except ResourceNotFoundError:
            logger.error(f"Blob not found: {blob_name}")
            return None
        except Exception as e:
            logger.error(f"Error downloading file from Azure: {e}")
            return None
    
    async def delete_file(self, blob_name: str) -> bool:
        """Delete file from Azure Blob Storage."""
        client = self.get_client()
        if not client:
            return False
            
        try:
            container_client = client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(blob_name)
            
            await asyncio.get_event_loop().run_in_executor(None, blob_client.delete_blob)
            logger.info(f"Successfully deleted file from Azure: {blob_name}")
            return True
        except ResourceNotFoundError:
            return True # Already deleted
        except Exception as e:
            logger.error(f"Error deleting file from Azure: {e}")
            return False
    
    def get_blob_url(self, blob_name: str) -> Optional[str]:
        """Get the URL for a blob."""
        client = self.get_client()
        if not client:
            return None
        return f"https://{client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"

# Export singleton instance
azure_storage = AzureStorageService()