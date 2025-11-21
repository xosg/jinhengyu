"""
Test MinIO Integration
Quick test to verify MinIO service is working correctly
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

print("=" * 80)
print("MinIO Integration Test")
print("=" * 80)
print()

# Test 1: Check configuration
print("[1/5] Checking configuration...")
try:
    import os
    endpoint = os.getenv('MINIO_ENDPOINT')
    access_key = os.getenv('MINIO_ACCESS_KEY')
    secret_key = os.getenv('MINIO_SECRET_KEY')

    print(f"  - Endpoint: {endpoint}")
    print(f"  - Access Key: {access_key}")
    print(f"  - Secret Key: {'*' * len(secret_key) if secret_key else 'None'}")
    print("  [OK] Configuration loaded")
except Exception as e:
    print(f"  [ERROR] Configuration failed: {e}")
    sys.exit(1)

print()

# Test 2: Import MinIO service
print("[2/5] Importing MinIO service...")
try:
    from src.api_integration.storage_service import create_storage_service
    print("  [OK] MinIO service imported")
except Exception as e:
    print(f"  [ERROR] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Create service instance
print("[3/5] Creating MinIO service instance...")
try:
    storage_service = create_storage_service()
    print(f"  [OK] Service instance created: {type(storage_service).__name__}")
except Exception as e:
    print(f"  [ERROR] Instance creation failed: {e}")
    print()
    print("  HINT: Make sure MinIO server is running!")
    print("        Run: start_minio.bat")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Create test bucket
print("[4/5] Creating test bucket...")
try:
    bucket_name = "test-bucket"
    result = storage_service.create_bucket(bucket_name)

    if result.get("status") == "success":
        print(f"  [OK] Bucket '{bucket_name}' created: {result.get('message')}")
    else:
        print(f"  [ERROR] Bucket creation failed: {result.get('error')}")
        sys.exit(1)
except Exception as e:
    print(f"  [ERROR] Bucket creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 5: Upload test file
print("[5/5] Testing file upload...")
try:
    # Create a simple test file
    test_file = project_root / "test_upload.txt"
    with open(test_file, 'w') as f:
        f.write("MinIO integration test file\n")
        f.write("This file tests the MinIO storage service.\n")

    # Upload file
    result = storage_service.upload_file(
        file_path=str(test_file),
        bucket=bucket_name,
        key="test_files/test_upload.txt"
    )

    if result.get("status") == "success":
        print(f"  [OK] File uploaded successfully")
        print(f"       URL: {result.get('url')}")
        print(f"       Size: {result.get('size_bytes')} bytes")
    else:
        print(f"  [ERROR] File upload failed: {result.get('error')}")
        sys.exit(1)

    # Clean up test file
    test_file.unlink()

except Exception as e:
    print(f"  [ERROR] File upload test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("ALL TESTS PASSED!")
print("=" * 80)
print()
print("MinIO is configured correctly and ready to use.")
print("You can now run: python examples/demo_comprehensive_workflow_enhanced.py")
print()
