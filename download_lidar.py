#!/usr/bin/env python3
"""
LiDAR Data Download Script

Downloads LiDAR files for analysis. Can download from a predefined list
or from custom URLs provided by the user.
"""

import argparse
import sys
import urllib.request
from urllib.error import URLError
from pathlib import Path
import time


# Sample URLs for Los Angeles LiDAR data
DEFAULT_URLS = [
    "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_LPC_CA_LosAngeles_2016_LAS_2018/laz/USGS_LPC_CA_LosAngeles_2016_L4_6374_1628c_LAS_2018.laz",
    "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_LPC_CA_LosAngeles_2016_LAS_2018/laz/USGS_LPC_CA_LosAngeles_2016_L4_6376_1622b_LAS_2018.laz",
    "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_LPC_CA_LosAngeles_2016_LAS_2018/laz/USGS_LPC_CA_LosAngeles_2016_L4_6376_1628b_LAS_2018.laz",
    "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_LPC_CA_LosAngeles_2016_LAS_2018/laz/USGS_LPC_CA_LosAngeles_2016_L4_6382_1617a_LAS_2018.laz",
    "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_LPC_CA_LosAngeles_2016_LAS_2018/laz/USGS_LPC_CA_LosAngeles_2016_L4_6382_1622a_LAS_2018.laz",
]


def download_file(url, output_path, max_retries=3):
    """
    Download a single file with retry logic and progress indication.
    
    Args:
        url: URL to download from
        output_path: Local path to save the file
        max_retries: Maximum number of retry attempts
    
    Returns:
        bool: True if download succeeded, False otherwise
    """
    for attempt in range(max_retries):
        try:
            print(f"  📥 Downloading {output_path.name} (attempt {attempt + 1}/{max_retries})...")
            
            # Download with progress indication
            def progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    if block_num % 50 == 0:  # Print every ~50 blocks to avoid spam
                        print(f"    Progress: {percent}%", end='\r')
            
            urllib.request.urlretrieve(url, output_path, reporthook=progress_hook)
            print(f"  ✓ Downloaded {output_path.name} successfully")
            return True
            
        except URLError as e:
            print(f"  ✗ Download failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print(f"    Retrying in 2 seconds...")
                time.sleep(2)
        except KeyboardInterrupt:
            print(f"  ⚠ Download cancelled by user")
            return False
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    return False


def load_urls_from_file(file_path):
    """
    Load URLs from a text file (one URL per line).
    
    Args:
        file_path: Path to the file containing URLs
    
    Returns:
        list: List of URLs, or None if file couldn't be read
    """
    try:
        with open(file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"✓ Loaded {len(urls)} URLs from {file_path}")
        return urls
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        return None
    except Exception as e:
        print(f"✗ Error reading file {file_path}: {e}")
        return None


def download_files(urls, output_dir, max_files=None, skip_existing=True):
    """
    Download multiple files to a directory.
    
    Args:
        urls: List of URLs to download
        output_dir: Directory to save files to
        max_files: Maximum number of files to download (None for all)
        skip_existing: Whether to skip files that already exist
    
    Returns:
        tuple: (successful_downloads, failed_downloads)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if max_files:
        urls = urls[:max_files]
    
    successful = 0
    failed = 0
    
    print(f"📂 Downloading to: {output_path.absolute()}")
    print(f"📊 Files to download: {len(urls)}")
    
    for i, url in enumerate(urls, 1):
        filename = url.split('/')[-1]
        file_path = output_path / filename
        
        print(f"\n[{i}/{len(urls)}] {filename}")
        
        if skip_existing and file_path.exists():
            print(f"  ⚠ File already exists, skipping")
            successful += 1
            continue
        
        if download_file(url, file_path):
            successful += 1
        else:
            failed += 1
    
    return successful, failed


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Download LiDAR files for metadata extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download default sample files
  python download_lidar.py
  
  # Download from a URL list file
  python download_lidar.py --url-file urls.txt
  
  # Download only first 3 files
  python download_lidar.py --max-files 3
  
  # Download to custom directory
  python download_lidar.py --output-dir my_data
  
  # Download specific URLs
  python download_lidar.py --urls "https://example.com/file1.laz" "https://example.com/file2.laz"
        """
    )
    
    parser.add_argument(
        '--url-file', '-f',
        help='Text file containing URLs (one per line)'
    )
    
    parser.add_argument(
        '--urls', '-u',
        nargs='+',
        help='Space-separated list of URLs to download'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default='data',
        help='Output directory for downloaded files (default: data)'
    )
    
    parser.add_argument(
        '--max-files', '-m',
        type=int,
        help='Maximum number of files to download'
    )
    
    parser.add_argument(
        '--force', '-F',
        action='store_true',
        help='Re-download files even if they already exist'
    )
    
    parser.add_argument(
        '--list-default',
        action='store_true',
        help='List the default URLs and exit'
    )
    
    args = parser.parse_args()
    
    # Handle special cases
    if args.list_default:
        print("Default URLs:")
        for i, url in enumerate(DEFAULT_URLS, 1):
            print(f"{i:2d}. {url}")
        return
    
    # Determine which URLs to use
    urls = None
    
    if args.url_file:
        urls = load_urls_from_file(args.url_file)
        if urls is None:
            sys.exit(1)
    elif args.urls:
        urls = args.urls
        print(f"✓ Using {len(urls)} URLs from command line")
    else:
        urls = DEFAULT_URLS
        print(f"✓ Using {len(urls)} default sample URLs")
    
    if not urls:
        print("✗ No URLs to download!")
        sys.exit(1)
    
    print("\nLiDAR Data Download")
    print("=" * 50)
    
    # Download files
    successful, failed = download_files(
        urls=urls,
        output_dir=args.output_dir,
        max_files=args.max_files,
        skip_existing=not args.force
    )
    
    # Summary
    print("\n" + "=" * 50)
    print("DOWNLOAD SUMMARY")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"📁 Location: {Path(args.output_dir).absolute()}")
    
    if successful > 0:
        print(f"\n🎯 Ready for metadata extraction!")
        print(f"   Run: python extract_metadata.py")
    else:
        print(f"\n⚠ No files downloaded successfully.")
        sys.exit(1)


if __name__ == "__main__":
    main()
