"""
ZukuriFlow Elite - Local-First AI Dictation Tool
Main application with PyQt6 floating button GUI
"""

from typing import Optional
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint, QPointF, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen

from utils.whisper_engine import WhisperEngine
from utils.audio_recorder import AudioRecorder, StreamingRecorder
from utils.text_refiner import TextRefiner
from utils.clipboard_manager import ClipboardManager


class TranscriptionWorker(QThread):
    """
    Worker thread for AI processing to prevent UI freezing.
    """
    finished = pyqtSignal(str, str)  # (transcription, refined)
    error = pyqtSignal(str)

    def __init__(
        self,
        whisper_engine: WhisperEngine,
        text_refiner: TextRefiner,
        audio_data
    ):
        super().__init__()
        self.whisper_engine = whisper_engine
        self.text_refiner = text_refiner
        self.audio_data = audio_data

    def run(self):
        """Execute transcription and refinement in background thread."""
        try:
            # Step 1: Transcribe with Whisper
            transcription = self.whisper_engine.transcribe(
                self.audio_data, use_vad=True)

            if not transcription.strip():
                self.error.emit("No speech detected")
                return

            # Step 2: Refine text
            refined = self.text_refiner.refine(transcription)

            # Emit results
            self.finished.emit(transcription, refined)

        except Exception as e:
            self.error.emit(f"Transcription error: {str(e)}")


class FloatingButton(QWidget):
    """
    Frameless, transparent, always-on-top floating button with three states:
    - Idle: Beige/Cream
    - Recording: Pulsing Red
    - Processing: Glowing Gold
    """

    # Color schemes for each state
    COLOR_IDLE = QColor(245, 235, 220)      # Beige/Cream
    COLOR_RECORDING = QColor(220, 50, 50)    # Red
    COLOR_PROCESSING = QColor(255, 215, 0)   # Gold

    def __init__(self):
        super().__init__()

        # Initialize AI components
        print("🚀 Initializing ZukuriFlow Elite...")
        self.whisper_engine = WhisperEngine(
            model_size="base",
            device="cpu",
            compute_type="int8",
            language="en"
        )
        self.audio_recorder = AudioRecorder(sample_rate=16000, channels=1)
        self.text_refiner = TextRefiner()
        self.clipboard_manager = ClipboardManager(output_dir="output")

        # State management
        self.state = "idle"  # idle, recording, processing
        self.streaming_recorder: Optional[StreamingRecorder] = None
        self.worker_thread: Optional[TranscriptionWorker] = None

        # Animation
        self.pulse_value = 0.0
        self.glow_value = 0.0

        # Setup UI
        self.setup_ui()
        self.setup_animations()

        # For dragging
        self.drag_position = None

        print("✅ ZukuriFlow Elite ready!")

    def setup_ui(self):
        """Configure the floating button appearance."""
        # Frameless, transparent, always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Size and position
        self.setFixedSize(100, 100)

        # Center on screen initially
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 100
        self.move(x, y)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setup_animations(self):
        """Setup timers for pulsing and glowing animations."""
        # Pulse animation for recording state
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_pulse)

        # Glow animation for processing state
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.update_glow)

    def update_pulse(self):
        """Update pulse animation value."""
        import math
        from time import time
        self.pulse_value = (math.sin(time() * 3) + 1) / 2  # 0.0 to 1.0
        self.update()

    def update_glow(self):
        """Update glow animation value."""
        import math
        from time import time
        self.glow_value = (math.sin(time() * 2) + 1) / 2  # 0.0 to 1.0
        self.update()

    def paintEvent(self, event):
        """Draw the button based on current state."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Determine color based on state
        if self.state == "idle":
            color = self.COLOR_IDLE
        elif self.state == "recording":
            # Pulsing red
            intensity = int(220 - (self.pulse_value * 70))
            color = QColor(intensity, 50, 50)
        elif self.state == "processing":
            # Glowing gold
            intensity = int(255 - (self.glow_value * 50))
            color = QColor(intensity, 215, 0)
        else:
            color = self.COLOR_IDLE

        # Draw circular button with gradient
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 10

        # Convert to QPointF and float for QRadialGradient
        center_f = QPointF(center.x(), center.y())
        gradient = QRadialGradient(center_f, float(radius))
        gradient.setColorAt(0.0, color.lighter(120))
        gradient.setColorAt(0.7, color)
        gradient.setColorAt(1.0, color.darker(120))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(color.darker(150), 2))
        painter.drawEllipse(center, radius, radius)

        # Draw icon/text in center
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        if self.state == "idle":
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🎤")
        elif self.state == "recording":
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "⏺")
        elif self.state == "processing":
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "⚡")

    def mousePressEvent(self, event):
        """Handle mouse press for dragging and click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - \
                self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle dragging the button."""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle click to toggle recording."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Only toggle if we didn't drag much
            if self.drag_position:
                drag_distance = (event.globalPosition().toPoint(
                ) - self.frameGeometry().topLeft() - self.drag_position).manhattanLength()
                if drag_distance < 10:  # Threshold for click vs drag
                    self.toggle_recording()
            self.drag_position = None
            event.accept()

    def toggle_recording(self):
        """Toggle between recording and idle states."""
        if self.state == "idle":
            self.start_recording()
        elif self.state == "recording":
            self.stop_recording()
        # Do nothing if processing

    def start_recording(self):
        """Start audio recording."""
        print("\n🔴 Starting recording...")
        self.state = "recording"
        self.pulse_timer.start(50)  # 20 FPS for smooth animation

        # Start streaming recorder
        self.streaming_recorder = self.audio_recorder.record_streaming()
        self.streaming_recorder.start()

    def stop_recording(self):
        """Stop recording and start processing."""
        print("⏹️ Stopping recording...")
        self.state = "processing"
        self.pulse_timer.stop()
        self.glow_timer.start(50)

        # Stop streaming recorder and get audio
        if self.streaming_recorder:
            audio_data = self.streaming_recorder.stop()
            self.streaming_recorder = None

            # Check if we got any audio
            if len(audio_data) == 0:
                print("⚠️ No audio recorded")
                self.reset_to_idle()
                return

            # Process in background thread
            self.process_audio(audio_data)

    def process_audio(self, audio_data):
        """Process audio in background thread."""
        print("⚙️ Processing audio...")

        # Create worker thread
        self.worker_thread = TranscriptionWorker(
            self.whisper_engine,
            self.text_refiner,
            audio_data
        )

        # Connect signals
        self.worker_thread.finished.connect(self.on_transcription_finished)
        self.worker_thread.error.connect(self.on_transcription_error)

        # Start processing
        self.worker_thread.start()

    def on_transcription_finished(self, transcription: str, refined: str):
        """Handle successful transcription."""
        print(f"\n📝 Transcription: {transcription}")
        print(f"✨ Refined: {refined}\n")

        # Save and paste
        self.clipboard_manager.copy_and_paste(
            transcription=transcription,
            refined_text=refined,
            auto_paste=True
        )

        self.reset_to_idle()

    def on_transcription_error(self, error_message: str):
        """Handle transcription error."""
        print(f"❌ Error: {error_message}")
        self.reset_to_idle()

    def reset_to_idle(self):
        """Reset button to idle state."""
        self.state = "idle"
        self.glow_timer.stop()
        self.pulse_timer.stop()
        self.worker_thread = None
        self.update()
        print("✅ Ready for next recording\n")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("ZukuriFlow Elite")

    # Create and show floating button
    button = FloatingButton()
    button.show()

    print("\n" + "="*60)
    print("🎙️ ZukuriFlow Elite - Local AI Dictation")
    print("="*60)
    print("Click the button to start/stop recording")
    print("Drag the button to reposition")
    print("Press Ctrl+C in terminal to quit")
    print("="*60 + "\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
