"""
MinIO Storage Service Implementation
S3-compatible object storage for local/private cloud deployment
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import yaml
from minio import Minio
from minio.error import S3Error

from .base import BaseStorageService


class MinIOService(BaseStorageService):
    """MinIO storage service - S3-compatible object storage"""

    def __init__(self, config_path: str = "config/api_config.yaml"):
        """
        Initialize MinIO service

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        # Get MinIO configuration
        storage_config = self.config.get('storage_service', {})
        minio_config = storage_config.get('minio', {})

        # MinIO connection parameters
        endpoint = os.getenv('MINIO_ENDPOINT', minio_config.get('endpoint', 'localhost:9000'))
        access_key = os.getenv('MINIO_ACCESS_KEY', minio_config.get('access_key', ''))
        secret_key = os.getenv('MINIO_SECRET_KEY', minio_config.get('secret_key', ''))
        secure = minio_config.get('secure', False)

        # Store endpoint for URL generation
        self.endpoint = endpoint
        self.secure = secure

        # Settings
        settings = storage_config.get('settings', {})
        self.retry_attempts = settings.get('retry_attempts', 3)
        self.timeout = settings.get('timeout_seconds', 60)
        self.max_file_size_mb = settings.get('max_file_size_mb', 100)
        self.default_bucket = minio_config.get('default_bucket', 'default-bucket')
        self.create_buckets_auto = minio_config.get('create_buckets_automatically', True)

        # Initialize MinIO client
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )

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
            "provider": "MinIO",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _ensure_bucket_exists(self, bucket: str):
        """Ensure bucket exists, create if it doesn't"""
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                self._log("create_bucket", "success", {"bucket": bucket})
        except S3Error as e:
            self._log("create_bucket", "error", {
                "bucket": bucket,
                "error": str(e)
            })
            raise

    def upload_file(self, file_path: str, bucket: str, key: str,
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload a file to MinIO storage

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

            # Upload file
            file_size = source_path.stat().st_size

            # Determine content type
            content_type = "application/octet-stream"
            if source_path.suffix.lower() == '.pdf':
                content_type = "application/pdf"
            elif source_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                content_type = f"image/{source_path.suffix[1:].lower()}"
            elif source_path.suffix.lower() == '.json':
                content_type = "application/json"

            # Upload to MinIO
            self.client.fput_object(
                bucket,
                key,
                str(source_path),
                content_type=content_type,
                metadata=metadata
            )

            # Generate URL
            protocol = "https" if self.secure else "http"
            url = f"{protocol}://{self.endpoint}/{bucket}/{key}"

            result = {
                "status": "success",
                "bucket": bucket,
                "key": key,
                "url": url,
                "size_bytes": file_size,
                "uploaded_at": datetime.now().isoformat()
            }

            self._log("upload_file", "success", result)
            return result

        except S3Error as e:
            error_result = {
                "status": "error",
                "bucket": bucket,
                "key": key,
                "error": str(e)
            }
            self._log("upload_file", "error", error_result)
            return error_result
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
        Download a file from MinIO storage

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
            # Ensure local directory exists
            dest_path = Path(local_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Download from MinIO
            self.client.fget_object(bucket, key, str(dest_path))

            result = {
                "status": "success",
                "bucket": bucket,
                "key": key,
                "local_path": str(dest_path),
                "size_bytes": dest_path.stat().st_size
            }

            self._log("download_file", "success", result)
            return result

        except S3Error as e:
            error_result = {
                "status": "error",
                "bucket": bucket,
                "key": key,
                "error": str(e)
            }
            self._log("download_file", "error", error_result)
            return error_result
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
        Delete a file from MinIO storage

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
            # Delete object from MinIO
            self.client.remove_object(bucket, key)

            result = {
                "status": "success",
                "bucket": bucket,
                "key": key,
                "deleted_at": datetime.now().isoformat()
            }

            self._log("delete_file", "success", result)
            return result

        except S3Error as e:
            error_result = {
                "status": "error",
                "bucket": bucket,
                "key": key,
                "error": str(e)
            }
            self._log("delete_file", "error", error_result)
            return error_result
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
        List files in MinIO storage

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
            # List objects in bucket
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)

            files = []
            for obj in objects:
                protocol = "https" if self.secure else "http"
                file_info = {
                    "key": obj.object_name,
                    "size_bytes": obj.size,
                    "size_mb": round(obj.size / (1024 * 1024), 2),
                    "modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "etag": obj.etag,
                    "url": f"{protocol}://{self.endpoint}/{bucket}/{obj.object_name}"
                }
                files.append(file_info)

            self._log("list_files", "success", {
                "bucket": bucket,
                "prefix": prefix,
                "count": len(files)
            })

            return files

        except S3Error as e:
            self._log("list_files", "error", {
                "bucket": bucket,
                "error": str(e)
            })
            return []
        except Exception as e:
            self._log("list_files", "error", {
                "bucket": bucket,
                "error": str(e)
            })
            return []

    def get_file_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """
        Get a presigned URL for file access

        Args:
            bucket: Bucket name
            key: Object key (path in storage)
            expires_in: URL expiration time in seconds

        Returns:
            Presigned URL string
        """
        try:
            # Generate presigned URL
            url = self.client.presigned_get_object(
                bucket,
                key,
                expires=timedelta(seconds=expires_in)
            )
            return url
        except S3Error as e:
            self._log("get_file_url", "error", {
                "bucket": bucket,
                "key": key,
                "error": str(e)
            })
            return f"error: {str(e)}"
        except Exception as e:
            self._log("get_file_url", "error", {
                "bucket": bucket,
                "key": key,
                "error": str(e)
            })
            return f"error: {str(e)}"

    def create_bucket(self, bucket: str) -> Dict[str, Any]:
        """
        Create a new bucket

        Args:
            bucket: Bucket name

        Returns:
            Dictionary with create result
        """
        try:
            # Check if bucket already exists
            if self.client.bucket_exists(bucket):
                result = {
                    "status": "success",
                    "bucket": bucket,
                    "message": "Bucket already exists"
                }
            else:
                # Create bucket
                self.client.make_bucket(bucket)
                result = {
                    "status": "success",
                    "bucket": bucket,
                    "message": "Bucket created successfully"
                }

            self._log("create_bucket", "success", result)
            return result

        except S3Error as e:
            error_result = {
                "status": "error",
                "bucket": bucket,
                "error": str(e)
            }
            self._log("create_bucket", "error", error_result)
            return error_result
        except Exception as e:
            error_result = {
                "status": "error",
                "bucket": bucket,
                "error": str(e)
            }
            self._log("create_bucket", "error", error_result)
            return error_result
