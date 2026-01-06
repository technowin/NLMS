# test_storage.py
import os
import django
import sys

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NLMS.settings')
django.setup()

from services.file_storage_service import FileStorageService
from django.core.files.uploadedfile import SimpleUploadedFile

def test_storage_service():
    print("=== Testing FileStorageService ===")
    
    # Create service
    service = FileStorageService()
    
    # Test 1: Environment detection
    print(f"Environment: {service.environment}")
    print(f"Is Local: {service.is_local}")
    print(f"Is Test: {service.is_test}")
    print(f"Is Production: {service.is_production}")
    
    # Test 2: Create a test file
    test_content = b"This is a test file content for storage service."
    test_file = SimpleUploadedFile(
        "test_file.txt",
        test_content,
        content_type="text/plain"
    )
    
    # Test 3: Save file
    save_path = "test/L01/test_user/Document - 99/test_file.txt"
    saved_path = service.save_file(test_file, save_path)
    print(f"Saved path: {saved_path}")
    
    # Test 4: Check if file exists
    exists = service.file_exists(saved_path)
    print(f"File exists: {exists}")
    
    # Test 5: Get file URL
    file_url = service.get_file_url(saved_path)
    print(f"File URL: {file_url}")
    
    # Test 6: Get file size
    file_size = service.get_file_size(saved_path)
    print(f"File size: {file_size} bytes")
    
    # Test 7: Test with existing data from your database
    print("\n=== Testing with your actual data ===")
    test_paths = [
        "L01/rutuja208/Document - 2/DocScanner Jan 2, 2026 15-09_1(2)_20260102T153602_a514ff72.jpg",
        "L01/Yash327/Document - 2/office_logo1_20260102T105522.png",
        "L01/Yash328/Document - 1/office_logo1_20260105T172203_0b5a54e7.png"
    ]
    
    for path in test_paths:
        url = service.get_file_url(path)
        exists = service.file_exists(path)
        print(f"Path: {path}")
        print(f"  URL: {url}")
        print(f"  Exists: {exists}")
    
    # Test 8: Delete test file
    service.delete_file(saved_path)
    print("\nTest file deleted")
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    test_storage_service()