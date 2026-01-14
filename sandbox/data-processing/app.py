"""Main Streamlit App for Intelligent File Selection"""
import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

# Import modules
from feature_extractor import extract_file_metadata, save_features, load_features
from case_selector import select_strategic_cases, get_case_selection_reason
from model_trainer import train_model, load_model
from model_predictor import predict_files, get_prediction_summary
from utils import format_file_size, format_date, save_predictions, load_predictions
from config import FEATURES_DIR, LABELS_DIR, MODELS_DIR, PREDICTIONS_DIR, N_STRATEGIC_CASES

# Page config
st.set_page_config(
    page_title="Intelligent File Selection",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = {
        'root_folder': None,
        'features_extracted': False,
        'features_df': None,
        'strategic_cases_selected': False,
        'strategic_indices': None,
        'labels': {},
        'model_trained': False,
        'model_name': None,
        'predictions_made': False,
        'predictions_df': None,
        'verification_complete': False,
        'features_path': None
    }

def main():
    st.title("📁 Intelligent File Selection System")
    st.markdown("AI-powered document selection for RAG system processing")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["1. Setup & Extract Features", "2. Label Strategic Cases", 
         "3. Train Model", "4. Verify Predictions", "5. View Processed Files"]
    )
    
    if page == "1. Setup & Extract Features":
        page_extract_features()
    elif page == "2. Label Strategic Cases":
        page_label_cases()
    elif page == "3. Train Model":
        page_train_model()
    elif page == "4. Verify Predictions":
        page_verify_predictions()
    elif page == "5. View Processed Files":
        page_view_processed()

def page_extract_features():
    st.header("Phase 1: Extract Features")
    st.markdown("Scan folder structure and extract file metadata")
    
    # Root folder input
    root_folder = st.text_input(
        "Root Folder Path",
        value=st.session_state.workflow_state.get('root_folder', ''),
        help="Enter the root folder path to scan"
    )
    
    if st.button("Extract Features", type="primary"):
        if not root_folder or not Path(root_folder).exists():
            st.error("Please enter a valid folder path")
            return
        
        st.session_state.workflow_state['root_folder'] = root_folder
        
        with st.spinner("Extracting features from files..."):
            try:
                df = extract_file_metadata(root_folder)
                
                if df.empty:
                    st.error("No files found in the specified folder")
                    return
                
                # Save features
                folder_name = Path(root_folder).name or "root"
                features_path = FEATURES_DIR / f"features_{folder_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                save_features(df, str(features_path))
                
                st.session_state.workflow_state['features_df'] = df
                st.session_state.workflow_state['features_extracted'] = True
                st.session_state.workflow_state['features_path'] = str(features_path)
                
                st.success(f"✅ Extracted features for {len(df)} files!")
                st.info(f"Features saved to: {features_path}")
                
                # Show summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Files", len(df))
                with col2:
                    st.metric("Total Size", format_file_size(df['file_size'].sum()))
                with col3:
                    st.metric("Unique Folders", df['folder_path'].nunique())
                
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    # Display features if available
    if st.session_state.workflow_state.get('features_extracted'):
        df = st.session_state.workflow_state['features_df']
        st.subheader("Extracted Features Preview")
        st.dataframe(df.head(10), use_container_width=True)

def page_label_cases():
    st.header("Phase 2 & 3: Label Strategic Cases")
    st.markdown("Review and label diverse cases for training")
    
    if not st.session_state.workflow_state.get('features_extracted'):
        st.warning("Please extract features first (Page 1)")
        return
    
    df = st.session_state.workflow_state['features_df'].copy()
    
    # Select strategic cases if not already done
    if not st.session_state.workflow_state.get('strategic_cases_selected'):
        if st.button("Select Strategic Cases", type="primary"):
            with st.spinner("Selecting diverse cases..."):
                indices = select_strategic_cases(df, n_cases=N_STRATEGIC_CASES)
                st.session_state.workflow_state['strategic_indices'] = indices
                st.session_state.workflow_state['strategic_cases_selected'] = True
                st.session_state.workflow_state['labels'] = {}
                st.session_state['current_case_idx'] = 0
                st.success(f"✅ Selected {len(indices)} strategic cases!")
                st.rerun()
    
    if st.session_state.workflow_state.get('strategic_cases_selected'):
        indices = st.session_state.workflow_state['strategic_indices']
        labels = st.session_state.workflow_state['labels']
        
        st.subheader(f"Label Cases ({len(labels)}/{len(indices)} labeled)")
        
        # Get current case index
        case_idx = st.session_state.get('current_case_idx', 0)
        if case_idx >= len(indices):
            case_idx = 0
        
        file_idx = indices[case_idx]
        row = df.loc[file_idx]
        
        # Display case info
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Case {case_idx + 1}/{len(indices)}**")
            st.markdown(f"**File:** `{row['file_name']}`")
            st.markdown(f"**Path:** `{row['relative_path']}`")
            st.markdown(f"**Size:** {format_file_size(row['file_size'])}")
            st.markdown(f"**Modified:** {format_date(row['date_modified'])}")
            st.markdown(f"**Folder:** `{row['folder_name']}`")
        
        with col2:
            st.markdown("**Context:**")
            st.info(get_case_selection_reason(df, file_idx))
            
            if 'folder_file_count' in row:
                st.metric("Files in Folder", int(row['folder_file_count']))
            if 'is_newest_in_folder' in row and row['is_newest_in_folder'] == 1:
                st.success("⭐ Newest in folder")
            if 'is_size_outlier' in row and row['is_size_outlier'] == 1:
                st.warning("⚠️ Size outlier")
        
        # Label buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ Process", type="primary", use_container_width=True):
                labels[file_idx] = 1
                st.session_state.workflow_state['labels'] = labels
                if case_idx < len(indices) - 1:
                    st.session_state['current_case_idx'] = case_idx + 1
                st.rerun()
        with col2:
            if st.button("❌ Skip", use_container_width=True):
                labels[file_idx] = 0
                st.session_state.workflow_state['labels'] = labels
                if case_idx < len(indices) - 1:
                    st.session_state['current_case_idx'] = case_idx + 1
                st.rerun()
        
        # Navigation
        if case_idx > 0:
            if st.button("← Previous"):
                st.session_state['current_case_idx'] = case_idx - 1
                st.rerun()
        
        # Progress and save
        progress = len(labels) / len(indices)
        st.progress(progress)
        st.caption(f"Progress: {len(labels)}/{len(indices)} cases labeled")
        
        if len(labels) == len(indices):
            st.success("🎉 All cases labeled! Proceed to Model Training (Page 3)")

def page_train_model():
    st.header("Phase 4: Train Model")
    st.markdown("Train XGBoost model on labeled data")
    
    if not st.session_state.workflow_state.get('strategic_cases_selected'):
        st.warning("Please label strategic cases first (Page 2)")
        return
    
    df = st.session_state.workflow_state['features_df'].copy()
    labels = st.session_state.workflow_state['labels']
    
    if len(labels) < 2:
        st.warning(f"Need at least 2 labeled examples, got {len(labels)}")
        return
    
    # Add labels to dataframe
    df['label'] = df.index.map(labels)
    
    labeled_df = df[df['label'].notna()]
    
    st.subheader("Labeled Data Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Labeled", len(labeled_df))
        st.metric("Selected (1)", (labeled_df['label'] == 1).sum())
    with col2:
        st.metric("Skipped (0)", (labeled_df['label'] == 0).sum())
    
    if st.button("Train Model", type="primary"):
        with st.spinner("Training XGBoost model..."):
            try:
                model_info = train_model(df)
                
                st.session_state.workflow_state['model_trained'] = True
                st.session_state.workflow_state['model_name'] = model_info['metadata']['model_name']
                
                st.success("✅ Model trained successfully!")
                st.info(f"Model saved as: {model_info['metadata']['model_name']}")
                
                # Show feature importance
                st.subheader("Top Feature Importance")
                importance = model_info['metadata']['feature_importance']
                top_features = list(importance.items())[:10]
                max_importance = max(importance.values()) if importance.values() else 1
                if max_importance > 0:
                    for feature, score in top_features:
                        st.progress(score / max_importance)
                        st.caption(f"{feature}: {score:.4f}")
                else:
                    # If all values are zero, just show the values
                    for feature, score in top_features:
                        st.caption(f"{feature}: {score:.4f}")
                
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())

def page_verify_predictions():
    st.header("Phase 5 & 6: Verify Predictions")
    st.markdown("Review model predictions and make corrections")
    
    if not st.session_state.workflow_state.get('model_trained'):
        st.warning("Please train model first (Page 3)")
        return
    
    df = st.session_state.workflow_state['features_df'].copy()
    model_name = st.session_state.workflow_state['model_name']
    
    if not st.session_state.workflow_state.get('predictions_made'):
        if st.button("Generate Predictions", type="primary"):
            with st.spinner("Generating predictions..."):
                try:
                    predictions_df = predict_files(df, model_name)
                    
                    # Save predictions
                    folder_name = Path(st.session_state.workflow_state['root_folder']).name or "root"
                    pred_path = save_predictions(predictions_df, folder_name)
                    
                    st.session_state.workflow_state['predictions_df'] = predictions_df
                    st.session_state.workflow_state['predictions_made'] = True
                    st.session_state.workflow_state['predictions_path'] = str(pred_path)
                    
                    summary = get_prediction_summary(predictions_df)
                    st.success("✅ Predictions generated!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Files", summary['total_files'])
                    with col2:
                        st.metric("Selected", summary['selected_files'])
                    with col3:
                        st.metric("Skipped", summary['skipped_files'])
                    with col4:
                        st.metric("Avg Confidence", f"{summary['average_confidence']:.2%}")
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    if st.session_state.workflow_state.get('predictions_made'):
        predictions_df = st.session_state.workflow_state['predictions_df'].copy()
        
        st.subheader("Review Predictions")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            show_only = st.selectbox(
                "Show",
                ["All Files", "Selected Files", "Skipped Files", "Low Confidence (<0.7)"]
            )
        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["Confidence (High to Low)", "Confidence (Low to High)", "File Size", "Date Modified"]
            )
        
        # Filter dataframe
        filtered_df = predictions_df.copy()
        if show_only == "Selected Files":
            filtered_df = filtered_df[filtered_df['selected_for_processing'] == True]
        elif show_only == "Skipped Files":
            filtered_df = filtered_df[filtered_df['selected_for_processing'] == False]
        elif show_only == "Low Confidence (<0.7)":
            filtered_df = filtered_df[filtered_df['confidence_score'] < 0.7]
        
        # Sort
        if sort_by == "Confidence (High to Low)":
            filtered_df = filtered_df.sort_values('confidence_score', ascending=False)
        elif sort_by == "Confidence (Low to High)":
            filtered_df = filtered_df.sort_values('confidence_score', ascending=True)
        elif sort_by == "File Size":
            filtered_df = filtered_df.sort_values('file_size', ascending=False)
        elif sort_by == "Date Modified":
            filtered_df = filtered_df.sort_values('date_modified', ascending=False)
        
        st.info(f"Showing {len(filtered_df)} files")
        
        # Display files with checkboxes
        selected_for_processing = {}
        for idx, row in filtered_df.iterrows():
            col1, col2, col3 = st.columns([0.5, 4, 1])
            with col1:
                is_selected = st.checkbox(
                    "",
                    value=bool(row['selected_for_processing']),
                    key=f"select_{idx}"
                )
                selected_for_processing[idx] = is_selected
            with col2:
                st.markdown(f"**{row['file_name']}**")
                st.caption(f"Path: {row['relative_path']} | Size: {format_file_size(row['file_size'])} | Modified: {format_date(row['date_modified'])}")
            with col3:
                confidence = row['confidence_score']
                st.metric("Confidence", f"{confidence:.2%}")
                if confidence < 0.7:
                    st.warning("Low")
                elif confidence > 0.9:
                    st.success("High")
        
        if st.button("Save Selections", type="primary"):
            # Update predictions_df
            for idx, is_selected in selected_for_processing.items():
                predictions_df.loc[idx, 'selected_for_processing'] = is_selected
                predictions_df.loc[idx, 'predicted_label'] = 1 if is_selected else 0
            
            # Save updated predictions
            folder_name = Path(st.session_state.workflow_state['root_folder']).name or "root"
            pred_path = save_predictions(predictions_df, folder_name)
            st.session_state.workflow_state['predictions_df'] = predictions_df
            st.session_state.workflow_state['predictions_path'] = str(pred_path)
            st.success("✅ Selections saved!")
            st.info("Proceed to 'View Processed Files' page to see the final results")

def page_view_processed():
    st.header("Phase 7: View Processed Files")
    st.markdown("View all files that have been selected for processing")
    
    # Option 1: Load from session state if available
    if st.session_state.workflow_state.get('predictions_made'):
        df = st.session_state.workflow_state['predictions_df'].copy()
        use_session = True
    else:
        use_session = False
        df = None
    
    # Option 2: Load from file
    prediction_files = list(PREDICTIONS_DIR.glob("predictions_*.csv"))
    
    if not use_session and len(prediction_files) > 0:
        st.subheader("Load Predictions from File")
        selected_file = st.selectbox(
            "Select prediction file",
            [f.name for f in sorted(prediction_files, key=lambda x: x.stat().st_mtime, reverse=True)]
        )
        if st.button("Load File"):
            file_path = PREDICTIONS_DIR / selected_file
            df = load_predictions(str(file_path))
            use_session = False
    
    if df is not None and 'selected_for_processing' in df.columns:
        # Filter to only processed files (selected_for_processing == True)
        processed_df = df[df['selected_for_processing'] == True].copy()
        
        st.subheader(f"Processed Files ({len(processed_df)} files)")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Processed", len(processed_df))
        with col2:
            st.metric("Total Size", format_file_size(processed_df['file_size'].sum()))
        with col3:
            st.metric("Unique Folders", processed_df['folder_path'].nunique())
        with col4:
            if 'confidence_score' in processed_df.columns:
                st.metric("Avg Confidence", f"{processed_df['confidence_score'].mean():.2%}")
        
        # Filter and search
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Search files", placeholder="Enter file name or path...")
        with col2:
            folder_filter = st.selectbox(
                "Filter by Folder",
                ["All Folders"] + sorted(processed_df['folder_path'].unique().tolist())[:20]
            )
        
        # Apply filters
        filtered_df = processed_df.copy()
        if search_term:
            filtered_df = filtered_df[
                filtered_df['file_name'].str.contains(search_term, case=False, na=False) |
                filtered_df['relative_path'].str.contains(search_term, case=False, na=False)
            ]
        if folder_filter != "All Folders":
            filtered_df = filtered_df[filtered_df['folder_path'] == folder_filter]
        
        st.info(f"Showing {len(filtered_df)} files")
        
        # Display table
        display_cols = ['file_name', 'relative_path', 'file_size', 'date_modified', 'folder_name']
        if 'confidence_score' in filtered_df.columns:
            display_cols.append('confidence_score')
        
        display_df = filtered_df[display_cols].copy()
        display_df['file_size'] = display_df['file_size'].apply(format_file_size)
        display_df['date_modified'] = display_df['date_modified'].apply(format_date)
        if 'confidence_score' in display_df.columns:
            display_df['confidence_score'] = display_df['confidence_score'].apply(lambda x: f"{x:.2%}")
        
        # Rename columns for display
        display_df.columns = ['File Name', 'Relative Path', 'Size', 'Date Modified', 'Folder', 'Confidence'] if 'confidence_score' in display_df.columns else ['File Name', 'Relative Path', 'Size', 'Date Modified', 'Folder']
        
        st.dataframe(display_df, use_container_width=True, height=600)
        
        # Download button
        csv = processed_df.to_csv(index=False)
        st.download_button(
            label="Download Processed Files (CSV)",
            data=csv,
            file_name=f"processed_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
    else:
        st.warning("No predictions found. Please:")
        st.markdown("1. Complete the workflow (Pages 1-4)")
        st.markdown("2. Or load a prediction file from the dropdown above")
        if len(prediction_files) == 0:
            st.info("No prediction files found in the predictions directory")

if __name__ == "__main__":
    main()

