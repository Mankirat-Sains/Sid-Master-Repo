"""Phase 1: Feature Extraction"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import re
from tqdm import tqdm
from config import VALID_EXTENSIONS

def extract_file_metadata(root_folder: str) -> pd.DataFrame:
    """
    Extract metadata for all files in root folder
    Returns DataFrame with file features
    """
    root_path = Path(root_folder)
    files_data = []
    
    # Get all files recursively
    all_files = []
    for ext in VALID_EXTENSIONS:
        all_files.extend(root_path.rglob(f"*{ext}"))
    
    print(f"Found {len(all_files)} files to process...")
    
    for file_path in tqdm(all_files, desc="Extracting metadata"):
        try:
            stat = file_path.stat()
            
            # Basic file info
            file_data = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_extension': file_path.suffix.lower(),
                'file_size': stat.st_size,
                'date_modified': datetime.fromtimestamp(stat.st_mtime),
                'date_created': datetime.fromtimestamp(stat.st_ctime),
                'folder_path': str(file_path.parent),
                'folder_name': file_path.parent.name,
                'depth': len(file_path.parts) - len(root_path.parts),
                'relative_path': str(file_path.relative_to(root_path)),
            }
            
            # Extract folder structure
            parts = file_path.relative_to(root_path).parts
            file_data['path_tokens'] = '|'.join(parts[:-1])  # All folder names
            
            # File name patterns
            name_lower = file_path.stem.lower()
            file_data['has_numbers'] = bool(re.search(r'\d', name_lower))
            file_data['has_letters'] = bool(re.search(r'[a-z]', name_lower))
            file_data['name_length'] = len(file_path.stem)
            
            files_data.append(file_data)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    df = pd.DataFrame(files_data)
    
    if df.empty:
        return df
    
    # Compute relative features
    df = compute_relative_features(df)
    
    return df

def compute_relative_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute relative features (size/date comparisons with siblings)
    """
    # Group by folder
    df['size_rank_in_folder'] = df.groupby('folder_path')['file_size'].rank(method='min', ascending=False)
    df['date_rank_in_folder'] = df.groupby('folder_path')['date_modified'].rank(method='min', ascending=False)
    
    # Compute folder statistics
    folder_stats = df.groupby('folder_path').agg({
        'file_size': ['mean', 'median', 'std', 'count'],
        'date_modified': ['min', 'max']
    }).reset_index()
    
    folder_stats.columns = ['folder_path', 'folder_size_mean', 'folder_size_median', 
                           'folder_size_std', 'folder_file_count', 'folder_date_min', 'folder_date_max']
    
    df = df.merge(folder_stats, on='folder_path', how='left')
    
    # Relative size features
    df['size_vs_folder_mean'] = df['file_size'] / (df['folder_size_mean'] + 1)
    df['size_vs_folder_median'] = df['file_size'] / (df['folder_size_median'] + 1)
    df['size_percentile'] = df.groupby('folder_path')['file_size'].transform(
        lambda x: pd.qcut(x.rank(method='first'), q=4, labels=[1, 2, 3, 4], duplicates='drop')
    ).astype(float)
    
    # Relative date features
    df['is_newest_in_folder'] = (df['date_rank_in_folder'] == 1).astype(int)
    df['is_oldest_in_folder'] = (df.groupby('folder_path')['date_modified'].transform('min') == df['date_modified']).astype(int)
    
    # Days since folder max date (0 if this is the newest)
    df['days_from_newest'] = (df['folder_date_max'] - df['date_modified']).dt.total_seconds() / 86400
    
    # Size anomaly detection
    df['size_zscore'] = (df['file_size'] - df['folder_size_mean']) / (df['folder_size_std'] + 1)
    df['is_size_outlier'] = (abs(df['size_zscore']) > 2).astype(int)
    
    # Folder keyword detection
    keywords = ['drawing', 'drawings', 'pdf', 'pdfs', 'project', 'projects', 'plan', 'plans']
    for keyword in keywords:
        df[f'folder_has_{keyword}'] = df['folder_name'].str.lower().str.contains(keyword, na=False).astype(int)
        df[f'path_has_{keyword}'] = df['path_tokens'].str.lower().str.contains(keyword, na=False).astype(int)
    
    return df

def save_features(df: pd.DataFrame, output_path: str):
    """Save extracted features to CSV"""
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} files to {output_path}")

def load_features(features_path: str) -> pd.DataFrame:
    """Load features from CSV"""
    df = pd.read_csv(features_path)
    df['date_modified'] = pd.to_datetime(df['date_modified'])
    df['date_created'] = pd.to_datetime(df['date_created'])
    if 'folder_date_min' in df.columns:
        df['folder_date_min'] = pd.to_datetime(df['folder_date_min'])
        df['folder_date_max'] = pd.to_datetime(df['folder_date_max'])
    return df

