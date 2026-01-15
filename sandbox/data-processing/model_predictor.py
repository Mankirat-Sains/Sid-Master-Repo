"""Phase 5: Prediction"""
import pandas as pd
import numpy as np
from config import PREDICTION_THRESHOLD
from model_trainer import load_model, get_feature_columns

def predict_files(df: pd.DataFrame, model_name: str, threshold: float = PREDICTION_THRESHOLD) -> pd.DataFrame:
    """
    Predict labels for all files using trained model
    Returns DataFrame with predictions
    """
    model_info = load_model(model_name)
    model = model_info['model']
    feature_cols = model_info['feature_columns']
    
    # Ensure all feature columns exist
    missing_cols = set(feature_cols) - set(df.columns)
    if missing_cols:
        for col in missing_cols:
            df[col] = 0
    
    X = df[feature_cols].fillna(0)
    
    # Get probabilities
    probabilities = model.predict_proba(X)[:, 1]  # Probability of class 1
    
    # Binary predictions
    predictions = (probabilities >= threshold).astype(int)
    
    # Add to dataframe
    df_result = df.copy()
    df_result['predicted_label'] = predictions
    df_result['confidence_score'] = probabilities
    
    # selected_for_processing = predicted_label == 1
    df_result['selected_for_processing'] = (predictions == 1)
    
    return df_result

def get_prediction_summary(df: pd.DataFrame) -> dict:
    """Get summary statistics of predictions"""
    total = len(df)
    selected = df['selected_for_processing'].sum() if 'selected_for_processing' in df.columns else 0
    avg_confidence = df['confidence_score'].mean() if 'confidence_score' in df.columns else 0
    
    return {
        'total_files': total,
        'selected_files': int(selected),
        'skipped_files': int(total - selected),
        'average_confidence': float(avg_confidence)
    }

