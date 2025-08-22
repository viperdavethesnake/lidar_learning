#!/usr/bin/env python3
"""
LiDAR Metadata Extraction Script

Extracts comprehensive metadata from LiDAR files and creates sidecar catalog files
optimized for orchestration and AI model feeding.
"""

import argparse
import json
import sys
import yaml
import hashlib
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import laspy
import numpy as np


def safe_stats(arr):
    """Calculate safe statistics for arrays, handling empty arrays."""
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
    """Convert numpy types to Python types for JSON/YAML serialization."""
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
    """Calculate classification counts from an array."""
    if len(arr) == 0:
        return {}
    
    arr = np.array(arr)
    counts = np.bincount(arr.astype(np.int64))
    return {int(i): int(c) for i, c in enumerate(counts) if c > 0}


def extract_complete_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract EVERYTHING that laspy can provide from a LiDAR file.
    This is the comprehensive version - all available metadata.
    """
    print(f"  🔍 Complete extraction: {file_path.name}...")
    
    with laspy.open(file_path) as reader:
        hdr = reader.header
        las = reader.read()
        
        # === COMPLETE METADATA ===
        metadata = {
            "extraction_info": {
                "extracted_at": datetime.now().isoformat(),
                "extractor": "extract_metadata.py - complete mode",
                "file_hash_sha256": hashlib.sha256(open(file_path, "rb").read()).hexdigest(),
            },
            
            "file_info": {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_size_bytes": file_path.stat().st_size,
            },
            
            "header_complete": {},
            "vlrs_complete": [],
            "point_data_complete": {},
            "coordinate_system_complete": {}
        }
        
        # === ALL HEADER ATTRIBUTES ===
        header_attrs = [
            'major_version', 'minor_version', 'file_source_id', 'uuid',
            'system_identifier', 'generating_software', 'creation_date',
            'point_count', 'offset_to_point_data', 'number_of_evlrs',
            'start_of_waveform_data_packet_record', 'are_points_compressed',
            'number_of_points_by_return'
        ]
        
        for attr in header_attrs:
            if hasattr(hdr, attr):
                try:
                    value = getattr(hdr, attr)
                    # Convert to serializable format
                    if hasattr(value, 'isoformat'):  # datetime/date
                        metadata["header_complete"][attr] = value.isoformat()
                    elif hasattr(value, '__str__') and 'UUID' in str(type(value)):  # UUID
                        metadata["header_complete"][attr] = str(value)
                    elif isinstance(value, np.ndarray):  # numpy arrays
                        metadata["header_complete"][attr] = value.tolist()
                    else:
                        metadata["header_complete"][attr] = value
                except Exception as e:
                    metadata["header_complete"][attr] = f"<error: {e}>"
        
        # Version details
        metadata["header_complete"]["version_full"] = f"{hdr.version.major}.{hdr.version.minor}"
        
        # Global encoding
        try:
            global_enc = hdr.global_encoding
            metadata["header_complete"]["global_encoding_value"] = int(global_enc) if global_enc else 0
        except:
            metadata["header_complete"]["global_encoding_value"] = 0
        
        # Point format details
        pf = hdr.point_format
        metadata["header_complete"]["point_format"] = {
            "id": int(pf.id),
            "size": pf.size,
            "dimensions": [{"name": d.name, "num_bytes": d.num_bytes, "dtype": str(d.dtype) if d.dtype else None} for d in pf.dimensions]
        }
        
        # === COORDINATE SYSTEM (COMPLETE) ===
        metadata["coordinate_system_complete"] = {
            "scales": {"x": hdr.scales[0], "y": hdr.scales[1], "z": hdr.scales[2]},
            "offsets": {"x": hdr.offsets[0], "y": hdr.offsets[1], "z": hdr.offsets[2]},
            "mins": {"x": hdr.mins[0], "y": hdr.mins[1], "z": hdr.mins[2]},
            "maxs": {"x": hdr.maxs[0], "y": hdr.maxs[1], "z": hdr.maxs[2]},
            "x_min": hdr.x_min, "x_max": hdr.x_max, "x_scale": hdr.x_scale, "x_offset": hdr.x_offset,
            "y_min": hdr.y_min, "y_max": hdr.y_max, "y_scale": hdr.y_scale, "y_offset": hdr.y_offset,
            "z_min": hdr.z_min, "z_max": hdr.z_max, "z_scale": hdr.z_scale, "z_offset": hdr.z_offset,
        }
        
        # CRS
        try:
            crs_obj = hdr.parse_crs()
            metadata["coordinate_system_complete"]["crs_wkt"] = crs_obj.to_wkt() if crs_obj else None
        except:
            metadata["coordinate_system_complete"]["crs_wkt"] = None
        
        # === VLRs (COMPLETE) ===
        for i, vlr in enumerate(hdr.vlrs):
            vlr_info = {
                "index": i,
                "type": type(vlr).__name__,
                "user_id": getattr(vlr, 'user_id', None),
                "record_id": getattr(vlr, 'record_id', None),
                "description": getattr(vlr, 'description', None),
            }
            metadata["vlrs_complete"].append(vlr_info)
        
        # === POINT DATA (COMPLETE ANALYSIS) ===
        point_data = {"total_points": len(las.points)}
        
        # Analyze all available attributes
        for attr in ['classification', 'intensity', 'return_number', 'number_of_returns', 
                     'synthetic', 'key_point', 'withheld', 'overlap', 'scanner_channel',
                     'scan_direction_flag', 'edge_of_flight_line', 'user_data', 
                     'scan_angle', 'point_source_id', 'gps_time']:
            if hasattr(las, attr):
                try:
                    data = getattr(las, attr)
                    if hasattr(data, 'dtype') and data.size > 0:
                        flat_data = data.flatten() if hasattr(data, 'flatten') else data
                        analysis = {
                            "dtype": str(data.dtype),
                            "min": convert_numpy_types(np.min(flat_data)),
                            "max": convert_numpy_types(np.max(flat_data)),
                            "unique_count": len(np.unique(flat_data)) if flat_data.size < 100000 else "many"
                        }
                        
                        # Special handling for classification and returns
                        if attr in ['classification', 'return_number', 'number_of_returns']:
                            unique_vals, counts = np.unique(flat_data, return_counts=True)
                            analysis["breakdown"] = {int(val): int(count) for val, count in zip(unique_vals, counts)}
                        
                        point_data[attr] = analysis
                except:
                    point_data[attr] = "unavailable"
        
        metadata["point_data_complete"] = point_data
        
        return metadata


def extract_curated_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract our curated subset of metadata for orchestration/AI workflows.
    This is our focused selection of what matters for business use cases.
    """
    print(f"  🎯 Curated extraction: {file_path.name}...")
    
    with laspy.open(file_path) as reader:
        hdr = reader.header
        las = reader.read()
        
        # === CURATED METADATA FOR ORCHESTRATION ===
        metadata = {
            # Core file identification
            "file": file_path.name,
            "file_path": str(file_path),
            "file_size_bytes": file_path.stat().st_size,
            
            # Essential LAS information
            "point_format_id": int(hdr.point_format.id),
            "version": f"{hdr.version.major}.{hdr.version.minor}",
            "point_count": int(hdr.point_count),
            
            # Data source tracking
            "system_identifier": hdr.system_identifier.strip() if hdr.system_identifier else None,
            "generating_software": hdr.generating_software.strip() if hdr.generating_software else None,
            "creation_date": hdr.creation_date.isoformat() if hdr.creation_date else None,
            
            # Geographic extent (critical for spatial queries)
            "bbox": {
                "minx": hdr.mins[0], "miny": hdr.mins[1], "minz": hdr.mins[2],
                "maxx": hdr.maxs[0], "maxy": hdr.maxs[1], "maxz": hdr.maxs[2],
                "width": hdr.maxs[0] - hdr.mins[0],
                "height": hdr.maxs[1] - hdr.mins[1],
                "area": (hdr.maxs[0] - hdr.mins[0]) * (hdr.maxs[1] - hdr.mins[1])
            },
            
            # Point density (critical for processing estimation)
            "point_density_per_unit2": None,  # calculated below
            
            # Coordinate system (essential for engineering)
            "coordinate_system": {
                "scales": {"x": hdr.scales[0], "y": hdr.scales[1], "z": hdr.scales[2]},
                "offsets": {"x": hdr.offsets[0], "y": hdr.offsets[1], "z": hdr.offsets[2]}
            }
        }
        
        # Calculate point density
        area = metadata["bbox"]["area"]
        metadata["point_density_per_unit2"] = metadata["point_count"] / area if area > 0 else 0
        
        # === POINT DATA ANALYSIS (CURATED) ===
        
        # Classification analysis (critical for feature detection)
        if hasattr(las, 'classification'):
            cls_unique, cls_counts = np.unique(las.classification, return_counts=True)
            metadata["classification_analysis"] = {
                "unique_classes": len(cls_unique),
                "breakdown": {int(cls): int(count) for cls, count in zip(cls_unique, cls_counts)}
            }
        else:
            metadata["classification_analysis"] = {"unique_classes": 0, "breakdown": {}}
        
        # Intensity analysis (useful for material differentiation)
        if hasattr(las, 'intensity'):
            intensity = las.intensity
            metadata["intensity_analysis"] = {
                "min": convert_numpy_types(np.min(intensity)),
                "max": convert_numpy_types(np.max(intensity)),
                "mean": convert_numpy_types(np.mean(intensity)),
                "std": convert_numpy_types(np.std(intensity))
            }
        else:
            metadata["intensity_analysis"] = None
        
        # Return analysis (important for vegetation studies)
        if hasattr(las, 'return_number'):
            ret_unique, ret_counts = np.unique(las.return_number, return_counts=True)
            metadata["return_analysis"] = {
                "max_return": int(np.max(las.return_number)),
                "breakdown": {int(ret): int(count) for ret, count in zip(ret_unique, ret_counts)}
            }
        else:
            metadata["return_analysis"] = None
        
        # === BUSINESS INTELLIGENCE FEATURES ===
        classes = metadata["classification_analysis"]["breakdown"]
        
        metadata["ml_features"] = {
            "has_ground_points": 2 in classes,          # Ground
            "has_buildings": 6 in classes,              # Building  
            "has_vegetation": any(c in classes for c in [3, 4, 5]),  # Low/Med/High vegetation
            "has_water": 9 in classes,                  # Water
            "has_bridges": 17 in classes,               # Bridge deck
            "point_density_category": (
                "high" if metadata["point_density_per_unit2"] > 10 else
                "medium" if metadata["point_density_per_unit2"] > 1 else "low"
            ),
            "classification_diversity": len(classes),
            "return_complexity": len(metadata["return_analysis"]["breakdown"]) if metadata["return_analysis"] else 0
        }
        
        # === PROCESSING ESTIMATES ===
        metadata["processing_estimates"] = {
            "estimated_processing_time_seconds": max(1, int(metadata["point_count"] / 100000)),
            "memory_requirements_mb": max(50, int(metadata["point_count"] * 100 / 1024 / 1024)),
            "suitable_for_batch": metadata["point_count"] < 5000000,  # Under 5M points
            "priority_score": (
                0.5 if 6 in classes else        # Higher priority for buildings
                0.4 if len(classes) > 5 else    # Higher for diverse data
                0.3                             # Base priority
            )
        }
        
        # CRS (essential for coordinate transformation)
        try:
            crs_obj = hdr.parse_crs()
            metadata["crs"] = {"wkt": crs_obj.to_wkt()} if crs_obj else None
        except:
            metadata["crs"] = None
        
        print(f"    ✓ Curated metadata: {metadata['point_count']:,} points, {len(classes)} classes, {metadata['ml_features']['point_density_category']} density")
        
        return metadata


def create_sidecar_catalog(file_metadatas: List[Dict[str, Any]], output_dir: Path) -> Dict[str, Any]:
    """
    Create sidecar catalog optimized for orchestration and AI model feeding.
    
    Args:
        file_metadatas: List of metadata dictionaries from individual files
        output_dir: Directory to save catalog files
    
    Returns:
        dict: The generated catalog
    """
    print(f"  🎯 Creating sidecar catalog for {len(file_metadatas)} files...")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Calculate catalog summary
    total_points = sum(m.get("point_count", 0) for m in file_metadatas)
    total_size = sum(m.get("file_size_bytes", 0) for m in file_metadatas)
    
    catalog = {
        "catalog_info": {
            "version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_files": len(file_metadatas),
            "total_points": total_points,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
        },
        "files": []
    }
    
    for file_meta in file_metadatas:
        # Calculate file hash if file exists
        file_path = Path(file_meta["file_path"])
        file_hash = None
        if file_path.exists():
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Analyze classifications for ML features
        classifications = file_meta.get("classification_counts", {})
        
        # Create sidecar entry
        entry = {
            "id": str(uuid.uuid4()),
            "file_name": file_meta["file"],
            "file_path": file_meta["file_path"],
            "file_hash": file_hash,
            "file_size_bytes": file_meta.get("file_size_bytes", 0),
            "processing_status": "ready",
            
            # Core LiDAR metadata for orchestration
            "point_count": file_meta["point_count"],
            "point_density_per_unit2": file_meta["point_density_per_unit2"],
            "bbox": file_meta["bbox"],
            
            # AI/ML features for model training
            "ml_features": {
                "has_ground_points": 2 in classifications,  # Ground
                "has_buildings": 6 in classifications,      # Building
                "has_vegetation": any(c in classifications for c in [3, 4, 5]),  # Low/Med/High vegetation
                "has_water": 9 in classifications,          # Water
                "has_bridges": 17 in classifications,       # Bridge decks
                "has_noise": 7 in classifications,          # Low point (noise)
                "point_density_category": (
                    "high" if file_meta["point_density_per_unit2"] > 10 else
                    "medium" if file_meta["point_density_per_unit2"] > 1 else "low"
                ),
                "has_rgb": file_meta.get("rgb_stats") is not None,
                "return_complexity": len(file_meta.get("return_number_counts", {})),
                "classification_diversity": len(classifications),
            },
            
            # Orchestration hints for processing optimization
            "orchestration": {
                "estimated_processing_time_seconds": max(1, int(file_meta["point_count"] / 100000)),
                "memory_requirements_mb": max(50, int(file_meta["point_count"] * 100 / 1024 / 1024)),
                "priority_score": calculate_priority_score(file_meta, classifications),
                "batch_size_recommendation": min(4, max(1, int(100000000 / file_meta["point_count"]))),
                "parallel_processing_suitable": file_meta["point_count"] > 1000000,
            },
            
            # Raw metadata for detailed analysis
            "raw_metadata": file_meta
        }
        
        catalog["files"].append(entry)
    
    return catalog


def calculate_priority_score(metadata: Dict[str, Any], classifications: Dict[int, int]) -> float:
    """Calculate a priority score for processing order optimization."""
    score = 0.3  # Base score
    
    # Higher priority for files with buildings (urban areas)
    if 6 in classifications:
        score += 0.3
    
    # Higher priority for diverse classification
    if len(classifications) > 5:
        score += 0.2
    
    # Higher priority for high-density data
    if metadata["point_density_per_unit2"] > 5:
        score += 0.2
    
    # Lower priority for very large files (processing complexity)
    if metadata["point_count"] > 5000000:
        score -= 0.1
    
    return min(1.0, max(0.1, score))


def save_catalog(catalog: Dict[str, Any], output_dir: Path, format_types: List[str]):
    """Save catalog in specified formats."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for fmt in format_types:
        if fmt.lower() == 'json':
            # Timestamped version
            json_file = output_dir / f"lidar_catalog_{timestamp}.json"
            with open(json_file, "w") as f:
                json.dump(catalog, f, indent=2)
            
            # Latest version
            with open(output_dir / "lidar_catalog_latest.json", "w") as f:
                json.dump(catalog, f, indent=2)
            
            print(f"    ✓ JSON catalog: {json_file.name}")
        
        elif fmt.lower() == 'yaml':
            # Timestamped version
            yaml_file = output_dir / f"lidar_catalog_{timestamp}.yaml"
            with open(yaml_file, "w") as f:
                yaml.safe_dump(convert_numpy_types(catalog), f, sort_keys=False)
            
            # Latest version
            with open(output_dir / "lidar_catalog_latest.yaml", "w") as f:
                yaml.safe_dump(convert_numpy_types(catalog), f, sort_keys=False)
            
            print(f"    ✓ YAML catalog: {yaml_file.name}")


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Extract metadata from LiDAR files and create sidecar catalogs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract metadata from data/ directory
  python extract_metadata.py
  
  # Extract from custom directory
  python extract_metadata.py --input-dir my_lidar_data
  
  # Save only JSON format
  python extract_metadata.py --format json
  
  # Save to custom output directory
  python extract_metadata.py --output-dir my_output
  
  # Process specific files
  python extract_metadata.py --files data/file1.laz data/file2.laz
        """
    )
    
    parser.add_argument(
        '--input-dir', '-i',
        default='data',
        help='Input directory containing LiDAR files (default: data)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default='output',
        help='Output directory for metadata and catalogs (default: output)'
    )
    
    parser.add_argument(
        '--files', '-f',
        nargs='+',
        help='Specific LiDAR files to process'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'yaml', 'both'],
        default='both',
        help='Output format for catalogs (default: both)'
    )
    
    parser.add_argument(
        '--basic-only',
        action='store_true',
        help='Generate only basic metadata, skip sidecar catalog'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--individual',
        action='store_true',
        help='Generate individual metadata/catalog files for each LiDAR file'
    )
    
    args = parser.parse_args()
    
    print("LiDAR Metadata Extraction")
    print("=" * 50)
    
    # Determine which files to process
    if args.files:
        lidar_files = [Path(f) for f in args.files]
        # Verify files exist
        for file_path in lidar_files:
            if not file_path.exists():
                print(f"✗ File not found: {file_path}")
                sys.exit(1)
        print(f"✓ Processing {len(lidar_files)} specified files")
    else:
        input_dir = Path(args.input_dir)
        if not input_dir.exists():
            print(f"✗ Input directory not found: {input_dir}")
            print(f"  Run 'python download_lidar.py' first to download data")
            sys.exit(1)
        
        lidar_files = list(input_dir.glob("*.laz")) + list(input_dir.glob("*.las"))
        if not lidar_files:
            print(f"✗ No LiDAR files found in {input_dir}")
            print(f"  Supported formats: .las, .laz")
            sys.exit(1)
        
        print(f"✓ Found {len(lidar_files)} LiDAR files in {input_dir}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract BOTH complete and curated metadata
    print(f"\n📊 Extracting metadata from {len(lidar_files)} files...")
    all_complete_metadata = []
    all_curated_metadata = []
    
    for file_path in sorted(lidar_files):
        try:
            # Extract complete metadata (EVERYTHING laspy can provide)
            complete_metadata = extract_complete_metadata(file_path)
            all_complete_metadata.append(complete_metadata)
            
            # Extract curated metadata (our focused subset)
            curated_metadata = extract_curated_metadata(file_path)
            all_curated_metadata.append(curated_metadata)
            
        except Exception as e:
            print(f"  ✗ Error processing {file_path.name}: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    if not all_complete_metadata:
        print("✗ No files processed successfully!")
        sys.exit(1)
    
    # Save COMPLETE metadata (everything available)
    print(f"\n💾 Saving COMPLETE metadata (everything laspy provides)...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    complete_json = output_dir / f"complete_metadata_{timestamp}.json"
    with open(complete_json, "w") as f:
        json.dump(all_complete_metadata, f, indent=2)
    print(f"  ✓ Complete metadata: {complete_json.name}")
    
    if 'yaml' in args.format or args.format == 'both':
        complete_yaml = output_dir / f"complete_metadata_{timestamp}.yaml"
        with open(complete_yaml, "w") as f:
            yaml.safe_dump(convert_numpy_types(all_complete_metadata), f, sort_keys=False)
        print(f"  ✓ Complete metadata: {complete_yaml.name}")
    
    # Save CURATED metadata (our focused subset)
    print(f"\n💾 Saving CURATED metadata (focused for orchestration)...")
    
    curated_json = output_dir / f"curated_metadata_{timestamp}.json"
    with open(curated_json, "w") as f:
        json.dump(all_curated_metadata, f, indent=2)
    print(f"  ✓ Curated metadata: {curated_json.name}")
    
    if 'yaml' in args.format or args.format == 'both':
        curated_yaml = output_dir / f"curated_metadata_{timestamp}.yaml"
        with open(curated_yaml, "w") as f:
            yaml.safe_dump(convert_numpy_types(all_curated_metadata), f, sort_keys=False)
        print(f"  ✓ Curated metadata: {curated_yaml.name}")
    
    # Also save "latest" versions for easy access
    with open(output_dir / "complete_metadata_latest.json", "w") as f:
        json.dump(all_complete_metadata, f, indent=2)
    with open(output_dir / "curated_metadata_latest.json", "w") as f:
        json.dump(all_curated_metadata, f, indent=2)
    
    # Save individual files if requested
    if args.individual:
        print(f"\n📄 Saving individual files...")
        
        # Determine format types based on args
        if args.format == 'both':
            format_types = ['json', 'yaml']
        else:
            format_types = [args.format]
        
        for complete_meta, curated_meta in zip(all_complete_metadata, all_curated_metadata):
            file_name = Path(curated_meta["file"]).stem
            
            generated_files = []
            
            # Generate files based on format option
            for fmt in format_types:
                if fmt.lower() == 'json':
                    # Individual complete JSON
                    complete_file = output_dir / f"{file_name}_complete.json"
                    with open(complete_file, "w") as f:
                        json.dump(complete_meta, f, indent=2)
                    generated_files.append(f"{file_name}_complete.json")
                    
                    # Individual curated JSON
                    curated_file = output_dir / f"{file_name}_curated.json"
                    with open(curated_file, "w") as f:
                        json.dump(curated_meta, f, indent=2)
                    generated_files.append(f"{file_name}_curated.json")
                
                elif fmt.lower() == 'yaml':
                    # Individual complete YAML
                    complete_file = output_dir / f"{file_name}_complete.yaml"
                    with open(complete_file, "w") as f:
                        yaml.safe_dump(convert_numpy_types(complete_meta), f, sort_keys=False)
                    generated_files.append(f"{file_name}_complete.yaml")
                    
                    # Individual curated YAML
                    curated_file = output_dir / f"{file_name}_curated.yaml"
                    with open(curated_file, "w") as f:
                        yaml.safe_dump(convert_numpy_types(curated_meta), f, sort_keys=False)
                    generated_files.append(f"{file_name}_curated.yaml")
            
            print(f"  ✓ Individual files: {', '.join(generated_files)}")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print(f"Files processed: {len(all_curated_metadata)}")
    
    total_points = sum(m['point_count'] for m in all_curated_metadata)
    total_size = sum(m.get('file_size_bytes', 0) for m in all_curated_metadata)
    
    print(f"Total points: {total_points:,}")
    print(f"Total size: {total_size / 1024 / 1024:.1f} MB")
    
    # Classification summary from curated data
    all_classes = {}
    for meta in all_curated_metadata:
        for class_id, count in meta.get("classification_analysis", {}).get("breakdown", {}).items():
            all_classes[class_id] = all_classes.get(class_id, 0) + count
    
    if all_classes:
        print(f"\nClassification summary:")
        for class_id in sorted(all_classes.keys()):
            percentage = (all_classes[class_id] / total_points) * 100
            print(f"  Class {class_id:2d}: {all_classes[class_id]:,} points ({percentage:.1f}%)")
    
    print(f"\n📁 Output location: {output_dir.absolute()}")
    print(f"📊 COMPLETE metadata: Everything laspy can extract")
    print(f"🎯 CURATED metadata: Focused subset for orchestration & AI")
    
    # File size comparison
    complete_size = complete_json.stat().st_size
    curated_size = curated_json.stat().st_size
    print(f"\n📏 File size comparison:")
    print(f"  Complete metadata: {complete_size:,} bytes")
    print(f"  Curated metadata: {curated_size:,} bytes") 
    print(f"  Compression ratio: {curated_size/complete_size:.1%} (curated is {curated_size/complete_size:.1%} of complete)")
    
    print(f"\n✅ Both complete and curated metadata ready for engineering workflows!")


if __name__ == "__main__":
    main()
