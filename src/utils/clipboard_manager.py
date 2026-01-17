"""
ClipboardManager - Persistence and system-wide paste automation
"""

from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json
import pyperclip
import pyautogui


class ClipboardManager:
    """
    Manages text persistence to history.json and automated clipboard paste operations.

    Attributes:
        history_file: Path to the history.json file
        history: In-memory list of history entries
    """

    def __init__(self, output_dir: str = "output") -> None:
        """
        Initialize ClipboardManager with output directory.

        Args:
            output_dir: Directory path for storing history.json
        """
        self.output_path = Path(output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.history_file = self.output_path / "history.json"
        self.history: List[Dict] = []

        self._load_history()

        print(f"📋 ClipboardManager initialized: {self.history_file}")

    def _load_history(self) -> None:
        """Load existing history from history.json."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                print(f"📂 Loaded {len(self.history)} history entries")
            except json.JSONDecodeError:
                print("⚠️ Could not parse history.json, starting fresh")
                self.history = []
        else:
            print("📝 Creating new history file")
            self.history = []
            self._save_history()

    def _save_history(self) -> None:
        """Save history to history.json."""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def save_entry(
        self,
        transcription: str,
        refined_text: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Save a new entry to history before pasting.

        Args:
            transcription: Raw transcription from Whisper
            refined_text: Refined text after processing
            metadata: Optional additional metadata (e.g., language, confidence)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "transcription": transcription,
            "refined": refined_text,
            "metadata": metadata or {}
        }

        self.history.append(entry)
        self._save_history()

        print(f"💾 Saved to history (total: {len(self.history)} entries)")

    def copy_to_clipboard(self, text: str) -> None:
        """
        Copy text to system clipboard.

        Args:
            text: Text to copy
        """
        pyperclip.copy(text)
        print(f"📋 Copied to clipboard: {text[:50]}...")

    def paste_to_active_window(self, delay: float = 0.1) -> None:
        """
        Simulate Ctrl+V (or Cmd+V on Mac) to paste from clipboard.

        Args:
            delay: Delay in seconds before pasting
        """
        import platform

        # Small delay to ensure clipboard is ready
        pyautogui.sleep(delay)

        # Detect OS and use appropriate paste shortcut
        if platform.system() == "Darwin":  # macOS
            pyautogui.hotkey('command', 'v')
            print("⌘+V Pasted to active window (macOS)")
        else:  # Windows/Linux
            pyautogui.hotkey('ctrl', 'v')
            print("🔽 Ctrl+V Pasted to active window")

    def copy_and_paste(
        self,
        transcription: str,
        refined_text: str,
        auto_paste: bool = True,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Complete workflow: save to history, copy to clipboard, and optionally paste.

        Args:
            transcription: Raw transcription
            refined_text: Refined text to paste
            auto_paste: Whether to automatically trigger paste
            metadata: Optional metadata
        """
        # Step 1: Save to history
        self.save_entry(transcription, refined_text, metadata)

        # Step 2: Copy to clipboard
        self.copy_to_clipboard(refined_text)

        # Step 3: Auto-paste if enabled
        if auto_paste:
            self.paste_to_active_window()

    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve history entries.

        Args:
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of history entries
        """
        if limit:
            return self.history[-limit:]
        return self.history

    def clear_history(self) -> None:
        """Clear all history entries."""
        self.history = []
        self._save_history()
        print("🗑️ History cleared")

    def export_history_to_text(self, output_file: str) -> None:
        """
        Export history to a plain text file.

        Args:
            output_file: Path to output text file
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, entry in enumerate(self.history, 1):
                f.write(f"Entry #{i}\n")
                f.write(f"Timestamp: {entry['timestamp']}\n")
                f.write(f"Transcription: {entry['transcription']}\n")
                f.write(f"Refined: {entry['refined']}\n")
                f.write("-" * 80 + "\n\n")

        print(f"📄 Exported history to: {output_file}")
