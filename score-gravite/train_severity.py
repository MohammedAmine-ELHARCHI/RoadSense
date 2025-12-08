"""
RoadSense - Severity Scoring Model Training
Train XGBoost model for road defect severity prediction
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import LabelEncoder
import joblib
import json
from pathlib import Path
from datetime import datetime

# Configuration
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

DEFECT_TYPES = ["D00", "D10", "D20", "D40", "D43", "D44", "D50"]

# Severity mapping based on Japanese road damage classification
SEVERITY_MAPPING = {
    "D00": 6.5,  # Longitudinal crack - Medium severity
    "D10": 7.5,  # Transverse crack - Medium-high severity
    "D20": 8.5,  # Alligator crack - High severity (structural issue)
    "D40": 9.5,  # Pothole - Critical severity (dangerous)
    "D43": 5.0,  # Cross walk blur - Low-medium severity
    "D44": 4.5,  # White line blur - Low severity
    "D50": 7.0,  # Lateral crack - Medium severity
}

def generate_synthetic_training_data(n_samples=5000):
    """
    Generate synthetic training data for severity scoring.
    In production, replace this with real labeled data.
    """
    print(f"🔧 Generating {n_samples} synthetic training samples...")
    
    np.random.seed(42)
    data = []
    
    for _ in range(n_samples):
        defect_type = np.random.choice(DEFECT_TYPES)
        
        # Base severity from defect type
        base_severity = SEVERITY_MAPPING[defect_type]
        
        # Generate features with realistic distributions
        area = np.random.exponential(5000) + 100  # Defect area in pixels
        width = np.sqrt(area) * np.random.uniform(0.8, 1.5)
        height = np.sqrt(area) * np.random.uniform(0.8, 1.5)
        confidence = np.random.beta(8, 2)  # Detection confidence (skewed high)
        
        # Additional features
        aspect_ratio = max(width, height) / (min(width, height) + 1e-6)
        perimeter = 2 * (width + height)
        compactness = (4 * np.pi * area) / (perimeter ** 2 + 1e-6)
        
        # Image context features
        distance_from_center = np.random.uniform(0, 0.5)  # Normalized distance
        lighting_quality = np.random.beta(5, 2)
        blur_score = np.random.beta(6, 3)
        
        # Calculate severity with some noise
        size_factor = np.log1p(area) / 10  # Logarithmic scaling
        confidence_factor = confidence * 2
        aspect_factor = min(aspect_ratio / 5, 1.0)
        
        severity = base_severity + \
                   size_factor * 1.5 + \
                   confidence_factor * 0.5 - \
                   aspect_factor * 0.5 + \
                   np.random.normal(0, 0.5)
        
        # Clip severity to 0-10 range
        severity = np.clip(severity, 0, 10)
        
        data.append({
            'defect_type': defect_type,
            'area': area,
            'width': width,
            'height': height,
            'confidence': confidence,
            'aspect_ratio': aspect_ratio,
            'perimeter': perimeter,
            'compactness': compactness,
            'distance_from_center': distance_from_center,
            'lighting_quality': lighting_quality,
            'blur_score': blur_score,
            'severity_score': severity
        })
    
    df = pd.DataFrame(data)
    print(f"✅ Generated {len(df)} samples")
    print(f"📊 Severity range: {df['severity_score'].min():.2f} - {df['severity_score'].max():.2f}")
    print(f"📊 Mean severity: {df['severity_score'].mean():.2f}")
    
    return df

def prepare_features(df):
    """Prepare features for training"""
    print("\n🔧 Preparing features...")
    
    # Encode categorical features
    le = LabelEncoder()
    df['defect_type_encoded'] = le.fit_transform(df['defect_type'])
    
    # Feature engineering
    df['area_log'] = np.log1p(df['area'])
    df['size_score'] = df['width'] * df['height']
    df['size_score_log'] = np.log1p(df['size_score'])
    
    # Feature columns
    feature_cols = [
        'defect_type_encoded',
        'area', 'area_log',
        'width', 'height',
        'confidence',
        'aspect_ratio',
        'perimeter',
        'compactness',
        'distance_from_center',
        'lighting_quality',
        'blur_score',
        'size_score', 'size_score_log'
    ]
    
    X = df[feature_cols]
    y = df['severity_score']
    
    print(f"✅ Features prepared: {X.shape[1]} features, {X.shape[0]} samples")
    
    return X, y, le, feature_cols

def train_model(X, y, feature_cols):
    """Train XGBoost regression model"""
    print("\n🚀 Training XGBoost model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"📊 Training set: {X_train.shape[0]} samples")
    print(f"📊 Test set: {X_test.shape[0]} samples")
    
    # XGBoost parameters
    params = {
        'objective': 'reg:squarederror',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 200,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'n_jobs': -1
    }
    
    # Train model
    model = xgb.XGBRegressor(**params)
    
    print("⏳ Training in progress...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    
    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Evaluation
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    
    print("\n" + "="*60)
    print("📊 MODEL PERFORMANCE")
    print("="*60)
    print(f"Training RMSE:    {train_rmse:.4f}")
    print(f"Test RMSE:        {test_rmse:.4f}")
    print(f"Training MAE:     {train_mae:.4f}")
    print(f"Test MAE:         {test_mae:.4f}")
    print(f"Training R²:      {train_r2:.4f}")
    print(f"Test R²:          {test_r2:.4f}")
    print("="*60)
    
    # Feature importance
    print("\n📊 TOP 10 FEATURE IMPORTANCE:")
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']:25s}: {row['importance']:.4f}")
    
    return model, {
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'feature_importance': feature_importance.to_dict('records')
    }

def save_model(model, label_encoder, feature_cols, metrics):
    """Save trained model and metadata"""
    print("\n💾 Saving model...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save model
    model_path = MODEL_DIR / f"severity_model_{timestamp}.pkl"
    joblib.dump(model, model_path)
    print(f"✅ Model saved: {model_path}")
    
    # Save best model (symlink/copy)
    best_model_path = MODEL_DIR / "severity_model_best.pkl"
    joblib.dump(model, best_model_path)
    print(f"✅ Best model saved: {best_model_path}")
    
    # Save label encoder
    encoder_path = MODEL_DIR / "label_encoder.pkl"
    joblib.dump(label_encoder, encoder_path)
    print(f"✅ Label encoder saved: {encoder_path}")
    
    # Save metadata
    metadata = {
        'timestamp': timestamp,
        'model_version': '1.0.0',
        'model_type': 'XGBoost Regressor',
        'feature_columns': feature_cols,
        'defect_types': DEFECT_TYPES,
        'severity_mapping': SEVERITY_MAPPING,
        'metrics': metrics,
        'target_range': [0, 10],
        'description': 'Road defect severity scoring model'
    }
    
    metadata_path = MODEL_DIR / "model_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata saved: {metadata_path}")
    
    return model_path, best_model_path

def test_predictions(model, label_encoder):
    """Test model with sample predictions"""
    print("\n🧪 TESTING MODEL PREDICTIONS")
    print("="*60)
    
    # Test cases
    test_cases = [
        {
            'defect_type': 'D40',  # Pothole - should be high severity
            'area': 8000,
            'width': 100,
            'height': 80,
            'confidence': 0.95,
            'description': 'Large pothole'
        },
        {
            'defect_type': 'D20',  # Alligator crack - should be high severity
            'area': 15000,
            'width': 150,
            'height': 100,
            'confidence': 0.88,
            'description': 'Extensive alligator crack'
        },
        {
            'defect_type': 'D44',  # White line blur - should be low severity
            'area': 2000,
            'width': 50,
            'height': 40,
            'confidence': 0.75,
            'description': 'Minor white line blur'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        # Prepare features
        defect_type_encoded = label_encoder.transform([case['defect_type']])[0]
        area = case['area']
        width = case['width']
        height = case['height']
        confidence = case['confidence']
        
        # Derived features
        aspect_ratio = max(width, height) / (min(width, height) + 1e-6)
        perimeter = 2 * (width + height)
        compactness = (4 * np.pi * area) / (perimeter ** 2 + 1e-6)
        area_log = np.log1p(area)
        size_score = width * height
        size_score_log = np.log1p(size_score)
        
        # Default values for additional features
        distance_from_center = 0.3
        lighting_quality = 0.8
        blur_score = 0.7
        
        # Create feature vector
        features = np.array([[
            defect_type_encoded, area, area_log, width, height,
            confidence, aspect_ratio, perimeter, compactness,
            distance_from_center, lighting_quality, blur_score,
            size_score, size_score_log
        ]])
        
        # Predict
        predicted_severity = model.predict(features)[0]
        predicted_severity = np.clip(predicted_severity, 0, 10)
        
        # Determine level
        if predicted_severity < 3.0:
            level = "LOW"
        elif predicted_severity < 6.0:
            level = "MEDIUM"
        elif predicted_severity < 8.5:
            level = "HIGH"
        else:
            level = "CRITICAL"
        
        print(f"\nTest Case {i}: {case['description']}")
        print(f"  Type: {case['defect_type']}")
        print(f"  Area: {area:.0f}px, Confidence: {confidence:.2f}")
        print(f"  ➡️  Predicted Severity: {predicted_severity:.2f}/10 [{level}]")
    
    print("\n" + "="*60)

def main():
    """Main training pipeline"""
    print("\n" + "="*60)
    print("🎯 ROADSENSE SEVERITY SCORING - MODEL TRAINING")
    print("="*60)
    
    # Generate training data
    df = generate_synthetic_training_data(n_samples=5000)
    
    # Prepare features
    X, y, label_encoder, feature_cols = prepare_features(df)
    
    # Train model
    model, metrics = train_model(X, y, feature_cols)
    
    # Save model
    model_path, best_model_path = save_model(model, label_encoder, feature_cols, metrics)
    
    # Test predictions
    test_predictions(model, label_encoder)
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE!")
    print("="*60)
    print(f"📦 Model saved to: {best_model_path}")
    print(f"📊 Test RMSE: {metrics['test_rmse']:.4f}")
    print(f"📊 Test MAE: {metrics['test_mae']:.4f}")
    print(f"📊 Test R²: {metrics['test_r2']:.4f}")
    print("\n🚀 You can now use this model in the severity service!")
    print("="*60)

if __name__ == "__main__":
    main()
