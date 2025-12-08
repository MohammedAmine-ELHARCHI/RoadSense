"""
Monitor YOLOv8 Training Progress

This script checks the training progress inside the Docker container.
"""

import subprocess
import time
import os

def check_training_status():
    """Check if training is running"""
    result = subprocess.run(
        ['docker', 'exec', 'roadsense-detection', 'ps', 'aux'],
        capture_output=True,
        text=True
    )
    
    if 'train_yolo.py' in result.stdout:
        return True
    return False

def get_training_logs():
    """Get recent training output"""
    try:
        # Check if results file exists
        result = subprocess.run(
            ['docker', 'exec', 'roadsense-detection', 'ls', '/app/models/road_defect_trained'],
            capture_output=True,
            text=True
        )
        
        if 'results.csv' in result.stdout:
            # Read last few lines of results
            result = subprocess.run(
                ['docker', 'exec', 'roadsense-detection', 'tail', '-n', '10', '/app/models/road_defect_trained/results.csv'],
                capture_output=True,
                text=True
            )
            return result.stdout
        else:
            return "Training just started, results file not yet created..."
    except:
        return "Unable to read training logs"

def main():
    print("🔍 YOLOV8 TRAINING MONITOR")
    print("=" * 60)
    
    if not check_training_status():
        print("❌ Training is not running!")
        print("\nTo start training:")
        print("  docker exec -d roadsense-detection python3 train_yolo.py --data /app/data/data.yaml --epochs 100")
        return
    
    print("✅ Training is running!\n")
    
    print("📊 Recent Training Metrics:")
    print("-" * 60)
    logs = get_training_logs()
    print(logs)
    print("-" * 60)
    
    print("\n📁 Training Output Location:")
    print("   Container: /app/models/road_defect_trained/")
    print("   Weights: /app/models/road_defect_trained/weights/best.pt")
    
    print("\n⏱️  Estimated Time:")
    print("   ~1-3 hours for 100 epochs (depends on GPU)")
    print("   Current batch: 16 images")
    print("   Total images: 798")
    
    print("\n🔄 To check progress again:")
    print("   python monitor_training.py")
    
    print("\n📋 To view full logs:")
    print("   docker exec roadsense-detection tail -f /app/models/road_defect_trained/train.log")
    
    print("\n📊 View results in real-time:")
    print("   1. Copy results folder from container:")
    print("      docker cp roadsense-detection:/app/models/road_defect_trained ../models/")
    print("   2. Open results.png, confusion_matrix.png, etc.")
    
    print("\n🛑 To stop training:")
    print("   docker exec roadsense-detection pkill -f train_yolo.py")

if __name__ == "__main__":
    main()
