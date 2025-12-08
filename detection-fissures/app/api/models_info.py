from fastapi import APIRouter, HTTPException
from app.models.detector import detector
from app.schemas import ModelInfo

router = APIRouter()

@router.get("/info", response_model=ModelInfo)
async def get_model_info():
    """
    Get information about the detection models
    
    Returns model type, version, classes, and performance metrics
    """
    try:
        info = detector.get_model_info()
        
        return ModelInfo(
            model_type=info["model_type"],
            version=info["version"],
            classes=info["classes"],
            input_size=info["input_size"],
            performance_metrics={
                "device": info["device"],
                "model_loaded": info["model_loaded"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model info: {str(e)}")

@router.get("/health")
async def models_health():
    """
    Check if models are loaded and ready
    """
    return {
        "models_loaded": detector.model_loaded,
        "device": str(detector.device) if detector.device else "unknown",
        "model_version": detector.model_version
    }

@router.post("/retrain")
async def trigger_retraining():
    """
    Trigger model retraining (placeholder)
    
    In production, this would trigger a background job to retrain the model
    """
    return {
        "message": "Model retraining triggered",
        "status": "pending",
        "note": "This is a placeholder endpoint. Implement actual retraining logic."
    }
