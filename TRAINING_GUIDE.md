# 🎓 Training Guide - Road Defect Detection Model

This guide will walk you through training the YOLOv8 model for road defect detection.

## 📋 Prerequisites

- Docker containers running (detection service already has YOLOv8 installed)
- At least 8GB RAM (16GB recommended)
- GPU with CUDA support (recommended but optional)

## 🚀 Quick Start (3 Options)

### Option 1: Use Roboflow Public Dataset (Recommended - Easiest)

```bash
cd C:\Users\Admin\Desktop\pfa\RoadSense\scripts

# 1. Get instructions
python download_roboflow.py

# 2. After following instructions, download dataset
python download_roboflow.py --api-key YOUR_KEY --workspace WORKSPACE --project PROJECT

# 3. Train with downloaded data
cd ../detection-fissures
python train_yolo.py --data PATH_TO_DOWNLOADED_DATASET/data.yaml --epochs 50
```

**Roboflow Steps:**
1. Visit https://roboflow.com and sign up (free)
2. Go to https://universe.roboflow.com
3. Search "road defect" or "pothole detection"
4. Choose a dataset with 500+ images
5. Click "Download" → Select "YOLOv8" format
6. Follow the code snippet provided

### Option 2: Use Sample Images for Testing

```bash
cd C:\Users\Admin\Desktop\pfa\RoadSense\scripts

# Create sample dataset structure
python quick_train.py --mode sample

# Manually add 20-50 road images to:
#   data/sample_dataset/train/images/
#   data/sample_dataset/val/images/

# Create labels (one .txt per image with YOLO format)
# Format: class_id x_center y_center width height (all normalized 0-1)

# Train
python quick_train.py --mode full --data ../data/sample_dataset/data.yaml --epochs 30
```

### Option 3: Use Pre-existing Dataset (Manual)

If you have your own road images:

```bash
# 1. Organize your data:
data/
└── my_dataset/
    ├── train/
    │   ├── images/
    │   └── labels/
    ├── val/
    │   ├── images/
    │   └── labels/
    └── data.yaml

# 2. Create data.yaml:
# path: C:/Users/Admin/Desktop/pfa/RoadSense/data/my_dataset
# train: train/images
# val: val/images
# names:
#   0: crack
#   1: pothole
#   2: alligator_crack
#   3: patch
# nc: 4

# 3. Train
cd detection-fissures
python train_yolo.py --data ../data/my_dataset/data.yaml --epochs 100
```

## 📊 Training Inside Docker Container

For training with GPU support using the detection service container:

```bash
# Enter the container
docker exec -it roadsense-detection bash

# Inside container, mount dataset and train
cd /app
python train_yolo.py --data /path/to/data.yaml --epochs 100 --device 0
```

## 🎯 Training Parameters Explained

### Basic Parameters
- `--data`: Path to data.yaml configuration file
- `--epochs`: Number of training epochs (default: 100)
  - Start with 30-50 for testing
  - Use 100-200 for production models
- `--batch`: Batch size (default: 16)
  - Reduce if you run out of memory (try 8 or 4)
  - Increase if you have more GPU memory (32, 64)
- `--imgsz`: Image size (default: 640)
  - 640 is good balance of speed/accuracy
  - 1280 for higher accuracy (slower)

### Model Selection
- `--model yolov8n.pt`: Nano (fastest, least accurate)
- `--model yolov8s.pt`: Small
- `--model yolov8m.pt`: Medium (default, good balance)
- `--model yolov8l.pt`: Large
- `--model yolov8x.pt`: Extra large (most accurate, slowest)

### Examples

```bash
# Quick test training (5 minutes)
python train_yolo.py --data data.yaml --epochs 10 --batch 8 --model yolov8n.pt

# Balanced training (1-2 hours)
python train_yolo.py --data data.yaml --epochs 50 --batch 16 --model yolov8m.pt

# Production training (4-8 hours)
python train_yolo.py --data data.yaml --epochs 200 --batch 32 --model yolov8l.pt
```

## 📈 Monitoring Training

Training outputs are saved to:
```
detection-fissures/runs/detect/roadsense_defect/
├── weights/
│   ├── best.pt      # Best model weights
│   └── last.pt      # Latest model weights
├── results.png      # Training metrics plots
├── confusion_matrix.png
├── F1_curve.png
└── PR_curve.png
```

### Real-time Monitoring with TensorBoard

```bash
# In another terminal
cd detection-fissures
tensorboard --logdir runs/detect
# Open http://localhost:6006
```

## 🔄 Transfer Learning Benefits

YOLOv8 uses transfer learning from COCO dataset:
- Faster convergence (needs fewer epochs)
- Better performance with small datasets
- Already knows general object detection

## 🎨 Data Augmentation

YOLOv8 automatically applies:
- Mosaic augmentation
- Random flips
- HSV color adjustments
- Random scaling/translation

Configured in train_yolo.py:
```python
fliplr=0.5,      # 50% horizontal flip
hsv_h=0.015,     # Hue variation
hsv_s=0.7,       # Saturation
hsv_v=0.4,       # Value
translate=0.1,   # Translation
scale=0.5        # Scaling
```

## ✅ Validation & Testing

```bash
# Validate trained model
python -c "from ultralytics import YOLO; model = YOLO('runs/detect/roadsense_defect/weights/best.pt'); model.val()"

# Test on single image
python -c "from ultralytics import YOLO; model = YOLO('runs/detect/roadsense_defect/weights/best.pt'); results = model('path/to/test/image.jpg'); results[0].save('result.jpg')"

# Test with API
curl -X POST http://localhost:8001/api/v1/detect \
  -F "file=@test_image.jpg" \
  -F "confidence_threshold=0.5"
```

## 🐛 Common Issues & Solutions

### Issue: Out of Memory (OOM)
**Solution:** Reduce batch size
```bash
python train_yolo.py --data data.yaml --batch 4  # or even --batch 1
```

### Issue: Training too slow
**Solution:** Use smaller model or reduce image size
```bash
python train_yolo.py --data data.yaml --model yolov8n.pt --imgsz 320
```

### Issue: Poor accuracy
**Solutions:**
1. Get more training data (500+ images minimum)
2. Increase epochs (100-200)
3. Check label quality
4. Use larger model (yolov8l.pt or yolov8x.pt)

### Issue: Not detecting small defects
**Solution:** Increase image size
```bash
python train_yolo.py --data data.yaml --imgsz 1280
```

## 📊 Expected Results

With good quality dataset (1000+ images):
- **mAP@0.5**: 0.70-0.85 (70-85% accuracy)
- **Precision**: 0.75-0.90
- **Recall**: 0.70-0.85

Training time estimates (on RTX 3080):
- 50 epochs: ~1 hour
- 100 epochs: ~2 hours
- 200 epochs: ~4 hours

## 🎯 Next Steps After Training

1. **Copy model to detection service:**
```bash
# Copy trained weights to detection service
docker cp runs/detect/roadsense_defect/weights/best.pt roadsense-detection:/app/models/
```

2. **Update detector to use new model:**
```python
# In detection-fissures/app/models/detector.py
self.yolo_model = YOLO('/app/models/best.pt')
```

3. **Restart service:**
```bash
docker-compose restart detection-service
```

4. **Test with API:**
```bash
curl -X POST http://localhost:8001/api/v1/detect \
  -F "file=@test_road_image.jpg" \
  -F "confidence_threshold=0.5"
```

## 📚 Additional Resources

- YOLOv8 Documentation: https://docs.ultralytics.com
- Roboflow Universe: https://universe.roboflow.com
- YOLO Format Guide: https://docs.ultralytics.com/datasets/
- Training Tips: https://docs.ultralytics.com/guides/

## 💡 Pro Tips

1. **Start small:** Train with 10 epochs first to verify everything works
2. **Use validation set:** Always split data (70% train, 20% val, 10% test)
3. **Monitor metrics:** Watch for overfitting (val loss increases while train loss decreases)
4. **Label quality matters:** Better to have 500 well-labeled images than 2000 poor ones
5. **Class balance:** Try to have similar number of samples for each defect type
6. **Augmentation:** More data augmentation helps with small datasets

---

Ready to start training? Choose one of the three options above! 🚀
