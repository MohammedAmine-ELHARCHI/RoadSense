"""
Download Road Defect Datasets

This script downloads public road defect datasets for training:
1. RDD2022 (Road Damage Detection 2022) - https://data.mendeley.com/datasets/5ty2wb6gvg/1
2. Crack500 - https://github.com/fyangneil/pavement-crack-detection
3. DeepCrack - Alternative source

Usage:
    python download_datasets.py --output ../data/raw
"""

import os
import argparse
import requests
from pathlib import Path
from tqdm import tqdm
import zipfile
import gdown

def download_file(url, output_path):
    """Download file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as file, tqdm(
        desc=output_path.name,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress_bar.update(size)

def extract_zip(zip_path, extract_to):
    """Extract zip file"""
    print(f"📦 Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"✅ Extracted to {extract_to}")

def download_rdd2022(output_dir):
    """
    Download RDD2022 dataset
    Note: Manual download might be required from Mendeley Data
    """
    print("\n🌐 Downloading RDD2022 Dataset...")
    print("=" * 60)
    
    rdd_dir = output_dir / "rdd2022"
    rdd_dir.mkdir(parents=True, exist_ok=True)
    
    print("⚠️  RDD2022 requires manual download from Mendeley Data:")
    print("   1. Visit: https://data.mendeley.com/datasets/5ty2wb6gvg/1")
    print("   2. Download the dataset (requires free account)")
    print("   3. Extract to:", rdd_dir.absolute())
    print("\nDataset structure should be:")
    print("   rdd2022/")
    print("   ├── train/")
    print("   │   ├── images/")
    print("   │   └── annotations/")
    print("   ├── val/")
    print("   └── test/")
    print()
    
    # Check if already downloaded
    if (rdd_dir / "train").exists():
        print("✅ RDD2022 dataset found!")
        return True
    else:
        print("❌ RDD2022 dataset not found. Please download manually.")
        return False

def download_crack500(output_dir):
    """Download Crack500 dataset from GitHub"""
    print("\n🌐 Downloading Crack500 Dataset...")
    print("=" * 60)
    
    crack500_dir = output_dir / "crack500"
    crack500_dir.mkdir(parents=True, exist_ok=True)
    
    # Crack500 GitHub repository
    repo_url = "https://github.com/fyangneil/pavement-crack-detection/archive/refs/heads/master.zip"
    zip_path = crack500_dir / "crack500.zip"
    
    try:
        if not zip_path.exists():
            print("📥 Downloading from GitHub...")
            download_file(repo_url, zip_path)
            extract_zip(zip_path, crack500_dir)
            zip_path.unlink()  # Remove zip after extraction
        
        print("✅ Crack500 dataset downloaded!")
        return True
    except Exception as e:
        print(f"❌ Error downloading Crack500: {e}")
        print("   You can manually clone: git clone https://github.com/fyangneil/pavement-crack-detection")
        return False

def download_sample_dataset(output_dir):
    """
    Create a small sample dataset for testing
    Uses public road images (placeholder - you need to add actual sources)
    """
    print("\n🎨 Creating sample dataset for testing...")
    print("=" * 60)
    
    sample_dir = output_dir / "sample"
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    images_dir = sample_dir / "images"
    labels_dir = sample_dir / "labels"
    images_dir.mkdir(exist_ok=True)
    labels_dir.mkdir(exist_ok=True)
    
    print("✅ Sample dataset structure created!")
    print("   Add your test images to:", images_dir.absolute())
    print("   Add corresponding labels to:", labels_dir.absolute())
    return True

def download_coco_pothole_dataset(output_dir):
    """
    Download pothole dataset from Roboflow or similar sources
    """
    print("\n🌐 Downloading Pothole Dataset...")
    print("=" * 60)
    
    pothole_dir = output_dir / "pothole"
    pothole_dir.mkdir(parents=True, exist_ok=True)
    
    print("💡 Alternative public datasets available:")
    print("   1. Roboflow Pothole Dataset: https://universe.roboflow.com/")
    print("   2. Kaggle Pothole Detection: https://www.kaggle.com/datasets/")
    print("   3. Search for 'road defect dataset' on academic repositories")
    print()
    
    return False

def main():
    parser = argparse.ArgumentParser(description="Download road defect datasets")
    parser.add_argument(
        "--output", 
        type=str, 
        default="../data/raw",
        help="Output directory for datasets"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        choices=["all", "rdd2022", "crack500", "sample", "pothole"],
        default="all",
        help="Which dataset to download"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 60)
    print("🚀 ROAD DEFECT DATASET DOWNLOADER")
    print("=" * 60)
    print(f"📁 Output directory: {output_dir.absolute()}")
    print()
    
    results = {}
    
    if args.dataset in ["all", "rdd2022"]:
        results["rdd2022"] = download_rdd2022(output_dir)
    
    if args.dataset in ["all", "crack500"]:
        results["crack500"] = download_crack500(output_dir)
    
    if args.dataset in ["all", "sample"]:
        results["sample"] = download_sample_dataset(output_dir)
    
    if args.dataset in ["all", "pothole"]:
        results["pothole"] = download_coco_pothole_dataset(output_dir)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DOWNLOAD SUMMARY")
    print("=" * 60)
    for dataset, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {dataset.upper()}: {status}")
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Complete any manual downloads required")
    print("   2. Run: python prepare_dataset.py --source", output_dir.absolute())
    print("   3. Start training: cd ../detection-fissures && python train_yolo.py")
    print()

if __name__ == "__main__":
    main()
