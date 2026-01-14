"""Phase 2: Strategic Case Selection"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import List
from config import N_STRATEGIC_CASES

def select_strategic_cases(df: pd.DataFrame, n_cases: int = N_STRATEGIC_CASES) -> List[int]:
    """
    Select diverse, informative cases for user labeling
    Uses clustering, outlier detection, and representative sampling
    """
    if len(df) <= n_cases:
        return list(df.index)
    
    # Select feature columns for clustering
    feature_cols = [
        'file_size', 'depth', 'size_vs_folder_mean', 'size_zscore',
        'days_from_newest', 'is_newest_in_folder', 'folder_file_count'
    ]
    
    # Add keyword features
    keyword_cols = [col for col in df.columns if col.startswith('folder_has_') or col.startswith('path_has_')]
    feature_cols.extend(keyword_cols[:5])  # Limit to avoid too many features
    
    # Get available features
    available_features = [col for col in feature_cols if col in df.columns]
    
    if len(available_features) < 3:
        # Fallback: use basic features
        available_features = ['file_size', 'depth', 'folder_file_count']
        available_features = [col for col in available_features if col in df.columns]
    
    # Prepare feature matrix
    X = df[available_features].fillna(0).values
    
    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    selected_indices = []
    
    # Strategy 1: Diversity sampling (60%)
    n_diversity = int(n_cases * 0.6)
    if n_diversity > 0 and len(df) >= n_diversity:
        try:
            n_clusters = min(n_diversity, len(df))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            
            # Select 1-2 files per cluster
            cluster_indices = {}
            for idx, cluster_id in enumerate(clusters):
                if cluster_id not in cluster_indices:
                    cluster_indices[cluster_id] = []
                cluster_indices[cluster_id].append(df.index[idx])
            
            for cluster_id, indices in cluster_indices.items():
                if len(selected_indices) < n_diversity:
                    # Select file closest to centroid
                    centroid = kmeans.cluster_centers_[cluster_id]
                    distances = [np.linalg.norm(X_scaled[df.index.get_loc(idx)] - centroid) 
                                for idx in indices]
                    closest_idx = indices[np.argmin(distances)]
                    selected_indices.append(closest_idx)
        except Exception as e:
            print(f"Clustering failed: {e}, using random sampling")
    
    # Strategy 2: Outlier detection (25%)
    n_outliers = int(n_cases * 0.25)
    if n_outliers > 0:
        # Size outliers
        if 'size_zscore' in df.columns:
            size_outliers = df[abs(df['size_zscore']) > 2].index.tolist()
            for idx in size_outliers[:n_outliers]:
                if idx not in selected_indices:
                    selected_indices.append(idx)
                    if len(selected_indices) >= n_cases:
                        break
    
    # Strategy 3: Representative sampling (15%)
    n_representative = n_cases - len(selected_indices)
    if n_representative > 0:
        # Select diverse files by size and date
        remaining_indices = [idx for idx in df.index if idx not in selected_indices]
        if len(remaining_indices) > n_representative:
            # Sample from different size ranges
            remaining_df = df.loc[remaining_indices]
            try:
                size_bins = pd.qcut(remaining_df['file_size'], q=min(4, n_representative), 
                                   labels=False, duplicates='drop')
                for bin_id in range(int(size_bins.max() + 1)):
                    bin_indices = [remaining_indices[i] for i in range(len(remaining_indices)) if size_bins.iloc[i] == bin_id]
                    if len(bin_indices) > 0:
                        selected_idx = np.random.choice(bin_indices)
                        selected_indices.append(selected_idx)
                        if len(selected_indices) >= n_cases:
                            break
            except:
                # If binning fails, just random sample
                selected_indices.extend(np.random.choice(remaining_indices, size=min(n_representative, len(remaining_indices)), replace=False).tolist())
        else:
            selected_indices.extend(remaining_indices[:n_representative])
    
    # Ensure we have exactly n_cases
    if len(selected_indices) < n_cases:
        remaining = [idx for idx in df.index if idx not in selected_indices]
        selected_indices.extend(remaining[:n_cases - len(selected_indices)])
    
    return selected_indices[:n_cases]

def get_case_selection_reason(df: pd.DataFrame, idx: int) -> str:
    """Generate explanation for why this case was selected"""
    row = df.loc[idx]
    reasons = []
    
    if row.get('is_newest_in_folder', 0) == 1:
        reasons.append("Newest file in folder")
    if row.get('is_size_outlier', 0) == 1:
        reasons.append("Size outlier (unusual size)")
    if row.get('size_rank_in_folder', 0) == 1:
        reasons.append("Largest file in folder")
    
    # Check keywords
    keyword_cols = [col for col in df.columns if col.startswith('folder_has_') or col.startswith('path_has_')]
    keywords_found = [col.replace('folder_has_', '').replace('path_has_', '') 
                     for col in keyword_cols if row.get(col, 0) == 1]
    if keywords_found:
        reasons.append(f"Contains keywords: {', '.join(keywords_found[:2])}")
    
    return "; ".join(reasons) if reasons else "Representative case"

