"""
Train YOLOv8 model for road defect detection

This script trains a YOLOv8 model on road defect datasets.
Make sure you have prepared your dataset in YOLO format first.

Usage:
    python train_yolo.py --data config/data.yaml --epochs 100 --batch 16
"""

from ultralytics import YOLO
import argparse
import torch

def main():
    parser = argparse.ArgumentParser(description='Train YOLOv8 for road defect detection')
    parser.add_argument('--data', type=str, required=True, help='Path to data.yaml')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch', type=int, default=16, help='Batch size')
    parser.add_argument('--imgsz', type=int, default=640, help='Image size')
    parser.add_argument('--model', type=str, default='yolov8m.pt', help='Base model')
    parser.add_argument('--device', type=int, default=0, help='GPU device')
    parser.add_argument('--project', type=str, default='runs/detect', help='Project folder')
    parser.add_argument('--name', type=str, default='roadsense_defect', help='Experiment name')
    
    args = parser.parse_args()
    
    # Check GPU availability
    if torch.cuda.is_available():
        print(f"✅ GPU available: {torch.cuda.get_device_name(args.device)}")
    else:
        print("⚠️  No GPU available, training on CPU (will be slower)")
    
    # Load model
    print(f"📦 Loading model: {args.model}")
    model = YOLO(args.model)
    
    # Train
    print(f"🚀 Starting training...")
    print(f"   Dataset: {args.data}")
    print(f"   Epochs: {args.epochs}")
    print(f"   Batch size: {args.batch}")
    print(f"   Image size: {args.imgsz}")
    
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        patience=20,
        save=True,
        project=args.project,
        name=args.name,
        exist_ok=True,
        pretrained=True,
        optimizer='AdamW',
        verbose=True,
        seed=42,
        deterministic=True,
        single_cls=False,
        rect=False,
        cos_lr=True,
        close_mosaic=10,
        resume=False,
        amp=True,
        fraction=1.0,
        profile=False,
        freeze=None,
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        pose=12.0,
        kobj=1.0,
        label_smoothing=0.0,
        nbs=64,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
        copy_paste=0.0
    )
    
    # Validate
    print("\n📊 Validating model...")
    metrics = model.val()
    
    print("\n✅ Training complete!")
    print(f"   Best model saved at: {args.project}/{args.name}/weights/best.pt")
    print(f"   mAP50: {metrics.box.map50:.4f}")
    print(f"   mAP50-95: {metrics.box.map:.4f}")
    
    # Export to ONNX (optional)
    print("\n📤 Exporting to ONNX...")
    try:
        model.export(format='onnx')
        print("✅ ONNX export successful")
    except Exception as e:
        print(f"⚠️  ONNX export failed: {e}")

if __name__ == "__main__":
    main()
