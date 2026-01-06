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
        
        # ✅ Get base path from settings
        self.base_path = getattr(settings, 'S3_BASE_PATH', '')
        
        # ✅ Store S3_AVAILABLE as instance variable
        try:
            from storages.backends.s3boto3 import S3Boto3Storage
            self.S3_AVAILABLE = True
            self.S3Boto3Storage = S3Boto3Storage
        except ImportError:
            self.S3_AVAILABLE = False
            self.S3Boto3Storage = None
        
        # Debug info
        print(f"[FileStorageService] Environment: {self.environment}")
        print(f"[FileStorageService] S3 Available: {self.S3_AVAILABLE}")
        print(f"[FileStorageService] Base Path: '{self.base_path}'")
        
    def _prepare_path(self, path, add_base=True):
        """
        Prepare path with base path if needed
        """
        if not path:
            return path
        
        # ✅ NORMALIZE PATH SEPARATORS FIRST
        path = self._normalize_path_separators(path)
        
        # Clean the path (remove leading slash)
        path = path.lstrip('/')
        
        # Debug
        print(f"  [_prepare_path] Input (normalized): '{path}', add_base: {add_base}")
        print(f"  [_prepare_path] Base path: '{self.base_path}'")
        
        # Remove base path if it's already there (for consistency)
        if self.base_path and path.startswith(self.base_path):
            path = path[len(self.base_path):]
            print(f"  [_prepare_path] Removed base path: '{path}'")
        
        # Add base path if needed
        if add_base and self.base_path and not path.startswith(self.base_path):
            path = self.base_path + path
            print(f"  [_prepare_path] Added base path: '{path}'")
        
        print(f"  [_prepare_path] Final: '{path}'")
        return path
    
    def _normalize_path_for_db(self, path):
        """
        Normalize path for database storage
        Returns path without environment-specific prefixes
        """
        if not path:
            return path
        
        # ✅ NORMALIZE PATH SEPARATORS FIRST
        path = self._normalize_path_separators(path)
        
        path = path.lstrip('/')
        
        # Remove base path if present
        if self.base_path and path.startswith(self.base_path):
            return path[len(self.base_path):]
        
        return path
    
    def save_file(self, file, save_path):
        """
        Save file and return normalized path for database
        """
        print(f"\n=== DEBUG FileStorageService.save_file ===")
        print(f"Environment: {self.environment}")
        print(f"Original path: {save_path}")
        
        # Prepare path for storage
        storage_path = self._prepare_path(save_path, add_base=True)
        print(f"Storage path: {storage_path}")
        
        try:
            # ✅ Changed: Use self.S3_AVAILABLE instead of S3_AVAILABLE
            if self.is_production and self.S3_AVAILABLE:
                # Save to S3
                s3_storage = self.S3Boto3Storage()
                saved_path = s3_storage.save(storage_path, file)
                print(f"Saved to S3: {saved_path}")
                
                # Return normalized path for DB
                normalized = self._normalize_path_for_db(saved_path)
                print(f"Normalized for DB: {normalized}")
                return normalized
                
            else:
                # Save locally
                saved_path = self._save_local(file, storage_path)
                print(f"Saved locally: {saved_path}")
                
                # Return normalized path for DB
                normalized = self._normalize_path_for_db(saved_path)
                print(f"Normalized for DB: {normalized}")
                return normalized
                
        except Exception as e:
            print(f"Error: {e}")
            saved_path = self._save_local(file, storage_path)
            return self._normalize_path_for_db(saved_path)
    
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
        """
        if not file_path:
            return "#"
        
        try:
            # Prepare path for current environment
            file_path = self._prepare_path(file_path, add_base=True)
            
            if self.is_production:
                # ========== PRODUCTION: Generate Signed S3 URL ==========
                # Check if already a full URL
                if file_path.startswith(('http://', 'https://')):
                    return file_path
                
                # Get AWS settings
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
                region = getattr(settings, 'AWS_S3_REGION_NAME', 'ap-south-1')
                
                # ✅ Changed: Use self.S3_AVAILABLE instead of S3_AVAILABLE
                if bucket_name and self.S3_AVAILABLE:
                    # Generate signed URL (expires in 1 hour)
                    import boto3
                    from botocore.exceptions import ClientError
                    
                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
                        aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
                        region_name=region
                    )
                    
                    try:
                        # Generate signed URL that expires in 1 hour (3600 seconds)
                        signed_url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={
                                'Bucket': bucket_name,
                                'Key': file_path
                            },
                            ExpiresIn=3600  # 1 hour
                        )
                        
                        print(f"[FileStorageService] Generated signed S3 URL: {signed_url}")
                        return signed_url
                        
                    except ClientError as e:
                        print(f"[FileStorageService] Error generating signed URL: {e}")
                        # Fallback to regular URL (will fail if bucket is private)
                        return f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_path}"
                else:
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
    
    def _local_exists(self, file_path):
        """
        Check if file exists locally
        """
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        return os.path.exists(full_path)
    
    def _local_size(self, file_path):
        """
        Get local file size
        """
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        if os.path.exists(full_path):
            return os.path.getsize(full_path)
        return 0

    def delete_file(self, file_path):
        """
        Delete file from storage
        """
        try:
            # ✅ Prepare path with base path
            file_path = self._prepare_path(file_path, add_base=True)
            
            # ✅ Changed: Use self.S3_AVAILABLE instead of S3_AVAILABLE
            if self.is_production and self.S3_AVAILABLE:
                # Delete from S3
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
                if bucket_name:
                    s3_storage = self.S3Boto3Storage(bucket_name=bucket_name)
                    s3_storage.delete(file_path)
                    print(f"[FileStorageService] Deleted from S3: {file_path}")
                else:
                    self._delete_local(file_path)
            else:
                # Delete from local
                self._delete_local(file_path)
                    
        except Exception as e:
            print(f"[FileStorageService] ERROR deleting file: {str(e)}")

    def file_exists(self, file_path):
        """
        Check if file exists in storage
        """
        try:
            # ✅ Prepare path with base path
            file_path = self._prepare_path(file_path, add_base=True)
            
            # ✅ Changed: Use self.S3_AVAILABLE instead of S3_AVAILABLE
            if self.is_production and self.S3_AVAILABLE:
                # Check in S3
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
                if bucket_name:
                    s3_storage = self.S3Boto3Storage(bucket_name=bucket_name)
                    return s3_storage.exists(file_path)
                else:
                    return self._local_exists(file_path)
            else:
                # Check locally
                return self._local_exists(file_path)
                
        except Exception as e:
            print(f"[FileStorageService] ERROR checking file: {str(e)}")
            return False

    def get_file_size(self, file_path):
        """
        Get file size in bytes
        """
        try:
            # ✅ Prepare path with base path
            file_path = self._prepare_path(file_path, add_base=True)
            
            # ✅ Changed: Use self.S3_AVAILABLE instead of S3_AVAILABLE
            if self.is_production and self.S3_AVAILABLE:
                # Get from S3
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
                if bucket_name:
                    s3_storage = self.S3Boto3Storage(bucket_name=bucket_name)
                    return s3_storage.size(file_path)
                else:
                    return self._local_size(file_path)
            else:
                # Get locally
                return self._local_size(file_path)
                
        except Exception as e:
            print(f"[FileStorageService] ERROR getting file size: {str(e)}")
            return 0
    
    def _normalize_path_separators(self, path):
        """
        Normalize path separators to forward slashes
        Always use forward slashes for consistency
        """
        if not path:
            return path
        
        # Replace backslashes with forward slashes
        path = path.replace('\\', '/')
        
        # Remove any duplicate slashes
        while '//' in path:
            path = path.replace('//', '/')
        
        # Ensure no leading slash (for consistency)
        path = path.lstrip('/')
        
        return path
# Global instance for convenience
file_storage_service = FileStorageService()