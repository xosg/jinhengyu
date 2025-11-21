# MinIO Setup Guide

## Overview

This project now uses MinIO as the storage backend instead of mock S3. MinIO is an S3-compatible object storage system that runs locally on your machine.

**Important**: This project uses the **MinIO Community Edition** (GNU AGPLv3 license), which is free and open source. The Enterprise version that was previously included has been replaced with the Community Edition in `minio.exe`. The Enterprise version is backed up as `minio_enterprise_backup.exe` if needed.

## Quick Start

### 1. Start MinIO Server

```bash
start_minio.bat
```

This will:
- Create a `minio_data` directory for storage
- Start MinIO server on `localhost:9000`
- Start MinIO console on `localhost:9001`
- Use default credentials: `minioadmin` / `minioadmin`

### 2. Access MinIO Console (Optional)

Open your browser and go to: **http://localhost:9001**

- Username: `minioadmin`
- Password: `minioadmin`

The console lets you browse buckets, upload/download files, and manage storage visually.

### 3. Run Your Application

```bash
python examples/demo_comprehensive_workflow_enhanced.py
```

The application will automatically connect to MinIO and create buckets as needed.

### 4. Stop MinIO Server

```bash
stop_minio.bat
```

Or press `Ctrl+C` in the MinIO server window.

## Utility Scripts

- **`start_minio.bat`** - Start MinIO server
- **`stop_minio.bat`** - Stop MinIO server
- **`check_minio.bat`** - Check if MinIO is running

## Configuration

MinIO configuration is stored in:

### `.env` file
```
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### `config/api_config.yaml`
```yaml
storage_service:
  provider: "MinIO"

  minio:
    endpoint: "${ENV:MINIO_ENDPOINT}"
    access_key: "${ENV:MINIO_ACCESS_KEY}"
    secret_key: "${ENV:MINIO_SECRET_KEY}"
    secure: false
    create_buckets_automatically: true
    default_bucket: "research-reports"
```

## Switching Back to Mock S3

If you want to switch back to the filesystem-based mock S3:

1. Edit `config/api_config.yaml`
2. Change `provider: "MinIO"` to `provider: "MockS3"`
3. Restart your application

## Python Dependencies

The MinIO Python client is required:

```bash
pip install minio
```

## Data Storage

- **MinIO data**: Stored in `minio_data/` directory
- **Mock S3 data**: Stored in `collected_data/mock_s3/` directory

## Troubleshooting

### MinIO won't start

1. Check if MinIO is already running: `check_minio.bat`
2. Stop existing instance: `stop_minio.bat`
3. Try starting again: `start_minio.bat`

### Connection errors in application

1. Verify MinIO is running: `check_minio.bat`
2. Check `.env` file has correct endpoint: `localhost:9000`
3. Ensure firewall isn't blocking port 9000

### Can't access console

1. Open http://localhost:9001 in browser
2. Login with `minioadmin` / `minioadmin`
3. If port 9001 is busy, MinIO will use a different port (check console output)

## Benefits of MinIO

✓ True S3-compatible API (easy migration to AWS S3 later)
✓ Web-based management console
✓ Better performance than filesystem mock
✓ Presigned URLs for secure file sharing
✓ Bucket versioning and lifecycle policies
✓ Works offline (no internet required)

## Architecture

```
┌──────────────────────────┐
│ Your Application         │
│ (Python)                 │
└────────┬─────────────────┘
         │ MinIO Client
         │ (S3 API)
         ▼
┌──────────────────────────┐
│ MinIO Server             │
│ localhost:9000           │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ minio_data/              │
│ (File Storage)           │
└──────────────────────────┘
```

## Security Notes

**Default credentials are for development only!**

For production use:
1. Change `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` in `.env`
2. Set `secure: true` in `api_config.yaml` to use HTTPS
3. Configure proper access policies in MinIO console

## References

- MinIO Official Documentation: https://min.io/docs/minio/windows/index.html
- MinIO Python Client: https://min.io/docs/minio/linux/developers/python/minio-py.html
