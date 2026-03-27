#!/usr/bin/env python3
"""
QZYNUX - Theme Manager
Handles dark/light themes, accent colors, and UI styling
"""

import json
import os
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt


class ThemeManager:
    """Central theme management for Qzynux GUI"""
    
    # Accent color options
    ACCENTS = {
        "red": "#ff0033",
        "blue": "#0066ff",
        "green": "#00cc66",
        "purple": "#aa66ff",
        "orange": "#ff6600",
        "cyan": "#00ccff"
    }
    
    # Theme colors
    THEMES = {
        "dark": {
            "window_bg": "#0a0e17",
            "sidebar_bg": "#1e1e2e",
            "chat_bg": "#0a0e17",
            "input_bg": "#2a2a2e",
            "bubble_user": "#8B0000",
            "bubble_ai": "#2a2a2e",
            "text_primary": "#ffffff",
            "text_secondary": "#cccccc",
            "border": "#333333",
            "scrollbar": "#ff0033",
            "button_bg": "#2a2a2e",
            "button_hover": "#3a3a3e",
            "new_chat_bg": "#2a2a2e",
            "settings_bg": "#2a2a2e"
        },
        "light": {
            "window_bg": "#f5f5f7",
            "sidebar_bg": "#e8e8ec",
            "chat_bg": "#f5f5f7",
            "input_bg": "#ffffff",
            "bubble_user": "#ff0033",
            "bubble_ai": "#e8e8ec",
            "text_primary": "#1a1a2e",
            "text_secondary": "#666666",
            "border": "#d0d0d4",
            "scrollbar": "#ff0033",
            "button_bg": "#ffffff",
            "button_hover": "#f0f0f4",
            "new_chat_bg": "#ffffff",
            "settings_bg": "#ffffff"
        }
    }
    
    def __init__(self):
        self.config_path = os.path.expanduser("~/.qzynux/theme_config.json")
        self.current_theme = "dark"
        self.current_accent = "red"
        self.load_config()
    
    def load_config(self):
        """Load saved theme preferences"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.current_theme = config.get("theme", "dark")
                    self.current_accent = config.get("accent", "red")
        except:
            pass
    
    def save_config(self):
        """Save theme preferences"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump({
                "theme": self.current_theme,
                "accent": self.current_accent
            }, f, indent=2)
    
    def set_theme(self, theme_name):
        """Set theme (dark/light)"""
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            self.save_config()
    
    def set_accent(self, accent_name):
        """Set accent color"""
        if accent_name in self.ACCENTS:
            self.current_accent = accent_name
            self.save_config()
    
    def get_accent_color(self):
        """Get current accent color hex"""
        return self.ACCENTS.get(self.current_accent, "#ff0033")
    
    def get_colors(self):
        """Get all colors for current theme"""
        colors = self.THEMES[self.current_theme].copy()
        colors["accent"] = self.get_accent_color()
        # Update scrollbar and button colors with accent
        colors["scrollbar"] = colors["accent"]
        return colors
    
    def apply_to_widget(self, widget, is_main_window=False):
        """Apply current theme to a widget"""
        colors = self.get_colors()
        accent = colors["accent"]
        
        if is_main_window:
            # Main window style
            widget.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {colors["window_bg"]};
                }}
                QScrollArea {{
                    background-color: {colors["chat_bg"]};
                    border: none;
                }}
                QScrollBar:vertical {{
                    background-color: {colors["sidebar_bg"]};
                    width: 10px;
                    border-radius: 5px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {accent};
                    border-radius: 5px;
                    min-height: 40px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: {accent}cc;
                }}
            """)
        else:
            # Generic widget style
            widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {colors["window_bg"]};
                    color: {colors["text_primary"]};
                }}
            """)
    
    def get_sidebar_style(self):
        """Get sidebar stylesheet"""
        colors = self.get_colors()
        accent = colors["accent"]
        return f"""
            QWidget {{
                background-color: {colors["sidebar_bg"]};
                border-right: 1px solid {colors["border"]};
            }}
            QPushButton {{
                background-color: {colors["button_bg"]};
                border: 1px solid {colors["border"]};
                border-radius: 20px;
                padding: 10px;
                color: {colors["text_primary"]};
            }}
            QPushButton:hover {{
                background-color: {colors["button_hover"]};
                border-color: {accent};
            }}
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 6px;
                color: {colors["text_secondary"]};
            }}
            QListWidget::item:selected {{
                background-color: {accent};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {colors["button_hover"]};
            }}
            QScrollBar:vertical {{
                background-color: {colors["sidebar_bg"]};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {accent};
                border-radius: 4px;
                min-height: 40px;
            }}
        """
    
    def get_chat_area_style(self):
        """Get chat area stylesheet"""
        colors = self.get_colors()
        accent = colors["accent"]
        return f"""
            QScrollArea {{
                background-color: {colors["chat_bg"]};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {colors["sidebar_bg"]};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {accent};
                border-radius: 5px;
                min-height: 40px;
            }}
        """
    
    def get_input_style(self):
        """Get input area stylesheet"""
        colors = self.get_colors()
        accent = colors["accent"]
        return f"""
            QTextEdit {{
                background-color: {colors["input_bg"]};
                border: 1px solid {colors["border"]};
                border-radius: 20px;
                padding: 10px 15px;
                color: {colors["text_primary"]};
            }}
            QTextEdit:focus {{
                border-color: {accent};
            }}
            QPushButton {{
                background-color: {colors["button_bg"]};
                border: 1px solid {colors["border"]};
                border-radius: 20px;
                font-size: 16px;
                color: {colors["text_primary"]};
            }}
            QPushButton:hover {{
                background-color: {colors["button_hover"]};
                border-color: {accent};
            }}
        """
    
    def get_message_bubble_style(self, is_user=True):
        """Get message bubble stylesheet"""
        colors = self.get_colors()
        if is_user:
            return f"""
                QLabel {{
                    background-color: {colors["bubble_user"]};
                    border: none;
                    border-radius: 12px;
                    padding: 10px 14px;
                    color: #ffffff;
                }}
            """
        else:
            return f"""
                QLabel {{
                    background-color: {colors["bubble_ai"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 12px;
                    padding: 10px 14px;
                    color: {colors["text_primary"]};
                }}
            """
    
    def get_button_style(self, button_type="default"):
        """Get button stylesheet"""
        colors = self.get_colors()
        accent = colors["accent"]
        
        if button_type == "new_chat":
            return f"""
                QPushButton {{
                    background-color: {colors["new_chat_bg"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 20px;
                    padding: 12px;
                    color: {colors["text_primary"]};
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {colors["button_hover"]};
                    border-color: {accent};
                }}
            """
        elif button_type == "settings":
            return f"""
                QPushButton {{
                    background-color: {colors["settings_bg"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 20px;
                    padding: 10px;
                    color: {colors["text_primary"]};
                }}
                QPushButton:hover {{
                    background-color: {colors["button_hover"]};
                    border-color: {accent};
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {colors["button_bg"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 20px;
                    padding: 8px 15px;
                    color: {colors["text_primary"]};
                }}
                QPushButton:hover {{
                    background-color: {colors["button_hover"]};
                    border-color: {accent};
                }}
            """


# Global theme manager instance
theme_manager = ThemeManager()