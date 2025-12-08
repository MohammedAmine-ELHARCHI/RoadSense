"""
Immediate Training Demo - No Dataset Required!

This script demonstrates YOLOv8 training using synthetic/test data.
Perfect for testing the training pipeline before getting real datasets.

Usage:
    python demo_train.py
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import random

def create_demo_dataset():
    """Create a tiny synthetic dataset for testing training pipeline"""
    print("🎨 Creating synthetic demo dataset...")
    
    base_dir = Path("../data/demo_dataset")
    
    # Create structure
    for split in ['train', 'val']:
        (base_dir / split / 'images').mkdir(parents=True, exist_ok=True)
        (base_dir / split / 'labels').mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic images with "defects"
    classes = ['crack', 'pothole', 'alligator_crack', 'patch']
    
    for split, num_images in [('train', 20), ('val', 5)]:
        print(f"   Generating {num_images} {split} images...")
        
        for i in range(num_images):
            # Create image (simulating road surface)
            img = Image.new('RGB', (640, 640), color=(100, 100, 100))
            draw = ImageDraw.Draw(img)
            
            # Save image
            img_path = base_dir / split / 'images' / f'road_{i:03d}.jpg'
            img.save(img_path)
            
            # Create label (random "defects")
            label_path = base_dir / split / 'labels' / f'road_{i:03d}.txt'
            with open(label_path, 'w') as f:
                # Generate 1-3 random bounding boxes
                num_boxes = random.randint(1, 3)
                for _ in range(num_boxes):
                    class_id = random.randint(0, len(classes) - 1)
                    x_center = random.uniform(0.2, 0.8)
                    y_center = random.uniform(0.2, 0.8)
                    width = random.uniform(0.05, 0.2)
                    height = random.uniform(0.05, 0.2)
                    f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")
    
    # Create data.yaml
    yaml_content = f"""path: {base_dir.absolute()}
train: train/images
val: val/images

names:
  0: crack
  1: pothole
  2: alligator_crack
  3: patch

nc: 4
"""
    
    yaml_path = base_dir / 'data.yaml'
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"✅ Demo dataset created!")
    print(f"   Location: {base_dir.absolute()}")
    print(f"   Config: {yaml_path.absolute()}")
    
    return yaml_path

def train_demo_model(data_yaml):
    """Train a quick demo model"""
    try:
        from ultralytics import YOLO
        import torch
        
        print("\n🚀 STARTING DEMO TRAINING")
        print("=" * 60)
        print("⚠️  This is a DEMO with synthetic data!")
        print("   Results will not be meaningful for real detection.")
        print("   Purpose: Test training pipeline, verify GPU, check setup.")
        print()
        
        # Check GPU
        if torch.cuda.is_available():
            device = 0
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = 'cpu'
            print("⚠️  Training on CPU (slower)")
        
        # Use smallest model for demo
        print("📦 Loading YOLOv8n (nano - fastest for demo)")
        model = YOLO('yolov8n.pt')
        
        print(f"\n🔄 Training for 5 epochs (demo only)...")
        print(f"   This will take 1-2 minutes...")
        print()
        
        # Quick training
        results = model.train(
            data=str(data_yaml),
            epochs=5,
            imgsz=640,
            batch=8,
            name='demo_training',
            patience=10,
            save=True,
            device=device,
            workers=2,
            project='../models',
            exist_ok=True,
            pretrained=True,
            optimizer='AdamW',
            verbose=False,
            plots=True
        )
        
        print("\n✅ DEMO TRAINING COMPLETED!")
        print("=" * 60)
        print("\n📊 Results:")
        print(f"   Model weights: models/demo_training/weights/best.pt")
        print(f"   Training plots: models/demo_training/")
        print()
        
        print("🎯 NEXT STEPS:")
        print("   1. Get real dataset from Roboflow")
        print("      → python download_roboflow.py")
        print()
        print("   2. Train on real data:")
        print("      → python quick_train.py --mode full --data REAL_DATA.yaml --epochs 50")
        print()
        print("   3. Or use our full training script:")
        print("      → cd ../detection-fissures")
        print("      → python train_yolo.py --data REAL_DATA.yaml --epochs 100")
        print()
        
        return True
        
    except ImportError:
        print("\n❌ ultralytics not installed!")
        print("   Install it: pip install ultralytics")
        return False
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("🧪 YOLOV8 DEMO TRAINING - PIPELINE TEST")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Create synthetic dataset (25 images)")
    print("  2. Train YOLOv8n for 5 epochs (~2 min)")
    print("  3. Verify your setup works")
    print()
    
    input("Press Enter to continue (or Ctrl+C to cancel)...")
    
    # Create demo dataset
    data_yaml = create_demo_dataset()
    
    # Train
    success = train_demo_model(data_yaml)
    
    if success:
        print("\n✨ Your training pipeline is working!")
        print("   Ready to train on real data!")
    else:
        print("\n❌ Setup needs attention - check errors above")

if __name__ == "__main__":
    main()
