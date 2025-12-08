"""
Train YOLOv8 model for road defect detection
"""
from ultralytics import YOLO
import torch

def main():
    # Check if GPU is available
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🔧 Using device: {device}")

    # Load a pretrained YOLOv8 model
    model = YOLO('yolov8m.pt')  # medium model for better accuracy

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
        resume=False,
        verbose=True,
        workers=0  # Disable multiprocessing on Windows
    )

    print("✅ Training complete!")
    print(f"📦 Best model saved at: runs/road_defect/yolov8m_road_defect/weights/best.pt")

if __name__ == '__main__':
    main()
