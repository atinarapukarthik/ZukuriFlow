"""
WhisperEngine - Advanced Faster-Whisper transcription with VAD and technical prompts
"""

from typing import Optional, List, Dict
import numpy as np
from faster_whisper import WhisperModel


class WhisperEngine:
    """
    Enhanced Whisper transcription engine with VAD support and technical vocabulary optimization.

    Attributes:
        model: Faster-Whisper model instance
        initial_prompt: Technical prompt to improve accuracy for specialized terms
    """

    # Technical vocabulary for improved recognition
    TECHNICAL_KEYWORDS = [
        "Python", "SQL", "RAG", "LangGraph", "SDE", "API",
        "REST", "GraphQL", "Docker", "Kubernetes", "AWS",
        "React", "Vue", "TypeScript", "JavaScript", "FastAPI",
        "PostgreSQL", "MongoDB", "Redis", "Nginx", "Git",
        "CI/CD", "DevOps", "LLM", "GPT", "Claude", "OpenAI"
    ]

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: Optional[str] = "en"
    ) -> None:
        """
        Initialize the WhisperEngine with specified configuration.

        Args:
            model_size: Model size ('tiny', 'base', 'small', 'medium', 'large')
            device: Compute device ('cpu' or 'cuda')
            compute_type: Quantization type ('int8', 'float16', 'float32')
            language: Target language code (e.g., 'en', 'es'). None for auto-detect.
        """
        print(
            f"🔧 Loading Faster-Whisper model: {model_size} on {device} ({compute_type})")

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )

        self.language = language

        # Construct technical initial prompt
        keywords_str = ", ".join(self.TECHNICAL_KEYWORDS)
        self.initial_prompt = (
            f"This is a technical recording containing specialized terminology. "
            f"Common terms include: {keywords_str}. "
            f"Transcribe accurately with proper capitalization and punctuation."
        )

        print("✅ WhisperEngine initialized successfully")

    def transcribe(
        self,
        audio_data: np.ndarray,
        use_vad: bool = True,
        beam_size: int = 5
    ) -> str:
        """
        Transcribe audio data with VAD filtering and technical prompt.

        Args:
            audio_data: Audio numpy array (float32, [-1, 1] range)
            use_vad: Enable Voice Activity Detection to filter silences
            beam_size: Beam search size for decoding

        Returns:
            Transcribed text with technical terms properly formatted
        """
        # Ensure audio is float32 and normalized
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Normalize if needed
        if np.abs(audio_data).max() > 1.0:
            audio_data = audio_data / np.abs(audio_data).max()

        # Transcribe with VAD and technical prompt
        segments, info = self.model.transcribe(
            audio_data,
            language=self.language,
            initial_prompt=self.initial_prompt,
            beam_size=beam_size,
            best_of=beam_size,
            temperature=0.0,
            vad_filter=use_vad,  # Enable VAD to filter silences
            vad_parameters=dict(
                threshold=0.5,
                min_speech_duration_ms=250,
                min_silence_duration_ms=500
            )
        )

        # Combine all segments
        transcription = " ".join([segment.text.strip()
                                 for segment in segments])

        detected_lang = info.language
        confidence = info.language_probability

        print(f"🎤 Detected: {detected_lang} ({confidence:.1%} confidence)")

        return transcription.strip()

    def transcribe_with_timestamps(
        self,
        audio_data: np.ndarray,
        use_vad: bool = True
    ) -> List[Dict[str, any]]:
        """
        Transcribe with word-level timestamps.

        Args:
            audio_data: Audio numpy array
            use_vad: Enable VAD filtering

        Returns:
            List of segments with start, end times and text
        """
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        if np.abs(audio_data).max() > 1.0:
            audio_data = audio_data / np.abs(audio_data).max()

        segments, _ = self.model.transcribe(
            audio_data,
            language=self.language,
            word_timestamps=True,
            vad_filter=use_vad
        )

        result = []
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

        return result
