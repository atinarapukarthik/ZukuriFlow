"""
Recorder - Audio Recording Utility using sounddevice and wavio
Handles microphone input and WAV file storage for ZukuriFlow Elite.
"""

import logging
import threading
from typing import Optional, List, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    import sounddevice as sd

import numpy as np
import wavio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Recorder:
    """
    Audio recorder using sounddevice for microphone capture.

    Features:
    - 16000Hz sample rate (optimal for Whisper)
    - Mono channel recording
    - Thread-safe start/stop operations
    - WAV file output using wavio
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        """
        Initialize the Recorder with audio settings.

        Args:
            sample_rate: Audio sample rate in Hz (16000 optimal for Whisper)
            channels: Number of audio channels (1 for mono)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = np.float32

        # Recording state
        self._frames: List[np.ndarray] = []
        self._stream: Optional["sd.InputStream"] = None
        self._is_recording: bool = False
        self._lock = threading.Lock()

        # Verify microphone is available
        self._check_microphone()

        logger.info(f"Recorder initialized: {sample_rate}Hz, {channels} channel(s)")

    def _check_microphone(self) -> None:
        """
        Verify that a microphone is available.

        Raises:
            RuntimeError: If no microphone is detected
        """
        import sounddevice as sd

        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d["max_input_channels"] > 0]

            if not input_devices:
                raise RuntimeError(
                    "No microphone detected. Please connect a microphone."
                )

            default_input = sd.query_devices(kind="input")
            logger.info(f"Using microphone: {default_input['name']}")

        except Exception as e:
            logger.error(f"Microphone check failed: {e}")
            raise RuntimeError(f"Microphone initialization failed: {e}")

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info, status
    ) -> None:
        """
        Callback function for audio stream - collects frames into list.

        Args:
            indata: Input audio data
            frames: Number of frames
            time_info: Stream timing information
            status: Stream status
        """
        if status:
            logger.warning(f"Audio stream status: {status}")

        if self._is_recording:
            self._frames.append(indata.copy())

    def start_recording(self) -> None:
        """
        Start recording audio from the microphone.

        Collects audio frames into an internal list for later processing.

        Raises:
            RuntimeError: If recording is already in progress or microphone fails
        """
        with self._lock:
            if self._is_recording:
                logger.warning("Recording already in progress")
                return

            try:
                # Clear previous frames
                self._frames = []
                self._is_recording = True

                import sounddevice as sd

                # Create and start input stream
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.dtype,
                    callback=self._audio_callback,
                )
                self._stream.start()

                logger.info("🔴 Recording started...")

            except Exception as e:
                self._is_recording = False
                logger.error(f"Failed to start recording: {e}")
                raise RuntimeError(f"Could not start recording: {e}")

    def stop_recording(self, output_filename: str) -> str:
        """
        Stop recording and save audio to a WAV file.

        Args:
            output_filename: Path for the output WAV file

        Returns:
            str: Path to the saved WAV file

        Raises:
            RuntimeError: If no recording is in progress or save fails
        """
        with self._lock:
            if not self._is_recording:
                logger.warning("No recording in progress")
                raise RuntimeError("No recording in progress to stop")

            try:
                # Stop the stream
                self._is_recording = False

                if self._stream:
                    self._stream.stop()
                    self._stream.close()
                    self._stream = None

                logger.info("⏹️ Recording stopped")

                # Check if we have audio data
                if not self._frames:
                    raise RuntimeError("No audio data recorded")

                # Concatenate all frames
                audio_data = np.concatenate(self._frames, axis=0)

                # Ensure output path exists
                output_path = Path(output_filename)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Convert float32 [-1, 1] to int16 for WAV file
                audio_int16 = np.int16(audio_data * 32767)

                # Reshape for mono output
                if audio_int16.ndim == 1:
                    audio_int16 = audio_int16.reshape(-1, 1)

                # Save using wavio (mono .wav file)
                wavio.write(
                    str(output_path),
                    audio_int16,
                    self.sample_rate,
                    sampwidth=2,  # 16-bit audio
                )

                duration = len(audio_data) / self.sample_rate
                logger.info(f"💾 Saved {duration:.1f}s audio to: {output_path}")

                # Clear frames
                self._frames = []

                return str(output_path)

            except Exception as e:
                self._frames = []
                logger.error(f"Failed to save recording: {e}")
                raise RuntimeError(f"Could not save recording: {e}")

    def is_recording(self) -> bool:
        """Check if recording is currently active."""
        return self._is_recording

    def get_recording_duration(self) -> float:
        """
        Get the current recording duration in seconds.

        Returns:
            float: Duration in seconds
        """
        if not self._frames:
            return 0.0

        total_frames = sum(len(f) for f in self._frames)
        return total_frames / self.sample_rate

    def __del__(self) -> None:
        """Cleanup resources on deletion."""
        if hasattr(self, "_stream") and self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass


# Legacy alias for backward compatibility
AudioHandler = Recorder
