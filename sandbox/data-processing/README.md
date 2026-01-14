# Intelligent File Selection System

AI-powered document selection system for RAG processing. Uses XGBoost machine learning to intelligently select files from client folders based on patterns learned from user feedback.

## Features

- **Feature Extraction**: Automatically extracts metadata from folder structures (file size, dates, folder hierarchy, etc.)
- **Strategic Case Selection**: Uses clustering and outlier detection to select diverse cases for labeling
- **Machine Learning**: XGBoost classifier learns from user-labeled examples
- **Active Learning**: Presents targeted scenarios to user for labeling
- **Verification Loop**: Allows user to review and correct predictions
- **View Processed Files**: Page to view all files selected for processing (filtered by boolean = 1)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Follow the workflow:
   - **Page 1**: Extract features from your root folder
   - **Page 2**: Label 10-20 strategic cases (selected by the system)
   - **Page 3**: Train the XGBoost model
   - **Page 4**: Verify predictions and make corrections
   - **Page 5**: View all processed files (filtered to selected_for_processing = True)

## Workflow

1. **Phase 1: Extract Features**
   - Scans folder structure recursively
   - Extracts file metadata (size, dates, folder hierarchy)
   - Computes relative features (comparisons with sibling files)

2. **Phase 2: Strategic Case Selection**
   - Uses K-means clustering for diversity
   - Includes outlier detection for edge cases
   - Selects 10-20 representative cases

3. **Phase 3: User Labeling**
   - User labels each strategic case (Process/Skip)
   - System learns patterns from these examples

4. **Phase 4: Model Training**
   - Trains XGBoost classifier on labeled data
   - Shows feature importance
   - Saves model for future use

5. **Phase 5: Prediction**
   - Model predicts on all files
   - Generates probability scores

6. **Phase 6: Verification**
   - User reviews predictions
   - Can make corrections
   - Final selections saved

7. **Phase 7: View Processed Files**
   - View all files with `selected_for_processing = True`
   - Filter and search capabilities
   - Download results as CSV

## Directory Structure

```
data-processing/
├── app.py                  # Main Streamlit app
├── config.py               # Configuration
├── feature_extractor.py    # Feature extraction
├── case_selector.py        # Strategic case selection
├── model_trainer.py        # XGBoost training
├── model_predictor.py      # Prediction
├── utils.py                # Utility functions
├── requirements.txt        # Dependencies
├── data/
│   ├── features/           # Extracted features (CSV)
│   ├── labels/             # User labels (CSV)
│   ├── models/             # Trained XGBoost models
│   └── predictions/        # Prediction results (CSV)
└── README.md
```

## Configuration

Edit `config.py` to customize:
- Number of strategic cases to label (default: 20)
- Prediction threshold (default: 0.5)
- Valid file extensions
- Feature extraction settings

## Data Storage

- Features: Saved as CSV in `data/features/`
- Models: Saved as pickle files in `data/models/`
- Predictions: Saved as CSV in `data/predictions/`
- All files include timestamps for versioning

## Notes

- The system learns patterns from folder structure, file sizes, dates, and naming conventions
- Works best with consistent folder structures per client
- Can be used for first client (with manual labeling) and subsequent clients (with transfer learning)
- "View Processed Files" page filters to `selected_for_processing == True` (boolean = 1)

