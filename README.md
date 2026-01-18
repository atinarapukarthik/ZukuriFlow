# ZukuriFlow Elite

A powerful local-first AI dictation tool with an elegant floating button interface. Built for developers and technical professionals who need accurate, context-aware voice-to-text transcription.

## Features

- **🎤 Smart Recording**: Voice Activity Detection (VAD) automatically filters silence
- **🧠 AI Transcription**: Powered by Faster-Whisper with technical vocabulary optimization
- **✨ Wispr-Style Refinement**: Auto-capitalization, punctuation, and technical jargon mapping
- **🎨 Floating Button GUI**: Frameless, draggable interface with visual state feedback
  - **Beige/Cream**: Idle state
  - **Pulsing Red**: Recording
  - **Glowing Gold**: Processing
- **📋 Auto-Paste**: Automatically pastes refined text to your active window
- **💾 Persistent History**: All transcriptions saved to `output/history.json`
- **⚡ Non-Blocking UI**: Heavy AI processing runs in background threads

## Project Structure

```
ZukuriFlow/
├── .gitignore
├── requirements.txt
├── README.md
├── src/
│   ├── zukuriflow_elite.py         # Main application with PyQt6 GUI
│   └── utils/
│       ├── __init__.py
│       ├── audio_recorder.py       # sounddevice + wavio recording
│       ├── whisper_engine.py       # Faster-Whisper with VAD & technical prompts
│       ├── text_refiner.py         # Wispr-style refinement + jargon mapping
│       └── clipboard_manager.py    # Persistence + pyperclip + pyautogui paste
└── output/                         # Created locally (not in git)
    └── history.json
```

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd ZukuriFlow
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage
ZukuriFlow Elite:
```bash
python src/zukuriflow_elite.py
```

## How to Use

1. **Click** the floating button to start recording
2. **Speak** your message (VAD automatically detects silence)
3. **Click again** to stop and process
4. The refined text will be **automatically pasted** to your active window!

## Technical Vocabulary

ZukuriFlow Elite is optimized for technical terminology including:
- Programming Languages: Python, JavaScript, TypeScript, Go, Rust
- AI/ML: RAG, LLM, GPT, LangChain, LangGraph, PyTorch, TensorFlow
- Databases: SQL, PostgreSQL, MongoDB, Redis, Elasticsearch
- DevOps: Docker, Kubernetes, AWS, CI/CD
- And 100+ more technical terms with proper capitalization

## CI/CD Pipeline

ZukuriFlow includes a GitHub Actions pipeline for automated testing and linting.

### Pipeline Features

- **Lint & Format**: Runs `flake8` and `black` for code quality
- **Test**: Runs `pytest` for unit tests
- **Multi-Python**: Tests on Python 3.9, 3.10, and 3.11
- **Auto-trigger**: Runs on push to `main` and pull requests

### Pipeline Status

The pipeline is defined in `.github/workflows/ci.yml` and runs automatically on every push.

To run checks locally:
```bash
# Lint
flake8 src/ --max-line-length=120

# Format check
black src/ --check

# Tests
pytest tests/ -v
```

## Requirements

- Python 3.9+
- Microphone access
- Works fully offline (local Whisper model)

## License

MIT License
