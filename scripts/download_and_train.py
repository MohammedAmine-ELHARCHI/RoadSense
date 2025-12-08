"""
Download and prepare the Road Defect dataset
"""

from roboflow import Roboflow

print("🌐 Downloading Road Defect Dataset from Roboflow...")
print("=" * 60)

# Initialize Roboflow
rf = Roboflow(api_key="AtsztMdfuPNrFqiNn4ei")
project = rf.workspace("pd-vl3mk").project("road-defect-1kdhj")
version = project.version(5)

print("📥 Downloading dataset (798 images)...")
print("   This may take a few minutes...")

dataset = version.download("yolov8")

print(f"\n✅ Dataset downloaded successfully!")
print(f"📁 Location: {dataset.location}")
print(f"📋 Data config: {dataset.location}/data.yaml")

print("\n🎯 READY TO TRAIN!")
print("\n" + "=" * 60)
print("Starting YOLOv8 training now...")
print("=" * 60)

# Now train immediately
import sys
sys.path.append('..')

try:
    from ultralytics import YOLO
    import torch
    
    # Check GPU
    if torch.cuda.is_available():
        device = 0
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = 'cpu'
        print("⚠️  Training on CPU (will be slower)")
    
    print(f"\n📊 Training Configuration:")
    print(f"   Model: YOLOv8m (medium)")
    print(f"   Epochs: 100")
    print(f"   Batch: 16")
    print(f"   Image size: 640")
    print(f"   Device: {device}")
    print()
    
    # Load model
    model = YOLO('yolov8m.pt')
    
    # Train
    print("🚀 Starting training... (this will take 1-3 hours)")
    results = model.train(
        data=f"{dataset.location}/data.yaml",
        epochs=100,
        imgsz=640,
        batch=16,
        name='road_defect_roboflow',
        patience=20,
        save=True,
        device=device,
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
    
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETED!")
    print("=" * 60)
    print(f"📁 Model saved to: ../models/road_defect_roboflow/weights/best.pt")
    print(f"📊 Results: ../models/road_defect_roboflow/")
    print()
    print("🎯 NEXT STEPS:")
    print("   1. Copy model to detection service:")
    print("      docker cp ../models/road_defect_roboflow/weights/best.pt roadsense-detection:/app/models/")
    print()
    print("   2. Update detection service to use new model")
    print("   3. Restart: docker-compose restart detection-service")
    print()
    print("   4. Test with API:")
    print("      curl -X POST http://localhost:8001/api/v1/detect -F 'file=@test_image.jpg'")
    
except ImportError:
    print("\n⚠️  ultralytics not installed in current environment")
    print("   Training script ready, run manually:")
    print(f"   cd ../detection-fissures")
    print(f"   python train_yolo.py --data {dataset.location}/data.yaml --epochs 100")
