"""
Feedback Logger Module with GitHub Integration
Stores feedback in hidden AppData folder AND syncs to GitHub repository for developer access
Works correctly when packaged with PyInstaller
"""

import json
import os
import sys
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def get_app_data_dir() -> Path:
    """
    Get the appropriate app data directory for the current platform.
    Works correctly whether running from source or PyInstaller bundle.

    Returns:
        Path: Platform-specific app data directory
            Windows: C:/Users/[User]/AppData/Local/Mantle
            macOS: ~/Library/Application Support/Mantle
            Linux: ~/.local/share/Mantle
    """
    app_name = "Mantle"

    if sys.platform == "win32":
        # Windows: Use LOCALAPPDATA
        base_dir = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        return Path(base_dir) / app_name
    elif sys.platform == "darwin":
        # macOS: Use Application Support
        return Path.home() / "Library" / "Application Support" / app_name
    else:
        # Linux: Use XDG data directory
        base_dir = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return Path(base_dir) / app_name


class FeedbackLogger:
    """
    Manages feedback storage:
    1. Saves locally to hidden AppData folder (monthly rotation)
    2. Automatically pushes to GitHub repo for developer access
    3. Works in dev mode AND when packaged with PyInstaller
    """

    def __init__(self, feedback_dir: str = None, github_token: str = None,
                 github_repo: str = None, github_owner: str = None):
        """
        Initialize the feedback logger.

        Args:
            feedback_dir: Override directory (default: AppData/Mantle/feedback)
            github_token: GitHub Personal Access Token (from env: GITHUB_FEEDBACK_TOKEN)
            github_repo: GitHub repository name (from env: GITHUB_FEEDBACK_REPO)
            github_owner: GitHub username/org (from env: GITHUB_FEEDBACK_OWNER)
        """
        # Local storage setup - use AppData by default
        if feedback_dir is None:
            app_data_dir = get_app_data_dir()
            feedback_dir = app_data_dir / "feedback"

        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

        # GitHub integration setup
        self.github_token = github_token or os.getenv("GITHUB_FEEDBACK_TOKEN")
        self.github_repo = github_repo or os.getenv("GITHUB_FEEDBACK_REPO")
        self.github_owner = github_owner or os.getenv("GITHUB_FEEDBACK_OWNER")

        self.github_enabled = all([self.github_token, self.github_repo, self.github_owner])

        if self.github_enabled:
            logger.info(f"✓ GitHub feedback sync enabled: {self.github_owner}/{self.github_repo}")
        else:
            logger.warning("⚠ GitHub feedback sync disabled. Set GITHUB_FEEDBACK_TOKEN, GITHUB_FEEDBACK_REPO, and GITHUB_FEEDBACK_OWNER to enable.")

        logger.info(f"✓ Feedback storage: {self.feedback_dir}")

    def _get_current_file_path(self) -> Path:
        """Get the path for the current month's feedback file."""
        now = datetime.now()
        filename = f"feedback_{now.year}-{now.month:02d}.json"
        return self.feedback_dir / filename

    def _get_current_filename(self) -> str:
        """Get just the filename (for GitHub)."""
        now = datetime.now()
        return f"feedback_{now.year}-{now.month:02d}.json"

    def _load_feedback_file(self, filepath: Path) -> List[Dict]:
        """Load existing feedback from a file."""
        if not filepath.exists():
            return []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse feedback file: {filepath}")
            return []
        except Exception as e:
            logger.error(f"Error loading feedback file: {e}")
            return []
        
    def _save_feedback_file(self, filepath: Path, data: List[Dict]):
        """Save feedback data to a file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved feedback locally: {filepath}")
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            raise

    def _push_to_github(self, filename: str, content: str) -> bool:
        """
        Push feedback file to GitHub repository using GitHub API.

        Args:
            filename: Name of the file to create/update
            content: JSON content to push

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.github_enabled:
            logger.debug("GitHub sync disabled, skipping push")
            return False

        try:
            import requests

            # GitHub API endpoint
            url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/contents/{filename}"

            # Encode content to base64
            content_bytes = content.encode('utf-8')
            content_b64 = base64.b64encode(content_bytes).decode('utf-8')

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }

            # Check if file exists (to get SHA for update)
            response = requests.get(url, headers=headers, timeout=10)

            data = {
                "message": f"Update feedback: {filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "content": content_b64,
            }

            # If file exists, include SHA for update
            if response.status_code == 200:
                existing = response.json()
                data["sha"] = existing["sha"]
                logger.debug(f"Updating existing file on GitHub: {filename}")
            else:
                logger.debug(f"Creating new file on GitHub: {filename}")

            # Create or update file
            response = requests.put(url, headers=headers, json=data, timeout=15)

            if response.status_code in [200, 201]:
                logger.info(f"✓ Synced to GitHub: {self.github_owner}/{self.github_repo}/{filename}")
                return True
            else:
                logger.error(f"GitHub API error: {response.status_code} - {response.text[:200]}")
                return False

        except ImportError:
            logger.error("requests library not installed. Run: pip install requests")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error pushing to GitHub: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to push to GitHub: {e}")
            return False

    def log_feedback(self, feedback_data: Dict) -> bool:
        """
        Log a new feedback entry.
        Saves locally to AppData AND syncs to GitHub if configured.

        Args:
            feedback_data: Dictionary containing:
                - message_id: str
                - rating: str ('positive' or 'negative')
                - comment: str (optional)
                - user_question: str
                - response: str
                - timestamp: str (ISO format)

        Returns:
            bool: True if local save successful, False otherwise
        """
        try:
            # Validate required fields
            required_fields = ['message_id', 'rating', 'user_question', 'response', 'timestamp']
            for field in required_fields:
                if field not in feedback_data:
                    logger.error(f"Missing required field: {field}")
                    return False

            # Add metadata
            feedback_entry = {
                **feedback_data,
                'logged_at': datetime.now().isoformat(),
            }

            # Get current month's file
            filepath = self._get_current_file_path()
            filename = self._get_current_filename()

            # Load existing feedback
            all_feedback = self._load_feedback_file(filepath)

            # Append new feedback
            all_feedback.append(feedback_entry)

            # Save locally (primary storage)
            self._save_feedback_file(filepath, all_feedback)
            logger.info(f"✓ Feedback logged: {feedback_data.get('rating')} | {feedback_data.get('message_id')}")

            # Push to GitHub (best effort - don't fail if this fails)
            if self.github_enabled:
                content = json.dumps(all_feedback, indent=2, ensure_ascii=False)
                github_success = self._push_to_github(filename, content)

                if not github_success:
                    logger.warning("⚠ Failed to sync to GitHub, but saved locally")

            return True

        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")
            return False

    def get_feedback_stats(self) -> Dict:
        """
        Get statistics about feedback collected.

        Returns:
            Dict with stats: total, positive, negative, monthly breakdown
        """
        stats = {
            'total': 0,
            'positive': 0,
            'negative': 0,
            'monthly': {},
            'storage_location': str(self.feedback_dir)
        }

        try:
            # Iterate through all feedback files
            for filepath in sorted(self.feedback_dir.glob("feedback_*.json")):
                month_key = filepath.stem.replace('feedback_', '')
                feedback_list = self._load_feedback_file(filepath)

                month_stats = {
                    'total': len(feedback_list),
                    'positive': sum(1 for f in feedback_list if f.get('rating') == 'positive'),
                    'negative': sum(1 for f in feedback_list if f.get('rating') == 'negative'),
                }

                stats['total'] += month_stats['total']
                stats['positive'] += month_stats['positive']
                stats['negative'] += month_stats['negative']
                stats['monthly'][month_key] = month_stats

            return stats

        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return stats

    def get_recent_feedback(self, limit: int = 20) -> List[Dict]:
        """
        Get the most recent feedback entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of feedback entries, most recent first
        """
        all_feedback = []

        try:
            # Get all feedback files sorted by date (newest first)
            feedback_files = sorted(
                self.feedback_dir.glob("feedback_*.json"),
                reverse=True
            )

            for filepath in feedback_files:
                feedback_list = self._load_feedback_file(filepath)
                all_feedback.extend(feedback_list)

                # Stop if we have enough
                if len(all_feedback) >= limit:
                    break

            # Sort by timestamp (newest first) and limit
            all_feedback.sort(
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )

            return all_feedback[:limit]

        except Exception as e:
            logger.error(f"Error getting recent feedback: {e}")
            return []


# Global instance
_feedback_logger = None

def get_feedback_logger(feedback_dir: str = None) -> FeedbackLogger:
    """Get the global feedback logger instance."""
    global _feedback_logger
    if _feedback_logger is None:
        _feedback_logger = FeedbackLogger(feedback_dir)
    return _feedback_logger
