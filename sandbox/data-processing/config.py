"""Configuration for file selection system"""
from pathlib import Path
import os

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FEATURES_DIR = DATA_DIR / "features"
LABELS_DIR = DATA_DIR / "labels"
MODELS_DIR = DATA_DIR / "models"
PREDICTIONS_DIR = DATA_DIR / "predictions"

# Create directories if they don't exist
for dir_path in [DATA_DIR, FEATURES_DIR, LABELS_DIR, MODELS_DIR, PREDICTIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Model configuration
N_STRATEGIC_CASES = 5  # Number of cases for user to label
PREDICTION_THRESHOLD = 0.5  # Threshold for binary classification
MODEL_FILE_PREFIX = "file_selection_model"

# File extensions to process
VALID_EXTENSIONS = {'.pdf', '.PDF'}

# Feature extraction settings
ENABLE_SIZE_FEATURES = True
ENABLE_DATE_FEATURES = True
ENABLE_FOLDER_FEATURES = True
ENABLE_CONTEXT_FEATURES = True

