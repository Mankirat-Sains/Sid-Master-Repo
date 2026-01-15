"""Phase 2: Strategic Case Selection"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import List, Optional, Dict
from config import N_STRATEGIC_CASES, SELECTION_BATCH_SIZE

def select_strategic_cases(df: pd.DataFrame, n_cases: int = N_STRATEGIC_CASES, 
                          selected_subfolders: Optional[List[str]] = None) -> List[int]:
    """
    Select diverse, informative cases for user labeling
    Uses clustering, outlier detection, and representative sampling
    Ensures only one file per parent_subfolder (one file per first-level subfolder)
    
    Args:
        df: DataFrame with file features (must have 'parent_subfolder' column)
        n_cases: Number of cases to select
        selected_subfolders: List of parent_subfolder paths to prioritize for outlier detection
    """
    if 'parent_subfolder' not in df.columns:
        raise ValueError("DataFrame must have 'parent_subfolder' column")
    
    if len(df) <= n_cases:
        # If we have fewer or equal files than n_cases, select one per parent_subfolder
        selected_indices = []
        selected_subfolders_set = set()
        for idx in df.index:
            parent_subfolder = df.loc[idx, 'parent_subfolder']
            if parent_subfolder not in selected_subfolders_set:
                selected_indices.append(idx)
                selected_subfolders_set.add(parent_subfolder)
                if len(selected_indices) >= n_cases:
                    break
        return selected_indices[:n_cases]
    
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
    selected_parent_subfolders = set()  # Track which parent subfolders we've already selected from
    
    # Strategy 1: Diversity sampling (60%) - ONE FILE PER PARENT SUBFOLDER
    n_diversity = int(n_cases * 0.6)
    if n_diversity > 0 and len(df) >= n_diversity:
        try:
            # Filter out parent subfolders we've already selected from
            available_df = df[~df['parent_subfolder'].isin(selected_parent_subfolders)].copy()
            if len(available_df) == 0:
                available_df = df.copy()
            
            n_clusters = min(n_diversity, len(available_df))
            if n_clusters > 0:
                available_X = available_df[available_features].fillna(0).values
                available_X_scaled = scaler.transform(available_X)
                
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(available_X_scaled)
                
                # Group indices by cluster and parent_subfolder
                cluster_parent_subfolders = {}
                for idx_pos, cluster_id in enumerate(clusters):
                    file_idx = available_df.index[idx_pos]
                    parent_subfolder = df.loc[file_idx, 'parent_subfolder']
                    
                    if cluster_id not in cluster_parent_subfolders:
                        cluster_parent_subfolders[cluster_id] = {}
                    if parent_subfolder not in cluster_parent_subfolders[cluster_id]:
                        cluster_parent_subfolders[cluster_id][parent_subfolder] = []
                    cluster_parent_subfolders[cluster_id][parent_subfolder].append(file_idx)
                
                # Select ONE file per parent_subfolder from each cluster
                for cluster_id, parent_subfolders_dict in cluster_parent_subfolders.items():
                    if len(selected_indices) >= n_diversity:
                        break
                    for parent_subfolder, indices in parent_subfolders_dict.items():
                        if parent_subfolder not in selected_parent_subfolders and len(selected_indices) < n_diversity:
                            # Select file closest to centroid in this parent_subfolder
                            centroid = kmeans.cluster_centers_[cluster_id]
                            distances = [np.linalg.norm(available_X_scaled[available_df.index.get_loc(idx)] - centroid) 
                                        for idx in indices]
                            closest_idx = indices[np.argmin(distances)]
                            selected_indices.append(closest_idx)
                            selected_parent_subfolders.add(parent_subfolder)
        except Exception as e:
            print(f"Clustering failed: {e}, using random sampling")
    
    # Strategy 2: Outlier detection (25%) - WITH SUBFOLDER SELECTION
    n_outliers = int(n_cases * 0.25)
    if n_outliers > 0:
        # Filter for outlier detection based on selected_subfolders
        if selected_subfolders and len(selected_subfolders) > 0:
            # Only look for outliers in selected parent subfolders
            outlier_df = df[df['parent_subfolder'].isin(selected_subfolders)].copy()
        else:
            # Use all parent subfolders if no specific selection
            outlier_df = df.copy()
        
        # Exclude parent subfolders we've already selected from
        outlier_df = outlier_df[~outlier_df['parent_subfolder'].isin(selected_parent_subfolders)].copy()
        
        if 'size_zscore' in outlier_df.columns and len(outlier_df) > 0:
            size_outliers = outlier_df[abs(outlier_df['size_zscore']) > 2].index.tolist()
            
            # Group by parent_subfolder and select one per parent_subfolder
            parent_subfolder_outliers = {}
            for idx in size_outliers:
                parent_subfolder = df.loc[idx, 'parent_subfolder']
                if parent_subfolder not in selected_parent_subfolders:
                    if parent_subfolder not in parent_subfolder_outliers:
                        parent_subfolder_outliers[parent_subfolder] = []
                    parent_subfolder_outliers[parent_subfolder].append(idx)
            
            # Select one outlier per parent_subfolder
            for parent_subfolder, indices in parent_subfolder_outliers.items():
                if len(selected_indices) >= n_cases:
                    break
                # Select the most extreme outlier (highest absolute zscore)
                best_idx = max(indices, key=lambda x: abs(outlier_df.loc[x, 'size_zscore']))
                selected_indices.append(best_idx)
                selected_parent_subfolders.add(parent_subfolder)
                if len(selected_indices) >= n_cases:
                    break
    
    # Strategy 3: Representative sampling (15%) - ONE FILE PER PARENT SUBFOLDER
    n_representative = n_cases - len(selected_indices)
    if n_representative > 0:
        # Get remaining files from parent subfolders we haven't selected from
        remaining_df = df[~df['parent_subfolder'].isin(selected_parent_subfolders)].copy()
        
        if len(remaining_df) > 0:
            # Group by parent_subfolder and select one per parent_subfolder
            parent_subfolders_list = remaining_df['parent_subfolder'].unique().tolist()
            
            # Prioritize parent subfolders if selected_subfolders were specified (re-ranking)
            if selected_subfolders and len(selected_subfolders) > 0:
                # Re-rank: prioritize parent subfolders in selected_subfolders first
                priority_subfolders = [f for f in parent_subfolders_list if f in selected_subfolders]
                other_subfolders = [f for f in parent_subfolders_list if f not in selected_subfolders]
                parent_subfolders_list = priority_subfolders + other_subfolders
            
            # Select one file per parent_subfolder
            for parent_subfolder in parent_subfolders_list[:n_representative]:
                if len(selected_indices) >= n_cases:
                    break
                subfolder_files = remaining_df[remaining_df['parent_subfolder'] == parent_subfolder]
                # Select file with highest priority (largest size)
                if len(subfolder_files) > 0:
                    best_file = subfolder_files.nlargest(1, 'file_size').index[0]
                    selected_indices.append(best_file)
                    selected_parent_subfolders.add(parent_subfolder)
    
    # Ensure we have exactly n_cases
    if len(selected_indices) < n_cases:
        remaining_df = df[~df['parent_subfolder'].isin(selected_parent_subfolders)].copy()
        if len(remaining_df) > 0:
            # Get one file per remaining parent_subfolder
            parent_subfolders_list = remaining_df['parent_subfolder'].unique().tolist()
            # Re-rank if selected_subfolders were specified
            if selected_subfolders and len(selected_subfolders) > 0:
                priority_subfolders = [f for f in parent_subfolders_list if f in selected_subfolders]
                other_subfolders = [f for f in parent_subfolders_list if f not in selected_subfolders]
                parent_subfolders_list = priority_subfolders + other_subfolders
            
            for parent_subfolder in parent_subfolders_list[:n_cases - len(selected_indices)]:
                if len(selected_indices) >= n_cases:
                    break
                subfolder_files = remaining_df[remaining_df['parent_subfolder'] == parent_subfolder]
                if len(subfolder_files) > 0:
                    best_file = subfolder_files.nlargest(1, 'file_size').index[0]
                    selected_indices.append(best_file)
                    selected_parent_subfolders.add(parent_subfolder)
    
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

def select_next_batch_adaptively(df: pd.DataFrame, existing_labels: Dict[int, int], 
                                 already_selected_indices: List[int], 
                                 batch_size: int = SELECTION_BATCH_SIZE,
                                 selected_subfolders: Optional[List[str]] = None) -> List[int]:
    """
    Select next batch of cases adaptively based on existing labels
    Avoids cases similar to rejected ones, ensures diversity
    
    Args:
        df: DataFrame with file features (must have 'parent_subfolder' column)
        existing_labels: Dict of {index: label} for already labeled cases
        already_selected_indices: List of indices already selected (to exclude)
        batch_size: Number of cases to select in this batch
        selected_subfolders: List of parent_subfolder paths to prioritize
    """
    if 'parent_subfolder' not in df.columns:
        raise ValueError("DataFrame must have 'parent_subfolder' column")
    
    # Get feature columns for similarity calculation
    feature_cols = [
        'file_size', 'depth', 'size_vs_folder_mean', 'size_zscore',
        'days_from_newest', 'is_newest_in_folder', 'folder_file_count'
    ]
    keyword_cols = [col for col in df.columns if col.startswith('folder_has_') or col.startswith('path_has_')]
    feature_cols.extend(keyword_cols[:5])
    available_features = [col for col in feature_cols if col in df.columns]
    
    if len(available_features) < 3:
        available_features = ['file_size', 'depth', 'folder_file_count']
        available_features = [col for col in available_features if col in df.columns]
    
    # Filter out already selected files and their parent_subfolders
    already_selected_set = set(already_selected_indices)
    already_selected_parent_subfolders = set(df.loc[already_selected_indices, 'parent_subfolder'].unique()) if already_selected_indices else set()
    
    available_df = df[~df.index.isin(already_selected_set)].copy()
    available_df = available_df[~available_df['parent_subfolder'].isin(already_selected_parent_subfolders)].copy()
    
    if len(available_df) == 0:
        return []
    
    # Prepare feature matrix
    X_available = available_df[available_features].fillna(0).values
    scaler = StandardScaler()
    X_available_scaled = scaler.fit_transform(X_available)
    
    # Calculate similarity scores - penalize similarity to rejected cases
    rejected_indices = [idx for idx, label in existing_labels.items() if label == 0]
    
    if len(rejected_indices) > 0 and len(X_available_scaled) > 0:
        rejected_df = df.loc[rejected_indices]
        X_rejected = rejected_df[available_features].fillna(0).values
        X_rejected_scaled = scaler.transform(X_rejected)
        
        # Calculate minimum distance to rejected cases (higher distance = better)
        # Use numpy for euclidean distance
        distances = np.sqrt(((X_available_scaled[:, np.newaxis, :] - X_rejected_scaled[np.newaxis, :, :]) ** 2).sum(axis=2))
        min_distances_to_rejected = distances.min(axis=1)
        
        # Use distance as a score (higher distance from rejected = higher score)
        similarity_scores = min_distances_to_rejected
    else:
        # If no rejected cases, use uniform scores
        similarity_scores = np.ones(len(available_df))
    
    # Get unique parent_subfolders and select one file per subfolder
    selected_indices = []
    selected_parent_subfolders_set = set()
    
    # Group by parent_subfolder and select best from each
    parent_subfolders = available_df['parent_subfolder'].unique()
    
    # Prioritize selected_subfolders if specified
    if selected_subfolders and len(selected_subfolders) > 0:
        priority_subfolders = [f for f in parent_subfolders if f in selected_subfolders]
        other_subfolders = [f for f in parent_subfolders if f not in selected_subfolders]
        parent_subfolders = list(priority_subfolders) + list(other_subfolders)
    
    # Select one file per parent_subfolder, prioritizing those with higher similarity scores (farther from rejected)
    for parent_subfolder in parent_subfolders:
        if len(selected_indices) >= batch_size:
            break
        
        subfolder_files = available_df[available_df['parent_subfolder'] == parent_subfolder]
        if len(subfolder_files) == 0:
            continue
        
        # Get positions in available_df for scoring
        subfolder_positions = [available_df.index.get_loc(idx) for idx in subfolder_files.index]
        subfolder_scores = similarity_scores[subfolder_positions]
        
        # Select file with highest score (farthest from rejected, or largest if no rejected cases)
        if len(rejected_indices) > 0:
            best_position = subfolder_positions[np.argmax(subfolder_scores)]
            selected_idx = available_df.index[best_position]
        else:
            # If no rejected cases, select largest file
            selected_idx = subfolder_files.nlargest(1, 'file_size').index[0]
        selected_indices.append(selected_idx)
        selected_parent_subfolders_set.add(parent_subfolder)
    
    return selected_indices[:batch_size]

