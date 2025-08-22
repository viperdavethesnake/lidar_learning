#!/usr/bin/env python3
"""
Simple LiDAR Metadata Extractor

This script downloads a few LiDAR files and extracts metadata to create
sidecar catalog files for orchestration and AI model feeding.

Based on the original macOS script, adapted for Linux with minimal dependencies.
"""

import json
import yaml
import urllib.request
from urllib.error import URLError
from pathlib import Path
import hashlib
import uuid
from datetime import datetime
import time

import laspy
import numpy as np


# Sample URLs for testing (just a few files)
SAMPLE_URLS = [
    "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_LPC_CA_LosAngeles_2016_LAS_2018/laz/USGS_LPC_CA_LosAngeles_2016_L4_6374_1628c_LAS_2018.laz",
    "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_LPC_CA_LosAngeles_2016_LAS_2018/laz/USGS_LPC_CA_LosAngeles_2016_L4_6376_1622b_LAS_2018.laz",
    "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_LPC_CA_LosAngeles_2016_LAS_2018/laz/USGS_LPC_CA_LosAngeles_2016_L4_6376_1628b_LAS_2018.laz"
]


def download_file(url, output_path, max_retries=3):
    """Download a single file with retry logic."""
    for attempt in range(max_retries):
        try:
            print(f"  Downloading {output_path.name} (attempt {attempt + 1}/{max_retries})...")
            urllib.request.urlretrieve(url, output_path)
            print(f"  ✓ Downloaded {output_path.name}")
            return True
        except URLError as e:
            print(f"  ✗ Download failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    return False


def safe_stats(arr):
    """Calculate safe statistics for arrays."""
    if len(arr) == 0:
        return {"min": None, "max": None, "mean": None, "std": None}
    
    arr = np.array(arr)
    return {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
    }


def convert_numpy_types(obj):
    """Convert numpy types to Python types for YAML serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


def class_counts(arr):
    """Calculate classification counts."""
    if len(arr) == 0:
        return {}
    
    arr = np.array(arr)
    counts = np.bincount(arr.astype(np.int64))
    return {int(i): int(c) for i, c in enumerate(counts) if c > 0}


def extract_metadata(file_path):
    """Extract metadata from a single LiDAR file."""
    with laspy.open(file_path) as reader:
        hdr = reader.header
        
        # Read the points
        las = reader.read()
        
        # Basic header info
        metadata = {
            "file": file_path.name,
            "point_format_id": int(hdr.point_format.id),
            "point_format_dimensions": [d.name for d in hdr.point_format.dimensions],
            "version": f"{hdr.version.major}.{hdr.version.minor}",
            "point_count": int(hdr.point_count),
            "scale": {"x": hdr.scales[0], "y": hdr.scales[1], "z": hdr.scales[2]},
            "offset": {"x": hdr.offsets[0], "y": hdr.offsets[1], "z": hdr.offsets[2]},
            "mins": {"x": hdr.mins[0], "y": hdr.mins[1], "z": hdr.mins[2]},
            "maxs": {"x": hdr.maxs[0], "y": hdr.maxs[1], "z": hdr.maxs[2]},
        }
        
        # Calculate bounding box and density
        width = hdr.maxs[0] - hdr.mins[0]
        height = hdr.maxs[1] - hdr.mins[1]
        area = width * height
        density = metadata["point_count"] / area if area > 0 else 0
        
        metadata["bbox"] = {
            "minx": hdr.mins[0], "miny": hdr.mins[1],
            "maxx": hdr.maxs[0], "maxy": hdr.maxs[1]
        }
        metadata["approx_points_per_unit2"] = density
        
        # Get arrays for analysis
        cls = np.array(las.classification) if hasattr(las, 'classification') else np.array([])
        intensity = np.array(las.intensity) if hasattr(las, 'intensity') else np.array([])
        ret_num = np.array(las.return_number) if hasattr(las, 'return_number') else np.array([])
        num_rets = np.array(las.number_of_returns) if hasattr(las, 'number_of_returns') else np.array([])
        
        # Analysis
        metadata["classification_counts"] = class_counts(cls)
        metadata["intensity_stats"] = safe_stats(intensity)
        metadata["return_number_counts"] = class_counts(ret_num)
        metadata["number_of_returns_counts"] = class_counts(num_rets)
        
        return metadata


def create_sidecar_catalog(file_metadatas, output_dir):
    """Create sidecar catalog optimized for orchestration."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    catalog = {
        "catalog_info": {
            "version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_files": len(file_metadatas),
            "total_points": sum(m.get("point_count", 0) for m in file_metadatas),
        },
        "files": []
    }
    
    for file_meta in file_metadatas:
        # Calculate file hash
        file_path = Path("data") / file_meta["file"]
        file_hash = hashlib.sha256(open(file_path, "rb").read()).hexdigest()
        
        # Create sidecar entry
        entry = {
            "id": str(uuid.uuid4()),
            "file_name": file_meta["file"],
            "file_hash": file_hash,
            "processing_status": "ready",
            
            # Core LiDAR metadata
            "point_count": file_meta["point_count"],
            "point_density_per_unit2": file_meta["approx_points_per_unit2"],
            "bbox": file_meta["bbox"],
            
            # AI/ML features
            "ml_features": {
                "has_ground_points": 2 in file_meta.get("classification_counts", {}),
                "has_buildings": 6 in file_meta.get("classification_counts", {}),
                "has_vegetation": any(c in file_meta.get("classification_counts", {}) for c in [3, 4, 5]),
                "has_water": 9 in file_meta.get("classification_counts", {}),
                "point_density_category": (
                    "high" if file_meta["approx_points_per_unit2"] > 10 else
                    "medium" if file_meta["approx_points_per_unit2"] > 1 else "low"
                ),
            },
            
            # Orchestration hints
            "orchestration": {
                "estimated_processing_time_seconds": max(1, int(file_meta["point_count"] / 100000)),
                "memory_requirements_mb": max(50, int(file_meta["point_count"] * 100 / 1024 / 1024)),
                "priority_score": (
                    0.5 if 6 in file_meta.get("classification_counts", {}) else 0.3  # Higher for buildings
                ),
            },
            
            # Raw metadata
            "raw_metadata": file_meta
        }
        
        catalog["files"].append(entry)
    
    # Write catalog files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    json_file = output_path / f"lidar_catalog_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(catalog, f, indent=2)
    
    yaml_file = output_path / f"lidar_catalog_{timestamp}.yaml"
    with open(yaml_file, "w") as f:
        yaml.safe_dump(convert_numpy_types(catalog), f, sort_keys=False)
    
    # Also create "latest" versions
    with open(output_path / "lidar_catalog_latest.json", "w") as f:
        json.dump(catalog, f, indent=2)
    
    with open(output_path / "lidar_catalog_latest.yaml", "w") as f:
        yaml.safe_dump(convert_numpy_types(catalog), f, sort_keys=False)
    
    print(f"✓ Sidecar catalog written to {output_path}")
    print(f"  - {json_file.name}")
    print(f"  - {yaml_file.name}")
    print(f"  - lidar_catalog_latest.json")
    print(f"  - lidar_catalog_latest.yaml")
    
    return catalog


def main():
    """Main function - download files, extract metadata, create sidecar catalog."""
    print("Simple LiDAR Metadata Extractor")
    print("=" * 50)
    
    # Setup directories
    data_dir = Path("data")
    output_dir = Path("output")
    data_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Download files
    print(f"\n1. Downloading {len(SAMPLE_URLS)} sample LiDAR files...")
    for url in SAMPLE_URLS:
        filename = url.split('/')[-1]
        file_path = data_dir / filename
        
        if file_path.exists():
            print(f"  ⚠ {filename} already exists, skipping download")
        else:
            if not download_file(url, file_path):
                print(f"  ✗ Failed to download {filename}")
                continue
    
    # Extract metadata
    print(f"\n2. Extracting metadata from downloaded files...")
    all_metadata = []
    
    for laz_file in sorted(data_dir.glob("*.laz")):
        try:
            print(f"  Processing {laz_file.name}...")
            metadata = extract_metadata(laz_file)
            all_metadata.append(metadata)
        except Exception as e:
            print(f"  ✗ Error processing {laz_file.name}: {e}")
    
    if not all_metadata:
        print("  ✗ No files processed successfully!")
        return
    
    # Write basic metadata
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(all_metadata, f, indent=2)
    
    with open(output_dir / "metadata.yaml", "w") as f:
        yaml.safe_dump(convert_numpy_types(all_metadata), f, sort_keys=False)
    
    print(f"  ✓ Basic metadata written to output/metadata.json and output/metadata.yaml")
    
    # Create sidecar catalog
    print(f"\n3. Generating sidecar catalog for orchestration...")
    catalog = create_sidecar_catalog(all_metadata, output_dir)
    
    # Summary
    print(f"\n" + "=" * 50)
    print("SUMMARY")
    print(f"Files processed: {len(all_metadata)}")
    print(f"Total points: {sum(m['point_count'] for m in all_metadata):,}")
    
    print(f"\nClassification summary:")
    all_classes = {}
    for meta in all_metadata:
        for class_id, count in meta.get("classification_counts", {}).items():
            all_classes[class_id] = all_classes.get(class_id, 0) + count
    
    for class_id in sorted(all_classes.keys()):
        print(f"  Class {class_id}: {all_classes[class_id]:,} points")
    
    print(f"\nFiles created:")
    print(f"  - output/metadata.json (basic metadata)")
    print(f"  - output/metadata.yaml (basic metadata)")
    print(f"  - output/lidar_catalog_latest.json (sidecar catalog)")
    print(f"  - output/lidar_catalog_latest.yaml (sidecar catalog)")
    
    print(f"\n🎯 Your LiDAR sidecar catalog is ready for orchestration and AI model feeding!")


if __name__ == "__main__":
    main()
