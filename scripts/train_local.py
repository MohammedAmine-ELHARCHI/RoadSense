"""
Train YOLOv8 locally and deploy to Docker container

This script trains on your local machine (avoids Docker memory issues)
then automatically deploys the trained model to the running container.
"""

from ultralytics import YOLO
import torch
import os
from pathlib import Path

def train_model():
    print("🚀 TRAINING YOLOV8 ON LOCAL MACHINE")
    print("=" * 60)
    
    # Dataset location
    data_yaml = Path("Road-Defect-5/data.yaml").absolute()
    
    if not data_yaml.exists():
        print(f"❌ Dataset not found at: {data_yaml}")
        print("\n📥 Dataset should be at: C:\\Users\\Admin\\Desktop\\pfa\\RoadSense\\scripts\\Road-Defect-5")
        return False
    
    print(f"📂 Dataset: {data_yaml}")
    
    # Check device
    if torch.cuda.is_available():
        device = 0
        batch_size = 16
        print(f"🚀 GPU ENABLED: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        training_time = "30-60 minutes"
    else:
        device = 'cpu'
        batch_size = 8
        training_time = "2-3 hours"
        print("⚠️  Using CPU (slower, but will work)")
    
    print(f"\n📊 Training Configuration:")
    print(f"   Model: YOLOv8m (medium)")
    print(f"   Epochs: 100")
    print(f"   Batch: {batch_size}")
    print(f"   Image size: 640")
    print(f"   Device: {device}")
    print(f"   Estimated time: {training_time}")
    print()
    
    # Load model
    print("📦 Loading YOLOv8m pretrained model...")
    model = YOLO('yolov8m.pt')
    
    # Train
    print("\n🔄 Starting training... (this will take 1-3 hours)")
    print("    You can minimize this window - training continues in background")
    print()
    
    try:
        results = model.train(
            data=str(data_yaml),
            epochs=100,
            imgsz=640,
            batch=batch_size,
            name='road_defect_local',
            patience=20,
            save=True,
            device=device,
            workers=2,  # Reduced to avoid memory issues
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
        
        model_path = Path("../models/road_defect_local/weights/best.pt")
        print(f"\n📁 Trained model saved to:")
        print(f"   {model_path.absolute()}")
        
        # Validate
        print("\n📊 Validating model...")
        metrics = model.val()
        print(f"   mAP@50: {metrics.box.map50:.3f}")
        print(f"   mAP@50-95: {metrics.box.map:.3f}")
        
        return str(model_path.absolute())
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def deploy_to_docker(model_path):
    """Copy trained model to Docker container"""
    import subprocess
    
    print("\n🚢 DEPLOYING TO DOCKER CONTAINER")
    print("=" * 60)
    
    try:
        # Copy model to container
        print("📦 Copying model to detection service...")
        result = subprocess.run([
            "docker", "cp", 
            model_path,
            "roadsense-detection:/app/models/road_defect_best.pt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Model copied successfully!")
            
            print("\n🔧 To use the new model, update detector.py:")
            print("   1. Edit: detection-fissures/app/models/detector.py")
            print("   2. Change: self.yolo_model = YOLO('yolov8m.pt')")
            print("   3. To: self.yolo_model = YOLO('/app/models/road_defect_best.pt')")
            print("   4. Rebuild: docker-compose up -d --build detection-service")
            
            return True
        else:
            print(f"❌ Failed to copy model: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("🎯 LOCAL TRAINING + DOCKER DEPLOYMENT")
    print("=" * 60)
    print("\nThis will:")
    print("  1. Train YOLOv8 on your local machine (1-3 hours)")
    print("  2. Save trained model")
    print("  3. Copy model to Docker container")
    print("  4. Keep your Docker services running")
    print()
    
    print("🚀 Starting automatically in 3 seconds...")
    import time
    time.sleep(3)
    
    # Train
    model_path = train_model()
    
    if model_path:
        # Deploy
        deploy_to_docker(model_path)
        
        print("\n🎉 SUCCESS!")
        print("   Your Docker services are still running")
        print("   Model is trained and ready to deploy")

if __name__ == "__main__":
    main()
