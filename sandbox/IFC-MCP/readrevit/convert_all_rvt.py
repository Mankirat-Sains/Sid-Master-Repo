#!/usr/bin/env python3
"""
Automated Pipeline: Revit (.rvt) → IFC Conversion
Uses Supabase Storage + Autodesk APS (Forge) Design Automation
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# Import Supabase client
from supabase_client import SupabaseClient

# Load environment variables
load_dotenv()

# Configuration
RVT_SOURCE_DIR = "/Volumes/J:/Projects/rvtfiles"
BUCKET_NAME = "rvtfiles"
APS_ACTIVITY = "IFCExporterActivity"
APS_OSS_BUCKET = "rvtfiles-oss"  # APS OSS bucket name
USE_APS_OSS = True  # Set to True to use APS OSS instead of Supabase (for large files)
OUTPUT_IFC_DIR = "out/ifc"
OUTPUT_LOG_DIR = "out/logs"
PROCESSED_LOG_FILE = "out/logs/processed_files.json"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
SUPABASE_MAX_SIZE_MB = 50  # Supabase free plan limit


def ensure_directories():
    """Create output directories if they don't exist."""
    os.makedirs(OUTPUT_IFC_DIR, exist_ok=True)
    os.makedirs(OUTPUT_LOG_DIR, exist_ok=True)


def load_processed_files() -> Dict[str, Dict]:
    """Load list of already processed files."""
    if os.path.exists(PROCESSED_LOG_FILE):
        try:
            with open(PROCESSED_LOG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load processed files log: {e}")
            return {}
    return {}


def save_processed_file(filename: str, status: str, details: Dict):
    """Save processed file information."""
    processed = load_processed_files()
    processed[filename] = {
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'details': details
    }
    try:
        with open(PROCESSED_LOG_FILE, 'w') as f:
            json.dump(processed, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save processed files log: {e}")


def log_message(message: str, log_file: Optional[str] = None):
    """Print and optionally log a message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    if log_file:
        try:
            with open(log_file, 'a') as f:
                f.write(log_entry + '\n')
        except Exception:
            pass


def find_rvt_files(source_dir: str) -> List[Path]:
    """Find all .rvt files in the source directory."""
    source_path = Path(source_dir)
    
    if not source_path.exists():
        log_message(f"ERROR: Source directory does not exist: {source_dir}")
        return []
    
    if not source_path.is_dir():
        log_message(f"ERROR: Source path is not a directory: {source_dir}")
        return []
    
    rvt_files = list(source_path.rglob("*.rvt"))
    log_message(f"Found {len(rvt_files)} .rvt file(s) in {source_dir}")
    return rvt_files


def upload_to_supabase(client: SupabaseClient, file_path: Path, bucket_name: str, max_retries: int = MAX_RETRIES) -> Tuple[bool, Optional[str]]:
    """
    Upload file to Supabase with retry logic.
    
    Returns:
        Tuple of (success: bool, object_name: Optional[str])
    """
    filename = file_path.name
    object_name = f"{filename}"
    
    for attempt in range(1, max_retries + 1):
        log_message(f"Upload attempt {attempt}/{max_retries}: {filename}")
        success, message = client.upload_file(bucket_name, str(file_path), object_name)
        
        if success:
            log_message(f"✓ Upload successful: {filename}")
            return True, object_name
        else:
            log_message(f"✗ Upload failed: {message}")
            if attempt < max_retries:
                log_message(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
    
    return False, None


def create_signed_url(client: SupabaseClient, bucket_name: str, object_name: str, max_retries: int = MAX_RETRIES) -> Tuple[bool, Optional[str]]:
    """
    Create signed URL with retry logic.
    
    Returns:
        Tuple of (success: bool, signed_url: Optional[str])
    """
    for attempt in range(1, max_retries + 1):
        log_message(f"Creating signed URL (attempt {attempt}/{max_retries}): {object_name}")
        success, signed_url, message = client.create_signed_url(bucket_name, object_name, expires_in=7200)
        
        if success and signed_url:
            log_message(f"✓ Signed URL created (valid for 2 hours)")
            return True, signed_url
        else:
            log_message(f"✗ Failed to create signed URL: {message}")
            if attempt < max_retries:
                log_message(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
    
    return False, None


def ensure_aps_oss_bucket(bucket_name: str, client_id: str, client_secret: str) -> bool:
    """Ensure APS OSS bucket exists, create if it doesn't."""
    auth_cmd = [
        'aps', 'auth', 'login',
        '--client-id', client_id,
        '--client-secret', client_secret
    ]
    
    # Check if bucket exists by trying to list it
    list_cmd = ['aps', 'oss', 'ls', bucket_name]
    
    try:
        subprocess.run(auth_cmd, capture_output=True, text=True, timeout=30)
        result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return True  # Bucket exists
    except:
        pass
    
    # Bucket doesn't exist, create it
    create_cmd = [
        'aps', 'oss', 'create-bucket', bucket_name, '--policy', 'transient'
    ]
    
    try:
        subprocess.run(auth_cmd, capture_output=True, text=True, timeout=30)
        result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except:
        return False


def upload_to_aps_oss(file_path: Path, bucket_name: str, client_id: str, client_secret: str, max_retries: int = MAX_RETRIES) -> Tuple[bool, Optional[str]]:
    """
    Upload file to APS OSS bucket with retry logic.
    
    Returns:
        Tuple of (success: bool, object_name: Optional[str])
    """
    filename = file_path.name
    object_name = filename
    
    # Authenticate first
    auth_cmd = [
        'aps', 'auth', 'login',
        '--client-id', client_id,
        '--client-secret', client_secret
    ]
    
    # Upload command
    upload_cmd = [
        'aps', 'oss', 'upload', bucket_name, str(file_path)
    ]
    
    for attempt in range(1, max_retries + 1):
        log_message(f"APS OSS upload attempt {attempt}/{max_retries}: {filename}")
        
        try:
            # Authenticate (silent mode)
            subprocess.run(
                auth_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Upload file
            result = subprocess.run(
                upload_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes for large files
            )
            
            if result.returncode == 0:
                log_message(f"✓ Upload successful: {filename}")
                return True, object_name
            else:
                error_msg = result.stderr or result.stdout
                log_message(f"✗ Upload failed: {error_msg}")
                if attempt < max_retries:
                    log_message(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
        except subprocess.TimeoutExpired:
            log_message(f"✗ Upload timed out")
            if attempt < max_retries:
                log_message(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
        except Exception as e:
            log_message(f"✗ Error uploading: {str(e)}")
            if attempt < max_retries:
                log_message(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
    
    return False, None


def create_aps_workitem(activity_name: str, input_url_or_object: str, output_filename: str, client_id: str, client_secret: str, is_oss_object: bool = False, max_retries: int = MAX_RETRIES) -> Tuple[bool, Optional[str]]:
    """
    Create APS workitem using CLI with retry logic.
    
    Returns:
        Tuple of (success: bool, workitem_id: Optional[str])
    """
    # Authenticate first (if needed)
    auth_cmd = [
        'aps', 'auth', 'login',
        '--client-id', client_id,
        '--client-secret', client_secret
    ]
    
    # Create workitem command
    if is_oss_object:
        # Use OSS object name directly
        workitem_cmd = [
            'aps', 'da', 'workitem', 'create', activity_name,
            '--input', f'inputRvt={input_url_or_object}',
            '--output', f'resultIfc=./out/ifc/{output_filename}'
        ]
    else:
        # Use signed URL
        workitem_cmd = [
            'aps', 'da', 'workitem', 'create', activity_name,
            '--input', f'inputRvt={input_url_or_object}',
            '--output', f'resultIfc=./out/ifc/{output_filename}'
        ]
    
    for attempt in range(1, max_retries + 1):
        log_message(f"Creating APS workitem (attempt {attempt}/{max_retries})")
        
        try:
            # Authenticate (silent mode)
            auth_result = subprocess.run(
                auth_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Create workitem
            result = subprocess.run(
                workitem_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Try to extract workitem ID from output
                output_lines = result.stdout.strip().split('\n')
                workitem_id = None
                for line in output_lines:
                    if 'workitem' in line.lower() or 'id' in line.lower():
                        # Try to extract ID (format may vary)
                        parts = line.split()
                        for part in parts:
                            if len(part) > 20:  # Workitem IDs are typically long
                                workitem_id = part
                                break
                
                log_message(f"✓ Workitem created successfully")
                if workitem_id:
                    log_message(f"  Workitem ID: {workitem_id}")
                return True, workitem_id
            else:
                error_msg = result.stderr or result.stdout
                log_message(f"✗ Workitem creation failed: {error_msg}")
                if attempt < max_retries:
                    log_message(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
        except subprocess.TimeoutExpired:
            log_message(f"✗ Workitem creation timed out")
            if attempt < max_retries:
                log_message(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
        except Exception as e:
            log_message(f"✗ Error creating workitem: {str(e)}")
            if attempt < max_retries:
                log_message(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
    
    return False, None


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)


def process_rvt_file(file_path: Path, supabase_client: Optional[SupabaseClient], aps_client_id: str, aps_client_secret: str) -> bool:
    """
    Process a single RVT file: upload to storage, create input reference, submit APS workitem.
    
    Returns:
        True if successful, False otherwise
    """
    filename = file_path.name
    file_size_mb = get_file_size_mb(file_path)
    
    log_message(f"\n{'='*60}")
    log_message(f"Processing: {filename} ({file_size_mb:.2f} MB)")
    log_message(f"{'='*60}")
    
    # Decide which storage to use
    use_oss = USE_APS_OSS or (file_size_mb > SUPABASE_MAX_SIZE_MB)
    
    if use_oss:
        log_message("Using APS OSS (bypassing Supabase size limits)")
        
        # Step 1: Upload to APS OSS
        log_message("Step 1: Uploading to APS OSS...")
        upload_success, object_name = upload_to_aps_oss(file_path, APS_OSS_BUCKET, aps_client_id, aps_client_secret)
        
        if not upload_success:
            log_message(f"✗ Failed to upload {filename} to APS OSS")
            save_processed_file(filename, 'failed', {'error': 'APS OSS upload failed', 'object_name': object_name})
            return False
        
        # Step 2: Create APS workitem with OSS object
        log_message("Step 2: Creating APS workitem with OSS object...")
        output_filename = filename.replace('.rvt', '.ifc')
        workitem_success, workitem_id = create_aps_workitem(
            APS_ACTIVITY,
            object_name,  # OSS object name
            output_filename,
            aps_client_id,
            aps_client_secret,
            is_oss_object=True
        )
        
        if not workitem_success:
            log_message(f"✗ Failed to create workitem for {filename}")
            save_processed_file(filename, 'failed', {
                'error': 'Workitem creation failed',
                'object_name': object_name,
                'storage': 'APS OSS'
            })
            return False
        
        # Success!
        log_message(f"✓ Successfully submitted {filename} for IFC conversion")
        save_processed_file(filename, 'submitted', {
            'object_name': object_name,
            'workitem_id': workitem_id,
            'output_filename': output_filename,
            'storage': 'APS OSS',
            'file_size_mb': file_size_mb
        })
        return True
    
    else:
        # Use Supabase (original flow)
        if not supabase_client:
            log_message(f"✗ Supabase client not available")
            return False
        
        log_message("Using Supabase storage")
        
        # Step 1: Upload to Supabase
        log_message("Step 1: Uploading to Supabase...")
        upload_success, object_name = upload_to_supabase(supabase_client, file_path, BUCKET_NAME)
        
        if not upload_success:
            log_message(f"✗ Failed to upload {filename}")
            save_processed_file(filename, 'failed', {'error': 'Upload failed', 'object_name': object_name})
            return False
        
        # Step 2: Create signed URL
        log_message("Step 2: Creating signed URL...")
        url_success, signed_url = create_signed_url(supabase_client, BUCKET_NAME, object_name)
        
        if not url_success or not signed_url:
            log_message(f"✗ Failed to create signed URL for {filename}")
            save_processed_file(filename, 'failed', {'error': 'Signed URL creation failed', 'object_name': object_name})
            return False
        
        # Step 3: Create APS workitem
        log_message("Step 3: Creating APS workitem...")
        output_filename = filename.replace('.rvt', '.ifc')
        workitem_success, workitem_id = create_aps_workitem(
            APS_ACTIVITY,
            signed_url,
            output_filename,
            aps_client_id,
            aps_client_secret,
            is_oss_object=False
        )
        
        if not workitem_success:
            log_message(f"✗ Failed to create workitem for {filename}")
            save_processed_file(filename, 'failed', {
                'error': 'Workitem creation failed',
                'object_name': object_name,
                'signed_url_created': True
            })
            return False
        
        # Success!
        log_message(f"✓ Successfully submitted {filename} for IFC conversion")
        save_processed_file(filename, 'submitted', {
            'object_name': object_name,
            'workitem_id': workitem_id,
            'output_filename': output_filename,
            'signed_url_expires_in': '7200 seconds (2 hours)',
            'storage': 'Supabase',
            'file_size_mb': file_size_mb
        })
        return True


def main():
    """Main pipeline execution."""
    print("="*60)
    print("Revit → IFC Conversion Pipeline")
    print("="*60)
    print()
    
    # Ensure directories exist
    ensure_directories()
    
    # Load environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    # Try service key first, fall back to anon key
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    aps_client_id = os.getenv('client_id')
    aps_client_secret = os.getenv('client_secret')
    
    # Validate environment variables
    missing_vars = []
    if not supabase_url:
        missing_vars.append('SUPABASE_URL')
    if not supabase_key:
        missing_vars.append('SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY')
    if not aps_client_id:
        missing_vars.append('client_id')
    if not aps_client_secret:
        missing_vars.append('client_secret')
    
    if missing_vars:
        print(f"ERROR: Missing environment variables: {', '.join(missing_vars)}")
        print("Please ensure your .env file contains all required variables.")
        if not os.getenv('SUPABASE_SERVICE_KEY') and os.getenv('SUPABASE_ANON_KEY'):
            print("\n⚠️  NOTE: Using SUPABASE_ANON_KEY. Service key is recommended for full permissions.")
        sys.exit(1)
    
    # Warn if using anon key
    if os.getenv('SUPABASE_ANON_KEY') and not os.getenv('SUPABASE_SERVICE_KEY'):
        log_message("⚠️  WARNING: Using SUPABASE_ANON_KEY instead of SUPABASE_SERVICE_KEY")
        log_message("   Service key is recommended for bucket creation and file uploads.")
    
    # Initialize Supabase client (only if not using OSS)
    supabase_client = None
    if not USE_APS_OSS:
        log_message("Initializing Supabase client...")
        supabase_client = SupabaseClient(supabase_url, supabase_key)
        
        # Ensure bucket exists
        log_message(f"Checking bucket '{BUCKET_NAME}'...")
        if not supabase_client.bucket_exists(BUCKET_NAME):
            log_message(f"Bucket '{BUCKET_NAME}' does not exist. Creating...")
            success, message = supabase_client.create_bucket(BUCKET_NAME, public=False)
            if not success:
                log_message(f"ERROR: {message}")
                sys.exit(1)
            log_message(f"✓ {message}")
        else:
            log_message(f"✓ Bucket '{BUCKET_NAME}' exists")
    else:
        log_message("Using APS OSS for file storage (bypassing Supabase)")
        log_message(f"Ensuring APS OSS bucket '{APS_OSS_BUCKET}' exists...")
        if ensure_aps_oss_bucket(APS_OSS_BUCKET, aps_client_id, aps_client_secret):
            log_message(f"✓ APS OSS bucket '{APS_OSS_BUCKET}' is ready")
        else:
            log_message(f"⚠️  Could not verify/create OSS bucket. Will attempt upload anyway.")
    
    # Find RVT files
    log_message(f"\nScanning for .rvt files in: {RVT_SOURCE_DIR}")
    rvt_files = find_rvt_files(RVT_SOURCE_DIR)
    
    if not rvt_files:
        log_message("No .rvt files found. Exiting.")
        sys.exit(0)
    
    # Load processed files
    processed_files = load_processed_files()
    
    # Process each file
    total_files = len(rvt_files)
    processed_count = 0
    skipped_count = 0
    failed_count = 0
    
    log_file = os.path.join(OUTPUT_LOG_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    for i, rvt_file in enumerate(rvt_files, 1):
        filename = rvt_file.name
        
        log_message(f"\n[{i}/{total_files}] Processing: {filename}", log_file)
        
        # Check if already processed
        if filename in processed_files:
            status = processed_files[filename].get('status', 'unknown')
            if status == 'submitted':
                log_message(f"⊘ Skipping {filename} (already submitted)", log_file)
                skipped_count += 1
                continue
        
        # Process file
        success = process_rvt_file(rvt_file, supabase_client, aps_client_id, aps_client_secret)
        
        if success:
            processed_count += 1
        else:
            failed_count += 1
        
        # Small delay between files
        if i < total_files:
            time.sleep(2)
    
    # Summary
    log_message("\n" + "="*60, log_file)
    log_message("Pipeline Summary", log_file)
    log_message("="*60, log_file)
    log_message(f"Total files found: {total_files}", log_file)
    log_message(f"Successfully processed: {processed_count}", log_file)
    log_message(f"Skipped (already processed): {skipped_count}", log_file)
    log_message(f"Failed: {failed_count}", log_file)
    log_message(f"\nLog file: {log_file}", log_file)
    log_message("="*60, log_file)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

