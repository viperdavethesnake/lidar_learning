# LiDAR Learning Project

This repository is dedicated to learning about LiDAR data processing and **metadata extraction**. The main goal is to create "sidecar" catalog files for **orchestration and AI model feeding** - the LiDAR equivalent of vision system catalogs.

## 🎯 Project Goal

Extract comprehensive metadata from LiDAR files and create sidecar catalogs that can be used for:
- **Data orchestration and pipeline management**
- **AI model training and inference**
- **Quality assessment and filtering**
- **Geographic indexing and spatial queries**

## 🚀 Quick Start (Three-Script Approach)

This project uses **three focused scripts** for maximum flexibility and learning:

```bash
# 1. Set up environment (creates venv, installs dependencies)
python setup_env.py

# 2. Activate environment and download LiDAR data
source venv/bin/activate  # or venv\Scripts\activate on Windows
python download_lidar.py

# 3. Extract metadata and create sidecar catalogs
python extract_metadata.py
```

**Alternative - Single Script:** For convenience, you can also use the all-in-one script:
```bash
python simple_lidar_metadata.py
```

The scripts will:
1. Set up Python environment with required dependencies
2. Download sample LiDAR files (6M+ points across 5 files)  
3. Extract DUAL metadata outputs (complete + curated)
4. Generate optimized sidecar catalogs for orchestration

## 📋 Prerequisites

- **Python 3.8 or higher** (tested with Python 3.13)
- **pip** (Python package installer)
- **Internet connection** (for downloading sample data)

## 📊 What You Get - DUAL METADATA SYSTEM

### 🎯 **Two-Tier Output System:**

**COMPLETE Metadata (Everything laspy provides):**
- `output/complete_metadata_latest.json` - Full LAS specification data
- `output/complete_metadata_TIMESTAMP.json` - Timestamped archive version

**CURATED Metadata (Optimized for workflows):**  
- `output/curated_metadata_latest.json` - Focused subset for orchestration
- `output/curated_metadata_TIMESTAMP.json` - Timestamped archive version

**Legacy/Compatibility Files:**
- `output/metadata.json` - Basic metadata (for backwards compatibility)
- `output/lidar_catalog_latest.json` - Old sidecar format (maintained for compatibility)

### 📊 **COMPLETE Metadata Structure:**

Contains everything laspy can extract:
```json
{
  "extraction_info": {
    "extracted_at": "2025-08-22T09:52:12.456789",
    "extractor": "extract_metadata.py - complete mode",
    "file_hash_sha256": "ce5d5a970dfd0f7d..."
  },
  "header_complete": {
    "uuid": "5b5bf517-e36a-4250-bd7b-2cb0a793808f",
    "creation_date": "2018-01-09",
    "number_of_points_by_return": [871668, 316, 0, ...],
    "are_points_compressed": true,
    "global_encoding_value": 17
  },
  "vlrs_complete": [...],
  "point_data_complete": {...}
}
```

### 🎯 **CURATED Metadata Structure:**

Optimized for orchestration and AI workflows:
```json
{
  "file": "filename.laz",
  "point_count": 871984,
  "point_density_per_unit2": 0.125,
  "bbox": {"minx": 6374080.0, "miny": 1630800.0, ...},
  
  "ml_features": {
    "has_ground_points": false,
    "has_buildings": false, 
    "has_vegetation": false,
    "has_water": true,
    "point_density_category": "low",
    "classification_diversity": 4
  },
  
  "processing_estimates": {
    "estimated_processing_time_seconds": 8,
    "memory_requirements_mb": 83,
    "priority_score": 0.3,
    "suitable_for_batch": true
  }
}
```

## 🔍 Dual Metadata Extraction

### 📊 **COMPLETE Metadata Includes:**
- **File identification**: UUID, SHA256 hash, extraction timestamp
- **Header analysis**: ALL LAS header attributes (creation date, encoding, compression)
- **VLR details**: Variable Length Records with coordinate system info
- **Point data**: Complete analysis of ALL available point attributes
- **Standards compliance**: Full LAS specification coverage

### 🎯 **CURATED Metadata Includes:**
- **Core identification**: File name, path, size, point count
- **Geographic extent**: Bounding box, point density, coordinate system
- **ML features**: `has_ground_points`, `has_buildings`, `has_vegetation`, `has_water`
- **Processing estimates**: Time, memory, priority scoring, batch suitability
- **Quality metrics**: Classification diversity, return complexity

### 💾 **File Size Comparison:**
- **Complete metadata**: ~29KB (5 files) - Everything available
- **Curated metadata**: ~9KB (5 files) - Focused subset  
- **Compression ratio**: 32% (curated is 1/3 the size of complete)

## 🧠 **Curated Metadata Design Philosophy**

### **Why Two Different Outputs?**

The **COMPLETE** metadata serves **compliance and archival** needs - everything laspy can extract from the LAS specification. The **CURATED** metadata serves **business workflows** - focused data for orchestration and AI systems.

### **🎯 Inclusion Criteria for CURATED Data:**

The curated metadata was designed around **3 core business questions**:

1. **"Can we process this file?"** → Processing estimates, file size, point count
2. **"What's in this data?"** → ML features, classification analysis, geographic extent  
3. **"How should we prioritize it?"** → Priority scoring, batch suitability, density categories

**✅ What's INCLUDED (actionable for business):**
- **Immediately actionable** for processing decisions
- **Required for spatial queries** (bounding boxes, coordinate systems)
- **Useful for AI/ML workflows** (feature detection, classification breakdown)
- **Essential for orchestration** (processing estimates, batch sizing)
- **Human-readable** and interpretable for engineering teams

**❌ What's EXCLUDED (technical overhead):**
- **LAS specification compliance** details (UUIDs, binary flags, compression status)
- **Archival information** (extraction timestamps, file hashes, detailed VLRs)
- **Raw unprocessed data** (point-by-return arrays, internal format details)
- **Technical metadata** not actionable for business workflows

### **🤖 Smart Business Intelligence Features:**

```python
"ml_features": {
    "has_ground_points": True,      # Class 2 (Ground) detected
    "has_buildings": False,         # Class 6 (Building) detected  
    "has_vegetation": False,        # Classes 3,4,5 (Low/Med/High vegetation)
    "has_water": True,             # Class 9 (Water) detected
    "has_bridges": False,          # Class 17 (Bridge deck) detected
    "point_density_category": "low", # Based on points per unit²
    "classification_diversity": 4,   # Number of different feature types
    "return_complexity": 2          # Multi-return analysis for vegetation
}

"processing_estimates": {
    "estimated_processing_time_seconds": 8,  # ~100K points/second rule
    "memory_requirements_mb": 83,            # ~100 bytes per point  
    "suitable_for_batch": True,              # Under 5M points threshold
    "priority_score": 0.3                    # 0.1-1.0 based on content value
}
```

### **🏗️ Real-World Use Cases This Enables:**

**🔍 Intelligent Data Discovery:**
```python
# Find all datasets with buildings for urban planning
building_files = [f for f in curated_data if f['ml_features']['has_buildings']]

# Get high-density data for detailed infrastructure analysis  
detailed_data = [f for f in curated_data 
                 if f['ml_features']['point_density_category'] == 'high']

# Locate water features for environmental monitoring
water_datasets = [f for f in curated_data if f['ml_features']['has_water']]
```

**⚙️ Processing Optimization:**
```python
# Create memory-optimized processing batches
small_batch = [f for f in curated_data 
               if f['processing_estimates']['memory_requirements_mb'] < 200]

# Priority queue - process important data first
priority_queue = sorted(curated_data, 
                       key=lambda x: x['processing_estimates']['priority_score'], 
                       reverse=True)

# Batch-suitable files for parallel processing
batch_ready = [f for f in curated_data 
               if f['processing_estimates']['suitable_for_batch']]
```

**🗺️ Spatial and Geographic Queries:**
```python
# Find datasets intersecting a specific region
def intersects_region(bbox, region):
    return not (bbox['maxx'] < region['minx'] or bbox['minx'] > region['maxx'] or
                bbox['maxy'] < region['miny'] or bbox['miny'] > region['maxy'])

region_data = [f for f in curated_data 
               if intersects_region(f['bbox'], my_target_region)]

# Filter by coordinate system for transformation compatibility
projected_data = [f for f in curated_data 
                  if f['crs'] and 'UTM' in f['crs'].get('wkt', '')]
```

### **📊 Result: Maximum Value, Minimum Overhead**

- **68% size reduction** (from 29KB to 9KB) while retaining **100% of actionable information**
- **Zero workflow disruption** - curated data contains everything needed for business decisions
- **Engineering-focused** - designed for real-world LiDAR processing pipelines
- **AI/ML ready** - feature flags and processing estimates optimized for machine learning workflows

**The curated metadata gives engineering firms everything they need to make smart decisions about LiDAR processing, without the technical overhead of full LAS specification compliance details.**

## 🛠 Customization

### Download Different Data:

Option 1 - Use command line arguments:
```bash
# Download from custom URLs
python download_lidar.py --urls "https://your-url-1.laz" "https://your-url-2.laz"

# Download from a URL file
python download_lidar.py --url-file my_urls.txt

# Limit number of files
python download_lidar.py --max-files 5
```

Option 2 - Edit the `DEFAULT_URLS` list in `download_lidar.py`:
```python
DEFAULT_URLS = [
    "https://your-lidar-data-url-1.laz",
    "https://your-lidar-data-url-2.laz",
    # Add more URLs...
]
```

### Modify ML Features:

Edit the `ml_features` section in `extract_metadata.py` to add your own feature detection logic. See the **Curated Metadata Design Philosophy** section above for details on the current business intelligence features and how they're calculated.

### Control Metadata Output:

```bash
# Generate only JSON (both complete and curated)
python extract_metadata.py --format json

# Generate only YAML (both complete and curated)  
python extract_metadata.py --format yaml

# Generate individual files per LiDAR dataset
python extract_metadata.py --individual

# Basic metadata only (skip curated extraction)
python extract_metadata.py --basic-only

# Verbose output for debugging
python extract_metadata.py --verbose
```

## 📁 Repository Structure

```
lidar_learning/
├── setup_env.py               # 1. Environment setup script
├── download_lidar.py          # 2. LiDAR data download script  
├── extract_metadata.py        # 3. DUAL metadata extraction script
├── simple_lidar_metadata.py   # Alternative: all-in-one script
├── comprehensive_extract.py   # Research tool for metadata exploration
├── data/                       # Downloaded LiDAR files (.gitignored)
├── output/                     # Generated metadata and catalogs (.gitignored)
│   ├── complete_metadata_latest.json    # Everything laspy provides
│   ├── curated_metadata_latest.json     # Focused orchestration data
│   └── [timestamped versions...]        # Archive copies
├── README.md                   # This documentation
├── .gitignore                  # Git ignore rules
└── venv/                       # Python virtual environment (.gitignored)
```

## 🔧 Script Details

### 1. setup_env.py - Environment Setup
- Creates Python virtual environment (`venv/`)
- Installs required dependencies (`laspy[lazrs]`, `pyyaml`, `numpy`)
- Creates project directories (`data/`, `output/`)
- Sets up `.gitignore` file
- Provides usage instructions

### 2. download_lidar.py - Data Download
- Downloads LiDAR files from USGS or custom URLs
- Supports LAZ (compressed) and LAS (uncompressed) formats
- Command line options for custom URLs, file limits, output directories
- Progress indication and retry logic
- Skips existing files by default

### 3. extract_metadata.py - DUAL Metadata Extraction  
- **COMPLETE extraction**: Everything laspy can provide (compliance/archival)
- **CURATED extraction**: Focused subset for orchestration/AI workflows  
- AI/ML feature detection (buildings, vegetation, water, etc.)
- Processing optimization hints (time, memory, priority)
- Multiple output formats (JSON, YAML) with timestamping
- Individual file generation with `--individual` flag
- Command line options: `--format`, `--basic-only`, `--verbose`

## 🔧 Core Technology: laspy

This project uses **laspy** as the core library for LiDAR file processing. Here's what you need to know:

### What is laspy?

**laspy** is a Python library for reading and writing LAS/LAZ files (the standard format for LiDAR data). It's specifically designed for the ASPRS LAS specification and is the most widely-used Python library for LiDAR file I/O.

### What laspy CAN do:

✅ **File Reading**: Read both `.las` (uncompressed) and `.laz` (compressed) files  
✅ **Header Access**: Extract all LAS header metadata (bounds, scales, point counts, etc.)  
✅ **Point Data**: Access individual point attributes (coordinates, classification, intensity, returns)  
✅ **Memory Efficient**: Read headers without loading all point data  
✅ **Standards Compliant**: Supports LAS versions 1.2, 1.3, 1.4 and all point formats  
✅ **Fast**: Optimized for performance with large datasets  
✅ **Compression**: Built-in LAZ compression support via `lazrs` extension  

### What laspy CANNOT do:

❌ **Coordinate Transformations**: No built-in CRS conversion (use `pyproj` separately)  
❌ **3D Processing**: No mesh generation, surface reconstruction, or 3D analysis  
❌ **Visualization**: No built-in plotting or 3D viewing capabilities  
❌ **Advanced Analytics**: No clustering, segmentation, or machine learning features  
❌ **Other Formats**: Only LAS/LAZ - doesn't read PLY, PCD, XYZ, or other point cloud formats  
❌ **Spatial Indexing**: No spatial trees or advanced spatial queries  

### Why laspy for Metadata Extraction?

For our specific goal (metadata extraction and sidecar catalog generation), laspy is perfect because:

1. **Header-focused**: We primarily need LAS header info, which laspy handles excellently
2. **Lightweight**: Minimal dependencies, fast installation
3. **Reliable**: Battle-tested library used throughout the LiDAR industry
4. **Complete**: Gives us everything in the LAS specification
5. **Efficient**: Can extract metadata without loading full point clouds into memory

### laspy Usage in Our Script:

```python
import laspy

# Open LAS/LAZ file
with laspy.open(file_path) as reader:
    hdr = reader.header          # Access header metadata
    las = reader.read()          # Read point data for analysis
    
    # Extract what we need for sidecar catalogs:
    point_count = hdr.point_count
    bbox = {"minx": hdr.mins[0], "maxx": hdr.maxs[0], ...}
    classifications = las.classification
    intensities = las.intensity
```

### Installation:

```bash
# Basic laspy
pip install laspy

# With LAZ compression support (recommended)
pip install "laspy[lazrs]"
```

## 🎯 Usage for Orchestration

*See the **Curated Metadata Design Philosophy** section above for detailed examples and business logic.*

### Filter by AI Features:
```python
import json

# Load curated metadata for orchestration
with open('output/curated_metadata_latest.json') as f:
    curated_data = json.load(f)

# Find files with buildings
building_files = [f for f in curated_data 
                  if f['ml_features']['has_buildings']]

# Get high-priority files  
high_priority = [f for f in curated_data
                 if f['processing_estimates']['priority_score'] > 0.5]

# Filter by density
high_density = [f for f in curated_data
                if f['ml_features']['point_density_category'] == 'high']

# Filter suitable for batch processing
batch_ready = [f for f in curated_data
               if f['processing_estimates']['suitable_for_batch']]
```

### Batch Processing:
```python
# Sort by processing time for optimal batching
files_by_time = sorted(curated_data, 
                       key=lambda x: x['processing_estimates']['estimated_processing_time_seconds'])

# Create batches based on memory requirements
batch_size = 4
for i in range(0, len(files_by_time), batch_size):
    batch = files_by_time[i:i+batch_size]
    total_memory = sum(f['processing_estimates']['memory_requirements_mb'] for f in batch)
    total_time = sum(f['processing_estimates']['estimated_processing_time_seconds'] for f in batch)
    print(f"Batch {i//batch_size + 1}: {len(batch)} files, {total_memory}MB memory, {total_time}s processing")
```

## 🚀 Advanced Usage

### Process Your Own Large Dataset:

1. Create a text file with URLs (one per line)
2. Modify the script to read from your URL file
3. Add parallel downloading for large datasets
4. Customize the ML features for your specific use case

### Integration with AI Pipelines:

The sidecar catalogs are designed to integrate seamlessly with:
- **Training data selection**: Filter by features and quality
- **Inference orchestration**: Batch by processing requirements  
- **Quality control**: Monitor data characteristics
- **Geographic analysis**: Spatial indexing and queries

## 📈 Example Results

From the current sample dataset (5 files, 6.02M points):

**Classification Summary:**
- Class 1 (Unassigned): 2,379,926 points (39.5%)
- Class 2 (Ground): 632,046 points (10.5%)  
- Class 9 (Water): 3,002,507 points (49.8%)
- Class 7 (Noise): 5,290 points (0.1%)
- Other classes: <0.1% each

**ML Features Detected:**
- Water features: ✅ (all files)
- Ground points: ✅ (all files)  
- Buildings: ❌ (none in sample - coastal data)
- Vegetation: ❌ (none in sample - water/urban area)

**File Size Results:**
- Complete metadata: 29KB total (5.8KB per file average)
- Curated metadata: 9KB total (1.8KB per file average)
- Compression efficiency: 68% reduction (curated vs complete)

## 📚 Learning Resources

This project is designed for learning. Key concepts covered:

1. **LAS/LAZ file format**: Understanding point cloud structure
2. **Metadata extraction**: Automated analysis of LiDAR characteristics
3. **Sidecar catalogs**: Creating orchestration-friendly metadata
4. **AI/ML features**: Detecting useful patterns for model training
5. **Batch processing**: Optimizing large-scale LiDAR workflows

## 🚀 Future Development: Phase 2

**📋 Phase 2 Extension**: GPS & POSPac Metadata Extraction

Our current system focuses on LAS/LAZ point cloud metadata. Phase 2 will extend this to process **GPS trajectory data** and **POSPac processing files** for comprehensive survey-level metadata.

**New file types to be supported:**
- **`.gps`** - GPS trajectory data from survey
- **`.pospac`** - POSPac GPS/IMU processing results  
- **`.ini`** - Processing configuration files
- **`.json`** - JSON configuration/data files
- **`.log`** - Processing log files

**Enhanced capabilities:**
- Survey coverage analysis and flight statistics
- GPS quality metrics and accuracy assessment
- Processing chain metadata and quality control
- Survey-level aggregated metadata for engineering workflows

**📖 See `README_PHASE2.md` for detailed Phase 2 planning and implementation roadmap.**

## ⚡ Performance

- **Processing speed**: ~100K points/second metadata extraction
- **Memory usage**: ~100 bytes per point for full analysis  
- **Storage**: Catalogs are ~2KB per file (very compact)

## 🤝 Contributing

This is a learning project. Feel free to:
- Add new feature detection algorithms
- Optimize processing for larger datasets  
- Create visualization tools
- Add support for other LiDAR formats

## 🗺️ Where to Find LiDAR Data

Learning about LiDAR metadata is much more meaningful with real datasets. Here are excellent sources for downloading LiDAR data:

### 🇺🇸 **United States Sources**

| Source | Project Type | Access Method | Data Quality |
|--------|-------------|---------------|--------------|
| **USGS 3DEP** | Urban/infrastructure, nationwide coverage | [USGS Lidar Explorer](https://apps.nationalmap.gov/lidar-explorer/) - Select AOI, download tiles | ⭐⭐⭐⭐⭐ |
| **OpenTopography** | Mountains, forests, research areas | [Portal](https://portal.opentopography.org/datasets) - Search by region, bulk LAZ download | ⭐⭐⭐⭐⭐ |
| **NOAA Digital Coast** | Coastal, riverbank, wetland surveys | [Data Access Viewer](https://coast.noaa.gov/dataviewer/) - Pick areas, download | ⭐⭐⭐⭐ |
| **State DOTs** | Transportation corridors, bridges | Varies by state - often free for research | ⭐⭐⭐⭐ |

### 🌍 **International Sources**

| Country/Region | Source | Notes |
|----------------|--------|-------|
| **Canada** | [Open Canada](https://open.canada.ca/) | Search "LiDAR" or "elevation" |
| **UK** | [Environment Agency](https://environment.data.gov.uk/) | Excellent coverage, free download |
| **Netherlands** | [AHN (Actueel Hoogtebestand Nederland)](https://www.ahn.nl/) | Complete country coverage |
| **Australia** | [ELVIS](https://elevation.fsdf.org.au/) | National elevation data |

### 🏙️ **Sample Datasets by Use Case**

**Urban Planning & Smart Cities:**
- **Los Angeles (used in this project)**: Dense urban, varied building types, perfect for classification learning
- **New York City**: Complex urban canyon effects, high-density points
- **San Francisco**: Hills + urban, interesting terrain challenges

**Environmental & Forestry:**
- **Pacific Northwest forests**: Multi-return patterns, vegetation analysis
- **Everglades**: Wetlands, water classification, low-elevation challenges
- **Yellowstone**: Natural terrain, geological features

**Coastal & Water Management:**
- **Florida Keys**: Coastal erosion, sea-level mapping
- **Louisiana Coast**: Wetland changes, subsidence monitoring
- **Great Lakes shoreline**: Seasonal changes, ice effects

### 💡 **Pro Tips for Data Selection**

1. **Start Small**: Download 3-5 tiles (~100MB total) before scaling up
2. **Diverse Areas**: Mix urban, rural, and natural areas for comprehensive learning
3. **Check Metadata**: Look for recent data (2018+) with good point density (>5 pts/m²)
4. **File Formats**: Prefer LAZ (compressed) over LAS for faster downloads
5. **Coordinate Systems**: Stick to projected coordinates (UTM, State Plane) for easier analysis

### 🔧 **Quick Download Commands**

```bash
# Example: Download specific tiles
wget "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_LPC_CA_LosAngeles_2016_LAS_2018/laz/USGS_LPC_CA_LosAngeles_2016_L4_6374_1628c_LAS_2018.laz"

# For bulk downloads, modify the SAMPLE_URLS in our script
```

### 📊 **What to Look for in Good Learning Data**

**Header Metadata:**
- Recent acquisition date (2018+)
- LAS version 1.4 (most complete)
- Point format 6+ (includes GPS time, RGB if available)
- Clear CRS definition

**Point Characteristics:**
- Density: 5-15 points/m² (good balance of detail vs. file size)
- Classifications: Mix of ground, buildings, vegetation for ML learning
- Multi-return: Shows vegetation structure and complexity
- Intensity variation: Good for material differentiation

### 🎯 **Recommended Starter Datasets**

1. **Los Angeles Urban** (this project): Perfect intro to urban LiDAR
2. **USGS 3DEP sample**: Pick your local area for familiar geography
3. **OpenTopography research site**: High-quality academic datasets
4. **NOAA coastal area**: Learn about water/land boundary challenges

## 📄 License

This project is for educational purposes.