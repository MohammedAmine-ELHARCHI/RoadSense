# RoadSense Setup Checklist

Use this checklist to ensure your RoadSense system is properly configured and running.

## ✅ Prerequisites

- [ ] Docker Desktop installed (version 20.10+)
- [ ] Docker Compose installed (version 2.0+)
- [ ] NVIDIA GPU with CUDA support (optional but recommended)
- [ ] NVIDIA Container Toolkit installed (for GPU support)
- [ ] 16GB+ RAM available
- [ ] 50GB+ free disk space
- [ ] Git installed
- [ ] Python 3.10+ installed (for local development)

## ✅ Project Setup

- [ ] Navigated to `C:\Users\Admin\Desktop\pfa\RoadSense` directory
- [ ] Copied `.env.example` to `.env`
- [ ] Reviewed and updated `.env` file if needed
- [ ] Created `data/raw` directory for datasets
- [ ] Created `data/processed` directory for prepared datasets

## ✅ Dataset Preparation

- [ ] Downloaded RDD2022 dataset
- [ ] Downloaded Crack500 dataset
- [ ] Extracted datasets to `data/raw/rdd2022` and `data/raw/crack500`
- [ ] Ran `python scripts/prepare_dataset.py` to prepare data
- [ ] Verified `data/processed/train`, `val`, `test` folders created
- [ ] Checked that images and labels are correctly organized

## ✅ Docker Infrastructure

- [ ] Ran `docker-compose up -d --build` to start all services
- [ ] Verified all containers are running: `docker-compose ps`
- [ ] Checked PostgreSQL is healthy: `docker-compose logs postgres`
- [ ] Checked MinIO is healthy: `docker-compose logs minio`
- [ ] Verified MinIO buckets created: `docker-compose logs minio-client`
- [ ] Accessed MinIO console at http://localhost:9001 (login with credentials from .env)
- [ ] Verified buckets exist: `raw-videos`, `extracted-frames`, `annotated-images`, `segmentation-masks`, `metadata`

## ✅ Detection Service

- [ ] Detection service container running: `docker-compose logs detection-service`
- [ ] Accessed API docs at http://localhost:8001/docs
- [ ] Health check passes: http://localhost:8001/health
- [ ] Model info endpoint works: http://localhost:8001/api/v1/models/info
- [ ] Uploaded test image and got detection results
- [ ] Verified annotated image saved to MinIO
- [ ] Checked database for detection results

## ✅ Severity Service

- [ ] Severity service container running: `docker-compose logs severity-service`
- [ ] Accessed API docs at http://localhost:8002/docs
- [ ] Health check passes: http://localhost:8002/health

## ✅ Database Verification

- [ ] Connected to PostgreSQL: `docker-compose exec postgres psql -U roadsense_user -d roadsense`
- [ ] Verified tables exist: `\dt`
- [ ] Checked table structure: `\d detection_results`
- [ ] PostGIS extension enabled: `SELECT PostGIS_version();`
- [ ] Sample query works: `SELECT COUNT(*) FROM detection_results;`

## ✅ Model Training (Optional)

- [ ] Created Python virtual environment in `detection-fissures/`
- [ ] Installed requirements: `pip install -r requirements.txt`
- [ ] Updated `config/data.yaml` with correct paths
- [ ] Started training: `python train_yolo.py --data config/data.yaml --epochs 100`
- [ ] Training completed without errors
- [ ] Model saved to `runs/detect/roadsense_defect/weights/best.pt`
- [ ] Copied trained model to `models/yolo/best.pt`
- [ ] Restarted detection service to load new model
- [ ] Verified improved detection accuracy

## ✅ API Testing

### Detection Endpoint:
- [ ] POST `/api/v1/detection/detect` - Single image detection works
- [ ] POST `/api/v1/detection/batch` - Batch detection works
- [ ] GET `/api/v1/detection/results/{image_id}` - Retrieve results works
- [ ] GET `/api/v1/detection/stats` - Statistics endpoint works

### Model Info:
- [ ] GET `/api/v1/models/info` - Returns model information
- [ ] GET `/api/v1/models/health` - Health check passes

## ✅ Storage Verification

- [ ] Images uploaded to MinIO successfully
- [ ] Annotated images viewable in MinIO console
- [ ] Presigned URLs generated correctly
- [ ] Images downloadable from MinIO

## ✅ Performance Testing

- [ ] Single image detection completes in < 1 second (with GPU)
- [ ] Batch detection handles 10+ images
- [ ] Memory usage acceptable (< 8GB for detection service)
- [ ] GPU utilization visible: `docker-compose exec detection-service nvidia-smi`
- [ ] CPU-only mode works (if no GPU available)

## ✅ Documentation Review

- [ ] Read `README.md` thoroughly
- [ ] Reviewed `QUICKSTART.md` for setup steps
- [ ] Checked `IMPLEMENTATION_SUMMARY.md` for project status
- [ ] Understood API documentation at `/docs` endpoints
- [ ] Reviewed code comments and docstrings

## ✅ Development Setup (Optional)

- [ ] Cloned repository to development machine
- [ ] Set up Python virtual environments for each service
- [ ] Configured IDE (VS Code, PyCharm, etc.)
- [ ] Installed development dependencies
- [ ] Ran services locally (outside Docker)
- [ ] Hot reload works for code changes

## ✅ Troubleshooting

If any checks fail, refer to these commands:

### Check Service Logs:
```powershell
docker-compose logs detection-service
docker-compose logs severity-service
docker-compose logs postgres
docker-compose logs minio
```

### Restart Services:
```powershell
docker-compose restart detection-service
docker-compose restart severity-service
```

### Rebuild Containers:
```powershell
docker-compose down
docker-compose up -d --build
```

### Check Database:
```powershell
docker-compose exec postgres psql -U roadsense_user -d roadsense
```

### Check MinIO:
```powershell
docker-compose exec minio-client mc ls roadsense/
```

### GPU Check:
```powershell
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## ✅ Next Steps

After completing this checklist:

1. **Train Your Model**: Use real datasets to train YOLOv8
2. **Implement Severity Scoring**: Add XGBoost model training
3. **Create Data Mining Notebooks**: Perform EDA and analysis
4. **Build Frontend**: Adapt OPTI_DASH for road defects
5. **Add Video Processing**: Implement ingestion service
6. **Deploy to Production**: Set up on server/cloud

## 📝 Notes

Use this space to track issues and resolutions:

```
Issue: _______________________
Solution: _____________________
Date: _______________________

Issue: _______________________
Solution: _____________________
Date: _______________________
```

## ✅ Final Verification

- [ ] All checkboxes above are completed
- [ ] System is running smoothly
- [ ] Ready for development/demonstration
- [ ] Documentation is understood

**Date Completed**: ______________
**Completed By**: ______________

---

**Status**: 
- 🟢 Green = All checks passed
- 🟡 Yellow = Some issues, but functional
- 🔴 Red = Major issues, needs troubleshooting
