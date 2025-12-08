# RoadSense - Intelligent Road Analysis System

## Project Overview
RoadSense is an intelligent system for automatic road analysis via embedded videos (dashcam/drone) to identify cracks, potholes, geolocate degradations, and generate a prioritization map.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Vue 3)                        │
│                    Road Defect Visualization                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                              │
└─────┬─────────┬──────────────┬─────────────┬────────────────────┘
      │         │              │             │
      ▼         ▼              ▼             ▼
┌──────────┐ ┌────────┐ ┌──────────┐ ┌─────────────┐
│Ingestion │ │Detection│ │  Score   │ │   GeoRef    │
│  Video   │ │Fissures │ │ Gravite  │ │   Service   │
│  (Go)    │ │(Python) │ │(Python)  │ │  (Python)   │
└────┬─────┘ └───┬────┘ └────┬─────┘ └──────┬──────┘
     │           │            │              │
     └───────────┴────────────┴──────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
    ┌──────────┐          ┌──────────────┐
    │  MinIO   │          │ PostgreSQL   │
    │ Storage  │          │  + PostGIS   │
    └──────────┘          └──────────────┘
```

## Services

### 1. **detection-fissures** (Python - FastAPI)
- YOLOv8 for object detection
- Detectron2 for instance segmentation
- Detects cracks, potholes, alligator cracks, patches
- REST API for defect detection

### 2. **score-gravite** (Python - FastAPI)
- XGBoost model for severity scoring
- Risk assessment and prioritization
- Feature engineering from defect data

### 3. **ingestion-video** (Go)
- Video upload and processing
- Frame extraction with GStreamer/FFmpeg
- GPS/IMU metadata extraction
- MinIO storage integration

### 4. **georef** (Python - FastAPI)
- Map-matching with OSRM
- Georeferencing defects to road network
- PostGIS spatial queries

### 5. **data-mining** (Python - Jupyter)
- Exploratory data analysis
- Pattern mining and clustering
- Predictive analytics

## Technology Stack

- **ML/DL**: PyTorch, YOLOv8, Detectron2, XGBoost, Scikit-learn
- **Backend**: Python FastAPI, Go
- **Database**: PostgreSQL with PostGIS extension
- **Storage**: MinIO object storage
- **Video Processing**: GStreamer, FFmpeg
- **Containerization**: Docker & Docker Compose
- **Frontend**: Vue 3, TypeScript, Leaflet/Mapbox

## Quick Start

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU with CUDA support (for ML services)
- 16GB+ RAM recommended

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YasserAet/RoadSense.git
cd RoadSense
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start all services:
```bash
docker-compose up -d
```

4. Initialize the database:
```bash
docker-compose exec detection-service python scripts/init_db.py
```

5. Access the services:
- Frontend: http://localhost:5173
- Detection API: http://localhost:8001/docs
- Severity API: http://localhost:8002/docs
- MinIO Console: http://localhost:9001

## Development Setup

### Detection Service (ML/DL)
```bash
cd detection-fissures
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Severity Service
```bash
cd score-gravite
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

### Ingestion Service (Go)
```bash
cd ingestion-video
go mod download
go run cmd/server/main.go
```

## Dataset Preparation

Download required datasets:
```bash
# RDD2022 (Road Damage Detection)
wget https://github.com/sekilab/RoadDamageDetector/releases/download/v1.0/RDD2022_all_countries.zip

# Crack500
git clone https://github.com/fyangneil/pavement-crack-detection.git
```

Organize datasets:
```bash
python scripts/prepare_dataset.py --source rdd2022 --output data/processed
```

## Training Models

### Train YOLOv8:
```bash
cd detection-fissures
python train_yolo.py --data config/data.yaml --epochs 100 --batch 16
```

### Train XGBoost Severity Model:
```bash
cd score-gravite
python train_severity_model.py --data data/severity_training.csv
```

## API Documentation

Once services are running, visit:
- Detection API: http://localhost:8001/docs
- Severity API: http://localhost:8002/docs

## Project Structure

```
RoadSense/
├── detection-fissures/       # ML/DL defect detection service
│   ├── app/
│   │   ├── api/             # FastAPI routes
│   │   ├── models/          # ML model wrappers
│   │   ├── storage/         # MinIO integration
│   │   └── database/        # PostgreSQL integration
│   ├── models/              # Trained model weights
│   ├── notebooks/           # Training notebooks
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py
│
├── score-gravite/           # Severity scoring service
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   └── database/
│   ├── models/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py
│
├── ingestion-video/         # Video processing service (Go)
│   ├── cmd/
│   │   └── server/
│   ├── internal/
│   │   ├── api/
│   │   ├── video/
│   │   ├── metadata/
│   │   └── storage/
│   ├── go.mod
│   ├── Dockerfile
│   └── main.go
│
├── georef/                  # Georeferencing service
│   ├── app/
│   ├── requirements.txt
│   └── main.py
│
├── data-mining/            # Data analysis notebooks
│   ├── notebooks/
│   │   ├── 01_eda.ipynb
│   │   ├── 02_clustering.ipynb
│   │   ├── 03_pattern_mining.ipynb
│   │   └── 04_predictive.ipynb
│   └── requirements.txt
│
├── frontend/               # Vue 3 frontend
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── infrastructure/         # Infrastructure configs
│   ├── postgresql/
│   │   └── init.sql
│   ├── minio/
│   └── nginx/
│
├── scripts/               # Utility scripts
│   ├── init_db.py
│   ├── prepare_dataset.py
│   └── download_models.py
│
├── docker-compose.yml
├── .env.example
└── README.md
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Testing

```bash
# Run all tests
docker-compose exec detection-service pytest

# Run specific service tests
cd detection-fissures
pytest tests/
```

## Stakeholders

- **Prof Lachgar** - Project Supervisor
- **Prof ML/DL** - Machine Learning Advisor
- **Prof Datamining** - Data Analysis Advisor

## License

This project is part of an academic final year project (PFA).

## Documentation

- [Model Cards](docs/model_cards/)
- [API Documentation](docs/api/)
- [Training Guide](docs/training.md)
- [Deployment Guide](docs/deployment.md)
