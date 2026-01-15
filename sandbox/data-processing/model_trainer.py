"""Phase 4 & 7: XGBoost Model Training"""
import pandas as pd
import xgboost as xgb
from pathlib import Path
import pickle
import json
from datetime import datetime
from config import MODELS_DIR, MODEL_FILE_PREFIX

def get_feature_columns(df: pd.DataFrame) -> list:
    """Get columns to use as features (exclude metadata and labels)"""
    exclude_cols = {
        'file_path', 'file_name', 'folder_path', 'folder_name', 
        'relative_path', 'path_tokens', 'date_modified', 'date_created',
        'folder_date_min', 'folder_date_max', 'label', 'predicted_label',
        'confidence_score', 'selected_for_processing', 'file_extension'
    }
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Filter to only numeric/boolean columns (XGBoost can't handle object/string columns)
    numeric_cols = []
    for col in feature_cols:
        dtype = df[col].dtype
        if dtype in ['int64', 'int32', 'float64', 'float32', 'bool']:
            numeric_cols.append(col)
        elif dtype.name == 'object':
            # Skip string columns
            continue
    
    return numeric_cols

def train_model(df: pd.DataFrame, model_name: str = None) -> dict:
    """
    Train XGBoost classifier on labeled data
    Returns model info dictionary
    """
    if 'label' not in df.columns:
        raise ValueError("DataFrame must have 'label' column")
    
    labeled_df = df[df['label'].notna()].copy()
    if len(labeled_df) < 2:
        raise ValueError(f"Need at least 2 labeled examples, got {len(labeled_df)}")
    
    feature_cols = get_feature_columns(labeled_df)
    if len(feature_cols) == 0:
        raise ValueError("No numeric features found after filtering")
    
    X = labeled_df[feature_cols].fillna(0)
    y = labeled_df['label'].astype(int)
    
    # Train model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X, y)
    
    # Get feature importance
    feature_importance = dict(zip(feature_cols, model.feature_importances_))
    feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
    
    # Save model
    if model_name is None:
        model_name = f"{MODEL_FILE_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    model_path = MODELS_DIR / f"{model_name}.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Save model metadata
    metadata = {
        'model_name': model_name,
        'model_path': str(model_path),
        'training_date': datetime.now().isoformat(),
        'n_samples': len(labeled_df),
        'n_features': len(feature_cols),
        'feature_columns': feature_cols,
        'feature_importance': {k: float(v) for k, v in feature_importance.items()},
        'accuracy': float((model.predict(X) == y).mean())
    }
    
    metadata_path = MODELS_DIR / f"{model_name}_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return {
        'model': model,
        'model_path': model_path,
        'metadata': metadata,
        'feature_columns': feature_cols
    }

def load_model(model_name: str) -> dict:
    """Load trained model"""
    model_path = MODELS_DIR / f"{model_name}.pkl"
    metadata_path = MODELS_DIR / f"{model_name}_metadata.json"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    
    return {
        'model': model,
        'metadata': metadata,
        'feature_columns': metadata.get('feature_columns', [])
    }

