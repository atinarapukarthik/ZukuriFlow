# ZukuriFlow Elite - Technical Documentation

## Architecture Overview

ZukuriFlow Elite is a modular, local-first AI dictation application built with clean architecture principles.

### Core Components

#### 1. WhisperEngine (`src/utils/whisper_engine.py`)
**Purpose**: AI transcription with technical vocabulary optimization

**Features**:
- Uses `faster-whisper` library with `base` model
- `int8` quantization for CPU efficiency
- Built-in VAD (Voice Activity Detection) in transcription
- Technical initial prompt with 100+ keywords (Python, SQL, RAG, LangGraph, etc.)
- Optional word-level timestamps

**Key Methods**:
```python
transcribe(audio_data, use_vad=True, beam_size=5) -> str
transcribe_with_timestamps(audio_data, use_vad=True) -> List[Dict]
```

#### 2. AudioRecorder (`src/utils/audio_recorder.py`)
**Purpose**: High-quality audio capture

**Features**:
- Uses `sounddevice` for recording, `wavio` for export
- 16000Hz sample rate (optimal for Whisper)
- Streaming recorder with manual start/stop
- Float32 normalized output [-1, 1]

**Key Classes**:
- `AudioRecorder`: Main recorder interface
- `StreamingRecorder`: Manual control recording

#### 3. TextRefiner (`src/utils/text_refiner.py`)
**Purpose**: Wispr-style text post-processing

**Features**:
- Auto-capitalization (first letter + after sentences)
- Smart punctuation (adds period if missing)
- 100+ technical jargon mappings (e.g., "rag" → "RAG", "python" → "Python")
- Contraction fixes ("dont" → "don't")
- Spacing normalization

**Jargon Categories**:
- Programming Languages (Python, JavaScript, TypeScript, etc.)
- AI/ML Terms (RAG, LLM, GPT, LangChain, LangGraph, etc.)
- Databases (SQL, PostgreSQL, MongoDB, Redis, etc.)
- DevOps/Cloud (Docker, Kubernetes, AWS, CI/CD, etc.)
- Web/APIs (REST, GraphQL, JSON, WebSocket, etc.)

#### 4. ClipboardManager (`src/utils/clipboard_manager.py`)
**Purpose**: Persistence and automated pasting

**Features**:
- Saves to `output/history.json` with timestamps
- Uses `pyperclip` for clipboard operations
- Uses `pyautogui` for system-wide paste (Ctrl+V or Cmd+V)
- Automatic history export to text

**Key Methods**:
```python
copy_and_paste(transcription, refined_text, auto_paste=True)
save_entry(transcription, refined_text, metadata)
get_history(limit) -> List[Dict]
```

#### 5. FloatingButton GUI (`src/zukuriflow_elite.py`)
**Purpose**: Elegant PyQt6 interface

**Features**:
- Frameless, transparent, always-on-top
- Draggable anywhere on screen
- Three visual states:
  - **Beige/Cream** (RGB: 245, 235, 220): Idle
  - **Pulsing Red** (RGB: 220, 50, 50): Recording
  - **Glowing Gold** (RGB: 255, 215, 0): Processing
- Non-blocking: AI processing in `QThread`
- Smooth animations (20 FPS)

### Workflow

1. **Click Button** → Enter Recording State (Pulsing Red)
2. **User Speaks** → StreamingRecorder captures audio
3. **Click Again** → Stop Recording → Enter Processing State (Glowing Gold)
4. **Background Thread**:
   - WhisperEngine transcribes (with VAD)
   - TextRefiner enhances text
5. **ClipboardManager**:
   - Saves to history.json
   - Copies to clipboard
   - Auto-pastes to active window (Ctrl+V)
6. **Return to Idle** (Beige)

### Type Safety

All modules use comprehensive type hints:
```python
from typing import Optional, List, Dict
import numpy as np

def transcribe(audio_data: np.ndarray, use_vad: bool = True) -> str:
    ...
```

### Thread Safety

- GUI runs on main thread
- AI processing (Whisper + Refiner) runs on `TranscriptionWorker` QThread
- Signals/slots for thread-safe communication

### Configuration

**Model Settings** (in `zukuriflow_elite.py`):
```python
WhisperEngine(
    model_size="base",      # tiny, base, small, medium, large
    device="cpu",           # cpu or cuda
    compute_type="int8",    # int8 (CPU), float16 (GPU)
    language="en"           # en, es, fr, etc.
)
```

**Audio Settings**:
```python
AudioRecorder(
    sample_rate=16000,      # 16kHz optimal for Whisper
    channels=1,             # Mono
    dtype="float32"         # Normalized float
)
```

### Error Handling

- Empty audio detection
- Transcription error signals
- Graceful fallback to idle state
- User-friendly console logging with emojis

### Performance Optimization

1. **int8 Quantization**: 4x faster inference on CPU
2. **VAD Integration**: Filters silence during transcription
3. **QThread Processing**: Prevents UI freezing
4. **Streaming Recording**: Low memory footprint

### Extensibility

**Add Custom Jargon**:
```python
refiner.add_custom_jargon("zukuri", "Zukuri")
```

**Custom Metadata**:
```python
clipboard_manager.save_entry(
    transcription,
    refined,
    metadata={"language": "en", "confidence": 0.95}
)
```

## File Structure

```
ZukuriFlow/
├── .gitignore                      # Ignores output/, __pycache__
├── requirements.txt                # All dependencies
├── README.md                       # User documentation
├── DOCUMENTATION.md                # This file
├── setup.bat / setup.sh            # Installation scripts
├── run.bat / run.sh                # Quick launch scripts
├── src/
│   ├── zukuriflow_elite.py         # Main app (PyQt6 GUI)
│   └── utils/
│       ├── __init__.py             # Package exports
│       ├── whisper_engine.py       # AI transcription
│       ├── audio_recorder.py       # Audio capture
│       ├── text_refiner.py         # Post-processing
│       └── clipboard_manager.py    # Persistence + paste
└── output/                         # Git-ignored
    └── history.json                # Transcription history
```

## Dependencies

- **AI**: `faster-whisper`, `torch`
- **Audio**: `sounddevice`, `wavio`, `numpy`
- **GUI**: `PyQt6`
- **Automation**: `pyperclip`, `pyautogui`

## System Requirements

- **Python**: 3.8+
- **OS**: Windows, macOS, Linux
- **RAM**: 4GB+ recommended
- **Microphone**: Any system microphone

## Future Enhancements

- [ ] GPU acceleration (CUDA support)
- [ ] Multiple language support with auto-detection
- [ ] Custom keyboard shortcuts
- [ ] Tray icon integration
- [ ] Real-time streaming transcription
- [ ] Cloud sync option
- [ ] Custom model selection in UI
