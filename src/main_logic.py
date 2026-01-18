"""
ZukuriFlowController - High-Level Integration for ZukuriFlow Elite
Orchestrates the complete voice-to-text-to-paste workflow.
"""

import logging
import threading
import tempfile
import os
from pathlib import Path
from typing import Optional, Callable

import pyperclip
import pyautogui

from utils.audio_handler import Recorder
from utils.ai_engine import WhisperEngine
from utils.refiner import TextRefiner
from utils.history_manager import log_to_history

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZukuriFlowController:
    """
    Main controller that orchestrates the ZukuriFlow Elite workflow.

    Workflow:
    1. Record audio from microphone
    2. Transcribe audio using WhisperEngine
    3. Refine text using TextRefiner
    4. Log to history
    5. Copy to clipboard and paste to active window
    6. Clean up temporary files

    All heavy processing runs on background threads to prevent UI blocking.
    """

    def __init__(
        self,
        on_status_change: Optional[Callable[[str], None]] = None,
        on_result: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Initialize ZukuriFlowController with all required components.

        Args:
            on_status_change: Callback for status updates (e.g., "Recording...", "Processing...")
            on_result: Callback when transcription is complete (receives refined text)
            on_error: Callback for error notifications
        """
        logger.info("Initializing ZukuriFlowController...")

        # Callbacks for UI updates
        self._on_status_change = on_status_change
        self._on_result = on_result
        self._on_error = on_error

        # Initialize components
        try:
            self._recorder = Recorder(sample_rate=16000, channels=1)
            self._whisper = WhisperEngine(
                model_size="base", device="cpu", compute_type="int8"
            )
            self._refiner = TextRefiner()

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise RuntimeError(f"ZukuriFlow initialization failed: {e}")

        # State
        self._is_processing = False
        self._processing_thread: Optional[threading.Thread] = None
        self._temp_file: Optional[str] = None

        logger.info("✅ ZukuriFlowController ready")

    def _notify_status(self, status: str) -> None:
        """Send status update to callback if available."""
        logger.info(f"Status: {status}")
        if self._on_status_change:
            self._on_status_change(status)

    def _notify_result(self, text: str) -> None:
        """Send result to callback if available."""
        if self._on_result:
            self._on_result(text)

    def _notify_error(self, error: str) -> None:
        """Send error to callback if available."""
        logger.error(f"Error: {error}")
        if self._on_error:
            self._on_error(error)

    def start_recording(self) -> bool:
        """
        Start recording audio from the microphone.

        Returns:
            bool: True if recording started successfully
        """
        if self._is_processing:
            logger.warning("Cannot start recording while processing")
            return False

        if self._recorder.is_recording():
            logger.warning("Recording already in progress")
            return False

        try:
            self._recorder.start_recording()
            self._notify_status("🔴 Recording...")
            return True

        except Exception as e:
            self._notify_error(f"Failed to start recording: {e}")
            return False

    def stop_recording_and_process(self) -> None:
        """
        Stop recording and start the processing workflow in a background thread.

        The process_voice method runs on a separate thread to prevent UI blocking.
        """
        if not self._recorder.is_recording():
            logger.warning("No recording to stop")
            return

        if self._is_processing:
            logger.warning("Already processing")
            return

        # Start processing in background thread
        self._processing_thread = threading.Thread(
            target=self._process_voice_workflow, daemon=True
        )
        self._processing_thread.start()

    def _process_voice_workflow(self) -> None:
        """
        Internal method that runs the complete voice processing workflow.

        Runs on a background thread to prevent UI blocking.
        """
        self._is_processing = True
        temp_file = None

        try:
            # Step 1: Stop recording and save to temp file
            self._notify_status("⏹️ Saving audio...")

            # Create temp file path
            temp_dir = Path(tempfile.gettempdir()) / "zukuriflow"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = str(temp_dir / "recording.wav")

            # Stop recording and save
            saved_path = self._recorder.stop_recording(temp_file)
            self._temp_file = saved_path

            # Step 2: Transcribe audio
            self._notify_status("🧠 Transcribing...")
            raw_text = self._whisper.transcribe_audio(saved_path)

            if not raw_text.strip():
                self._notify_error("No speech detected in recording")
                return

            logger.info(f"Raw transcription: {raw_text}")

            # Step 3: Refine text
            self._notify_status("✨ Refining text...")
            refined_text = self._refiner.refine(raw_text)

            logger.info(f"Refined text: {refined_text}")

            # Step 4: Log to history
            self._notify_status("💾 Saving to history...")
            log_to_history(refined_text)

            # Step 5: Copy to clipboard and paste
            self._notify_status("📋 Pasting...")
            self._copy_and_paste(refined_text)

            # Step 6: Notify success
            self._notify_status("✅ Done!")
            self._notify_result(refined_text)

        except FileNotFoundError as e:
            self._notify_error(f"Audio file error: {e}")

        except RuntimeError as e:
            self._notify_error(f"Processing error: {e}")

        except Exception as e:
            self._notify_error(f"Unexpected error: {e}")

        finally:
            # Cleanup: Delete temporary WAV file
            self._cleanup_temp_file(temp_file)
            self._is_processing = False

    def process_voice(self, audio_file: str) -> Optional[str]:
        """
        Process an existing audio file through the complete workflow.

        This is a synchronous method for processing pre-recorded audio.

        Args:
            audio_file: Path to the audio file

        Returns:
            str: Refined text, or None if processing failed
        """
        try:
            # Step 1: Transcribe audio using WhisperEngine
            logger.info(f"Transcribing: {audio_file}")
            raw_text = self._whisper.transcribe_audio(audio_file)

            if not raw_text.strip():
                logger.warning("No speech detected")
                return None

            # Step 2: Refine text using TextRefiner
            logger.info("Refining text...")
            refined_text = self._refiner.refine(raw_text)

            # Step 3: Log to history
            logger.info("Logging to history...")
            log_to_history(refined_text)

            # Step 4: Copy to clipboard and paste
            logger.info("Copying and pasting...")
            self._copy_and_paste(refined_text)

            # Step 5: Delete temporary file
            self._cleanup_temp_file(audio_file)

            return refined_text

        except Exception as e:
            logger.error(f"process_voice failed: {e}")
            return None

    def _copy_and_paste(self, text: str) -> None:
        """
        Copy text to clipboard and paste to active window.

        Uses pyperclip for clipboard and pyautogui for paste shortcut.

        Args:
            text: Text to copy and paste
        """
        try:
            # Copy to clipboard
            pyperclip.copy(text)
            logger.info(f"Copied to clipboard: {text[:50]}...")

            # Small delay to ensure clipboard is ready
            pyautogui.sleep(0.1)

            # Paste using Ctrl+V (Windows/Linux) or Cmd+V (macOS)
            import platform

            if platform.system() == "Darwin":
                pyautogui.hotkey("command", "v")
                logger.info("Pasted using Cmd+V (macOS)")
            else:
                pyautogui.hotkey("ctrl", "v")
                logger.info("Pasted using Ctrl+V")

        except Exception as e:
            logger.error(f"Copy/paste failed: {e}")
            raise RuntimeError(f"Failed to paste text: {e}")

    def _cleanup_temp_file(self, file_path: Optional[str]) -> None:
        """
        Delete temporary WAV file to keep system clean.

        Args:
            file_path: Path to the temporary file
        """
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"🗑️ Deleted temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not delete temp file: {e}")

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recorder.is_recording()

    def is_processing(self) -> bool:
        """Check if currently processing audio."""
        return self._is_processing

    def cancel_processing(self) -> None:
        """Attempt to cancel ongoing processing."""
        if self._is_processing:
            logger.info("Cancellation requested (will complete current step)")
            # Note: Thread cannot be forcefully stopped, but we can set a flag
            self._is_processing = False


# Convenience function for simple usage
def quick_process(audio_file: str) -> Optional[str]:
    """
    Quick one-shot processing of an audio file.

    Args:
        audio_file: Path to the audio file

    Returns:
        str: Refined text, or None if failed
    """
    controller = ZukuriFlowController()
    return controller.process_voice(audio_file)
