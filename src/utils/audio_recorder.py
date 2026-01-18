"""
AudioRecorder - High-quality audio recording using sounddevice and wavio
"""

from typing import Optional
import numpy as np
import sounddevice as sd
import wavio


class AudioRecorder:
    """
    Professional audio recorder using sounddevice for capture and wavio for export.

    Attributes:
        sample_rate: Recording sample rate in Hz
        channels: Number of audio channels (1 for mono)
        dtype: NumPy data type for audio samples
    """

    def __init__(
        self, sample_rate: int = 16000, channels: int = 1, dtype: str = "float32"
    ) -> None:
        """
        Initialize the AudioRecorder.

        Args:
            sample_rate: Sample rate in Hz (16000 is optimal for Whisper)
            channels: Number of audio channels (1=mono, 2=stereo)
            dtype: Data type for audio recording ('float32' recommended)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype

        print(f"🎙️ AudioRecorder initialized: {sample_rate}Hz, {channels}ch, {dtype}")

    def record(self, duration: Optional[float] = None) -> np.ndarray:
        """
        Record audio for a specified duration.

        Args:
            duration: Recording duration in seconds. If None, records until stopped.

        Returns:
            NumPy array of audio samples (float32, normalized to [-1, 1])
        """
        if duration:
            print(f"🔴 Recording for {duration}s...")
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
            )
            sd.wait()  # Wait until recording is finished
            print("✅ Recording complete")
            return audio_data.flatten()
        else:
            # For manual control, use record_streaming instead
            raise NotImplementedError("Use record_streaming for manual control")

    def record_streaming(self) -> "StreamingRecorder":
        """
        Create a streaming recorder for manual start/stop control.

        Returns:
            StreamingRecorder instance
        """
        return StreamingRecorder(
            sample_rate=self.sample_rate, channels=self.channels, dtype=self.dtype
        )

    def save_wav(self, audio_data: np.ndarray, filename: str) -> None:
        """
        Save audio data to a WAV file.

        Args:
            audio_data: Audio numpy array
            filename: Output file path
        """
        # Ensure audio is in correct format
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Reshape for wavio if needed
        if audio_data.ndim == 1:
            audio_data = audio_data.reshape(-1, 1)

        # Convert float32 [-1, 1] to int16 for WAV
        audio_int16 = np.int16(audio_data * 32767)

        wavio.write(filename, audio_int16, self.sample_rate, sampwidth=2)
        print(f"💾 Saved audio to: {filename}")


class StreamingRecorder:
    """
    Streaming audio recorder with manual start/stop control.
    """

    def __init__(
        self, sample_rate: int = 16000, channels: int = 1, dtype: str = "float32"
    ) -> None:
        """
        Initialize streaming recorder.

        Args:
            sample_rate: Sample rate in Hz
            channels: Number of channels
            dtype: Audio data type
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.audio_frames = []
        self.stream = None
        self.is_recording = False

    def start(self) -> None:
        """Start recording audio stream."""
        if self.is_recording:
            return

        self.audio_frames = []
        self.is_recording = True

        def callback(indata, frames, time, status):
            if status:
                print(f"⚠️ Audio status: {status}")
            if self.is_recording:
                self.audio_frames.append(indata.copy())

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            callback=callback,
        )
        self.stream.start()
        print("🔴 Recording started...")

    def stop(self) -> np.ndarray:
        """
        Stop recording and return audio data.

        Returns:
            Recorded audio as NumPy array
        """
        if not self.is_recording:
            return np.array([], dtype=np.float32)

        self.is_recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        print("⏹️ Recording stopped")

        if not self.audio_frames:
            return np.array([], dtype=np.float32)

        # Concatenate all frames
        audio_data = np.concatenate(self.audio_frames, axis=0)

        # Flatten if needed
        if audio_data.ndim > 1:
            audio_data = audio_data.flatten()

        return audio_data

    def is_active(self) -> bool:
        """Check if recording is active."""
        return self.is_recording
