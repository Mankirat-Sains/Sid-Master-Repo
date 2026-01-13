"""
Local Excel Sync Agent
======================
This agent runs on a local machine or shared drive where Excel calculation 
files are stored. It monitors specified Excel files and syncs data to the 
cloud platform when requested.

Requirements:
- Python 3.8+
- openpyxl (pip install openpyxl)
- requests (pip install requests)
- watchdog (pip install watchdog)

Usage:
    python local_sync_agent.py --config config.json
"""

import openpyxl
import requests
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ExcelSyncAgent')


class ExcelReader:
    """Handles reading specific cells from Excel files"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def read_cells(self, sheet_name: str, cell_mappings: Dict[str, str]) -> Dict[str, Any]:
        """
        Read specific cells from an Excel sheet
        
        Args:
            sheet_name: Name of the sheet to read from
            cell_mappings: Dict mapping field names to cell references
                          e.g., {"ground_snow_load": "B6", "wind_load": "B8"}
        
        Returns:
            Dict with field names as keys and cell values as values
        """
        try:
            workbook = openpyxl.load_workbook(self.file_path, data_only=True)
            
            if sheet_name not in workbook.sheetnames:
                logger.error(f"Sheet '{sheet_name}' not found in {self.file_path}")
                return {}
            
            sheet = workbook[sheet_name]
            data = {}
            
            for field_name, cell_ref in cell_mappings.items():
                try:
                    cell_value = sheet[cell_ref].value
                    data[field_name] = cell_value
                    logger.debug(f"Read {field_name} from {cell_ref}: {cell_value}")
                except Exception as e:
                    logger.warning(f"Could not read cell {cell_ref}: {e}")
                    data[field_name] = None
            
            workbook.close()
            return data
            
        except Exception as e:
            logger.error(f"Error reading Excel file {self.file_path}: {e}")
            return {}


class PlatformAPI:
    """Handles communication with the cloud platform"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def send_calculation_data(self, project_id: str, data: Dict[str, Any]) -> bool:
        """
        Send calculation data to the platform
        
        Args:
            project_id: Unique identifier for the project
            data: Dictionary containing the calculation data
        
        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.api_url}/api/projects/{project_id}/calculations"
        
        payload = {
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'local_agent'
        }
        
        try:
            response = self.session.post(endpoint, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Successfully synced data for project {project_id}")
                return True
            else:
                logger.error(f"Failed to sync: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during sync: {e}")
            return False
    
    def check_sync_request(self, project_id: str) -> Optional[Dict]:
        """
        Check if platform has requested a sync
        
        Returns:
            Dict with sync request details if pending, None otherwise
        """
        endpoint = f"{self.api_url}/api/projects/{project_id}/sync-requests"
        
        try:
            response = self.session.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('sync_requested'):
                    return data
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking sync request: {e}")
            return None


class ExcelFileHandler(FileSystemEventHandler):
    """Monitors Excel file changes"""
    
    def __init__(self, callback):
        self.callback = callback
        self.last_modified = {}
        
    def on_modified(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith(('.xlsx', '.xlsm')):
            # Debounce: only trigger if file hasn't been modified in last 2 seconds
            current_time = time.time()
            last_time = self.last_modified.get(event.src_path, 0)
            
            if current_time - last_time > 2:
                self.last_modified[event.src_path] = current_time
                logger.info(f"Detected change in {event.src_path}")
                self.callback(event.src_path)


class SyncAgent:
    """Main agent that coordinates Excel reading and platform syncing"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.api = PlatformAPI(
            config['platform_url'],
            config['api_key']
        )
        self.projects = config['projects']
        self.poll_interval = config.get('poll_interval', 30)  # seconds
        self.auto_sync_on_change = config.get('auto_sync_on_change', False)
        
    def sync_project(self, project_config: Dict) -> bool:
        """Sync a single project's data"""
        project_id = project_config['project_id']
        excel_path = project_config['excel_file']
        sheet_name = project_config['sheet_name']
        cell_mappings = project_config['cell_mappings']
        
        logger.info(f"Syncing project {project_id} from {excel_path}")
        
        reader = ExcelReader(excel_path)
        data = reader.read_cells(sheet_name, cell_mappings)
        
        if not data:
            logger.warning(f"No data extracted for project {project_id}")
            return False
        
        return self.api.send_calculation_data(project_id, data)
    
    def sync_all_projects(self):
        """Sync all configured projects"""
        logger.info("Starting sync for all projects")
        
        for project in self.projects:
            try:
                self.sync_project(project)
            except Exception as e:
                logger.error(f"Error syncing project {project.get('project_id')}: {e}")
        
        logger.info("Completed sync for all projects")
    
    def start_polling_mode(self):
        """Run agent in polling mode - checks for sync requests periodically"""
        logger.info(f"Starting polling mode (interval: {self.poll_interval}s)")
        
        try:
            while True:
                for project in self.projects:
                    project_id = project['project_id']
                    
                    # Check if platform requested a sync
                    sync_request = self.api.check_sync_request(project_id)
                    
                    if sync_request:
                        logger.info(f"Sync requested for project {project_id}")
                        self.sync_project(project)
                
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Agent stopped by user")
    
    def start_watch_mode(self):
        """Run agent in watch mode - syncs when files change"""
        logger.info("Starting watch mode")
        
        observer = Observer()
        
        # Get unique directories to watch
        watch_dirs = set()
        for project in self.projects:
            excel_path = Path(project['excel_file'])
            watch_dirs.add(excel_path.parent)
        
        def on_file_change(file_path):
            # Find which project this file belongs to
            for project in self.projects:
                if Path(project['excel_file']).resolve() == Path(file_path).resolve():
                    if self.auto_sync_on_change:
                        self.sync_project(project)
                    else:
                        logger.info(f"File changed but auto-sync disabled: {file_path}")
        
        handler = ExcelFileHandler(on_file_change)
        
        for watch_dir in watch_dirs:
            observer.schedule(handler, str(watch_dir), recursive=False)
            logger.info(f"Watching directory: {watch_dir}")
        
        observer.start()
        
        try:
            # Also poll for sync requests
            while True:
                for project in self.projects:
                    sync_request = self.api.check_sync_request(project['project_id'])
                    if sync_request:
                        self.sync_project(project)
                
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Agent stopped by user")
            observer.stop()
        
        observer.join()


def load_config(config_path: str) -> Dict:
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='Excel Sync Agent for Engineering Platform')
    parser.add_argument('--config', required=True, help='Path to configuration JSON file')
    parser.add_argument('--mode', choices=['polling', 'watch', 'once'], default='polling',
                       help='Agent mode: polling (check for requests), watch (monitor files), once (sync once and exit)')
    parser.add_argument('--sync-now', action='store_true',
                       help='Trigger immediate sync for all projects')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    agent = SyncAgent(config)
    
    # Execute based on mode
    if args.sync_now or args.mode == 'once':
        agent.sync_all_projects()
    elif args.mode == 'polling':
        agent.start_polling_mode()
    elif args.mode == 'watch':
        agent.start_watch_mode()


if __name__ == '__main__':
    main()
