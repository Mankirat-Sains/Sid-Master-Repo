"""Main Streamlit App for Intelligent File Selection"""
import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

# Import modules
from feature_extractor import extract_file_metadata, save_features, load_features
from model_trainer import train_model, load_model
from model_predictor import predict_files, get_prediction_summary
from utils import format_file_size, format_date, save_predictions, load_predictions
from config import FEATURES_DIR, LABELS_DIR, MODELS_DIR, PREDICTIONS_DIR, N_STRATEGIC_CASES, MAX_FOLDERS, FOLDER_NAME_PREFIX_FILTER

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
        ["1. Setup & Extract Features", "2. Select Files for Training", 
         "3. Train Model", "4. Verify Predictions", "5. View Processed Files"]
    )
    
    if page == "1. Setup & Extract Features":
        page_extract_features()
    elif page == "2. Select Files for Training":
        page_select_files()
    elif page == "3. Train Model":
        page_train_model()
    elif page == "4. Verify Predictions":
        page_verify_predictions()
    elif page == "5. View Processed Files":
        page_view_processed()

def page_extract_features():
    st.header("Phase 1: Extract Features")
    st.markdown("Extract metadata and features from your folder structure")
    
    root_folder = st.text_input("Root Folder Path", value=st.session_state.workflow_state.get('root_folder', ''))
    
    if st.button("Extract Features", type="primary"):
        if not root_folder or not Path(root_folder).exists():
            st.error("Please enter a valid folder path")
            return
        
        with st.spinner("Extracting features from files..."):
            try:
                df = extract_file_metadata(root_folder)
                
                if df.empty:
                    st.warning("No files found in the specified folder")
                    return
                
                # Save features
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                features_path = FEATURES_DIR / f"features_{timestamp}.csv"
                save_features(df, str(features_path))
                
                # Update session state
                st.session_state.workflow_state['root_folder'] = root_folder
                st.session_state.workflow_state['features_df'] = df
                st.session_state.workflow_state['features_extracted'] = True
                st.session_state.workflow_state['features_path'] = str(features_path)
                
                st.success("✅ Features extracted successfully!")
                
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
    
    # Show existing features if available
    if st.session_state.workflow_state.get('features_extracted'):
        st.info("✅ Features already extracted. You can proceed to 'Select Files for Training' page.")


def page_select_files():
    st.header("Phase 2: Select Files for Training")
    st.markdown("Select files you want to process. For each selected file, all other files in the same subfolder will be marked as negative examples.")
    
    if not st.session_state.workflow_state.get('features_extracted'):
        st.warning("Please extract features first (Page 1)")
        return
    
    df = st.session_state.workflow_state['features_df'].copy()
    root_folder = st.session_state.workflow_state.get('root_folder', '')
    
    # Filter to only files with depth > 1 (files inside subfolders, not directly in root)
    if 'depth' in df.columns:
        df = df[df['depth'] > 1].copy()
        if df.empty:
            st.warning("No files found in subfolders. Please check your folder structure.")
            return
    
    # Ensure parent_subfolder exists (identifies the first-level subfolder for each file)
    if 'parent_subfolder' not in df.columns and root_folder:
        root_path = Path(root_folder)
        def get_parent_subfolder(relative_path_str):
            try:
                parts = Path(relative_path_str).parts
                if len(parts) > 1:
                    return str(root_path / parts[0])
                return str(root_path)
            except:
                return str(root_path)
        df['parent_subfolder'] = df['relative_path'].apply(get_parent_subfolder)
    
    if 'parent_subfolder' not in df.columns:
        st.error("Cannot identify parent subfolders. Please re-extract features.")
        return
    
    # Filter by folder name prefix if configured (for testing)
    if FOLDER_NAME_PREFIX_FILTER:
        def get_folder_name_from_path(path_str):
            try:
                return Path(path_str).name
            except:
                return ""
        df['parent_folder_name'] = df['parent_subfolder'].apply(get_folder_name_from_path)
        original_count = len(df)
        df = df[df['parent_folder_name'].str.startswith(FOLDER_NAME_PREFIX_FILTER, na=False)].copy()
        if df.empty:
            st.warning(f"No files found in folders starting with '{FOLDER_NAME_PREFIX_FILTER}'. Please adjust the filter or root folder.")
            return
        if len(df) < original_count:
            st.info(f"🔍 Filtered to folders starting with '{FOLDER_NAME_PREFIX_FILTER}': {len(df)} files (from {original_count} total)")
    
    total_subfolders = df['parent_subfolder'].nunique()
    st.info(f"📁 Found {len(df)} files across {total_subfolders} first-level subfolders")
    
    # Cap to MAX_FOLDERS
    unique_folders = sorted(df['parent_subfolder'].unique().tolist())
    if len(unique_folders) > MAX_FOLDERS:
        unique_folders = unique_folders[:MAX_FOLDERS]
        st.warning(f"⚠️ Limited to first {MAX_FOLDERS} folders (out of {total_subfolders} total) to prevent system overload. Adjust MAX_FOLDERS in config.py if needed.")
        df = df[df['parent_subfolder'].isin(unique_folders)].copy()
    
    # Initialize labels in session state
    if 'labels' not in st.session_state.workflow_state:
        st.session_state.workflow_state['labels'] = {}
    
    labels = st.session_state.workflow_state['labels']
    
    # Get selected files (positive examples)
    selected_file_indices = set(idx for idx, label in labels.items() if label == 1)
    
    st.subheader("Select Files")
    st.markdown(f"**Selected: {len(selected_file_indices)} files** (Target: {N_STRATEGIC_CASES} files)")
    st.info("ℹ️ **Note:** Only one file can be selected per subfolder. Selecting a new file in a subfolder will automatically deselect the previous selection in that subfolder.")
    
    # Folder navigation
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("**Navigate by Subfolder:**")
        folder_options = ["All Subfolders"] + sorted(unique_folders)[:100]  # Limit for performance
        selected_folder = st.selectbox(
            "Select subfolder to view",
            folder_options,
            key="folder_selector",
            help="Select a subfolder to view files in that subfolder only"
        )
    
    # Filter dataframe based on selected folder
    display_df = df.copy()
    if selected_folder != "All Subfolders":
        display_df = display_df[display_df['parent_subfolder'] == selected_folder].copy()
        folder_name = Path(selected_folder).name
        st.markdown(f"**Viewing files in:** `{folder_name}` ({len(display_df)} files)")
    
    if len(display_df) == 0:
        st.warning("No files found in selected subfolder")
        return
    
    # Prepare table display with checkboxes
    st.markdown("**Select files you want to process:**")
    
    # Create display dataframe with selection status (keep original index for mapping)
    display_table = display_df.copy()
    display_table['Selected'] = display_table.index.isin(selected_file_indices)
    
    # Create a display table with relevant columns (keep original index)
    display_cols = ['Selected', 'file_name', 'file_size', 'date_modified', 'folder_name', 'relative_path']
    display_table_display = display_table[display_cols].copy()
    
    # Format columns for display (create copies to avoid SettingWithCopyWarning)
    display_table_display = display_table_display.copy()
    display_table_display['file_size_display'] = display_table_display['file_size'].apply(format_file_size)
    display_table_display['date_modified_display'] = display_table_display['date_modified'].apply(format_date)
    
    # Reorder columns for display
    display_cols_ordered = ['Selected', 'file_name', 'file_size_display', 'date_modified_display', 'folder_name', 'relative_path']
    display_table_display = display_table_display[display_cols_ordered]
    
    # Rename columns for better display
    display_table_display.columns = ['✅', 'File Name', 'Size', 'Date Modified', 'Folder', 'Path']
    
    # Use data_editor for interactive selection
    edited_df = st.data_editor(
        display_table_display,
        column_config={
            "✅": st.column_config.CheckboxColumn(
                "Selected",
                help="Select files to process",
                default=False,
            ),
            "File Name": st.column_config.TextColumn("File Name", width="medium"),
            "Size": st.column_config.TextColumn("Size", width="small"),
            "Date Modified": st.column_config.TextColumn("Date Modified", width="medium"),
            "Folder": st.column_config.TextColumn("Folder", width="small"),
            "Path": st.column_config.TextColumn("Path", width="large"),
        },
        hide_index=False,  # Keep index visible for debugging, or hide it
        use_container_width=True,
        height=500,
        key=f"file_selector_table_{selected_folder}"  # Unique key per folder
    )
    
    # Update labels based on checkbox changes
    if st.button("Save Selection", type="primary"):
        # Get currently selected files from the CURRENT folder view only
        current_view_selected_indices = set()
        for original_idx in edited_df.index:
            if edited_df.loc[original_idx, '✅']:  # If checkbox is checked
                current_view_selected_indices.add(original_idx)
        
        # Get subfolders in the current view
        current_view_subfolders = set(display_df['parent_subfolder'].unique())
        
        # Preserve selections from OTHER folders (not in current view)
        all_selected_indices = set()
        for idx, label in labels.items():
            if label == 1:  # Positive example
                parent_subfolder = df.loc[idx, 'parent_subfolder']
                # Only keep if not in current view (we'll update current view selections)
                if parent_subfolder not in current_view_subfolders:
                    all_selected_indices.add(idx)
        
        # Add selections from current view (ensuring only one per subfolder)
        for file_idx in current_view_selected_indices:
            all_selected_indices.add(file_idx)
            labels[file_idx] = 1
        
        # For each selected file, mark all other files in the same subfolder as negative (0)
        # Also unselect any previous selection in subfolders from current view
        for file_idx in current_view_selected_indices:
            parent_subfolder = df.loc[file_idx, 'parent_subfolder']
            
            # Unselect any previous selection in this subfolder (from current or other folders)
            subfolder_files = df[df['parent_subfolder'] == parent_subfolder]
            for other_idx in subfolder_files.index:
                if other_idx != file_idx:
                    # Unselect if it was previously selected
                    if other_idx in labels and labels[other_idx] == 1:
                        if other_idx in labels:
                            del labels[other_idx]
                        if other_idx in all_selected_indices:
                            all_selected_indices.remove(other_idx)
                    # Mark as negative
                    labels[other_idx] = 0
        
        # Also handle deselections in current view - if a file was unchecked, remove its label
        for file_idx in display_df.index:
            if file_idx not in current_view_selected_indices:
                # Was previously selected but now unchecked
                if file_idx in labels and labels[file_idx] == 1:
                    del labels[file_idx]
                    if file_idx in all_selected_indices:
                        all_selected_indices.remove(file_idx)
                    # Remove negative labels from this subfolder since no file is selected
                    parent_subfolder = df.loc[file_idx, 'parent_subfolder']
                    subfolder_files = df[df['parent_subfolder'] == parent_subfolder]
                    for other_idx in subfolder_files.index:
                        if other_idx in labels and labels[other_idx] == 0:
                            del labels[other_idx]
        
        st.session_state.workflow_state['labels'] = labels
        st.session_state.workflow_state['strategic_cases_selected'] = True
        total_selected = sum(1 for label in labels.values() if label == 1)
        st.success(f"✅ Selection saved! {total_selected} file(s) selected as positive examples (across all folders).")
        st.rerun()
    
    # Show summary of current labels
    if len(labels) > 0:
        positive_count = sum(1 for label in labels.values() if label == 1)
        negative_count = sum(1 for label in labels.values() if label == 0)
        
        st.subheader("Labeling Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Positive Examples (Selected)", positive_count)
        with col2:
            st.metric("Negative Examples (From Same Subfolders)", negative_count)
        
        if positive_count >= N_STRATEGIC_CASES:
            st.success(f"🎉 You've selected {positive_count} files! You can proceed to Model Training (Page 3)")
        else:
            st.info(f"Select at least {N_STRATEGIC_CASES} files for training. Currently: {positive_count}/{N_STRATEGIC_CASES}")

def page_train_model():
    st.header("Phase 3: Train Model")
    st.markdown("Train XGBoost model on your selected files")
    
    if not st.session_state.workflow_state.get('strategic_cases_selected'):
        st.warning("Please select files for training first (Page 2)")
        return
    
    df = st.session_state.workflow_state['features_df'].copy()
    labels = st.session_state.workflow_state['labels']
    
    if len(labels) < 2:
        st.warning(f"Need at least 2 labeled examples, got {len(labels)}")
        return
    
    # Add labels to dataframe
    df['label'] = df.index.map(labels)
    
    labeled_df = df[df['label'].notna()].copy()
    
    st.subheader("Labeled Data Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Labeled", len(labeled_df))
        st.metric("Positive (1)", (labeled_df['label'] == 1).sum())
    with col2:
        st.metric("Negative (0)", (labeled_df['label'] == 0).sum())
    
    if st.button("Train Model", type="primary"):
        with st.spinner("Training XGBoost model..."):
            try:
                model_info = train_model(df)
                
                st.session_state.workflow_state['model_trained'] = True
                st.session_state.workflow_state['model_name'] = model_info['metadata']['model_name']
                
                st.success("✅ Model trained successfully!")
                st.info(f"Model saved as: {model_info['metadata']['model_name']}")
                
                # Show feature importance
                st.subheader("Feature Importance (Top 10)")
                feature_importance = model_info['metadata']['feature_importance']
                top_features = list(feature_importance.items())[:10]
                
                feature_df = pd.DataFrame(top_features, columns=['Feature', 'Importance'])
                st.bar_chart(feature_df.set_index('Feature'))
                
            except Exception as e:
                st.error(f"Error training model: {e}")

def page_verify_predictions():
    st.header("Phase 4: Verify Predictions")
    st.markdown("Review and verify model predictions")
    
    if not st.session_state.workflow_state.get('model_trained'):
        st.warning("Please train a model first (Page 3)")
        return
    
    df = st.session_state.workflow_state['features_df'].copy()
    model_name = st.session_state.workflow_state.get('model_name')
    
    if not model_name:
        st.error("No model found. Please train a model first.")
        return
    
    if st.button("Generate Predictions", type="primary"):
        with st.spinner("Generating predictions for all files..."):
            try:
                predictions_df = predict_files(df, model_name)
                
                st.session_state.workflow_state['predictions_df'] = predictions_df
                st.session_state.workflow_state['predictions_made'] = True
                
                st.success("✅ Predictions generated!")
                
                summary = get_prediction_summary(predictions_df)
                
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
                st.error(f"Error generating predictions: {e}")
    
    if st.session_state.workflow_state.get('predictions_made'):
        predictions_df = st.session_state.workflow_state['predictions_df']
        
        st.subheader("Review Predictions")
        
        show_only = st.selectbox(
            "Show",
            ["All Files", "Selected Files", "Skipped Files", "Low Confidence (<0.7)"]
        )
        
        filtered_df = predictions_df.copy()
        if show_only == "Selected Files":
            filtered_df = filtered_df[filtered_df['predicted_label'] == 1]
        elif show_only == "Skipped Files":
            filtered_df = filtered_df[filtered_df['predicted_label'] == 0]
        elif show_only == "Low Confidence (<0.7)":
            filtered_df = filtered_df[filtered_df['confidence_score'] < 0.7]
        
        # Display predictions
        for idx, row in filtered_df.head(20).iterrows():
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    predicted_label = row['predicted_label']
                    st.markdown("✅ Selected" if predicted_label == 1 else "❌ Skipped")
                with col2:
                    st.markdown(f"**{row['file_name']}**")
                    st.caption(f"Path: {row['relative_path']} | Size: {format_file_size(row['file_size'])} | Modified: {format_date(row['date_modified'])}")
                with col3:
                    confidence = row['confidence_score']
                    st.metric("Confidence", f"{confidence:.2%}")
                    if confidence < 0.7:
                        st.warning("Low")
                
                st.divider()
        
        if len(filtered_df) > 20:
            st.info(f"Showing first 20 of {len(filtered_df)} files")
        
        # Save predictions
        if st.button("Save Predictions", type="primary"):
            try:
                save_predictions(predictions_df, str(PREDICTIONS_DIR / f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"))
                st.success("✅ Predictions saved!")
            except Exception as e:
                st.error(f"Error saving predictions: {e}")


def page_view_processed():
    st.header("Phase 5: View Processed Files")
    st.markdown("View all files selected for processing")
    
    # Try to load predictions from session state first
    df = None
    prediction_files = sorted(PREDICTIONS_DIR.glob("predictions_*.csv"), reverse=True)
    
    if st.session_state.workflow_state.get('predictions_made'):
        df = st.session_state.workflow_state.get('predictions_df')
    else:
        # Try to load from file
        if len(prediction_files) > 0:
            file_path = st.selectbox("Select prediction file", prediction_files)
            if st.button("Load"):
                df = load_predictions(str(file_path))
    
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
