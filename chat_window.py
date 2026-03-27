#!/usr/bin/env python3
"""
QZYNUX - Chat Window
Part of Qzynux GUI module

This file is part of Qzynux GUI module, which is licensed under GPL v3.
See modules/gui/LICENSE.md for full license text.

Copyright (c) 2026 ExploitX_Passion
"""

import sys
import os
import uuid
import tempfile
import re
from threading import Lock
from PyQt6.QtCore import QTimer
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QListWidget, QSplitter, QListWidgetItem,
    QMessageBox, QLabel, QScrollArea, QFileDialog, QDialog, QDialogButtonBox,
    QFrame, QAbstractItemView, QSizePolicy, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QSize, QEvent, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QPixmap, QTextCursor, QAction, QKeyEvent, QIcon

# Safe PIL import
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None


# ========== CONSTANTS ==========
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_MESSAGES_PER_SESSION = 500
MAX_MESSAGE_LENGTH = 10000
MAX_PENDING_FILES = 20
LARGE_FILE_WARNING_THRESHOLD = 20 * 1024 * 1024  # 20MB


class LoginDialog(QDialog):
    """Login dialog for user authentication"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - QZYNUX")
        self.setFixedSize(400, 250)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Welcome to QZYNUX")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ff0033; margin: 10px;")
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setContentsMargins(10, 10, 10, 10)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setMinimumHeight(35)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
            }
        """)        

        form_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(35)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
            }
        """)
            
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setMinimumHeight(45)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0033;
                border: none;
                border-radius: 22px;
                padding: 12px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #cc0029;
            }
        """)

        self.login_btn.clicked.connect(self.accept)
        layout.addWidget(self.login_btn)
        
    def get_username(self):
        return self.username_input.text().strip()
    
    def get_password(self):
        return self.password_input.text().strip()


class UserProfile:
    """User profile data"""
    def __init__(self):
        self.username = "Guest"
        self.is_logged_in = False
        self.avatar_path = None
        
    def set_user(self, username):
        self.username = username
        self.is_logged_in = True
        
    def logout(self):
        self.username = "Guest"
        self.is_logged_in = False
        self.avatar_path = None


class AnimatedWidget(QWidget):
    """Widget with animated width"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._width = 250
        self.setFixedWidth(self._width)
        self.animation = QPropertyAnimation(self, b"width")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def getWidth(self):
        return self._width

    def setWidth(self, w):
        self._width = w
        self.setFixedWidth(w)

    width = pyqtProperty(int, getWidth, setWidth)

    def animate_width(self, target_width):
        self.animation.stop()
        self.animation.setEndValue(target_width)
        self.animation.start()


class ImageViewer(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Qzynux Logo")
        layout = QVBoxLayout(self)
        label = QLabel()
        scaled = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(scaled)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.resize(450, 450)


class FileBubble(QWidget):
    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)

        ext = os.path.splitext(self.filename)[1].lower()
        icon = "📄"
        if ext in ['.py']:
            icon = "🐍"
        elif ext in ['.txt', '.md']:
            icon = "📝"
        elif ext in ['.png', '.jpg', '.jpeg', '.gif']:
            icon = "🖼️"
        elif ext in ['.pdf']:
            icon = "📕"
        elif ext in ['.zip', '.tar', '.gz']:
            icon = "📦"

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(icon_label)

        name_label = QLabel(self.filename)
        name_label.setFont(QFont("Segoe UI", 9))
        name_label.setStyleSheet("color: #888888;")
        layout.addWidget(name_label)

        self.setStyleSheet("""
            QWidget {
                background-color: #2a2a2e;
                border-radius: 12px;
                padding: 4px 8px;
            }
        """)


class MessageWidget(QWidget):
    def __init__(self, text, files=None, is_user=True, parent=None, main_window=None):
        super().__init__(parent)
        self.text = text
        self.files = files or []
        self.is_user = is_user
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(4)

        if self.text.strip():
            bubble_container = QHBoxLayout()
            bubble_container.setContentsMargins(0, 0, 0, 0)

            bubble = QLabel()
            bubble.setText(self.text)
            bubble.setWordWrap(True)
            bubble.setMaximumWidth(650)
            bubble.setMinimumHeight(35)
            bubble.setFont(QFont("Segoe UI", 11))
            bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

            if self.is_user:
                bubble.setStyleSheet("""
                    QLabel {
                        background-color: #8B0000;
                        border: none;
                        border-radius: 12px;
                        padding: 10px 14px;
                        color: #ffffff;
                    }
                """)
                bubble_container.addStretch()
                bubble_container.addWidget(bubble)
            else:
                bubble.setStyleSheet("""
                    QLabel {
                        background-color: #2a2a2e;
                        border: none;
                        border-radius: 12px;
                        padding: 10px 14px;
                        color: #ffffff;
                    }
                """)
                bubble_container.addWidget(bubble)
                bubble_container.addStretch()

            layout.addLayout(bubble_container)

        if self.files:
            files_layout = QHBoxLayout()
            files_layout.setContentsMargins(0, 0, 0, 0)

            if self.is_user:
                files_layout.addStretch()

            for filepath in self.files:
                try:
                    if os.path.exists(filepath):
                        file_bubble = FileBubble(filepath)
                        files_layout.addWidget(file_bubble)
                except Exception:
                    pass

            if not self.is_user:
                files_layout.addStretch()

            layout.addLayout(files_layout)

        if self.text.strip():
            copy_layout = QHBoxLayout()
            copy_layout.setContentsMargins(0, 2, 0, 0)

            copy_btn = QPushButton("📋")
            copy_btn.setFixedSize(24, 24)
            copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            copy_btn.setToolTip("Copy message")
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    font-size: 12px;
                    color: #888888;
                }
                QPushButton:hover {
                    color: #ff0033;
                }
            """)
            
            copy_btn.clicked.connect(self.copy_text)

            if self.is_user:
                copy_layout.addStretch()
                copy_layout.addWidget(copy_btn)
            else:
                copy_layout.addWidget(copy_btn)
                copy_layout.addStretch()

            layout.addLayout(copy_layout)

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text)
        if self.main_window:
            self.main_window.statusBar().showMessage("Copied!", 1000)


class ChatSession:
    def __init__(self, name):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.messages = []
        self.created_at = datetime.now()


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qzynux Agent: Powered By EXPLOITX PASSION ")
        self.setMinimumSize(900, 600)
        self.setGeometry(200, 200, 1000, 700)

        self.logo_pixmap = None
        self.sessions = []
        self.current_session = None
        self.pending_files = []
        self.is_at_bottom = True
        self.sidebar_collapsed = False
        self.sidebar_width = 250
        
        self.user_profile = UserProfile()
        self.pending_files_lock = Lock()
        self.temp_logo_file = None
        self._sending = False

        self.setup_ui()
        self.apply_styles()
        self.installEventFilter(self)
        self.show_login_dialog()
        self.create_new_chat()
        self.update_user_profile_display()

    def show_login_dialog(self):
        while True:
            login_dialog = LoginDialog(self)
            result = login_dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                username = login_dialog.get_username()
                password = login_dialog.get_password()
                if username and password:  # Both required
                    self.user_profile.set_user(username)
                    self.statusBar().showMessage(f"Welcome, {username}!", 3000)
                    break
                else:
                    QMessageBox.warning(self, "Login Failed", 
                        "Username and password are required!")
            else:
                reply = QMessageBox.question(self, "Exit Application", 
                    "Login is required to use QZYNUX.\n\nDo you want to exit?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    sys.exit(0)
                # Otherwise, continue loop (show login dialog again)

    def update_user_profile_display(self):
        """Update user profile bubble in sidebar"""
        if self.user_profile.is_logged_in:
            self.user_bubble.setText(f"👤  {self.user_profile.username}")
            self.user_bubble.setToolTip(f"Logged in as: {self.user_profile.username}")
            self.user_bubble.setStyleSheet("""
                QPushButton {
                    background-color: #ff0033;
                    border: none;
                    border-radius: 20px;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #cc0029;
                }
            """)
        else:
            self.user_bubble.setText("👤  Guest")
            self.user_bubble.setToolTip("Click to login in Settings")
            self.user_bubble.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2e;
                    border: 1px solid #3a3a3e;
                    border-radius: 20px;
                    padding: 8px 16px;
                    font-size: 14px;
                    color: #888888;
                }
                QPushButton:hover {
                    background-color: #3a3a3e;
                    color: #ff0033;
                }
            """)

    def show_profile_info(self):
        """Show profile information (will be managed in Settings)"""
        if self.user_profile.is_logged_in:
            QMessageBox.information(self, "Profile", 
                f"Logged in as: {self.user_profile.username}\n\n"
                "Manage your account in Settings.")
        else:
            QMessageBox.information(self, "Profile", 
                "You are not logged in.\n\n"
                "Please go to Settings to login.")
            
    def get_logo_path(self):
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "logo.png"),
            os.path.join(os.path.dirname(__file__), "logo.png"),
            os.path.join(os.path.expanduser("~"), ".qzynux", "logo.png"),
            "/mnt/QZY/qzynux-ai/data/images/Exploitx_logo.png"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def load_logo_pixmap_safe(self):
        logo_path = self.get_logo_path()
        if logo_path and os.path.exists(logo_path):
            try:
                return QPixmap(logo_path)
            except Exception:
                pass
        return None

    def create_temp_logo(self, img):
        try:
            fd, path = tempfile.mkstemp(suffix='.png', prefix='qzynux_logo_')
            os.close(fd)
            img.save(path)
            return path
        except Exception:
            return None

    def cleanup_temp_files(self):
        if self.temp_logo_file and os.path.exists(self.temp_logo_file):
            try:
                os.unlink(self.temp_logo_file)
            except Exception:
                pass

    def create_new_chat(self):
        if len(self.sessions) > 100:
            oldest = self.sessions.pop(0)
            oldest.messages.clear()
        
        new_session = ChatSession("New Chat")
        self.sessions.append(new_session)
        self.current_session = new_session
        self.load_session(new_session)

    def load_session(self, session):
        self.current_session = session
        
        with self.pending_files_lock:
            self.pending_files = []

        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        messages_to_load = session.messages[-MAX_MESSAGES_PER_SESSION:]
        for msg in messages_to_load:
            try:
                msg_widget = MessageWidget(
                    msg['text'], msg.get('files', []),
                    msg['is_user'], self, main_window=self
                )
                self.messages_layout.insertWidget(self.messages_layout.count() - 1, msg_widget)
            except Exception:
                continue

        self.update_history_list()
        self.scroll_to_end()

    def update_history_list(self):
        self.history_list.clear()
        for session in self.sessions:
            item = QListWidgetItem(session.name)
            item.setData(Qt.ItemDataRole.UserRole, session.id)
            self.history_list.addItem(item)

        for i in range(self.history_list.count()):
            if self.history_list.item(i).data(Qt.ItemDataRole.UserRole) == self.current_session.id:
                self.history_list.setCurrentRow(i)
                break

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = AnimatedWidget()
        self.sidebar.setStyleSheet("""
            QWidget {
                background-color: #333333; 
                border-right: 1px solid #1e1e2e;
            }
        """)
        self.setup_sidebar_content()

        splitter_container = QWidget()
        splitter_container.setFixedWidth(24)
        splitter_container.setStyleSheet("background-color: transparent;")
        splitter_layout = QVBoxLayout(splitter_container)
        splitter_layout.setContentsMargins(0, 20, 0, 0)
        splitter_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.splitter_btn = QPushButton("◀")
        self.splitter_btn.setFixedSize(24, 40)
        self.splitter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.splitter_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 12px;
                font-size: 12px;
                color: #888888;
            }
            QPushButton:hover {
                background-color: #3a3a3e;
                color: #ff0033;
            }
        """)
        self.splitter_btn.clicked.connect(self.toggle_sidebar)
        splitter_layout.addWidget(self.splitter_btn)

        self.setup_chat_area()

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(splitter_container)
        main_layout.addWidget(self.splitter, 1)

    def setup_sidebar_content(self):
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(15)

        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setSpacing(5)
        
        logo_path = self.get_logo_path()
        if logo_path and os.path.exists(logo_path) and PIL_AVAILABLE:
            try:
                img = Image.open(logo_path)
                img = img.resize((70, 70), Image.Resampling.LANCZOS)
                temp_path = self.create_temp_logo(img)
                if temp_path:
                    self.temp_logo_file = temp_path
                    logo_pixmap = QPixmap(temp_path)
                    self.logo_label = QLabel()
                    self.logo_label.setPixmap(logo_pixmap)
                    self.logo_label.setCursor(Qt.CursorShape.PointingHandCursor)
                    self.logo_label.setToolTip("Click to view logo")
                    self.logo_label.mousePressEvent = self.show_logo_full
                    self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    logo_layout.addWidget(self.logo_label)
                    self.logo_pixmap = self.load_logo_pixmap_safe()
            except Exception:
                pass
        
        brand_name = QLabel("QZYNUX")
        brand_name.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        brand_name.setStyleSheet("color: #ff0033;")
        brand_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(brand_name)
        
        branding_label = QLabel("Powered By: EXPLOITX PASSION")
        branding_label.setFont(QFont("Segoe UI", 10))
        branding_label.setStyleSheet("color: #00aaff;")
        branding_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(branding_label)
        
        sidebar_layout.addWidget(logo_widget)

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("background-color: #333333; max-height: 1px;")
        sidebar_layout.addWidget(separator1)

        self.new_chat_btn = QPushButton("+ New Chat")
        self.new_chat_btn.setFont(QFont("Segoe UI", 11))
        self.new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_chat_btn.clicked.connect(self.create_new_chat)
        self.new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 20px;
                padding: 12px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #3a3a3e;
            }
        """)
        sidebar_layout.addWidget(self.new_chat_btn)

        history_section = QFrame()
        history_section.setStyleSheet("""
            QFrame {
                background-color: #2a2a2e;
                border-radius: 12px;
            }
        """)
        history_layout = QVBoxLayout(history_section)
        history_layout.setContentsMargins(10, 10, 10, 10)
        history_layout.setSpacing(10)

        chat_label = QLabel("Chat History")
        chat_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        chat_label.setStyleSheet("color: #F8F8FF; padding: 5px 0;")
        history_layout.addWidget(chat_label)

        self.history_list = QListWidget()
        self.history_list.setFont(QFont("Segoe UI", 10))
        self.history_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e2e;
                border: 1px solid #3a3a3e;
                border-radius: 8px;
                outline: none;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px 8px;
                border-radius: 6px;
                color: #cccccc;
                margin: 2px 0px;
            }
            QListWidget::item:selected {
                background-color: #DC143C;
                color: white;
                border-radius: 6px;
            }
            QListWidget::item:hover {
                background-color: #3a3a3e;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                background-color: #1e1e2e;
                width: 10px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #DC143C;
                border-radius: 6px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #ff6666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.history_list.itemClicked.connect(self.on_history_selected)
        history_layout.addWidget(self.history_list)

        sidebar_layout.addWidget(history_section, 1)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("background-color: #333333; max-height: 1px;")
        sidebar_layout.addWidget(separator2)

        # === BOTTOM SECTION: Settings + User Bubble (Capsule Shape) ===
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        self.settings_btn = QPushButton("⚙️  Settings")
        self.settings_btn.setFixedHeight(40)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 14px;
                color: #888888;
            }
            QPushButton:hover {
                background-color: #3a3a3e;
                color: #ff0033;
            }
        """)
        self.settings_btn.clicked.connect(self.open_settings_placeholder)
        bottom_layout.addWidget(self.settings_btn)
        
        bottom_layout.addStretch()
        
        self.user_bubble = QPushButton()
        self.user_bubble.setFixedHeight(40)
        self.user_bubble.setMinimumWidth(100)
        self.user_bubble.setCursor(Qt.CursorShape.PointingHandCursor)
        self.user_bubble.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.user_bubble.setToolTip("User Profile")
        self.user_bubble.setStyleSheet("""
            QPushButton {
                background-color: #ff0033;
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #cc0029;
            }
        """)

        self.user_bubble.clicked.connect(self.show_profile_info)        
        # self.user_bubble.clicked.connect(self.toggle_login)
        
        if self.user_profile.is_logged_in:
            self.user_bubble.setText(f"👤  {self.user_profile.username}")
        else:
            self.user_bubble.setText("👤  Guest")
        
        bottom_layout.addWidget(self.user_bubble)
        
        sidebar_layout.addWidget(bottom_widget)

    def toggle_login(self):
        if self.user_profile.is_logged_in:
            self.user_profile.logout()
            self.statusBar().showMessage("Logged out", 2000)
        else:
            login_dialog = LoginDialog(self)
            result = login_dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                username = login_dialog.get_username()
                password = login_dialog.get_password()
                if username and password:  # Both required
                    self.user_profile.set_user(username)
                    self.statusBar().showMessage(f"Welcome, {username}!", 3000)
                else:
                    QMessageBox.warning(self, "Login Failed", "Username and password required!")
            else:
                self.statusBar().showMessage("Login cancelled", 2000)
        
        self.update_user_profile_display()

    def open_settings_placeholder(self):
        QMessageBox.information(self, "Settings", 
            "Settings window will be implemented separately.\n\n"
            "This is a placeholder for future settings functionality.")

    def setup_chat_area(self):
        self.splitter = QSplitter(Qt.Orientation.Vertical)

        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.messages_area.setStyleSheet("""
            QScrollArea {
                background-color: #0a0e17;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2a2a2e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #ff0033;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #ff3366;
            }
        """)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setSpacing(15)
        self.messages_layout.addStretch()
        self.messages_area.setWidget(self.messages_container)

        input_widget = QWidget()
        input_widget.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                border-top: 1px solid #333333;
            }
        """)
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(15, 10, 15, 10)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Write message here...")
        self.message_input.setMaximumHeight(80)
        self.message_input.setFont(QFont("Segoe UI", 11))
        self.message_input.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 20px;
                padding: 10px 15px;
                color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #2a2a2e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #ff0033;
                border-radius: 4px;
            }
        """)

        input_layout.addWidget(self.message_input, 1)
        self.message_input.installEventFilter(self)

        self.add_doc_btn = QPushButton("📎")
        self.add_doc_btn.setFixedSize(40, 40)
        self.add_doc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_doc_btn.setToolTip("Add Document")
        self.add_doc_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #3a3a3e;
            }
        """)
        self.add_doc_btn.clicked.connect(self.add_document)
        input_layout.addWidget(self.add_doc_btn)

        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setToolTip("Send message (Enter)")
        self.send_btn.setAutoDefault(False)
        self.send_btn.setDefault(False)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0033;
                border: none;
                border-radius: 20px;
                font-size: 20px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #cc0029;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        self.scroll_btn = QPushButton("⬇️")
        self.scroll_btn.setFixedSize(40, 40)
        self.scroll_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scroll_btn.setToolTip("Scroll to bottom")
        self.scroll_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #3a3a3e;
            }
        """)
        self.scroll_btn.clicked.connect(self.scroll_to_end)
        self.scroll_btn.hide()
        button_layout.addWidget(self.scroll_btn)

        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(40, 40)
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.setToolTip("Speech to Text")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #3a3a3e;
                color: #ff0033;
            }
        """)
        self.mic_btn.clicked.connect(self.on_mic_clicked)
        button_layout.addWidget(self.mic_btn)

        input_layout.addWidget(button_container)

        self.splitter.addWidget(self.messages_area)
        self.splitter.addWidget(input_widget)
        self.splitter.setSizes([600, 150])

    def on_mic_clicked(self):
        self.statusBar().showMessage("Speech recognition will be implemented separately", 2000)

    def eventFilter(self, obj, event):
        if hasattr(self, 'message_input') and obj == self.message_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1f2a;
            }
        """)

    def on_scroll(self, value):
        max_val = self.messages_area.verticalScrollBar().maximum()
        if value >= max_val - 50:
            self.is_at_bottom = True
            self.scroll_btn.hide()
        else:
            self.is_at_bottom = False
            self.scroll_btn.show()

    def add_message(self, text, files=None, is_user=True):
        if text:
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        if len(self.current_session.messages) >= MAX_MESSAGES_PER_SESSION:
            oldest = self.current_session.messages.pop(0)
            if self.messages_layout.count() > 1:
                first_widget = self.messages_layout.itemAt(0)
                if first_widget and first_widget.widget():
                    first_widget.widget().deleteLater()
        
        msg_widget = MessageWidget(text, files or [], is_user, self, main_window=self)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, msg_widget)

        self.current_session.messages.append({
            'text': text,
            'files': files or [],
            'is_user': is_user,
            'timestamp': datetime.now()
        })

        if is_user and len([m for m in self.current_session.messages if m['is_user']]) == 1:
            name = text[:50] + ('...' if len(text) > 50 else '')
            if name.strip():
                self.current_session.name = name
                self.update_history_list()

        if self.is_at_bottom:
            QTimer.singleShot(50, self.scroll_to_end)

    def add_document(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Add Documents", "",
            "All Files (*.*);;Text Files (*.txt);;Images (*.png *.jpg);;PDF (*.pdf)"
        )
        
        if not file_paths:
            return
        
        valid_paths = []
        for path in file_paths:
            try:
                if not os.path.exists(path) or not os.path.isfile(path):
                    QMessageBox.warning(self, "File Not Found", f"File not found: {os.path.basename(path)}")
                    continue
                
                size = os.path.getsize(path)
                if size > MAX_FILE_SIZE:
                    QMessageBox.warning(self, "File Too Large", 
                        f"{os.path.basename(path)} exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit")
                    continue
                
                if size > LARGE_FILE_WARNING_THRESHOLD:
                    size_mb = size // (1024 * 1024)
                    reply = QMessageBox.question(self, "Large File", 
                        f"{os.path.basename(path)} is {size_mb}MB. Large files may affect performance. Continue?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        continue
                
                valid_paths.append(path)
            except (OSError, IOError) as e:
                QMessageBox.warning(self, "Error", f"Cannot access file: {e}")
                continue
        
        if not valid_paths:
            return
        
        if len(valid_paths) > MAX_PENDING_FILES:
            QMessageBox.warning(self, "Too Many Files", f"Cannot attach more than {MAX_PENDING_FILES} files")
            valid_paths = valid_paths[:MAX_PENDING_FILES]
        
        current_text = self.message_input.toPlainText()
        with self.pending_files_lock:
            self.pending_files.extend(valid_paths)
        
        file_names = [os.path.basename(f) for f in valid_paths]
        file_display = f"📎 {len(valid_paths)} file(s): {', '.join(file_names[:3])}{'...' if len(file_names) > 3 else ''}"
        
        if current_text.strip():
            display_text = current_text + "\n\n" + file_display
        else:
            display_text = file_display + "\n\n"
        
        self.message_input.setPlainText(display_text)
        self.message_input.moveCursor(QTextCursor.MoveOperation.End)

    def send_message(self):
        if hasattr(self, '_sending') and self._sending:
            return
        
        self._sending = True
        
        try:
            full_text = self.message_input.toPlainText()
            full_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', full_text)
            full_text = full_text.strip()
            
            if len(full_text) > MAX_MESSAGE_LENGTH:
                QMessageBox.warning(self, "Message Too Long", f"Message exceeds {MAX_MESSAGE_LENGTH} characters")
                return
            
            actual_message = ""
            files_to_send = []
            
            with self.pending_files_lock:
                if self.pending_files:
                    files_to_send = self.pending_files.copy()
                    self.pending_files = []
            
            if files_to_send:
                if full_text:
                    lines = full_text.split('\n')
                    text_lines = []
                    for line in lines:
                        if not line.startswith('📎'):
                            text_lines.append(line)
                    actual_message = '\n'.join(text_lines).strip()
                
                self.message_input.clear()
                self.add_message(actual_message, files=files_to_send, is_user=True)
                return
            
            if not full_text:
                return
            
            self.add_message(full_text, is_user=True)
            self.message_input.clear()
            
            response = f"I received your message: '{full_text}'\n\nThis is a placeholder response. The AI engine will be connected soon!"
            self.add_message(response, is_user=False)
            
        finally:
            QTimer.singleShot(200, lambda: setattr(self, '_sending', False))

    def scroll_to_end(self):
        scrollbar = self.messages_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.scroll_btn.hide()
        self.is_at_bottom = True

    def toggle_sidebar(self):
        if self.sidebar_collapsed:
            self.sidebar.animate_width(250)
            self.splitter_btn.setText("◀")
            self.sidebar_collapsed = False
        else:
            self.sidebar.animate_width(0)
            self.splitter_btn.setText("▶")
            self.sidebar_collapsed = True

    def show_logo_full(self, event):
        if self.logo_pixmap:
            viewer = ImageViewer(self.logo_pixmap, self)
            viewer.exec()

    def on_history_selected(self, item):
        session_id = item.data(Qt.ItemDataRole.UserRole)
        for session in self.sessions:
            if session.id == session_id:
                self.load_session(session)
                break
    
    def closeEvent(self, event):
        self.cleanup_temp_files()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())

