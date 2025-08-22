#!/usr/bin/env python3
"""
Comprehensive LiDAR Metadata Extraction

This script extracts EVERY piece of metadata that laspy can provide from LAS/LAZ files.
It creates two outputs:
1. Complete metadata - everything laspy can extract
2. Curated metadata - our selected subset for orchestration

This answers the question: "Are we extracting everything available?"
"""

import argparse
import json
import yaml
import hashlib
import uuid
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Optional

import laspy
import numpy as np


def convert_for_serialization(obj):
    """Convert numpy types and other objects for JSON/YAML serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):  # Custom objects
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_for_serialization(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_serialization(item) for item in obj]
    else:
        return obj


def extract_complete_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract EVERY piece of metadata that laspy can provide.
    This is the comprehensive version - everything available.
    """
    print(f"  🔍 Complete extraction: {file_path.name}...")
    
    with laspy.open(file_path) as reader:
        hdr = reader.header
        las = reader.read()
        
        # === FILE LEVEL METADATA ===
        metadata = {
            "extraction_info": {
                "extracted_at": datetime.utcnow().isoformat() + "Z",
                "extractor": "comprehensive_extract.py",
                "laspy_version": laspy.__version__ if hasattr(laspy, '__version__') else "unknown"
            },
            
            "file_info": {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_size_bytes": file_path.stat().st_size,
                "file_hash_sha256": hashlib.sha256(open(file_path, "rb").read()).hexdigest(),
            }
        }
        
        # === COMPLETE HEADER METADATA ===
        header_metadata = {}
        
        # Core header attributes
        header_attrs = [
            'major_version', 'minor_version', 'file_source_id', 'global_encoding',
            'uuid', 'creating_software', 'system_identifier', 'generating_software',
            'creation_date', 'point_count', 'offset_to_point_data',
            'number_of_evlrs', 'start_of_waveform_data_packet_record',
            'are_points_compressed', 'number_of_points_by_return'
        ]
        
        for attr in header_attrs:
            if hasattr(hdr, attr):
                try:
                    value = getattr(hdr, attr)
                    header_metadata[attr] = convert_for_serialization(value)
                except Exception as e:
                    header_metadata[attr] = f"<error: {e}>"
        
        # Version info
        header_metadata["version"] = {
            "major": hdr.version.major,
            "minor": hdr.version.minor,
            "full": str(hdr.version)
        }
        
        # Global encoding details
        try:
            global_enc = hdr.global_encoding
            header_metadata["global_encoding_details"] = {
                "value": int(global_enc) if global_enc else 0,
                "gps_time_type": "GPS Standard Time" if hasattr(global_enc, 'gps_time_type') else "unknown",
                "waveform_data_internal": getattr(global_enc, 'waveform_data_internal', None),
                "waveform_data_external": getattr(global_enc, 'waveform_data_external', None),
                "synthetic_return_numbers": getattr(global_enc, 'synthetic_return_numbers', None),
                "wkt": getattr(global_enc, 'wkt', None)
            }
        except Exception as e:
            header_metadata["global_encoding_details"] = f"<error: {e}>"
        
        # Coordinate system information
        header_metadata["coordinate_system"] = {
            "scales": {"x": hdr.scales[0], "y": hdr.scales[1], "z": hdr.scales[2]},
            "offsets": {"x": hdr.offsets[0], "y": hdr.offsets[1], "z": hdr.offsets[2]},
            "mins": {"x": hdr.mins[0], "y": hdr.mins[1], "z": hdr.mins[2]},
            "maxs": {"x": hdr.maxs[0], "y": hdr.maxs[1], "z": hdr.maxs[2]},
            "x_min": hdr.x_min, "x_max": hdr.x_max, "x_scale": hdr.x_scale, "x_offset": hdr.x_offset,
            "y_min": hdr.y_min, "y_max": hdr.y_max, "y_scale": hdr.y_scale, "y_offset": hdr.y_offset,
            "z_min": hdr.z_min, "z_max": hdr.z_max, "z_scale": hdr.z_scale, "z_offset": hdr.z_offset,
        }
        
        # Point format details
        pf = hdr.point_format
        header_metadata["point_format"] = {
            "id": int(pf.id),
            "size": pf.size,
            "extra_bytes_per_point": len(pf.extra_dims) if hasattr(pf, 'extra_dims') else 0,
            "dimensions": []
        }
        
        for dim in pf.dimensions:
            dim_info = {
                "name": dim.name,
                "num_bytes": dim.num_bytes,
                "dtype": str(dim.dtype) if dim.dtype else None,
            }
            if hasattr(dim, 'description'):
                dim_info["description"] = dim.description
            header_metadata["point_format"]["dimensions"].append(dim_info)
        
        # === VLR (Variable Length Records) ANALYSIS ===
        vlr_metadata = []
        for i, vlr in enumerate(hdr.vlrs):
            vlr_info = {
                "index": i,
                "type": type(vlr).__name__,
                "user_id": getattr(vlr, 'user_id', None),
                "record_id": getattr(vlr, 'record_id', None),
                "description": getattr(vlr, 'description', None),
            }
            
            # Try to get VLR-specific data
            if hasattr(vlr, 'data'):
                vlr_info["data_length"] = len(vlr.data) if vlr.data else 0
            
            # Special handling for known VLR types
            if 'WktCoordinateSystem' in type(vlr).__name__:
                try:
                    vlr_info["coordinate_system_wkt"] = str(vlr)
                except:
                    vlr_info["coordinate_system_wkt"] = "<could not extract>"
            
            vlr_metadata.append(vlr_info)
        
        # === CRS INFORMATION ===
        try:
            crs_obj = hdr.parse_crs()
            if crs_obj:
                crs_metadata = {
                    "wkt": crs_obj.to_wkt(),
                    "authority": getattr(crs_obj, 'authority', None),
                    "code": getattr(crs_obj, 'code', None),
                    "name": getattr(crs_obj, 'name', None),
                }
            else:
                crs_metadata = None
        except Exception as e:
            crs_metadata = {"error": str(e)}
        
        # === POINT DATA ANALYSIS ===
        point_data_metadata = {
            "total_points": len(las.points),
            "point_record_length": hdr.point_format.size,
            "available_dimensions": []
        }
        
        # Analyze all available point dimensions
        for attr in dir(las):
            if not attr.startswith('_') and hasattr(las, attr):
                try:
                    data = getattr(las, attr)
                    if hasattr(data, 'shape') and hasattr(data, 'dtype'):
                        dim_analysis = {
                            "name": attr,
                            "dtype": str(data.dtype),
                            "shape": list(data.shape),
                            "size_bytes": data.nbytes,
                        }
                        
                        # Statistical analysis for numeric data
                        if np.issubdtype(data.dtype, np.number) and data.size > 0:
                            flat_data = data.flatten()
                            dim_analysis["statistics"] = {
                                "min": convert_for_serialization(np.min(flat_data)),
                                "max": convert_for_serialization(np.max(flat_data)),
                                "mean": convert_for_serialization(np.mean(flat_data)),
                                "std": convert_for_serialization(np.std(flat_data)),
                                "unique_values": len(np.unique(flat_data)) if flat_data.size < 100000 else "too_many"
                            }
                            
                            # Special analysis for classification
                            if attr == 'classification':
                                unique_classes, counts = np.unique(flat_data, return_counts=True)
                                dim_analysis["classification_breakdown"] = {
                                    int(cls): int(count) for cls, count in zip(unique_classes, counts)
                                }
                        
                        point_data_metadata["available_dimensions"].append(dim_analysis)
                except:
                    pass
        
        # === EXTENDED VLR ANALYSIS ===
        evlr_metadata = []
        if hdr.number_of_evlrs > 0:
            try:
                evlrs = hdr.read_evlrs()
                for i, evlr in enumerate(evlrs):
                    evlr_info = {
                        "index": i,
                        "type": type(evlr).__name__,
                        "user_id": getattr(evlr, 'user_id', None),
                        "record_id": getattr(evlr, 'record_id', None),
                        "description": getattr(evlr, 'description', None),
                    }
                    evlr_metadata.append(evlr_info)
            except Exception as e:
                evlr_metadata = [{"error": str(e)}]
        
        # === COMPILE COMPLETE METADATA ===
        metadata.update({
            "header": header_metadata,
            "vlrs": vlr_metadata,
            "evlrs": evlr_metadata,
            "coordinate_reference_system": crs_metadata,
            "point_data": point_data_metadata,
        })
        
        return metadata


def extract_curated_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract our curated subset of metadata for orchestration.
    This is our current focused extraction.
    """
    print(f"  🎯 Curated extraction: {file_path.name}...")
    
    with laspy.open(file_path) as reader:
        hdr = reader.header
        las = reader.read()
        
        # This is essentially our current extract_metadata function
        metadata = {
            "file": file_path.name,
            "file_path": str(file_path),
            "file_size_bytes": file_path.stat().st_size,
            "point_format_id": int(hdr.point_format.id),
            "version": f"{hdr.version.major}.{hdr.version.minor}",
            "point_count": int(hdr.point_count),
            "system_identifier": hdr.system_identifier.strip() if hdr.system_identifier else None,
            "generating_software": hdr.generating_software.strip() if hdr.generating_software else None,
            "creation_date": {
                "full": hdr.creation_date.isoformat() if hdr.creation_date else None,
                "year": hdr.creation_date.year if hdr.creation_date else None,
                "day_of_year": hdr.creation_date.timetuple().tm_yday if hdr.creation_date else None,
            },
            
            # Coordinate system
            "coordinate_system": {
                "scales": {"x": hdr.scales[0], "y": hdr.scales[1], "z": hdr.scales[2]},
                "offsets": {"x": hdr.offsets[0], "y": hdr.offsets[1], "z": hdr.offsets[2]},
                "bbox": {
                    "minx": hdr.mins[0], "miny": hdr.mins[1], "minz": hdr.mins[2],
                    "maxx": hdr.maxs[0], "maxy": hdr.maxs[1], "maxz": hdr.maxs[2],
                    "width": hdr.maxs[0] - hdr.mins[0],
                    "height": hdr.maxs[1] - hdr.mins[1],
                    "depth": hdr.maxs[2] - hdr.mins[2],
                    "area_2d": (hdr.maxs[0] - hdr.mins[0]) * (hdr.maxs[1] - hdr.mins[1])
                }
            }
        }
        
        # Point density
        area_2d = metadata["coordinate_system"]["bbox"]["area_2d"]
        metadata["point_density_per_unit2"] = metadata["point_count"] / area_2d if area_2d > 0 else 0
        
        # Classification analysis
        if hasattr(las, 'classification'):
            unique_classes, counts = np.unique(las.classification, return_counts=True)
            metadata["classification_analysis"] = {
                "unique_classes": len(unique_classes),
                "breakdown": {int(cls): int(count) for cls, count in zip(unique_classes, counts)}
            }
        
        # Intensity analysis
        if hasattr(las, 'intensity'):
            intensity = las.intensity
            metadata["intensity_analysis"] = {
                "min": convert_for_serialization(np.min(intensity)),
                "max": convert_for_serialization(np.max(intensity)),
                "mean": convert_for_serialization(np.mean(intensity)),
                "std": convert_for_serialization(np.std(intensity)),
            }
        
        # Return analysis
        if hasattr(las, 'return_number'):
            unique_returns, counts = np.unique(las.return_number, return_counts=True)
            metadata["return_analysis"] = {
                "breakdown": {int(ret): int(count) for ret, count in zip(unique_returns, counts)},
                "max_return": int(np.max(las.return_number))
            }
        
        # CRS
        try:
            crs_obj = hdr.parse_crs()
            metadata["crs"] = {"wkt": crs_obj.to_wkt()} if crs_obj else None
        except:
            metadata["crs"] = None
        
        return metadata


def main():
    parser = argparse.ArgumentParser(description="Compare complete vs curated LiDAR metadata extraction")
    parser.add_argument('--input-dir', '-i', default='data', help='Input directory with LiDAR files')
    parser.add_argument('--output-dir', '-o', default='output', help='Output directory')
    parser.add_argument('--files', '-f', nargs='+', help='Specific files to process')
    parser.add_argument('--format', choices=['json', 'yaml', 'both'], default='both', help='Output format')
    
    args = parser.parse_args()
    
    print("Comprehensive vs Curated LiDAR Metadata Extraction")
    print("=" * 60)
    
    # Determine files to process
    if args.files:
        lidar_files = [Path(f) for f in args.files]
    else:
        input_dir = Path(args.input_dir)
        lidar_files = list(input_dir.glob("*.laz")) + list(input_dir.glob("*.las"))
    
    if not lidar_files:
        print("No LiDAR files found!")
        return
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_complete = []
    all_curated = []
    
    for file_path in lidar_files:
        print(f"\nProcessing {file_path.name}...")
        
        try:
            complete_meta = extract_complete_metadata(file_path)
            curated_meta = extract_curated_metadata(file_path)
            
            all_complete.append(complete_meta)
            all_curated.append(curated_meta)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    files_to_write = [
        ("complete_metadata", all_complete),
        ("curated_metadata", all_curated)
    ]
    
    for name, data in files_to_write:
        if args.format in ['json', 'both']:
            json_file = output_dir / f"{name}_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ {json_file}")
        
        if args.format in ['yaml', 'both']:
            yaml_file = output_dir / f"{name}_{timestamp}.yaml"
            with open(yaml_file, 'w') as f:
                yaml.safe_dump(data, f, sort_keys=False)
            print(f"✓ {yaml_file}")
    
    print(f"\n📊 Analysis complete!")
    print(f"Complete metadata: Everything laspy can extract")
    print(f"Curated metadata: Our focused subset for orchestration")


if __name__ == "__main__":
    main()
