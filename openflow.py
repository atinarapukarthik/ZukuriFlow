import sys
import os
import time
import datetime
import threading
import math
import sounddevice as sd
import wavio
import numpy as np
import pyautogui
import pyperclip
from faster_whisper import WhisperModel
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QLinearGradient, QRadialGradient

# ===========================
# ⚙️ CONFIGURATION
# ===========================
MODEL_SIZE = "base"        # 'tiny', 'base', 'small', 'medium', 'large-v2'
DEVICE = "cpu"             # Change to "cuda" if you have an NVIDIA GPU
COMPUTE_TYPE = "int8"      # "int8" is faster on CPU. Use "float16" for GPU.
# Set to None for auto-detection, or "en", "es", etc.
LANGUAGE = "en"

# Output settings
OUTPUT_DIR = os.path.abspath("output")
TRANSCRIPT_FILE = os.path.join(OUTPUT_DIR, "transcripts.txt")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===========================
# 🎨 FLOATING BUTTON WIDGET
# ===========================


class FloatingButton(QWidget):
    # Signals for thread-safe UI updates
    transcription_done = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, whisper_model):
        super().__init__()
        self.model = whisper_model
        self.is_recording = False
        self.is_processing = False
        self.audio_frames = []
        self.samplerate = 16000
        self.animation_angle = 0
        self.audio_level = 0

        # Connect signals
        self.transcription_done.connect(self.on_transcription_done)
        self.status_changed.connect(self.on_status_changed)

        self.initUI()
        self.start_animation_timer()

    def initUI(self):
        # Window Settings (Frameless, Always on Top, Transparent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Size of the button
        self.button_size = 80
        self.setFixedSize(self.button_size + 20, self.button_size + 20)

        # Position: Bottom right of screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 150, screen.height() - 200)

        # For dragging
        self.drag_pos = None

        # Tooltip
        self.setToolTip("Click to record • Drag to move")

    def start_animation_timer(self):
        """Timer for smooth animations"""
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(30)  # ~33 FPS

    def update_animation(self):
        """Update animation state"""
        if self.is_recording:
            self.animation_angle = (self.animation_angle + 5) % 360
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Custom paint for the beautiful circular button"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = self.button_size // 2

        # Draw shadow
        shadow_gradient = QRadialGradient(center_x, center_y + 5, radius + 15)
        shadow_gradient.setColorAt(0, QColor(0, 0, 0, 50))
        shadow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(shadow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_x - radius - 10, center_y - radius - 5,
                            (radius + 10) * 2, (radius + 10) * 2)

        # Main button gradient
        if self.is_processing:
            # Yellow/Gold for processing
            gradient = QRadialGradient(
                center_x - 10, center_y - 10, radius * 2)
            gradient.setColorAt(0, QColor(255, 215, 100))
            gradient.setColorAt(1, QColor(255, 180, 50))
        elif self.is_recording:
            # Red/Orange for recording
            gradient = QRadialGradient(
                center_x - 10, center_y - 10, radius * 2)
            gradient.setColorAt(0, QColor(255, 120, 100))
            gradient.setColorAt(1, QColor(220, 60, 60))
        else:
            # Warm beige/cream (like the image) for idle
            gradient = QRadialGradient(
                center_x - 10, center_y - 10, radius * 2)
            gradient.setColorAt(0, QColor(210, 195, 170))
            gradient.setColorAt(1, QColor(180, 160, 130))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_x - radius, center_y - radius,
                            radius * 2, radius * 2)

        # Draw sound wave bars (like the image)
        self.draw_sound_waves(painter, center_x, center_y, radius)

        # Draw ring animation when recording
        if self.is_recording:
            self.draw_recording_ring(painter, center_x, center_y, radius)

    def draw_sound_waves(self, painter, cx, cy, radius):
        """Draw the sound wave bars in the center"""
        bar_count = 5
        bar_width = 4
        bar_spacing = 6
        total_width = bar_count * bar_width + (bar_count - 1) * bar_spacing
        start_x = cx - total_width // 2

        # Bar heights (middle is tallest)
        if self.is_recording:
            # Animated heights when recording
            base_heights = [15, 25, 35, 25, 15]
            heights = []
            for i, h in enumerate(base_heights):
                # Add some wave animation
                wave = math.sin((self.animation_angle + i * 30)
                                * math.pi / 180) * 8
                heights.append(int(h + wave + self.audio_level * 10))
        else:
            heights = [12, 20, 28, 20, 12]

        painter.setPen(Qt.PenStyle.NoPen)

        for i in range(bar_count):
            x = start_x + i * (bar_width + bar_spacing)
            h = heights[i]
            y = cy - h // 2

            # Bar gradient (white/cream)
            bar_gradient = QLinearGradient(x, y, x, y + h)
            bar_gradient.setColorAt(0, QColor(255, 255, 255, 230))
            bar_gradient.setColorAt(1, QColor(240, 235, 220, 200))

            painter.setBrush(QBrush(bar_gradient))
            painter.drawRoundedRect(x, y, bar_width, h, 2, 2)

    def draw_recording_ring(self, painter, cx, cy, radius):
        """Draw animated ring when recording"""
        pen = QPen(QColor(255, 255, 255, 150))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Pulsing ring
        pulse = math.sin(self.animation_angle * math.pi / 180) * 5
        ring_radius = radius + 5 + pulse
        painter.drawEllipse(int(cx - ring_radius), int(cy - ring_radius),
                            int(ring_radius * 2), int(ring_radius * 2))

    # === MOUSE EVENTS ===
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if it was a click (not a drag)
            if self.drag_pos:
                moved = (event.globalPosition().toPoint() -
                         self.frameGeometry().topLeft() - self.drag_pos)
                if abs(moved.x()) < 5 and abs(moved.y()) < 5:
                    # It's a click - toggle recording
                    self.toggle_recording()
            self.drag_pos = None
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        from PyQt6.QtCore import Qt as QtKey
        if event.key() == QtKey.Key.Key_Escape:
            # ESC to cancel recording or quit
            if self.is_recording:
                self.cancel_recording()
            else:
                self.close_app()
            event.accept()

    def contextMenuEvent(self, event):
        """Right-click menu"""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        if self.is_recording:
            cancel_action = menu.addAction("⏹️ Cancel Recording")

        quit_action = menu.addAction("❌ Quit")

        action = menu.exec(event.globalPos())

        if self.is_recording and action == cancel_action:
            self.cancel_recording()
        elif action == quit_action:
            self.close_app()

    # === RECORDING LOGIC ===
    def toggle_recording(self):
        if self.is_processing:
            return  # Don't allow toggle while processing

        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.audio_frames = []
        print("🔴 Recording started...")

        # Start recording in background thread
        threading.Thread(target=self._record_audio, daemon=True).start()

    def _record_audio(self):
        """Background thread for recording"""
        def callback(indata, frames, time_info, status):
            if status:
                print(f"⚠️ {status}")
            if self.is_recording:
                self.audio_frames.append(indata.copy())
                # Calculate audio level for visualization
                self.audio_level = min(1.0, np.sqrt(np.mean(indata ** 2)) * 10)

        try:
            with sd.InputStream(samplerate=self.samplerate, channels=1,
                                callback=callback, blocksize=1024):
                while self.is_recording:
                    sd.sleep(50)
        except Exception as e:
            print(f"❌ Recording error: {e}")
            self.is_recording = False

    def cancel_recording(self):
        """Cancel current recording without processing"""
        if self.is_recording:
            self.is_recording = False
            self.is_processing = False
            self.audio_level = 0
            self.audio_frames = []
            print("⏹️ Recording cancelled")
    
    def stop_recording(self):
        self.is_recording = False
        self.is_processing = True
        self.audio_level = 0
        print("⏳ Processing...")

        # Process in background thread
        threading.Thread(target=self._process_audio, daemon=True).start()

    def _process_audio(self):
        """Background thread for transcription"""
        if not self.audio_frames:
            self.status_changed.emit("idle")
            return

        try:
            # Save audio
            filename = os.path.join(OUTPUT_DIR, "temp_recording.wav")
            recording = np.concatenate(self.audio_frames, axis=0)
            wavio.write(filename, recording, self.samplerate, sampwidth=2)

            duration = len(recording) / self.samplerate
            print(f"📁 Audio: {duration:.1f}s")

            # Transcribe with VAD
            segments, info = self.model.transcribe(
                filename,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400,
                    threshold=0.5
                ),
                language=LANGUAGE,
                condition_on_previous_text=False
            )

            text = " ".join([seg.text for seg in segments]).strip()

            if text:
                print(f"🗣️ {text}")
                self.log_transcript(text)
                self.transcription_done.emit(text)
            else:
                print("⚠️ No speech detected")
                self.status_changed.emit("idle")

        except Exception as e:
            print(f"❌ Error: {e}")
            self.status_changed.emit("idle")

    def log_transcript(self, text):
        """Save to transcript file"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(TRANSCRIPT_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")

    # === SIGNAL HANDLERS ===
    def on_transcription_done(self, text):
        """Called when transcription is complete - paste the text"""
        self.is_processing = False

        # Paste to active window
        pyperclip.copy(text)
        time.sleep(0.15)

        try:
            if os.name == 'nt':
                pyautogui.hotkey('ctrl', 'v', interval=0.05)
            else:
                pyautogui.hotkey('command', 'v', interval=0.05)
            print("✅ Text pasted!")
        except Exception as e:
            print(f"⚠️ Paste failed: {e}")
            print("   Text is in clipboard - Ctrl+V to paste")

    def on_status_changed(self, status):
        """Update UI status"""
        if status == "idle":
            self.is_processing = False
            self.is_recording = False
    
    def close_app(self):
        """Properly close the application"""
        print("\n👋 Closing...")
        # Stop any recording
        self.is_recording = False
        self.is_processing = False
        # Close window
        self.close()
        QApplication.instance().quit()
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.is_recording = False
        self.is_processing = False
        event.accept()

# ===========================
# 🚀 MAIN
# ===========================


def main():
    print("=" * 55)
    print("   🎙️ OFFLINE FLOW - Voice-to-Text")
    print("   With Beautiful Floating Button")
    print("=" * 55)
    print()
    print(f"⏳ Loading Faster-Whisper ({MODEL_SIZE})...")

    # Load model
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    print(f"✅ Model loaded! ({DEVICE})")
    print()
    print("📋 INSTRUCTIONS:")
    print("   • Click button to START recording")
    print("   • Click again to STOP and transcribe")
    print("   • Drag button to move it")
    print("   • Right-click to quit")
    print("=" * 55)

    # Create Qt App
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # Create floating button
    button = FloatingButton(model)
    button.show()

    print("✅ Ready! Click the floating button to record.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
