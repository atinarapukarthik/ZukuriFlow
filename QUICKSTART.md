# ZukuriFlow Elite - Quick Reference

## Installation

### Windows
```bash
# Run setup script
setup.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### macOS/Linux
```bash
# Run setup script
chmod +x setup.sh
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Start Application
```bash
# Windows
run.bat

# macOS/Linux
chmod +x run.sh
./run.sh

# Or directly
python src/zukuriflow_elite.py
```

### Basic Workflow
1. **Click** floating button → Starts recording (Red)
2. **Speak** your message
3. **Click** again → Stops & processes (Gold)
4. Text is **auto-pasted** to active window
5. Button returns to **Idle** (Beige)

## Configuration

### Change Model Size
Edit `src/zukuriflow_elite.py`:
```python
self.whisper_engine = WhisperEngine(
    model_size="small",    # tiny, base, small, medium, large
    device="cpu",          # or "cuda" for GPU
    compute_type="int8",   # int8 (CPU), float16 (GPU)
    language="en"          # or None for auto-detect
)
```

### Add Custom Jargon
Edit `src/utils/text_refiner.py` → `JARGON_MAP`:
```python
JARGON_MAP = {
    # Add your custom terms
    "zukuri": "Zukuri",
    "mycompany": "MyCompany",
    # ... existing entries
}
```

### Disable Auto-Paste
Edit `src/zukuriflow_elite.py` → `on_transcription_finished()`:
```python
self.clipboard_manager.copy_and_paste(
    transcription=transcription,
    refined_text=refined,
    auto_paste=False  # Change to False
)
```

## Keyboard Shortcuts (Future)
Currently: **Mouse only** (click to start/stop)

## Visual States

| State      | Color         | Icon | Meaning               |
|------------|---------------|------|-----------------------|
| Idle       | Beige/Cream   | 🎤   | Ready to record       |
| Recording  | Pulsing Red   | ⏺    | Actively recording    |
| Processing | Glowing Gold  | ⚡   | Transcribing & refining|

## File Locations

| File                    | Purpose                           |
|-------------------------|-----------------------------------|
| `output/history.json`   | All transcription history         |
| `src/zukuriflow_elite.py`| Main application                 |
| `requirements.txt`      | Python dependencies               |
| `.gitignore`            | Excludes output/ from git         |

## Troubleshooting

### No audio detected
- Check microphone permissions
- Verify microphone is default input device
- Try speaking louder

### Slow transcription
- Use `model_size="tiny"` for faster processing
- Enable GPU with `device="cuda"` (requires NVIDIA GPU)
- Use `compute_type="float16"` with GPU

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Button not appearing
- Check if another app is blocking always-on-top
- Try restarting application
- Check console for error messages

## Technical Specifications

| Aspect              | Details                          |
|---------------------|----------------------------------|
| Sample Rate         | 16000 Hz                         |
| Audio Format        | Float32 mono                     |
| Model               | faster-whisper base (int8)       |
| VAD Threshold       | 0.5                              |
| Min Speech Duration | 250ms                            |
| Min Silence Duration| 500ms                            |
| GUI Framework       | PyQt6                            |
| Threading Model     | QThread for AI processing        |

## History Management

### View History
Check `output/history.json`:
```json
[
  {
    "timestamp": "2026-01-17T10:30:00.123456",
    "transcription": "need to implement rag for the api",
    "refined": "Need to implement RAG for the API.",
    "metadata": {}
  }
]
```

### Export History
```python
from utils.clipboard_manager import ClipboardManager

cm = ClipboardManager()
cm.export_history_to_text("my_transcriptions.txt")
```

### Clear History
```python
cm.clear_history()
```

## Performance Tips

1. **CPU Optimization**: Use `model_size="base"` with `compute_type="int8"`
2. **GPU Acceleration**: Use `device="cuda"` with `compute_type="float16"`
3. **Faster Models**: Use `model_size="tiny"` (less accurate but 3x faster)
4. **Quality Models**: Use `model_size="small"` or `"medium"` (slower but better)

## Supported Platforms

| OS       | Status      | Notes                     |
|----------|-------------|---------------------------|
| Windows  | ✅ Full     | Ctrl+V paste              |
| macOS    | ✅ Full     | Cmd+V paste               |
| Linux    | ✅ Full     | Ctrl+V paste              |

## Dependencies Overview

```
faster-whisper    # AI transcription
torch            # ML backend
sounddevice      # Audio capture
wavio            # WAV export
numpy            # Array operations
PyQt6            # GUI framework
pyperclip        # Clipboard operations
pyautogui        # Keyboard automation
```

## Getting Help

1. Check console output for error messages
2. Review `DOCUMENTATION.md` for architecture details
3. Review `ARCHITECTURE.md` for system flow
4. Check Python version: `python --version` (requires 3.8+)
5. Verify microphone access in OS settings

## Best Practices

✅ **DO**:
- Speak clearly and at normal pace
- Use in quiet environment for best accuracy
- Let VAD detect silence (don't click too early)
- Review `history.json` for past transcriptions

❌ **DON'T**:
- Click button rapidly (wait for state transition)
- Record with loud background noise
- Expect perfect accuracy with very technical terms (add them to jargon map)
- Run multiple instances simultaneously

## Advanced Usage

### Run as Background Service (Windows)
```bash
# Run minimized
start /B pythonw src\zukuriflow_elite.py
```

### Custom Python Environment
```bash
# Use specific Python version
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Development Mode
```bash
# Install with dev tools
pip install -r requirements.txt
pip install black flake8 mypy  # code formatters & linters
```

---

**Version**: 1.0.0  
**Last Updated**: January 17, 2026  
**License**: MIT
