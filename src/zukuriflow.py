"""
ZukuriFlow - Main GUI and Recording Logic
AI-powered audio recording with transcription and refinement
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import json
from pathlib import Path
from datetime import datetime

from utils.audio_handler import AudioHandler
from utils.ai_engine import AIEngine
from utils.refiner import Refiner


class ZukuriFlowGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZukuriFlow - AI Voice Transcription")
        self.root.geometry("800x600")

        # Initialize components
        self.audio_handler = AudioHandler()
        self.ai_engine = AIEngine()
        self.refiner = Refiner()

        # State
        self.is_recording = False
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        self.history_file = self.output_dir / "history.json"

        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        """Create the GUI layout"""
        # Title
        title_label = ttk.Label(
            self.root,
            text="ZukuriFlow",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=10)

        # Recording button
        self.record_btn = ttk.Button(
            self.root,
            text="Start Recording",
            command=self.toggle_recording,
            width=20
        )
        self.record_btn.pack(pady=10)

        # Status label
        self.status_label = ttk.Label(
            self.root,
            text="Ready to record",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=5)

        # Transcription output
        ttk.Label(self.root, text="Transcription:", font=(
            "Arial", 12, "bold")).pack(pady=(20, 5))
        self.transcription_text = scrolledtext.ScrolledText(
            self.root,
            height=10,
            width=90,
            wrap=tk.WORD,
            font=("Arial", 10)
        )
        self.transcription_text.pack(padx=10, pady=5)

        # Refined output
        ttk.Label(self.root, text="Refined Text:", font=(
            "Arial", 12, "bold")).pack(pady=(10, 5))
        self.refined_text = scrolledtext.ScrolledText(
            self.root,
            height=10,
            width=90,
            wrap=tk.WORD,
            font=("Arial", 10)
        )
        self.refined_text.pack(padx=10, pady=5)

    def toggle_recording(self):
        """Start or stop recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start audio recording"""
        self.is_recording = True
        self.record_btn.config(text="Stop Recording")
        self.status_label.config(text="Recording... (speak now)")
        self.transcription_text.delete(1.0, tk.END)
        self.refined_text.delete(1.0, tk.END)

        # Start recording in a separate thread
        threading.Thread(target=self.record_audio, daemon=True).start()

    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        self.record_btn.config(text="Start Recording")
        self.status_label.config(text="Processing audio...")

    def record_audio(self):
        """Record audio and process it"""
        # Record audio with VAD
        audio_data = self.audio_handler.record_with_vad()

        if not self.is_recording:
            # Recording was stopped
            self.root.after(
                0, lambda: self.status_label.config(text="Processing..."))

            # Transcribe with Faster-Whisper
            transcription = self.ai_engine.transcribe(audio_data)

            # Update UI with transcription
            self.root.after(
                0, lambda: self.update_transcription(transcription))

            # Refine the text
            refined = self.refiner.refine_text(transcription)

            # Update UI with refined text
            self.root.after(0, lambda: self.update_refined(refined))

            # Save to history
            self.save_to_history(transcription, refined)

            self.root.after(0, lambda: self.status_label.config(
                text="Ready to record"))

    def update_transcription(self, text):
        """Update transcription text box"""
        self.transcription_text.delete(1.0, tk.END)
        self.transcription_text.insert(1.0, text)

    def update_refined(self, text):
        """Update refined text box"""
        self.refined_text.delete(1.0, tk.END)
        self.refined_text.insert(1.0, text)

    def save_to_history(self, transcription, refined):
        """Save transcription to history.json"""
        history = []
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "transcription": transcription,
            "refined": refined
        }
        history.append(entry)

        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def load_history(self):
        """Load history on startup"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                print(f"Loaded {len(history)} history entries")


def main():
    root = tk.Tk()
    ZukuriFlowGUI(root)  # noqa: F841
    root.mainloop()


if __name__ == "__main__":
    main()
