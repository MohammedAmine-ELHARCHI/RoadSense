"""
Prepare road defect dataset for YOLOv8 training

This script:
1. Downloads/locates RDD2022 and Crack500 datasets
2. Converts annotations to YOLO format
3. Splits data into train/val/test sets
4. Organizes files in the correct structure

Usage:
    python prepare_dataset.py
"""

import os
import shutil
from pathlib import Path
import json
import random
from PIL import Image
import argparse

def convert_bbox_to_yolo(bbox, img_width, img_height):
    """
    Convert bounding box from [x, y, w, h] to YOLO format [x_center, y_center, width, height]
    All values normalized by image dimensions
    """
    x, y, w, h = bbox
    x_center = (x + w / 2) / img_width
    y_center = (y + h / 2) / img_height
    width = w / img_width
    height = h / img_height
    return x_center, y_center, width, height

def prepare_dataset(source_dir, output_dir, train_ratio=0.7, val_ratio=0.15):
    """
    Prepare dataset in YOLO format
    
    Args:
        source_dir: Directory containing raw datasets
        output_dir: Output directory for processed dataset
        train_ratio: Ratio of training data
        val_ratio: Ratio of validation data
    """
    print("🚀 Starting dataset preparation...")
    
    # Create output directories
    output_path = Path(output_dir)
    splits = ['train', 'val', 'test']
    
    for split in splits:
        (output_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (output_path / split / 'labels').mkdir(parents=True, exist_ok=True)
    
    # Class mapping (adjust based on your datasets)
    class_map = {
        'crack': 0,
        'longitudinal_crack': 0,  # Map to crack
        'transverse_crack': 0,    # Map to crack
        'pothole': 1,
        'alligator_crack': 2,
        'alligator': 2,           # Alias
        'patch': 3,
        'patching': 3             # Alias
    }
    
    print("\n📦 Processing datasets...")
    print(f"   Source: {source_dir}")
    print(f"   Output: {output_dir}")
    print(f"   Split: {train_ratio:.1%} train, {val_ratio:.1%} val, {1-train_ratio-val_ratio:.1%} test")
    
    all_samples = []
    
    # Process RDD2022 dataset (if exists)
    rdd2022_path = Path(source_dir) / 'rdd2022'
    if rdd2022_path.exists():
        print("\n📁 Processing RDD2022 dataset...")
        # Add RDD2022 processing logic here
        # This is a placeholder - implement based on RDD2022 structure
        pass
    else:
        print("\n⚠️  RDD2022 dataset not found in", rdd2022_path)
    
    # Process Crack500 dataset (if exists)
    crack500_path = Path(source_dir) / 'crack500'
    if crack500_path.exists():
        print("\n📁 Processing Crack500 dataset...")
        # Add Crack500 processing logic here
        # This is a placeholder - implement based on Crack500 structure
        pass
    else:
        print("\n⚠️  Crack500 dataset not found in", crack500_path)
    
    # If no samples found, create dummy data for testing
    if len(all_samples) == 0:
        print("\n⚠️  No datasets found. Creating dummy samples for testing...")
        create_dummy_dataset(output_path)
        return
    
    # Shuffle samples
    random.shuffle(all_samples)
    
    # Split dataset
    total = len(all_samples)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    train_samples = all_samples[:train_end]
    val_samples = all_samples[train_end:val_end]
    test_samples = all_samples[val_end:]
    
    print(f"\n📊 Dataset statistics:")
    print(f"   Total samples: {total}")
    print(f"   Training: {len(train_samples)}")
    print(f"   Validation: {len(val_samples)}")
    print(f"   Test: {len(test_samples)}")
    
    # Copy files to appropriate splits
    for split, samples in [('train', train_samples), ('val', val_samples), ('test', test_samples)]:
        print(f"\n📝 Copying {split} samples...")
        for sample in samples:
            # Copy image
            src_img = sample['image_path']
            dst_img = output_path / split / 'images' / sample['image_name']
            shutil.copy2(src_img, dst_img)
            
            # Write label file
            label_file = output_path / split / 'labels' / (Path(sample['image_name']).stem + '.txt')
            with open(label_file, 'w') as f:
                for anno in sample['annotations']:
                    f.write(f"{anno['class_id']} {anno['x_center']} {anno['y_center']} {anno['width']} {anno['height']}\n")
    
    print("\n✅ Dataset preparation complete!")
    print(f"   Output directory: {output_dir}")

def create_dummy_dataset(output_path):
    """
    Create a small dummy dataset for testing when real datasets are not available
    """
    print("Creating dummy dataset with synthetic images...")
    
    import numpy as np
    
    for split in ['train', 'val', 'test']:
        num_samples = {'train': 10, 'val': 3, 'test': 3}[split]
        
        for i in range(num_samples):
            # Create dummy image (640x640 with random noise)
            img_array = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            
            img_name = f"dummy_{split}_{i:04d}.jpg"
            img_path = output_path / split / 'images' / img_name
            img.save(img_path)
            
            # Create dummy label with random bbox
            label_path = output_path / split / 'labels' / f"dummy_{split}_{i:04d}.txt"
            with open(label_path, 'w') as f:
                # Random defect annotation
                class_id = random.randint(0, 3)
                x_center = random.uniform(0.2, 0.8)
                y_center = random.uniform(0.2, 0.8)
                width = random.uniform(0.1, 0.3)
                height = random.uniform(0.1, 0.3)
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
    
    print(f"✅ Created dummy dataset: 10 train, 3 val, 3 test samples")
    print("⚠️  Replace with real datasets for actual training!")

def main():
    parser = argparse.ArgumentParser(description='Prepare road defect dataset for YOLOv8')
    parser.add_argument('--source', type=str, default='data/raw', help='Source directory with raw datasets')
    parser.add_argument('--output', type=str, default='data/processed', help='Output directory')
    parser.add_argument('--train-ratio', type=float, default=0.7, help='Training set ratio')
    parser.add_argument('--val-ratio', type=float, default=0.15, help='Validation set ratio')
    
    args = parser.parse_args()
    
    prepare_dataset(
        source_dir=args.source,
        output_dir=args.output,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio
    )

if __name__ == "__main__":
    main()
