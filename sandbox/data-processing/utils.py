"""Utility functions"""
import pandas as pd
from pathlib import Path
from config import FEATURES_DIR, LABELS_DIR, PREDICTIONS_DIR
from datetime import datetime

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def format_date(date_val) -> str:
    """Format date for display"""
    if pd.isna(date_val):
        return "N/A"
    if isinstance(date_val, str):
        date_val = pd.to_datetime(date_val)
    return date_val.strftime("%Y-%m-%d %H:%M")

def save_predictions(df: pd.DataFrame, root_folder_name: str):
    """Save predictions to CSV"""
    output_path = PREDICTIONS_DIR / f"predictions_{root_folder_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(output_path, index=False)
    return output_path

def load_predictions(prediction_file: str) -> pd.DataFrame:
    """Load predictions from CSV"""
    df = pd.read_csv(prediction_file)
    # Convert date columns
    date_cols = ['date_modified', 'date_created', 'folder_date_min', 'folder_date_max']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

