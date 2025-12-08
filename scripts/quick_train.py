"""
Quick Start Training Script for Road Defect Detection

This script provides a simplified path to train YOLOv8 using:
1. A small sample dataset for immediate testing
2. Pre-trained YOLOv8 weights for transfer learning

Usage:
    python quick_train.py --mode sample    # Train on sample data (for testing)
    python quick_train.py --mode full      # Train on full dataset
"""

import os
import sys
from pathlib import Path
import argparse
import yaml

def create_sample_dataset():
    """Create a minimal sample dataset with synthetic/test data"""
    print("🎨 Creating sample dataset structure...")
    
    base_dir = Path("../data")
    dataset_dir = base_dir / "sample_dataset"
    
    # Create directory structure
    for split in ['train', 'val', 'test']:
        (dataset_dir / split / 'images').mkdir(parents=True, exist_ok=True)
        (dataset_dir / split / 'labels').mkdir(parents=True, exist_ok=True)
    
    # Create data.yaml
    yaml_content = {
        'path': str(dataset_dir.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'names': {
            0: 'crack',
            1: 'pothole',
            2: 'alligator_crack',
            3: 'patch'
        },
        'nc': 4
    }
    
    yaml_path = dataset_dir / 'data.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False)
    
    print(f"✅ Sample dataset structure created at: {dataset_dir.absolute()}")
    print(f"📋 Configuration saved to: {yaml_path.absolute()}")
    print("\n⚠️  To train effectively, you need to add images and labels:")
    print(f"   - Add training images to: {dataset_dir / 'train' / 'images'}")
    print(f"   - Add training labels to: {dataset_dir / 'train' / 'labels'}")
    print(f"   - Add validation images/labels to: {dataset_dir / 'val'}")
    print("\n💡 RECOMMENDED: Download a public dataset instead:")
    print("   Option 1: Roboflow Universe - Search for 'road defect detection'")
    print("   Option 2: Kaggle Datasets - Search for 'pothole detection'")
    print("   Option 3: Use our download script: python download_datasets.py")
    
    return yaml_path

def download_roboflow_dataset():
    """Instructions to download from Roboflow"""
    print("\n🌐 ROBOFLOW DATASET DOWNLOAD INSTRUCTIONS")
    print("=" * 60)
    print("1. Visit: https://universe.roboflow.com/")
    print("2. Search for 'road defect' or 'pothole detection'")
    print("3. Choose a dataset (look for YOLO format)")
    print("4. Click 'Download' and select 'YOLOv8' format")
    print("5. Copy the provided code snippet or download zip")
    print("\nExample datasets:")
    print("  - Road Damage Detection")
    print("  - Pothole Detection")
    print("  - Crack Detection")
    print()

def train_with_pretrained(data_yaml, model_size='m', epochs=100, imgsz=640, batch=16):
    """Train YOLOv8 with transfer learning"""
    try:
        from ultralytics import YOLO
        
        print("\n🚀 STARTING YOLOV8 TRAINING")
        print("=" * 60)
        print(f"📊 Model: YOLOv8{model_size}")
        print(f"📂 Data config: {data_yaml}")
        print(f"🔄 Epochs: {epochs}")
        print(f"📐 Image size: {imgsz}")
        print(f"📦 Batch size: {batch}")
        print()
        
        # Initialize model
        model = YOLO(f'yolov8{model_size}.pt')
        
        # Train
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            name='road_defect_detection',
            patience=20,
            save=True,
            device='0',  # Use GPU 0, or 'cpu' for CPU training
            workers=4,
            project='../models',
            exist_ok=True,
            pretrained=True,
            optimizer='AdamW',
            lr0=0.01,
            lrf=0.01,
            momentum=0.937,
            weight_decay=0.0005,
            warmup_epochs=3,
            warmup_momentum=0.8,
            box=7.5,
            cls=0.5,
            dfl=1.5,
            plots=True,
            verbose=True
        )
        
        print("\n✅ TRAINING COMPLETED!")
        print(f"📁 Model saved to: models/road_defect_detection/weights/best.pt")
        print(f"📊 Training results: models/road_defect_detection/")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure you have images in the dataset directories")
        print("  2. Check that labels are in YOLO format (one .txt per image)")
        print("  3. Verify data.yaml paths are correct")
        print("  4. Try reducing batch size if out of memory")
        return False

def main():
    parser = argparse.ArgumentParser(description="Quick start training for road defect detection")
    parser.add_argument(
        "--mode",
        choices=["sample", "full", "download-info"],
        default="download-info",
        help="Training mode"
    )
    parser.add_argument("--data", type=str, help="Path to data.yaml file")
    parser.add_argument("--model", type=str, default="m", choices=['n', 's', 'm', 'l', 'x'], help="Model size")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    
    args = parser.parse_args()
    
    if args.mode == "download-info":
        print("\n🎓 ROAD DEFECT DATASET GUIDE")
        print("=" * 60)
        download_roboflow_dataset()
        print("\n📥 ALTERNATIVE: Use our download script")
        print("   python download_datasets.py --dataset crack500")
        print()
        
    elif args.mode == "sample":
        data_yaml = create_sample_dataset()
        print("\n⚠️  Sample mode creates structure only!")
        print("You need to add actual images before training.")
        print("\nTo train when ready:")
        print(f"   python quick_train.py --mode full --data {data_yaml}")
        
    elif args.mode == "full":
        if not args.data:
            print("❌ Please provide --data path to your data.yaml file")
            print("\nExample:")
            print("   python quick_train.py --mode full --data ../data/my_dataset/data.yaml")
            sys.exit(1)
        
        data_yaml = Path(args.data)
        if not data_yaml.exists():
            print(f"❌ Data config not found: {data_yaml}")
            sys.exit(1)
        
        train_with_pretrained(
            data_yaml,
            model_size=args.model,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch
        )

if __name__ == "__main__":
    main()
