"""
WhisperEngine - High-Performance Transcription with Faster-Whisper
Optimized for technical vocabulary with initial prompt and VAD filtering.
"""

import logging
from typing import List, Dict, Any
from pathlib import Path

from faster_whisper import WhisperModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperEngine:
    """
    High-performance speech-to-text engine using Faster-Whisper.

    Features:
    - Base model with int8 quantization for CPU efficiency
    - Initial prompt with technical keywords for improved accuracy
    - VAD (Voice Activity Detection) for automatic silence removal
    """

    # CRITICAL: Technical keywords for initial prompt - fixes "wrong word" detection
    TECHNICAL_KEYWORDS: str = (
        "ZukuriFlow, SDE, Python, LangGraph, Next.js, SQL, RAG, Internshala"
    )

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ) -> None:
        """
        Initialize WhisperEngine with optimized settings.

        Args:
            model_size: Model size - 'base' recommended for balance
            device: Compute device - 'cpu' or 'cuda'
            compute_type: Quantization type - 'int8' for maximum CPU efficiency
        """
        logger.info(
            f"Initializing WhisperEngine: model={model_size}, device={device}, compute={compute_type}")

        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

        # Initialize the Whisper model with specified settings
        self.model: WhisperModel = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )

        # CRITICAL: Initial prompt with technical keywords to fix "wrong word" detection
        self.initial_prompt: str = (
            f"Technical transcription containing: {self.TECHNICAL_KEYWORDS}. "
            "Transcribe accurately with proper capitalization and punctuation."
        )

        logger.info("WhisperEngine initialized successfully")

    def transcribe_audio(self, file_path: str) -> str:
        """
        Transcribe audio file to text with VAD and technical keyword optimization.

        CRITICAL: Uses initial_prompt parameter containing keywords:
        "ZukuriFlow, SDE, Python, LangGraph, Next.js, SQL, RAG, Internshala"
        to fix "wrong word" detection.

        Enables vad_filter=True to automatically remove silences.

        Args:
            file_path: Path to the audio file (WAV, MP3, etc.)

        Returns:
            str: Transcribed text

        Raises:
            FileNotFoundError: If the audio file doesn't exist
            Exception: If transcription fails
        """
        # Validate file exists
        audio_path = Path(file_path)
        if not audio_path.exists():
            logger.error(f"Audio file not found: {file_path}")
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        logger.info(f"Transcribing audio: {file_path}")

        try:
            # Use this specific parameter to fix wrong word detection
            segments, info = self.model.transcribe(
                str(audio_path),
                # Context-aware words
                initial_prompt="ZukuriFlow, SDE, Python, LangGraph, Next.js, SQL, RAG, Internshala",
                vad_filter=True,  # Auto-detect and remove silence
                beam_size=5  # Balanced speed and accuracy
            )

            # Combine all segments into final text
            transcription = " ".join([segment.text.strip()
                                     for segment in segments])

            logger.info(
                f"Detected language: {info.language} (confidence: {info.language_probability:.1%})")
            logger.info(
                f"Transcription complete: {len(transcription)} characters")

            return transcription.strip()

        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

    def transcribe_with_timestamps(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe audio with word-level timestamps.

        Args:
            file_path: Path to the audio file

        Returns:
            List of segments with start, end times and text
        """
        audio_path = Path(file_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        logger.info(f"Transcribing with timestamps: {file_path}")

        segments, info = self.model.transcribe(
            str(audio_path),
            language="en",
            initial_prompt=self.initial_prompt,
            vad_filter=True,
            word_timestamps=True
        )

        result: List[Dict[str, Any]] = []
        for segment in segments:
            result.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "words": [
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability
                    }
                    for word in (segment.words or [])
                ]
            })

        logger.info(f"Extracted {len(result)} segments with timestamps")
        return result

    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the current model configuration.

        Returns:
            Dict with model configuration details
        """
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "initial_prompt": self.initial_prompt
        }
