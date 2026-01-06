"""
File Storage Service for handling files in different environments
"""
import os
from django.conf import settings
try:
    from storages.backends.s3boto3 import S3Boto3Storage
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False


class FileStorageService:
    """
    Service to handle file operations for local, test, and production environments
    """
    
    def __init__(self):
        self.environment = getattr(settings, 'ENVIRONMENT', 'local')
        self.is_production = (self.environment == 'production')
        self.is_test = (self.environment == 'test')
        self.is_local = (self.environment == 'local')
        
        # Print debug info
        print(f"[FileStorageService] Environment: {self.environment}")
        print(f"[FileStorageService] MEDIA_ROOT: {settings.MEDIA_ROOT}")
    
    def save_file(self, file, save_path):
        """
        Save file to appropriate storage based on environment
        
        Args:
            file: Django UploadedFile object
            save_path: Relative path where to save (e.g., 'L01/user123/Document - 1/file.pdf')
        
        Returns:
            str: The saved file path (same as input save_path)
        """
        try:
            if self.is_production and S3_AVAILABLE:
                # ========== PRODUCTION: Save to AWS S3 ==========
                print(f"[FileStorageService] Saving to S3: {save_path}")
                
                # Get AWS settings
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
                if not bucket_name:
                    print("[FileStorageService] WARNING: AWS bucket not configured, falling back to local")
                    return self._save_local(file, save_path)
                
                # Get S3 storage
                s3_storage = S3Boto3Storage(
                    bucket_name=bucket_name,
                    location='',  # Store at root of bucket
                    querystring_auth=getattr(settings, 'AWS_QUERYSTRING_AUTH', False),
                    file_overwrite=getattr(settings, 'AWS_S3_FILE_OVERWRITE', False),
                )
                
                # Save to S3
                saved_path = s3_storage.save(save_path, file)
                print(f"[FileStorageService] Saved to S3: {saved_path}")
                
                return saved_path
                
            else:
                # ========== LOCAL/TEST: Save to local filesystem ==========
                return self._save_local(file, save_path)
                
        except Exception as e:
            print(f"[FileStorageService] ERROR saving file: {str(e)}")
            # Fallback to local saving
            return self._save_local(file, save_path)
    
    def _save_local(self, file, save_path):
        """
        Save file to local filesystem (used by local, test, and as fallback)
        """
        # Build full local path
        full_path = os.path.join(settings.MEDIA_ROOT, save_path)
        print(f"[FileStorageService] Saving locally: {full_path}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Save file
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        print(f"[FileStorageService] Saved locally: {save_path}")
        return save_path
    
    def get_file_url(self, file_path):
        """
        Get URL for a file based on environment
        
        Args:
            file_path: Relative file path from database
        
        Returns:
            str: Full URL to access the file
        """
        if not file_path:
            return "#"
        
        try:
            if self.is_production:
                # ========== PRODUCTION: S3 URL ==========
                # Check if already a full URL
                if file_path.startswith(('http://', 'https://')):
                    return file_path
                
                # Get AWS settings
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
                region = getattr(settings, 'AWS_S3_REGION_NAME', 'ap-south-1')
                
                if bucket_name and S3_AVAILABLE:
                    # Clean path (remove leading slash if present)
                    clean_path = file_path.lstrip('/')
                    url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{clean_path}"
                    print(f"[FileStorageService] Generated S3 URL: {url}")
                    return url
                else:
                    # Fallback to local URL if S3 not configured
                    print("[FileStorageService] WARNING: S3 not configured, using local URL")
                    return self._get_local_url(file_path)
                    
            else:
                # ========== LOCAL/TEST: Local URL ==========
                return self._get_local_url(file_path)
                
        except Exception as e:
            print(f"[FileStorageService] ERROR getting URL: {str(e)}")
            return "#"
    
    def _get_local_url(self, file_path):
        """
        Get local file URL (used by local and test environments)
        """
        # Check if already a full URL
        if file_path.startswith(('http://', 'https://')):
            return file_path
        
        # Create local URL
        base_url = getattr(settings, 'MEDIA_URL', '/media/')
        url = f"{base_url.rstrip('/')}/{file_path.lstrip('/')}"
        print(f"[FileStorageService] Generated local URL: {url}")
        return url
    
    def delete_file(self, file_path):
        """
        Delete file from storage
        
        Args:
            file_path: Relative file path
        """
        try:
            if self.is_production and S3_AVAILABLE:
                # Delete from S3
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
                if bucket_name:
                    s3_storage = S3Boto3Storage(bucket_name=bucket_name)
                    s3_storage.delete(file_path)
                    print(f"[FileStorageService] Deleted from S3: {file_path}")
                else:
                    self._delete_local(file_path)
            else:
                # Delete from local
                self._delete_local(file_path)
                    
        except Exception as e:
            print(f"[FileStorageService] ERROR deleting file: {str(e)}")
    
    def _delete_local(self, file_path):
        """
        Delete local file
        """
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"[FileStorageService] Deleted locally: {file_path}")
        else:
            print(f"[FileStorageService] File not found: {full_path}")
    
    def file_exists(self, file_path):
        """
        Check if file exists in storage
        
        Args:
            file_path: Relative file path
        
        Returns:
            bool: True if file exists
        """
        try:
            if self.is_production and S3_AVAILABLE:
                # Check in S3
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
                if bucket_name:
                    s3_storage = S3Boto3Storage(bucket_name=bucket_name)
                    return s3_storage.exists(file_path)
                else:
                    return self._local_exists(file_path)
            else:
                # Check locally
                return self._local_exists(file_path)
                
        except Exception as e:
            print(f"[FileStorageService] ERROR checking file: {str(e)}")
            return False
    
    def _local_exists(self, file_path):
        """
        Check if file exists locally
        """
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        return os.path.exists(full_path)
    
    def get_file_size(self, file_path):
        """
        Get file size in bytes
        
        Args:
            file_path: Relative file path
        
        Returns:
            int: File size in bytes, or 0 if not found
        """
        try:
            if self.is_production and S3_AVAILABLE:
                # Get from S3
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
                if bucket_name:
                    s3_storage = S3Boto3Storage(bucket_name=bucket_name)
                    return s3_storage.size(file_path)
                else:
                    return self._local_size(file_path)
            else:
                # Get locally
                return self._local_size(file_path)
                
        except Exception as e:
            print(f"[FileStorageService] ERROR getting file size: {str(e)}")
            return 0
    
    def _local_size(self, file_path):
        """
        Get local file size
        """
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        if os.path.exists(full_path):
            return os.path.getsize(full_path)
        return 0


# Global instance for convenience
file_storage_service = FileStorageService()