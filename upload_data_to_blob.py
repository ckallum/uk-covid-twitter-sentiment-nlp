#!/usr/bin/env python3
"""
Script to upload data files to Vercel Blob storage
Run this once to move data files from local to cloud storage
"""
import os
import glob
from pathlib import Path

# Note: This script shows the structure for uploading to Vercel Blob
# You'll need to install @vercel/blob and set up proper authentication
# For now, we'll create a manifest of files that need to be uploaded

def create_upload_manifest():
    """Create a manifest of all data files that need to be uploaded"""
    data_dir = Path("data")
    manifest = {}
    
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(data_dir)
            file_size = file_path.stat().st_size
            manifest[str(relative_path)] = {
                "local_path": str(file_path),
                "size_bytes": file_size,
                "blob_url": f"https://your-blob-store.vercel-storage.com/{relative_path}"
            }
    
    return manifest

def main():
    manifest = create_upload_manifest()
    
    print("Data files that need to be uploaded to Vercel Blob:")
    print("=" * 60)
    
    total_size = 0
    for file_path, info in manifest.items():
        size_mb = info["size_bytes"] / 1024 / 1024
        total_size += size_mb
        print(f"{file_path:<50} {size_mb:>8.2f} MB")
    
    print("=" * 60)
    print(f"Total size: {total_size:.2f} MB")
    
    # Save manifest for reference
    import json
    with open("data_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nManifest saved to data_manifest.json")
    print("\nNext steps:")
    print("1. Set up Vercel Blob storage")
    print("2. Upload files using Vercel CLI or dashboard")
    print("3. Update shared.py to load from URLs")

if __name__ == "__main__":
    main() 