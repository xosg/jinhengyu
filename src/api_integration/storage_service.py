"""
Storage Service Implementation
Supports Mock S3 (free, local filesystem) - easily swappable to AWS S3
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

import yaml

from .base import BaseStorageService


class MockS3Service(BaseStorageService):
    """Mock S3 storage service using local filesystem"""

    def __init__(self, config_path: str = "config/api_config.yaml"):
        """
        Initialize Mock S3 service

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        # Get Mock S3 configuration
        storage_config = self.config.get('storage_service', {})
        mock_config = storage_config.get('mock_s3', {})

        self.base_path = Path(mock_config.get('base_path', 'collected_data/mock_s3'))
        self.create_buckets_auto = mock_config.get('create_buckets_automatically', True)
        self.default_bucket = mock_config.get('default_bucket', 'default-bucket')

        # Settings
        settings = storage_config.get('settings', {})
        self.retry_attempts = settings.get('retry_attempts', 3)
        self.timeout = settings.get('timeout_seconds', 60)
        self.max_file_size_mb = settings.get('max_file_size_mb', 100)

        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Create default bucket if configured
        if self.create_buckets_auto and self.default_bucket:
            self._ensure_bucket_exists(self.default_bucket)

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_file = self.config.get('logging', {}).get('log_file', 'logs/api_call_log.jsonl')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "storage_service",
            "provider": "MockS3",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _ensure_bucket_exists(self, bucket: str):
        """Ensure bucket directory exists"""
        bucket_path = self.base_path / bucket
        bucket_path.mkdir(parents=True, exist_ok=True)
        return bucket_path

    def _get_file_path(self, bucket: str, key: str) -> Path:
        """Get full file path from bucket and key"""
        bucket_path = self.base_path / bucket
        file_path = bucket_path / key
        return file_path

    def upload_file(self, file_path: str, bucket: str, key: str,
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload a file to Mock S3 storage

        Args:
            file_path: Local file path
            bucket: Bucket name
            key: Object key (path in storage)
            metadata: Optional metadata dictionary

        Returns:
            Dictionary with upload result
        """
        source_path = Path(file_path)

        # Validate source file
        if not source_path.exists():
            return {"status": "error", "error": f"Source file not found: {file_path}"}

        # Check file size
        file_size_mb = source_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            return {
                "status": "error",
                "error": f"File too large: {file_size_mb:.2f}MB (max: {self.max_file_size_mb}MB)"
            }

        self._log("upload_file", "started", {
            "file": file_path,
            "bucket": bucket,
            "key": key,
            "size_mb": round(file_size_mb, 2)
        })

        try:
            # Ensure bucket exists
            self._ensure_bucket_exists(bucket)

            # Get destination path
            dest_path = self._get_file_path(bucket, key)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source_path, dest_path)

            # Save metadata if provided
            if metadata:
                metadata_path = dest_path.with_suffix(dest_path.suffix + '.metadata.json')
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)

            # Generate mock URL
            url = f"mock-s3://{bucket}/{key}"

            result = {
                "status": "success",
                "bucket": bucket,
                "key": key,
                "url": url,
                "size_bytes": dest_path.stat().st_size,
                "uploaded_at": datetime.now().isoformat()
            }

            self._log("upload_file", "success", result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "bucket": bucket,
                "key": key,
                "error": str(e)
            }
            self._log("upload_file", "error", error_result)
            return error_result

    def download_file(self, bucket: str, key: str, local_path: str) -> Dict[str, Any]:
        """
        Download a file from Mock S3 storage

        Args:
            bucket: Bucket name
            key: Object key (path in storage)
            local_path: Local file path to save to

        Returns:
            Dictionary with download result
        """
        self._log("download_file", "started", {
            "bucket": bucket,
            "key": key,
            "local_path": local_path
        })

        try:
            # Get source path
            source_path = self._get_file_path(bucket, key)

            if not source_path.exists():
                return {
                    "status": "error",
                    "error": f"File not found: {bucket}/{key}"
                }

            # Copy to local path
            dest_path = Path(local_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)

            result = {
                "status": "success",
                "bucket": bucket,
                "key": key,
                "local_path": str(dest_path),
                "size_bytes": dest_path.stat().st_size
            }

            self._log("download_file", "success", result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "bucket": bucket,
                "key": key,
                "error": str(e)
            }
            self._log("download_file", "error", error_result)
            return error_result

    def delete_file(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Delete a file from Mock S3 storage

        Args:
            bucket: Bucket name
            key: Object key (path in storage)

        Returns:
            Dictionary with delete result
        """
        self._log("delete_file", "started", {
            "bucket": bucket,
            "key": key
        })

        try:
            file_path = self._get_file_path(bucket, key)

            if not file_path.exists():
                return {
                    "status": "error",
                    "error": f"File not found: {bucket}/{key}"
                }

            # Delete file
            file_path.unlink()

            # Delete metadata if exists
            metadata_path = file_path.with_suffix(file_path.suffix + '.metadata.json')
            if metadata_path.exists():
                metadata_path.unlink()

            result = {
                "status": "success",
                "bucket": bucket,
                "key": key,
                "deleted_at": datetime.now().isoformat()
            }

            self._log("delete_file", "success", result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "bucket": bucket,
                "key": key,
                "error": str(e)
            }
            self._log("delete_file", "error", error_result)
            return error_result

    def list_files(self, bucket: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in Mock S3 storage

        Args:
            bucket: Bucket name
            prefix: Optional prefix to filter by

        Returns:
            List of file information dictionaries
        """
        self._log("list_files", "started", {
            "bucket": bucket,
            "prefix": prefix
        })

        try:
            bucket_path = self.base_path / bucket

            if not bucket_path.exists():
                self._log("list_files", "warning", {
                    "bucket": bucket,
                    "message": "Bucket not found"
                })
                return []

            files = []

            # Get all files in bucket
            for file_path in bucket_path.rglob('*'):
                if not file_path.is_file():
                    continue

                # Skip metadata files
                if file_path.suffix == '.json' and '.metadata' in file_path.name:
                    continue

                # Calculate relative key
                relative_path = file_path.relative_to(bucket_path)
                key = str(relative_path).replace('\\', '/')

                # Filter by prefix if specified
                if prefix and not key.startswith(prefix):
                    continue

                # Get file info
                stat = file_path.stat()
                file_info = {
                    "key": key,
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "url": f"mock-s3://{bucket}/{key}"
                }

                files.append(file_info)

            self._log("list_files", "success", {
                "bucket": bucket,
                "prefix": prefix,
                "count": len(files)
            })

            return files

        except Exception as e:
            self._log("list_files", "error", {
                "bucket": bucket,
                "error": str(e)
            })
            return []

    def get_file_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """
        Get a mock presigned URL for file access

        Args:
            bucket: Bucket name
            key: Object key (path in storage)
            expires_in: URL expiration time in seconds (ignored in mock)

        Returns:
            Mock presigned URL string
        """
        # In mock implementation, just return a mock URL
        # Real S3 would generate a time-limited presigned URL
        file_path = self._get_file_path(bucket, key)

        if file_path.exists():
            expires_at = datetime.fromtimestamp(
                datetime.now().timestamp() + expires_in
            ).isoformat()
            return f"mock-s3://{bucket}/{key}?expires={expires_at}"
        else:
            return f"mock-s3://{bucket}/{key}?error=not_found"

    def create_bucket(self, bucket: str) -> Dict[str, Any]:
        """
        Create a new bucket

        Args:
            bucket: Bucket name

        Returns:
            Dictionary with create result
        """
        try:
            bucket_path = self._ensure_bucket_exists(bucket)

            result = {
                "status": "success",
                "bucket": bucket,
                "path": str(bucket_path)
            }

            self._log("create_bucket", "success", result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "bucket": bucket,
                "error": str(e)
            }
            self._log("create_bucket", "error", error_result)
            return error_result


# Factory function to create storage service based on config
def create_storage_service(config_path: str = "config/api_config.yaml") -> BaseStorageService:
    """
    Factory function to create storage service based on configuration

    Args:
        config_path: Path to configuration file

    Returns:
        Storage service instance
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    provider = config.get('storage_service', {}).get('provider', 'MockS3')

    if provider == 'MockS3':
        return MockS3Service(config_path)
    elif provider == 'MinIO':
        from .minio_service import MinIOService
        return MinIOService(config_path)
    # elif provider == 'AWSS3':
    #     return AWSS3Service(config_path)  # Future implementation
    else:
        raise ValueError(f"Unknown storage service provider: {provider}")
