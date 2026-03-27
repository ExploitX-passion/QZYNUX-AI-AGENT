#!/usr/bin/env python3
"""
QZYNUX - Settings Window
Part of Qzynux GUI module

This file is part of Qzynux GUI module, which is licensed under GPL v3.
See modules/gui/LICENSE.md for full license text.

Copyright (c) 2026 EXPLOITX PASSION.
"""


import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QPushButton, QComboBox, QFrame,
    QScrollArea, QMessageBox, QFileDialog, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PIL import Image

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from themes import theme_manager


class SettingsWindow(QDialog):
    # Add signals
    logout_signal = pyqtSignal()
    login_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings - QZYNUX")
        self.setMinimumSize(750, 650)
        self.setGeometry(250, 150, 800, 700)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #0a0e17;
            }
        """)

        self.logo = self.load_logo()
        self.parent_window = parent

        # Get user info from parent (chat_window)
        self.user_profile = None
        self.user_email = ""
        
        if parent and hasattr(parent, 'user_profile'):
            self.user_profile = parent.user_profile
            if hasattr(parent, 'user_email'):
                self.user_email = parent.user_email
            elif self.user_profile and self.user_profile.is_logged_in:
                # Generate default email from username
                self.user_email = f"{self.user_profile.username.lower()}@qzynux.local"

        self.setup_ui()
        self.load_current_settings()
        self.update_profile_display()

    def load_logo(self):
        logo_path = "/mnt/QZY/qzynux-ai/data/images/Exploitx_logo.png"
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img = img.resize((70, 70), Image.Resampling.LANCZOS)
                img.save("/tmp/qzynux_settings_logo.png")
                return QPixmap("/tmp/qzynux_settings_logo.png")
            except:
                pass
        return None

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === HEADER WITH LOGO ===
        header = QFrame()
        header.setFixedHeight(140)
        header.setStyleSheet("background-color: #1e1e2e; border-bottom: 1px solid #333333;")
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.logo:
            logo_label = QLabel()
            logo_label.setPixmap(self.logo)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(logo_label)

        title_label = QLabel("QZYNUX Settings")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ff0033;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        main_layout.addWidget(header)

        # === TABS ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { background-color: #0a0e17; border: none; }
            QTabBar::tab { background-color: #1e1e2e; padding: 10px 20px; margin-right: 2px; color: #cccccc; }
            QTabBar::tab:selected { background-color: #ff0033; color: white; }
            QTabBar::tab:hover { background-color: #3a3a3e; }
        """)

        self.setup_account_tab()
        self.setup_appearance_tab()
        self.setup_about_tab()
        self.setup_legal_tab()
        self.setup_developers_tab()

        self.tabs.addTab(self.tab_account, "👤 Account")
        self.tabs.addTab(self.tab_appearance, "🎨 Appearance")
        self.tabs.addTab(self.tab_about, "ℹ️ About")
        self.tabs.addTab(self.tab_legal, "📜 Legal")
        self.tabs.addTab(self.tab_dev, "👨‍💻 Developers")

        main_layout.addWidget(self.tabs)

        # === FOOTER ===
        footer = QFrame()
        footer.setFixedHeight(70)
        footer.setStyleSheet("background-color: #1e1e2e; border-top: 1px solid #333333;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)

        footer_layout.addStretch()

        # LOGOUT BUTTON
        self.logout_btn = QPushButton("🚪 Logout")
        self.logout_btn.setMinimumHeight(45)
        self.logout_btn.setMinimumWidth(150)
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                border: none;
                border-radius: 22px;
                padding: 10px 25px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff0033;
            }
        """)
        self.logout_btn.clicked.connect(self.logout_user)
        footer_layout.addWidget(self.logout_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(45)
        close_btn.setMinimumWidth(100)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 22px;
                padding: 10px 25px;
                color: white;
            }
            QPushButton:hover {
                background-color: #3a3a3e;
            }
        """)
        close_btn.clicked.connect(self.close)
        footer_layout.addWidget(close_btn)

        main_layout.addWidget(footer)

    def setup_account_tab(self):
        """Profile tab with IC on left, Username and Email in rounded card on right, with scrollable account info"""
        self.tab_account = QWidget()
        layout = QVBoxLayout(self.tab_account)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)

        # ========== TOP SECTION: Profile Card ==========
        profile_card = QFrame()
        profile_card.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 24px;
                border: 1px solid #2a2a2e;
            }
        """)
        profile_layout = QHBoxLayout(profile_card)
        profile_layout.setContentsMargins(35, 35, 35, 35)
        profile_layout.setSpacing(25)

        # Left side - Avatar (IC)
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(80, 80)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel {
                background-color: #ff0033;
                border-radius: 40px;
                font-size: 36px;
                font-weight: bold;
                color: white;
            }
        """)
        profile_layout.addWidget(self.avatar_label)

        # Right side - User Info Card (rounded background)
        user_info_card = QFrame()
        user_info_card.setStyleSheet("""
            QFrame {
                background-color: #2a2a2e;
                border-radius: 16px;
                border: 1px solid #3a3a3e;
            }
            QFrame > QLabel {
                border: none;
                background-color: transparent;
            }
        """)
        user_info_layout = QVBoxLayout(user_info_card)
        user_info_layout.setContentsMargins(20, 15, 20, 15)
        user_info_layout.setSpacing(5)

        # Username
        self.profile_username_label = QLabel()
        self.profile_username_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Normal))
        self.profile_username_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                border: none;
                background-color: transparent;
                padding: 0;
            }
        """)
        self.profile_username_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        user_info_layout.addWidget(self.profile_username_label)

        # Email
        self.profile_email_label = QLabel()
        self.profile_email_label.setFont(QFont("Segoe UI", 11))
        self.profile_email_label.setStyleSheet("""
            QLabel {
                color: #888888;
                border: none;
                background-color: transparent;
                padding: 0;
            }
        """)
        self.profile_email_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        user_info_layout.addWidget(self.profile_email_label)

        profile_layout.addWidget(user_info_card)
        profile_layout.addStretch()

        layout.addWidget(profile_card)

        # ========== BOTTOM SECTION: Account Information (with ScrollArea) ==========
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(180)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1e1e2e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #ff0033;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #ff6666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")

        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)

        # Account Information Card
        account_info_card = QFrame()
        account_info_card.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 16px;
                border: 1px solid #2a2a2e;
            }
            QFrame > QLabel {
                border: none;
                background-color: transparent;
            }
        """)
        account_info_layout = QVBoxLayout(account_info_card)
        account_info_layout.setContentsMargins(25, 20, 25, 20)
        account_info_layout.setSpacing(12)

        info_title = QLabel("Account Information")
        info_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        info_title.setStyleSheet("""
            QLabel {
                color: #ff0033;
                border: none;
                background-color: transparent;
                padding: 0;
            }
        """)
        account_info_layout.addWidget(info_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #2a2a2e; min-height: 1px;")
        account_info_layout.addWidget(sep)

        # Status
        self.status_label = QLabel()
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                border: none;
                background-color: transparent;
                padding: 5px 0;
            }
        """)
        self.status_label.setWordWrap(True)
        self.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        account_info_layout.addWidget(self.status_label)

        # Session
        self.session_label = QLabel()
        self.session_label.setFont(QFont("Segoe UI", 11))
        self.session_label.setStyleSheet("""
            QLabel {
                color: #888888;
                border: none;
                background-color: transparent;
                padding: 5px 0;
            }
        """)
        self.session_label.setWordWrap(True)
        self.session_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        account_info_layout.addWidget(self.session_label)

        # Info note
        info_note = QLabel(
            "ℹ️ Your account information is stored securely on your local device.\n"
            "No data is sent to external servers."
        )
        info_note.setWordWrap(True)
        info_note.setFont(QFont("Segoe UI", 15))
        info_note.setStyleSheet("color: #666666; padding-top: 8px;")
        info_note.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        account_info_layout.addWidget(info_note)

        scroll_layout.addWidget(account_info_card)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        layout.addStretch()

    def update_profile_display(self):
        """Update profile display with user info"""
        if self.user_profile and self.user_profile.is_logged_in:
            username = self.user_profile.username
            
            # Get email
            email = ""
            if self.parent_window and hasattr(self.parent_window, 'user_email'):
                email = self.parent_window.user_email
            else:
                email = f"{username.lower()}@qzynux.local"
            
            # Update avatar - show first letter
            self.avatar_label.setText(username[0].upper())
            self.avatar_label.setStyleSheet("""
                QLabel {
                    background-color: #ff0033;
                    border-radius: 40px;
                    font-size: 36px;
                    font-weight: bold;
                    color: white;
                }
            """)
            
            # Update username
            self.profile_username_label.setText(username)
            self.profile_username_label.setStyleSheet("color: #ffffff;")
            
            # Update email
            self.profile_email_label.setText(email)
            self.profile_email_label.setStyleSheet("color: #888888;")
            
            # Update account information
            self.status_label.setText("✅ Status: Logged In")
            self.status_label.setStyleSheet("color: #00ff00; padding: 5px 0;")
            self.session_label.setText("🔐 Session: Active")
            self.session_label.setStyleSheet("color: #888888; padding: 5px 0;")
            
        else:
            # Guest state
            self.avatar_label.setText("👤")
            self.avatar_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2e;
                    border-radius: 40px;
                    font-size: 36px;
                    color: #888888;
                }
            """)
            
            self.profile_username_label.setText("Guest")
            self.profile_username_label.setStyleSheet("color: #cccccc;")
            
            self.profile_email_label.setText("guest@qzynux.local")
            self.profile_email_label.setStyleSheet("color: #666666;")
            
            # Update account information
            self.status_label.setText("⚠️ Status: Not Logged In")
            self.status_label.setStyleSheet("color: #888888; padding: 5px 0;")
            self.session_label.setText("🔐 Session: Inactive")
            self.session_label.setStyleSheet("color: #888888; padding: 5px 0;")

    def setup_appearance_tab(self):
        self.tab_appearance = QWidget()
        layout = QVBoxLayout(self.tab_appearance)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # Theme selector
        theme_frame = QFrame()
        theme_frame.setStyleSheet("background-color: #1e1e2e; border-radius: 12px; padding: 15px;")
        theme_layout = QHBoxLayout(theme_frame)

        theme_label = QLabel("Theme:")
        theme_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        theme_label.setStyleSheet("color: white;")
        theme_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_combo.setStyleSheet("""
            QComboBox { background-color: #2a2a2e; border: 1px solid #3a3a3e; border-radius: 8px; padding: 8px 15px; color: white; }
        """)
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addWidget(theme_frame)

        # Accent color
        accent_frame = QFrame()
        accent_frame.setStyleSheet("background-color: #1e1e2e; border-radius: 12px; padding: 15px;")
        accent_layout = QHBoxLayout(accent_frame)

        accent_label = QLabel("Accent Color:")
        accent_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        accent_label.setStyleSheet("color: white;")
        accent_layout.addWidget(accent_label)

        self.accent_combo = QComboBox()
        self.accent_combo.addItems(["Red", "Blue", "Green", "Purple", "Orange", "Cyan"])
        self.accent_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.accent_combo.setStyleSheet("""
            QComboBox { background-color: #2a2a2e; border: 1px solid #3a3a3e; border-radius: 8px; padding: 8px 15px; color: white; }
        """)
        self.accent_combo.currentTextChanged.connect(self.on_accent_changed)
        accent_layout.addWidget(self.accent_combo)
        accent_layout.addStretch()
        layout.addWidget(accent_frame)

        # Font size
        font_frame = QFrame()
        font_frame.setStyleSheet("background-color: #1e1e2e; border-radius: 12px; padding: 15px;")
        font_layout = QHBoxLayout(font_frame)

        font_label = QLabel("Font Size:")
        font_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        font_label.setStyleSheet("color: white;")
        font_layout.addWidget(font_label)

        self.font_combo = QComboBox()
        self.font_combo.addItems(["Small", "Medium", "Large"])
        self.font_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.font_combo.setStyleSheet("""
            QComboBox { background-color: #2a2a2e; border: 1px solid #3a3a3e; border-radius: 8px; padding: 8px 15px; color: white; }
        """)
        font_layout.addWidget(self.font_combo)
        font_layout.addStretch()
        layout.addWidget(font_frame)

        layout.addStretch()

    def setup_about_tab(self):
        self.tab_about = QWidget()
        layout = QVBoxLayout(self.tab_about)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1e1e2e; border-radius: 12px; border: none;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        model_label = QLabel("QZYNUX AI Assistant")
        model_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        model_label.setStyleSheet("color: #ff0033;")
        model_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_layout.addWidget(model_label)

        version_label = QLabel("Version: 1.0.0")
        version_label.setFont(QFont("Segoe UI", 12))
        version_label.setStyleSheet("color: #cccccc;")
        version_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_layout.addWidget(version_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #333333;")
        content_layout.addWidget(sep)

        desc = QLabel(
            "Qzynux is a <b>privacy-first, dual-mode AI assistant</b> designed for "
            "security researchers, ethical hackers, and power users.<br><br>"
            "• Installed <b>locally</b> on your system <br>"
            "• Works offline AND online (dual-mode)<br>"
            "• Understands Hindi & English<br>"
            "• Controls terminals & security tools<br>"
            "• Never sends your data anywhere"
        )
        desc.setWordWrap(True)
        desc.setFont(QFont("Segoe UI", 11))
        desc.setStyleSheet("color: #ffffff;")
        desc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_layout.addWidget(desc)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def setup_legal_tab(self):
        self.tab_legal = QWidget()
        layout = QVBoxLayout(self.tab_legal)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(12)

        # Create a scroll area for legal documents
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1e1e2e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #ff0033;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #ff6666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Container for buttons
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)

        # Button style
        button_style = """
            QPushButton {
                background-color: #2a2a2e;
                border: 1px solid #3a3a3e;
                border-radius: 12px;
                padding: 12px 20px;
                text-align: left;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a3a3e;
            }
        """

        # README button
        self.readme_btn = QPushButton("📖 README")
        self.readme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.readme_btn.setStyleSheet(button_style)
        self.readme_btn.clicked.connect(self.show_readme)
        buttons_layout.addWidget(self.readme_btn)

        # NOTICE button
        self.notice_btn = QPushButton("📢 NOTICE")
        self.notice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notice_btn.setStyleSheet(button_style)
        self.notice_btn.clicked.connect(self.show_notice)
        buttons_layout.addWidget(self.notice_btn)

        # LICENSE button
        self.license_btn = QPushButton("📜 LICENSE")
        self.license_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.license_btn.setStyleSheet(button_style)
        self.license_btn.clicked.connect(self.show_license)
        buttons_layout.addWidget(self.license_btn)

        # COMMERCIAL LICENSE button
        self.pyqt_license_btn = QPushButton("⚖️ PYQT6-LICENSE")
        self.pyqt_license_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pyqt_license_btn.setStyleSheet(button_style)
        self.pyqt_license_btn.clicked.connect(self.show_pyqt_license)
        buttons_layout.addWidget(self.pyqt_license_btn)

        # COMMERCIAL LICENSE button
        self.comlicense_btn = QPushButton("💼 COMMERCIAL LICENSE")
        self.comlicense_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.comlicense_btn.setStyleSheet(button_style)
        self.comlicense_btn.clicked.connect(self.show_comLicense)
        buttons_layout.addWidget(self.comlicense_btn)

        # PRIVACY POLICY button
        self.privacy_btn = QPushButton("🔒 Privacy Policy")
        self.privacy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.privacy_btn.setStyleSheet(button_style)
        self.privacy_btn.clicked.connect(self.show_privacy_policy)
        buttons_layout.addWidget(self.privacy_btn)

        # TERMS AND CONDITIONS button
        self.terms_btn = QPushButton("📋 Terms and Conditions")
        self.terms_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.terms_btn.setStyleSheet(button_style)
        self.terms_btn.clicked.connect(self.show_terms)
        buttons_layout.addWidget(self.terms_btn)

        buttons_layout.addStretch()

        scroll_area.setWidget(buttons_container)
        layout.addWidget(scroll_area)

    def setup_developers_tab(self):
        self.tab_dev = QWidget()
        layout = QVBoxLayout(self.tab_dev)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        dev_frame = QFrame()
        dev_frame.setStyleSheet("""
            QFrame {
            background-color: #1e1e2e;
            border-radius: 12px;
            padding: 15px;
            }
        """)
        dev_layout = QVBoxLayout(dev_frame)

        creator_label = QLabel("Created by")
        creator_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        creator_label.setStyleSheet("color: #ff0033;")
        creator_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        dev_layout.addWidget(creator_label)

        name_label = QLabel("ExploitX Passion")
        name_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        name_label.setStyleSheet("color: white;")
        name_label.setWordWrap(True)  # Add this to wrap text if needed
        name_label.setMinimumHeight(40)  # Add minimum height
        name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        dev_layout.addWidget(name_label)

        firm_label = QLabel("Security Research & Development")
        firm_label.setFont(QFont("Segoe UI", 11))
        firm_label.setStyleSheet("color: #cccccc;")
        firm_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        dev_layout.addWidget(firm_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #333333; margin: 10px 0;")
        dev_layout.addWidget(sep)

        contact_label = QLabel("📧 Contact: exploitxpassion@proton.me")
        contact_label.setFont(QFont("Segoe UI", 11))
        contact_label.setStyleSheet("color: #cccccc;")
        contact_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        dev_layout.addWidget(contact_label)

        github_label = QLabel("🐙 GitHub: https://github.com/ExploitX-passion/QZYNUX-AI-AGENT")
        github_label.setFont(QFont("Segoe UI", 11))
        github_label.setStyleSheet("color: #cccccc;")
        github_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        dev_layout.addWidget(github_label)

        dev_layout.addStretch()
        layout.addWidget(dev_frame)

    def load_current_settings(self):
        self.theme_combo.setCurrentText("Dark" if theme_manager.current_theme == "dark" else "Light")
        accent_map = {"red": "Red", "blue": "Blue", "green": "Green",
                      "purple": "Purple", "orange": "Orange", "cyan": "Cyan"}
        self.accent_combo.setCurrentText(accent_map.get(theme_manager.current_accent, "Red"))
        self.font_combo.setCurrentText("Medium")

    def on_theme_changed(self, theme):
        theme_manager.set_theme(theme.lower())
        self.apply_theme_to_parent()

    def on_accent_changed(self, accent):
        accent_map = {"Red": "red", "Blue": "blue", "Green": "green",
                      "Purple": "purple", "Orange": "orange", "Cyan": "cyan"}
        theme_manager.set_accent(accent_map.get(accent, "red"))
        self.apply_theme_to_parent()

    def apply_theme_to_parent(self):
        if self.parent_window and hasattr(self.parent_window, 'apply_theme'):
            self.parent_window.apply_theme()

    def logout_user(self):
        """Logout: Clear session and shutdown Qzynux"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?\n\n"
            "Qzynux will shut down completely.\n"
            "You will need to login again to use Qzynux.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear session in parent window
            if self.parent_window and hasattr(self.parent_window, 'user_profile'):
                self.parent_window.user_profile.logout()
                
                # Clear session data
                if hasattr(self.parent_window, 'session_token'):
                    self.parent_window.session_token = None
                if hasattr(self.parent_window, 'isLoggedIn'):
                    self.parent_window.isLoggedIn = False
                
                # Save logout state
                if hasattr(self.parent_window, 'save_local_session'):
                    self.parent_window.clear_local_session()
            
            # Close settings window
            self.accept()
            
            # Shutdown Qzynux completely
            QTimer.singleShot(100, self.shutdown_qzynux)
    
    def shutdown_qzynux(self):
        """Shutdown the entire application"""
        if self.parent_window:
            self.parent_window.close()
        QApplication.quit()

    def show_readme(self):
        self.show_legal_file("README", "/mnt/QZY/qzynux-ai/docs/README.md")
    
    def show_notice(self):
        self.show_legal_file("NOTICE", "/mnt/QZY/qzynux-ai/docs/NOTICE.md")
    
    def show_license(self):
        self.show_legal_file("LICENSE", "/mnt/QZY/qzynux-ai/docs/LICENSE.md")

    def show_pyqt_license(self):
        self.show_legal_file("PyQt6 License & Qzynux", "/mnt/QZY/qzynux-ai/docs/PYQT6-LICENSE.md")

    def show_comLicense(self):
        self.show_legal_file("COMMERCIAL LICENSE", "/mnt/QZY/qzynux-ai/docs/COMMERCIAL-LICENSE.md")
    
    def show_privacy_policy(self):
        self.show_legal_file("Privacy Policy", "/mnt/QZY/qzynux-ai/docs/PRIVACYandPOLICY.md")

    def show_terms(self):
        self.show_legal_file("Terms and Conditions", "/mnt/QZY/qzynux-ai/docs/TERMSandCONDITIONS.md")

    def show_legal_file(self, title, filepath):
        content = "Document not available yet."
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                content = "Error reading document."

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(500, 400)
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        text = QLabel(content)
        text.setWordWrap(True)
        text.setFont(QFont("Segoe UI", 11))
        text.setStyleSheet("color: #cccccc; padding: 10px;")
        text.setTextFormat(Qt.TextFormat.PlainText)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        scroll = QScrollArea()
        scroll.setWidget(text)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1e1e2e; border-radius: 8px; border: none;")

        layout.addWidget(scroll)

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { background-color: #ff0033; border: none; border-radius: 20px; padding: 8px 20px; color: white; }
        """)
        close_btn.clicked.connect(dialog.close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SettingsWindow()
    win.show()
    sys.exit(app.exec())