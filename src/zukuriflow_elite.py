"""
ZukuriFlow Elite - Local-First AI Dictation Tool
Main application with PyQt6 floating button GUI
"""

import os
from typing import Optional
import sys

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPointF, QSize
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QMovie, QPixmap

from utils.whisper_engine import WhisperEngine
from utils.audio_recorder import AudioRecorder, StreamingRecorder
from utils.text_refiner import TextRefiner
from utils.clipboard_manager import ClipboardManager

# Assets directory for GIF/images
ASSETS_DIR = os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), "assets")
MIC_GIF_PATH = os.path.join(ASSETS_DIR, "mic_wave.gif")
MIC_PNG_PATH = os.path.join(ASSETS_DIR, "mic_wave.png")


class TranscriptionWorker(QThread):
    """
    Worker thread for AI processing to prevent UI freezing.
    """

    finished = pyqtSignal(str, str)  # (transcription, refined)
    error = pyqtSignal(str)

    def __init__(
        self, whisper_engine: WhisperEngine, text_refiner: TextRefiner, audio_data
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
                self.audio_data, use_vad=True
            )

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
    Frameless, transparent, always-on-top floating button with GIF animation.
    Features: Close button, status indicator, draggable interface.
    """

    # Color schemes for each state
    COLOR_IDLE = QColor(245, 235, 220)  # Beige/Cream
    COLOR_RECORDING = QColor(220, 50, 50)  # Red
    COLOR_PROCESSING = QColor(255, 215, 0)  # Gold

    def __init__(self):
        super().__init__()

        # Initialize AI components
        print("🚀 Initializing ZukuriFlow Elite...")
        self.whisper_engine = WhisperEngine(
            model_size="base", device="cpu", compute_type="int8", language="en"
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
        self.movie = None

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
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)

        # Container with dark background
        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-radius: 15px;
            }
        """)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(10, 8, 10, 10)
        container_layout.setSpacing(5)

        # Top bar with status and close button
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        # Status label
        self.status_label = QLabel("Click to record")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
            }
        """)
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()

        # Close button (X) - terminates the app
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: none;
                font-size: 14px;
                font-weight: bold;
                border-radius: 11px;
            }
            QPushButton:hover {
                background-color: #ff4444;
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.close_app)
        self.close_btn.setToolTip("Close ZukuriFlow (Terminate)")
        top_bar.addWidget(self.close_btn)

        container_layout.addLayout(top_bar)

        # GIF/Image label for mic animation
        self.gif_label = QLabel()
        self.gif_label.setFixedSize(80, 80)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gif_label.setStyleSheet("background: transparent;")

        # Load GIF or static image
        image_loaded = False

        # Try loading GIF first
        if os.path.exists(MIC_GIF_PATH):
            try:
                self.movie = QMovie(MIC_GIF_PATH)
                if self.movie.isValid():
                    self.movie.setScaledSize(QSize(75, 75))
                    self.gif_label.setMovie(self.movie)
                    self.movie.start()
                    image_loaded = True
                    print(f"✅ GIF loaded: {MIC_GIF_PATH}")
                else:
                    self.movie = None
            except Exception as e:
                print(f"⚠️ GIF load error: {e}")
                self.movie = None

        # Try loading PNG if GIF failed
        if not image_loaded and os.path.exists(MIC_PNG_PATH):
            try:
                pixmap = QPixmap(MIC_PNG_PATH)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        75, 75, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.gif_label.setPixmap(scaled)
                    image_loaded = True
                    print(f"✅ PNG loaded: {MIC_PNG_PATH}")
            except Exception as e:
                print(f"⚠️ PNG load error: {e}")

        # Fallback to emoji
        if not image_loaded:
            self.gif_label.setText("🎙️")
            self.gif_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    border-radius: 40px;
                    font-size: 35px;
                }
            """)
            print("ℹ️ Using fallback mic icon")

        # Make clickable
        self.gif_label.mousePressEvent = self.on_gif_click

        container_layout.addWidget(
            self.gif_label, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self.container)

        # Set total size
        self.setFixedSize(120, 130)

        # Position bottom-right of screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 150, screen.height() - 200)

    def on_gif_click(self, event):
        """Handle click on the GIF/mic area."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_recording()
            event.accept()

    def update_status_appearance(self):
        """Update UI based on current state."""
        if self.state == "processing":
            self.status_label.setText("Processing...")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #ffd700;
                    font-size: 10px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: transparent;
                }
            """)
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #1a1a1a;
                    border: 2px solid #ffd700;
                    border-radius: 15px;
                }
            """)
        elif self.state == "recording":
            self.status_label.setText("Recording...")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #ff4444;
                    font-size: 10px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: transparent;
                }
            """)
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #1a1a1a;
                    border: 2px solid #ff4444;
                    border-radius: 15px;
                }
            """)
        else:
            self.status_label.setText("Click to record")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 10px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: transparent;
                }
            """)
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #1a1a1a;
                    border-radius: 15px;
                }
            """)

    def close_app(self):
        """Properly terminate the application."""
        print("\n👋 Closing ZukuriFlow Elite...")
        # Stop any ongoing recording
        if self.streaming_recorder:
            try:
                self.streaming_recorder.stop()
            except:
                pass
        # Stop movie if running
        if self.movie:
            self.movie.stop()
        # Close window and quit app
        self.close()
        QApplication.instance().quit()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Escape:
            if self.state == "recording":
                self.cancel_recording()
            else:
                self.close_app()
            event.accept()

    def cancel_recording(self):
        """Cancel current recording without processing."""
        if self.state == "recording":
            print("⏹️ Recording cancelled")
            if self.streaming_recorder:
                try:
                    self.streaming_recorder.stop()
                except:
                    pass
                self.streaming_recorder = None
            self.reset_to_idle()

    def contextMenuEvent(self, event):
        """Right-click menu."""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        if self.state == "recording":
            cancel_action = menu.addAction("⏹️ Cancel Recording")

        quit_action = menu.addAction("❌ Quit")

        action = menu.exec(event.globalPos())

        if self.state == "recording" and action == cancel_action:
            self.cancel_recording()
        elif action == quit_action:
            self.close_app()

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
        self.update()

    def update_glow(self):
        """Update glow animation value."""
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle dragging the button."""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release - reset drag."""
        if event.button() == Qt.MouseButton.LeftButton:
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
        self.update_status_appearance()
        self.pulse_timer.start(50)  # 20 FPS for smooth animation

        # Start streaming recorder
        self.streaming_recorder = self.audio_recorder.record_streaming()
        self.streaming_recorder.start()

    def stop_recording(self):
        """Stop recording and start processing."""
        print("⏹️ Stopping recording...")
        self.state = "processing"
        self.update_status_appearance()
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
            self.whisper_engine, self.text_refiner, audio_data
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
            transcription=transcription, refined_text=refined, auto_paste=True
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
        self.update_status_appearance()
        self.update()
        print("✅ Ready for next recording\n")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("ZukuriFlow Elite")

    # Create and show floating button
    button = FloatingButton()
    button.show()

    print("\n" + "=" * 60)
    print("🎙️ ZukuriFlow Elite - Local AI Dictation")
    print("=" * 60)
    print("Click the GIF/mic to start/stop recording")
    print("Drag the widget to reposition")
    print("Click ✕ button or Right-click → Quit to close")
    print("Press ESC to cancel recording or quit")
    print("=" * 60 + "\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
