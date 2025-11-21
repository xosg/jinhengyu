"""
Attachment Handler Module
Classifies and organizes files by type
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

import yaml
import filetype


class AttachmentHandler:
    """Handle file classification and organization"""

    def __init__(self, config_path: str = "config/collection_config.yaml"):
        """
        Initialize attachment handler with configuration

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        # File type categories
        self.type_categories = {
            'pdf': ['pdf'],
            'excel': ['xlsx', 'xls', 'xlsm', 'xlsb'],
            'word': ['docx', 'doc', 'docm'],
            'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'],
            'archives': ['zip', 'rar', '7z', 'tar', 'gz'],
            'text': ['txt', 'csv', 'log', 'md'],
            'other': []
        }

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_file = self.config.get('logging', {}).get('log_file', 'logs/collection_log.jsonl')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "attachment_handler",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def classify_file(self, file_path: str) -> str:
        """
        Classify file by type

        Args:
            file_path: Path to file

        Returns:
            Category name (e.g., 'pdf', 'excel', 'images', 'other')
        """
        file_path = Path(file_path)

        # First try by extension
        extension = file_path.suffix.lstrip('.').lower()

        for category, extensions in self.type_categories.items():
            if extension in extensions:
                return category

        # Try using filetype library (magic number detection)
        try:
            kind = filetype.guess(str(file_path))
            if kind is not None:
                mime = kind.mime
                if 'pdf' in mime:
                    return 'pdf'
                elif 'image' in mime:
                    return 'images'
                elif 'zip' in mime or 'compressed' in mime:
                    return 'archives'
        except:
            pass

        return 'other'

    def organize_files(self, source_dir: str, output_dir: str = None,
                      organize_by_type: bool = True) -> Dict[str, Any]:
        """
        Organize files from source directory into categorized folders

        Args:
            source_dir: Source directory containing files
            output_dir: Output directory (if None, organize in place)
            organize_by_type: Whether to create subdirectories by file type

        Returns:
            Dictionary with organization results
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        # Use source directory if output not specified
        if output_dir is None:
            output_dir = source_dir
        output_path = Path(output_dir)

        self._log("organize_files", "started", {
            "source_dir": str(source_path),
            "output_dir": str(output_path),
            "organize_by_type": organize_by_type
        })

        results = {
            "total_files": 0,
            "organized": 0,
            "failed": 0,
            "by_category": {},
            "details": []
        }

        try:
            # Find all files in source directory
            files = [f for f in source_path.rglob('*') if f.is_file()]
            results["total_files"] = len(files)

            for file_path in files:
                try:
                    # Classify file
                    category = self.classify_file(file_path)

                    # Determine destination
                    if organize_by_type:
                        dest_dir = output_path / category
                        dest_dir.mkdir(parents=True, exist_ok=True)
                    else:
                        dest_dir = output_path

                    # Copy or move file
                    dest_file = dest_dir / file_path.name

                    # Handle filename conflicts
                    counter = 1
                    while dest_file.exists() and dest_file != file_path:
                        stem = file_path.stem
                        suffix = file_path.suffix
                        dest_file = dest_dir / f"{stem}_{counter}{suffix}"
                        counter += 1

                    # Only copy if different location
                    if dest_file != file_path:
                        shutil.copy2(file_path, dest_file)

                    # Update results
                    results["organized"] += 1
                    if category not in results["by_category"]:
                        results["by_category"][category] = 0
                    results["by_category"][category] += 1

                    results["details"].append({
                        "file": file_path.name,
                        "category": category,
                        "destination": str(dest_file)
                    })

                    self._log("organize_file", "success", {
                        "file": file_path.name,
                        "category": category,
                        "destination": str(dest_file)
                    })

                except Exception as e:
                    results["failed"] += 1
                    self._log("organize_file", "error", {
                        "file": str(file_path),
                        "error": str(e)
                    })

            self._log("organize_files", "completed", {
                "total_files": results["total_files"],
                "organized": results["organized"],
                "failed": results["failed"]
            })

            return results

        except Exception as e:
            self._log("organize_files", "error", {"error": str(e)})
            raise

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file information
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Basic file stats
        stat = file_path.stat()

        info = {
            "name": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "extension": file_path.suffix.lstrip('.').lower(),
            "category": self.classify_file(file_path),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

        # Try to detect MIME type
        try:
            kind = filetype.guess(str(file_path))
            if kind is not None:
                info["mime_type"] = kind.mime
                info["detected_extension"] = kind.extension
        except:
            pass

        return info

    def filter_files_by_type(self, directory: str, file_types: List[str]) -> List[Path]:
        """
        Filter files in directory by type

        Args:
            directory: Directory to search
            file_types: List of file extensions (e.g., ['pdf', 'xlsx'])

        Returns:
            List of matching file paths
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        matching_files = []

        for file_path in dir_path.rglob('*'):
            if not file_path.is_file():
                continue

            extension = file_path.suffix.lstrip('.').lower()
            if extension in file_types:
                matching_files.append(file_path)

        return matching_files

    def create_file_inventory(self, directory: str, output_file: str = None) -> Dict[str, Any]:
        """
        Create inventory of all files in directory

        Args:
            directory: Directory to inventory
            output_file: Optional JSON file to save inventory

        Returns:
            Dictionary with inventory data
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        self._log("create_inventory", "started", {"directory": str(dir_path)})

        inventory = {
            "directory": str(dir_path),
            "created_at": datetime.now().isoformat(),
            "total_files": 0,
            "total_size_mb": 0,
            "by_category": {},
            "files": []
        }

        try:
            for file_path in dir_path.rglob('*'):
                if not file_path.is_file():
                    continue

                file_info = self.get_file_info(file_path)
                inventory["files"].append(file_info)
                inventory["total_files"] += 1
                inventory["total_size_mb"] += file_info["size_mb"]

                # Count by category
                category = file_info["category"]
                if category not in inventory["by_category"]:
                    inventory["by_category"][category] = {
                        "count": 0,
                        "total_size_mb": 0
                    }
                inventory["by_category"][category]["count"] += 1
                inventory["by_category"][category]["total_size_mb"] += file_info["size_mb"]

            inventory["total_size_mb"] = round(inventory["total_size_mb"], 2)

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(inventory, f, indent=2, ensure_ascii=False)

            self._log("create_inventory", "success", {
                "directory": str(dir_path),
                "total_files": inventory["total_files"],
                "total_size_mb": inventory["total_size_mb"]
            })

            return inventory

        except Exception as e:
            self._log("create_inventory", "error", {"error": str(e)})
            raise

    def cleanup_duplicates(self, directory: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Find and optionally remove duplicate files

        Args:
            directory: Directory to check
            dry_run: If True, only report duplicates without deleting

        Returns:
            Dictionary with duplicate information
        """
        import hashlib

        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        self._log("cleanup_duplicates", "started", {
            "directory": str(dir_path),
            "dry_run": dry_run
        })

        # Calculate file hashes
        file_hashes = {}
        for file_path in dir_path.rglob('*'):
            if not file_path.is_file():
                continue

            try:
                # Calculate MD5 hash
                hasher = hashlib.md5()
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
                file_hash = hasher.hexdigest()

                if file_hash not in file_hashes:
                    file_hashes[file_hash] = []
                file_hashes[file_hash].append(file_path)
            except:
                continue

        # Find duplicates
        duplicates = {h: files for h, files in file_hashes.items() if len(files) > 1}

        results = {
            "total_files_checked": sum(len(files) for files in file_hashes.values()),
            "duplicate_groups": len(duplicates),
            "duplicate_files": sum(len(files) - 1 for files in duplicates.values()),
            "dry_run": dry_run,
            "groups": []
        }

        # Process duplicates
        for file_hash, files in duplicates.items():
            group = {
                "hash": file_hash,
                "count": len(files),
                "files": [str(f) for f in files],
                "kept": str(files[0]),
                "removed": []
            }

            # Remove duplicates if not dry run
            if not dry_run:
                for duplicate_file in files[1:]:
                    try:
                        duplicate_file.unlink()
                        group["removed"].append(str(duplicate_file))
                    except:
                        pass

            results["groups"].append(group)

        self._log("cleanup_duplicates", "completed", {
            "duplicate_groups": results["duplicate_groups"],
            "duplicate_files": results["duplicate_files"],
            "dry_run": dry_run
        })

        return results
