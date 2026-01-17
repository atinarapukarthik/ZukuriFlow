"""
HistoryManager - Dictation Memory Management Utility
Handles persistent storage of transcription history to JSON.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default history file path
DEFAULT_HISTORY_PATH = Path("output/history.json")


def log_to_history(
    refined_text: str,
    history_path: Optional[Path] = None
) -> bool:
    """
    Append a transcription entry to the history JSON file.

    Creates the output directory and history.json file if they don't exist.
    Each entry contains a timestamp and the refined content.

    Args:
        refined_text: The refined transcription text to log
        history_path: Custom path to history.json (optional)

    Returns:
        bool: True if logging succeeded, False otherwise

    Example:
        >>> log_to_history("This is a test transcription about Python and RAG.")
        True

    Output format in history.json:
        [
            {
                "timestamp": "2026-01-17T10:30:45.123456",
                "content": "This is a test transcription about Python and RAG."
            }
        ]
    """
    if not refined_text or not refined_text.strip():
        logger.warning("Empty text received, skipping history log")
        return False

    # Use default path if not specified
    file_path = history_path or DEFAULT_HISTORY_PATH

    try:
        # Ensure output directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history or create new list
        history: List[Dict[str, str]] = []
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        history = json.loads(content)
                        if not isinstance(history, list):
                            logger.warning(
                                "History file corrupted, starting fresh")
                            history = []
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Could not parse history.json: {e}. Starting fresh.")
                history = []

        # Create new entry with timestamp
        entry: Dict[str, str] = {
            "timestamp": datetime.now().isoformat(),
            "content": refined_text.strip()
        }

        # Append to history
        history.append(entry)

        # Save updated history
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Logged to history: '{refined_text[:50]}...' (total: {len(history)} entries)")
        return True

    except Exception as e:
        logger.error(f"Failed to log to history: {str(e)}")
        return False


def get_history(
    history_path: Optional[Path] = None,
    limit: Optional[int] = None
) -> List[Dict[str, str]]:
    """
    Retrieve transcription history from JSON file.

    Args:
        history_path: Custom path to history.json (optional)
        limit: Maximum number of entries to return (most recent first)

    Returns:
        List of history entries with timestamp and content
    """
    file_path = history_path or DEFAULT_HISTORY_PATH

    if not file_path.exists():
        logger.info("No history file found")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            history = json.load(f)

        if not isinstance(history, list):
            logger.warning("Invalid history format")
            return []

        # Return limited entries if specified (most recent)
        if limit:
            return history[-limit:]

        return history

    except Exception as e:
        logger.error(f"Failed to read history: {str(e)}")
        return []


def clear_history(history_path: Optional[Path] = None) -> bool:
    """
    Clear all history entries.

    Args:
        history_path: Custom path to history.json (optional)

    Returns:
        bool: True if cleared successfully
    """
    file_path = history_path or DEFAULT_HISTORY_PATH

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f)

        logger.info("History cleared successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to clear history: {str(e)}")
        return False


def get_history_stats(history_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get statistics about the history file.

    Args:
        history_path: Custom path to history.json (optional)

    Returns:
        Dict with entry count, file size, and date range
    """
    file_path = history_path or DEFAULT_HISTORY_PATH

    history = get_history(history_path)

    stats: Dict[str, Any] = {
        "total_entries": len(history),
        "file_exists": file_path.exists(),
        "file_path": str(file_path)
    }

    if history:
        stats["first_entry"] = history[0].get("timestamp")
        stats["last_entry"] = history[-1].get("timestamp")
        stats["total_characters"] = sum(
            len(h.get("content", "")) for h in history)

    if file_path.exists():
        stats["file_size_kb"] = round(file_path.stat().st_size / 1024, 2)

    logger.info(f"History stats: {stats['total_entries']} entries")
    return stats


class HistoryManager:
    """
    Class-based wrapper for history management functions.
    Provides instance-based access with custom configuration.
    """

    def __init__(self, history_path: Optional[str] = None) -> None:
        """
        Initialize HistoryManager with optional custom path.

        Args:
            history_path: Custom path to history.json
        """
        self.history_path = Path(
            history_path) if history_path else DEFAULT_HISTORY_PATH
        logger.info(f"HistoryManager initialized: {self.history_path}")

    def log(self, refined_text: str) -> bool:
        """Log refined text to history."""
        return log_to_history(refined_text, self.history_path)

    def get_all(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get all history entries."""
        return get_history(self.history_path, limit)

    def clear(self) -> bool:
        """Clear all history."""
        return clear_history(self.history_path)

    def stats(self) -> Dict[str, Any]:
        """Get history statistics."""
        return get_history_stats(self.history_path)
