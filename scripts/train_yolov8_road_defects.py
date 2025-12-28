"""
Train YOLOv8 model for road defect detection
"""
from ultralytics import YOLO
import torch
import os
import glob

def main():
    # Check if GPU is available
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🔧 Using device: {device}")
    
    # Find the most recent checkpoint
    checkpoint_pattern = 'runs/road_defect/yolov8m_road_defect*/weights/last.pt'
    checkpoints = glob.glob(checkpoint_pattern)
    
    if checkpoints:
        # Get the most recent checkpoint by modification time
        latest_checkpoint = max(checkpoints, key=os.path.getmtime)
        print(f"📦 Resuming from checkpoint: {latest_checkpoint}")
        model = YOLO(latest_checkpoint)
        resume = True
    else:
        print("🆕 Starting fresh training from pretrained yolov8m.pt")
        model = YOLO('yolov8m.pt')  # medium model for better accuracy
        resume = False

    # Train the model
    results = model.train(
        data='Road-Defect-5/data.yaml',
        epochs=100,
        imgsz=640,
        batch=16,
        device=device,
        project='runs/road_defect',
        name='yolov8m_road_defect',
        patience=20,
        save=True,
        plots=True,
        val=True,
        resume=resume,
        verbose=True,
        workers=0  # Disable multiprocessing on Windows
    )

    print("✅ Training complete!")
    print(f"📦 Best model saved at: runs/road_defect/yolov8m_road_defect/weights/best.pt")

if __name__ == '__main__':
    main()
