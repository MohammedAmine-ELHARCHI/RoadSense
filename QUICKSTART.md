# RoadSense - Quick Start Guide

This guide will help you get the RoadSense system up and running quickly.

## Prerequisites

- **Docker** & **Docker Compose** installed
- **NVIDIA GPU** with CUDA support (for ML services)
- **NVIDIA Container Toolkit** installed
- **16GB+ RAM** recommended
- **50GB+ disk space** for models and data

## Installation Steps

### 1. Clone the Repository

```powershell
cd C:\Users\Admin\Desktop\pfa
cd RoadSense
```

### 2. Set Up Environment Variables

```powershell
# Copy the example environment file
Copy-Item .env.example .env

# Edit .env with your preferred settings (optional)
notepad .env
```

### 3. Download Road Defect Datasets

You need to download and prepare datasets before training models:

```powershell
# Create data directory
New-Item -ItemType Directory -Path "data" -Force
cd data

# Download RDD2022 (Road Damage Detection 2022)
# Visit: https://github.com/sekilab/RoadDamageDetector
# Download and extract to: data/rdd2022/

# Download Crack500
# Visit: https://github.com/fyangneil/pavement-crack-detection
# Download and extract to: data/crack500/

cd ..
```

### 4. Prepare Dataset for YOLOv8

```powershell
# Organize dataset in YOLO format
python scripts/prepare_dataset.py

# This will create:
# data/processed/
# ├── train/
# │   ├── images/
# │   └── labels/
# ├── val/
# │   ├── images/
# │   └── labels/
# └── test/
#     ├── images/
#     └── labels/
```

### 5. Train YOLOv8 Model (Optional but Recommended)

```powershell
cd detection-fissures

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Train the model
python train_yolo.py --data config/data.yaml --epochs 100 --batch 16

# The trained model will be saved to: runs/detect/roadsense_defect/weights/best.pt
# Copy it to: models/yolo/best.pt
```

### 6. Start All Services with Docker Compose

```powershell
# Build and start all services
docker-compose up -d --build

# Check if all services are running
docker-compose ps

# View logs
docker-compose logs -f
```

### 7. Initialize the Database

```powershell
# The database is automatically initialized via init.sql
# Verify it's working
docker-compose exec postgres psql -U roadsense_user -d roadsense -c "\dt"
```

### 8. Access the Services

Once all services are running:

- **Detection API Documentation**: http://localhost:8001/docs
- **Severity API Documentation**: http://localhost:8002/docs
- **MinIO Console**: http://localhost:9001
  - Username: `roadsense_access`
  - Password: `roadsense_secret_key_2025`
- **PostgreSQL**: localhost:5432
  - Database: `roadsense`
  - User: `roadsense_user`
  - Password: `roadsense_password_2025`

## Testing the Detection Service

### Using cURL (PowerShell):

```powershell
# Test health endpoint
Invoke-WebRequest -Uri "http://localhost:8001/health"

# Test detection with an image
$image = "C:\path\to\road_image.jpg"
$uri = "http://localhost:8001/api/v1/detection/detect"

$fileBin = [System.IO.File]::ReadAllBytes($image)
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"image`"; filename=`"road.jpg`"",
    "Content-Type: image/jpeg$LF",
    [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($fileBin),
    "--$boundary",
    "Content-Disposition: form-data; name=`"confidence_threshold`"$LF",
    "0.5",
    "--$boundary--$LF"
) -join $LF

Invoke-RestMethod -Uri $uri -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyLines
```

### Using Python:

```python
import requests

url = "http://localhost:8001/api/v1/detection/detect"
files = {"image": open("road_image.jpg", "rb")}
data = {"confidence_threshold": 0.5}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Using the Interactive API Docs:

1. Navigate to http://localhost:8001/docs
2. Click on `/api/v1/detection/detect`
3. Click "Try it out"
4. Upload an image file
5. Click "Execute"

## Viewing Results

### Get Detection Statistics:

```powershell
Invoke-WebRequest -Uri "http://localhost:8001/api/v1/detection/stats" | ConvertFrom-Json
```

### Get Results for a Specific Image:

```powershell
$imageId = "your-image-uuid-here"
Invoke-WebRequest -Uri "http://localhost:8001/api/v1/detection/results/$imageId" | ConvertFrom-Json
```

### View Annotated Images:

1. Go to MinIO Console: http://localhost:9001
2. Login with credentials from .env
3. Navigate to `annotated-images` bucket
4. View/download annotated images

## Development Mode

### Run Detection Service Locally:

```powershell
cd detection-fissures
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt

# Set environment variables
$env:POSTGRES_HOST = "localhost"
$env:MINIO_ENDPOINT = "localhost:9000"

# Run service
uvicorn main:app --reload --port 8001
```

### Run Severity Service Locally:

```powershell
cd score-gravite
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt

uvicorn main:app --reload --port 8002
```

## Troubleshooting

### GPU Not Detected:

```powershell
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If this fails, install NVIDIA Container Toolkit:
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### MinIO Buckets Not Created:

```powershell
# Manually create buckets
docker-compose exec minio-client /bin/sh
mc config host add roadsense http://minio:9000 roadsense_access roadsense_secret_key_2025
mc mb roadsense/raw-videos
mc mb roadsense/extracted-frames
mc mb roadsense/annotated-images
mc mb roadsense/segmentation-masks
mc mb roadsense/metadata
exit
```

### Database Connection Issues:

```powershell
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Connect manually
docker-compose exec postgres psql -U roadsense_user -d roadsense
```

### Services Not Starting:

```powershell
# Check logs for errors
docker-compose logs detection-service
docker-compose logs severity-service

# Restart specific service
docker-compose restart detection-service
```

## Next Steps

1. **Train Your Model**: Follow the training guide to train YOLOv8 on road defect datasets
2. **Prepare Severity Model**: Collect labeled data and train the XGBoost severity model
3. **Set Up Frontend**: Build the Vue.js dashboard to visualize detections
4. **Configure OSRM**: Download OSM data and set up map-matching for georeferencing
5. **Implement Video Ingestion**: Build the Go service for video processing

## Stopping Services

```powershell
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Support

For issues or questions:
- Check the logs: `docker-compose logs [service-name]`
- Review the API documentation: http://localhost:8001/docs
- Contact your project supervisor
