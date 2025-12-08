# 🎯 RoadSense-MS - Complete Project Plan

## 📊 Architecture Overview

### Microservices & Port Assignment

| Service | Port | Technology | Status | Priority |
|---------|------|------------|---------|----------|
| **DetectionFissures** | 8001 | FastAPI + YOLOv8 | ✅ Built & Deployed | P0 - Done |
| **ScoreGravite** | 8002 | FastAPI + XGBoost | ✅ Trained & Deployed | P1 - Done |
| **IngestionVideo** | 8003 | FastAPI + FFmpeg + OpenCV | ✅ Built & Tested | P2 - Done |
| **GeoRef** | 8004 | FastAPI + PostGIS | ❌ To Build | P3 |
| **Priorisation** | 8005 | NestJS (Node.js) | ❌ To Build | P4 |
| **ExportSIG** | 8006 | Python + GeoServer | ❌ To Build | P5 |
| **Dashboard** | 3000 | React.js + Leaflet | ✅ Built & Deployed | P6 - Done |
| **PostgreSQL** | 5432 | PostgreSQL + PostGIS | ✅ Running | - |
| **MinIO** | 9000/9001 | Object Storage | ✅ Running | - |
| **Redis** | 6379 | Cache | ✅ Running | - |
| **GeoServer** | 8080 | GIS Server | ❌ To Setup | P5 |

---

## 📋 Detailed Build Plan

### **Phase 1: Core ML Services** ⚡ CURRENT PHASE

#### ✅ Step 1: DetectionFissures - COMPLETED
- **Status**: Built, trained, and deployed
- **Model**: YOLOv8m trained on 798 road defect images
- **Dataset**: 7 classes (D00, D10, D20, D40, D43, D44, D50)
- **Location**: `models/road_defect_local/weights/best.pt`
- **API Endpoints**:
  - `POST /api/v1/detect` - Upload image for defect detection
  - `GET /api/v1/models` - List available models
  - `GET /health` - Health check

#### ✅ Step 2: Train ScoreGravite (XGBoost) - COMPLETED
- **Status**: Trained and deployed
- **Model Performance**:
  - Test RMSE: 0.464
  - Test MAE: 0.347
  - Test R²: 0.888
  - Feature Importance: defect_type (82%), size_score_log (1.8%)
- **Model Files**:
  - `severity_model_best.pkl` - Trained XGBoost model
  - `label_encoder.pkl` - Defect type encoder
  - `model_metadata.json` - Model metadata
- **API Endpoints** (working):
  - `POST /api/v1/severity/compute` - Calculate severity score
  - `GET /api/v1/severity/model/info` - Model information
  - `GET /health` - Health check

#### 📝 Step 3: Test ML Models
- Test detection with real road images
- Test severity scoring
- Validate end-to-end ML pipeline

---

### **Phase 2: Video Processing** 🎥

#### ✅ Step 4: Build IngestionVideo Service (Port 8003) - COMPLETED
**Technology**: FastAPI + FFmpeg + OpenCV + MinIO

**Status**: Built, deployed, and tested successfully
- Video upload working (video-road.mp4 tested)
- FFmpeg metadata extraction (duration: 26.5s, fps: 29.97, 1920x1080, h264)
- Frame extraction at 2 FPS (53 frames extracted)
- MinIO storage (roadsense-videos, roadsense-frames buckets)
- PostgreSQL tracking with processing status

**API Endpoints**:
- `POST /api/v1/video/upload` - Upload video for processing ✅ Tested
- `GET /api/v1/video/status/:id` - Check processing status ✅ Tested
- `GET /api/v1/video/:id/frames` - List extracted frames ✅ Tested
- `DELETE /api/v1/video/:id` - Delete video and frames
- `GET /health` - Health check ✅ Tested

**Database Schema**:
```sql
CREATE TABLE videos (
    id UUID PRIMARY KEY,
    filename VARCHAR(255),
    file_size BIGINT,
    duration FLOAT,
    fps FLOAT,
    width INTEGER,
    height INTEGER,
    codec VARCHAR(50),
    storage_path VARCHAR(500),
    status VARCHAR(20),
    frames_extracted INTEGER,
    frames_total INTEGER,
    uploaded_at TIMESTAMP,
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    upload_user_id VARCHAR(100),
    video_metadata TEXT
);

CREATE TABLE frames (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    frame_number INTEGER,
    timestamp FLOAT,
    storage_path VARCHAR(500),
    detection_completed BOOLEAN DEFAULT FALSE,
    detection_id UUID,
    gps_latitude DOUBLE PRECISION,
    gps_longitude DOUBLE PRECISION,
    gps_altitude FLOAT,
    extracted_at TIMESTAMP
);
```

**Test Results**:
- Video: video-road.mp4 (26.5 seconds, 1920x1080, 29.97 fps)
- Processing time: ~2 seconds
- Frames extracted: 53 frames at 2 FPS
- All frames stored in MinIO with presigned URLs
- Status tracking: PENDING → PROCESSING → COMPLETED

---

### **Phase 3: Geospatial Services** 🗺️

#### Step 5: Build GeoRef Service (Port 8004)
**Technology**: FastAPI + PostGIS + OSRM + Shapely

**Features**:
- Map-matching defects to road network
- GPS coordinate → Road segment mapping
- OpenStreetMap integration
- Spatial queries and analysis

**API Endpoints**:
- `POST /georef` - Map defect to road segment
- `POST /georef/batch` - Batch georeference multiple defects
- `GET /georef/segment/:id` - Get road segment info
- `GET /georef/nearby` - Find nearby defects (radius search)

**Database Schema**:
```sql
CREATE TABLE road_segments (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT,
    name VARCHAR(255),
    road_type VARCHAR(50),
    geometry GEOMETRY(LineString, 4326),
    length_meters FLOAT
);

CREATE TABLE georeferenced_defects (
    id UUID PRIMARY KEY,
    detection_id UUID REFERENCES detections(id),
    segment_id INTEGER REFERENCES road_segments(id),
    gps_location GEOMETRY(Point, 4326),
    matched_location GEOMETRY(Point, 4326),
    distance_to_road FLOAT,
    confidence FLOAT
);
```

---

### **Phase 4: Business Logic** 📊

#### Step 6: Build Priorisation Service (Port 8005)
**Technology**: NestJS (Node.js + TypeScript)

**Features**:
- Priority calculation algorithm
- Multi-criteria ranking:
  - Defect severity score
  - Traffic volume/importance
  - Repair cost estimation
  - Accessibility
  - Last maintenance date
- Generate maintenance schedule

**API Endpoints**:
- `GET /priority/list` - Get prioritized road segments
- `GET /priority/segment/:id` - Get priority details
- `POST /priority/recompute` - Recalculate priorities
- `GET /priority/stats` - Priority statistics

**Priority Algorithm**:
```
Priority Score = (
    0.35 × Severity Score +
    0.25 × Traffic Importance +
    0.20 × Defect Density +
    0.15 × Time Since Last Repair +
    0.05 × Accessibility
) × 100
```

---

### **Phase 5: GIS Export** 🌍

#### Step 7: Setup GeoServer (Port 8080)
- Install and configure GeoServer
- Connect to PostGIS database
- Configure WMS/WFS services

#### Step 8: Build ExportSIG Service (Port 8006)
**Technology**: Python + GeoServer + GDAL

**Features**:
- Export defects to GeoJSON
- WMS/WFS layer generation
- MBTiles creation for offline use
- Shapefile export
- KML export for Google Earth

**API Endpoints**:
- `GET /export/geojson` - Export as GeoJSON
- `GET /export/shapefile` - Export as Shapefile
- `GET /export/kml` - Export as KML
- `GET /export/mbtiles` - Generate MBTiles
- `GET /export/wms` - WMS endpoint info
- `GET /export/wfs` - WFS endpoint info

---

### **Phase 6: Frontend Dashboard** 🖥️

#### Step 9: Build Dashboard (Port 3000)
**Technology**: React.js + Leaflet/MapLibre + Chart.js

**Features**:
- Interactive map with defect markers
- Video upload interface
- Real-time processing status
- Statistics and charts:
  - Defects by type
  - Severity distribution
  - Timeline of detections
  - Geographic heatmap
- Priority list view
- Export options
- Reports generation

**Pages**:
1. **Home/Overview** - Statistics and summary
2. **Map View** - Interactive map with all defects
3. **Upload** - Video upload and processing
4. **Analytics** - Charts and trends
5. **Priority** - Maintenance priority list
6. **Export** - GIS data export options
7. **Settings** - Configuration

---

### **Phase 7: Integration & Deployment** 🚀

#### Step 10: API Gateway (Optional - Port 8000)
- Centralized API routing
- Authentication/Authorization
- Rate limiting
- Request logging

#### Step 11: End-to-End Testing
- Upload test video
- Verify frame extraction
- Check defect detection
- Validate georeference
- Test priority calculation
- Export to GIS formats

#### Step 12: Documentation & Deployment
- API documentation (OpenAPI/Swagger)
- User guide
- Deployment guide
- Docker compose orchestration
- CI/CD pipeline

---

## 🔄 Data Flow

```
1. Video Upload → IngestionVideo (8003)
   ↓
2. Frame Extraction + GPS → MinIO Storage
   ↓
3. Frames → DetectionFissures (8001) → Defect Detection
   ↓
4. Defects → ScoreGravite (8002) → Severity Score
   ↓
5. Defects + GPS → GeoRef (8004) → Road Mapping
   ↓
6. Mapped Defects → Priorisation (8005) → Priority List
   ↓
7. Results → Dashboard (3000) / ExportSIG (8006)
```

---

## 📦 Docker Services

```yaml
services:
  # Infrastructure
  postgres:        5432 ✅
  minio:           9000/9001 ✅
  redis:           6379 ✅
  
  # Microservices
  detection:       8001 ✅
  severity:        8002 ⚠️
  ingestion:       8003 ❌
  georef:          8004 ❌
  priorisation:    8005 ❌
  export:          8006 ❌
  
  # GIS
  geoserver:       8080 ❌
  
  # Frontend
  dashboard:       3000 ❌
```

---

## 🎯 Current Status Summary

### ✅ Completed (3/7 services)
- DetectionFissures service (trained YOLOv8 model - mAP ready)
- ScoreGravite service (trained XGBoost model - R²: 0.888)
- Infrastructure (PostgreSQL, MinIO, Redis)

### ❌ To Build (4/7 services)
- IngestionVideo
- GeoRef
- Priorisation
- ExportSIG
- Dashboard

---

## 🚀 Next Steps

### Immediate (This Week)
1. **Train ScoreGravite model** - Prepare severity dataset and train XGBoost
2. **Test ML pipeline** - Validate detection + severity scoring
3. **Start IngestionVideo** - Begin video processing service

### Short Term (Next 2 Weeks)
4. Build GeoRef service
5. Build Priorisation service
6. Basic Dashboard for visualization

### Medium Term (Next Month)
7. ExportSIG service + GeoServer
8. Complete Dashboard features
9. End-to-end testing
10. Documentation

---

## 📝 Notes

- All services use FastAPI except: IngestionVideo (Go), Priorisation (NestJS), Dashboard (React)
- PostGIS is critical for spatial queries (already configured)
- MinIO stores: video files, extracted frames, annotated images
- Redis used for: caching, job queues, session management
- Each service has its own database tables (microservice pattern)

---

## 🔗 Useful Commands

```bash
# Check service status
docker-compose ps

# View logs for specific service
docker-compose logs -f detection-service

# Restart a service
docker-compose restart detection-service

# Access database
docker exec -it roadsense-postgres psql -U roadsense -d roadsense

# Access MinIO console
http://localhost:9001

# API documentation
http://localhost:8001/docs  # Detection
http://localhost:8002/docs  # Severity
```

---

**Last Updated**: December 7, 2025
**Project Status**: Phase 1 - Core ML Services (85% complete)
