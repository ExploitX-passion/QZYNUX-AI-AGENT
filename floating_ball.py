#!/usr/bin/env python3
"""
QZYNUX - Floating Ball
Part of Qzynux GUI module

This file is part of Qzynux GUI module, which is licensed under GPL v3.
See modules/gui/LICENSE.md for full license text.

Copyright (c) 2026 EXPLOITX PASSION.
"""

# PyQt6 Version
import sys
import os
import tempfile
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMenu, QGraphicsDropShadowEffect,
    QGraphicsBlurEffect
)
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont, QPixmap, QBitmap
)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None


class FloatingBall(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.size = 60
        self.setFixedSize(self.size, self.size)
        self.setMask(self.create_round_mask())
        
        # Drag tracking
        self.drag_start_pos = None
        self.drag_threshold = 5
        self.is_dragging = False
        
        self.logo = self.load_logo()
        
        # Glow effect (will be created on hover)
        self.glow_effect = None
        
        # Blur radius
        self.blur_radius = 12  # 🔧 CHANGE THIS
        
        self.menu = None
        self.temp_logo_file = None # Add this line
        self.show()

    def create_round_mask(self):
        from PyQt6.QtGui import QBitmap
        bitmap = QBitmap(self.size, self.size)
        bitmap.fill(Qt.GlobalColor.white)
        painter = QPainter(bitmap)
        painter.setBrush(Qt.GlobalColor.black)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.size, self.size, self.size//2, self.size//2)
        painter.end()
        return bitmap

    def load_logo(self):
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "logo.png"),
            os.path.join(os.path.dirname(__file__), "logo.png"),
            os.path.join(os.path.expanduser("~"), ".qzynux", "logo.png"),
            "/mnt/QZY/qzynux-ai/data/images/Exploitx_logo.png"
        ]
        
        for logo_path in possible_paths:
            if os.path.exists(logo_path):
                try:
                    img = Image.open(logo_path)
                    img = img.resize((self.size - 15, self.size - 15), Image.Resampling.LANCZOS)
                    
                    # Create unique temp file
                    temp_fd, temp_path = tempfile.mkstemp(suffix='.png', prefix='qzynux_ball_')
                    os.close(temp_fd)
                    img.save(temp_path)
                    self.temp_logo_file = temp_path  # Store for cleanup
                    return QPixmap(temp_path)
                except Exception:
                    continue
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        margin = 2
        rect_size = self.size - (margin * 2)
        radius = self.size // 2
        
        painter.setBrush(QBrush(QColor(255, 0, 51)))
        painter.setPen(QPen(QColor(255, 102, 102), 2))
        painter.drawRoundedRect(margin, margin, rect_size, rect_size, radius, radius)
        
        if self.logo:
            logo_size = self.size - (margin * 8)  # 60 - 16 = 44px
            logo_x = (self.size - logo_size) // 2  # 8px
            painter.drawPixmap(logo_x, logo_x, logo_size, logo_size, self.logo)
        else:
            painter.setFont(QFont("Segoe UI", 28))
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "💀")

    def create_glow_effect(self):
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(25)
        effect.setOffset(0, 0)
        effect.setColor(QColor(255, 80, 120, 220))
        return effect

    def create_blur_effect(self):
        effect = QGraphicsBlurEffect()
        effect.setBlurRadius(self.blur_radius)
        return effect

    def enterEvent(self, event):
        """Mouse near → GLOW effect"""
        self.glow_effect = self.create_glow_effect()
        self.setGraphicsEffect(self.glow_effect)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Mouse far → BLUR effect"""
        self.setGraphicsEffect(None)
        blur_effect = self.create_blur_effect()
        self.setGraphicsEffect(blur_effect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint()
            self.is_dragging = False

    def mouseMoveEvent(self, event):
        if self.drag_start_pos is not None:
            delta = (event.globalPosition().toPoint() - self.drag_start_pos).manhattanLength()
            if delta > self.drag_threshold:
                self.is_dragging = True
                self.move(self.pos() + (event.globalPosition().toPoint() - self.drag_start_pos))
                self.drag_start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_dragging:
                self.open_menu()
            self.drag_start_pos = None
            self.is_dragging = False

    def open_menu(self):
        if self.menu and self.menu.isVisible():
            self.menu.close()
            return
        
        self.menu = QMenu(self)
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: white;
                border: 1px solid #ff0033;
                border-radius: 12px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 8px;
            }
            QMenu::item:selected {
                background-color: #ff0033;
            }
        """)
        
        chat_action = self.menu.addAction("💬 Chat Window")
        settings_action = self.menu.addAction("⚙️ Settings")
        self.menu.addSeparator()
        quit_action = self.menu.addAction("【🛑】 Power Off")
        
        chat_action.triggered.connect(self.open_chat_window)
        settings_action.triggered.connect(self.open_settings)
        quit_action.triggered.connect(self.shutdown_qzynux)
        
        self.menu.exec(self.mapToGlobal(QPoint(self.width() // 2, self.height() + 5)))

    def open_chat_window(self):
        print("📬 Opening chat window...")
        QMessageBox.information(self, "Qzynux", "Chat Window Coming Soon!")

    def open_settings(self):
        print("⚙️ Opening settings...")
        QMessageBox.information(self, "Qzynux", "Settings Coming Soon!")

    def shutdown_qzynux(self):
        print("🛑 Shutting down Qzynux...")
        QApplication.quit()

    def closeEvent(self, event):
        """Clean up temp logo file on close"""
        if hasattr(self, 'temp_logo_file') and self.temp_logo_file and os.path.exists(self.temp_logo_file):
            try:
                os.unlink(self.temp_logo_file)
            except:
                pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    ball = FloatingBall()
    sys.exit(app.exec())