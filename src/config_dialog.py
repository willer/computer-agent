from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QTextEdit, QComboBox, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QScreen
import json
import os
import qtawesome as qta

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setFixedWidth(500)
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # API Key Section
        api_layout = QVBoxLayout()
        api_label = QLabel("Anthropic API Key:")
        api_label.setStyleSheet("color: white; font-weight: bold;")
        
        # Create a read-only field for env var
        self.env_key_input = QLineEdit()
        self.env_key_input.setPlaceholderText("Environment variable: ANTHROPIC_API_KEY")
        self.env_key_input.setReadOnly(True)
        self.env_key_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 4px;
                color: #666;
            }
        """)
        
        # Create the editable field
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter new API key here...")
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                background-color: #262626;
                border: 1px solid #333;
                border-radius: 4px;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.env_key_input)
        api_layout.addWidget(self.api_key_input)
        layout.addLayout(api_layout)

        # System Prompt Section
        prompt_layout = QVBoxLayout()
        prompt_label = QLabel("Additional System Prompt:")
        prompt_label.setStyleSheet("color: white; font-weight: bold;")
        prompt_desc = QLabel("This will be added to the default system prompt")
        prompt_desc.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        self.system_prompt = QTextEdit()
        self.system_prompt.setStyleSheet("""
            QTextEdit {
                background-color: #262626;
                border: 1px solid #333;
                border-radius: 4px;
                color: white;
                padding: 8px;
            }
            QTextEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
        self.system_prompt.setFixedHeight(150)
        prompt_layout.addWidget(prompt_label)
        prompt_layout.addWidget(prompt_desc)
        prompt_layout.addWidget(self.system_prompt)
        layout.addLayout(prompt_layout)

        # Screen Selection
        screen_layout = QVBoxLayout()
        screen_label = QLabel("Test Screen:")
        screen_label.setStyleSheet("color: white; font-weight: bold;")
        self.screen_combo = QComboBox()
        self.screen_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                background-color: #262626;
                border: 1px solid #333;
                border-radius: 4px;
                color: white;
            }
            QComboBox:focus {
                border: 1px solid #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down-arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        
        # Get available screens using Qt's screen detection
        app = self.parent().window().app if self.parent() else None
        if app:
            screens = app.screens()
            for i, screen in enumerate(screens):
                geometry = screen.geometry()
                self.screen_combo.addItem(
                    f"Screen {i+1} ({geometry.width()}x{geometry.height()})"
                )
        
        screen_layout.addWidget(screen_label)
        screen_layout.addWidget(self.screen_combo)
        layout.addLayout(screen_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton(qta.icon('fa5s.save', color='white'), "Save")
        cancel_button = QPushButton(qta.icon('fa5s.times', color='white'), "Cancel")
        
        for button in (save_button, cancel_button):
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        
        cancel_button.setStyleSheet(cancel_button.styleSheet().replace("#4CAF50", "#ff4444").replace("#45a049", "#ff3333"))
        
        save_button.clicked.connect(self.save_config)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                border-radius: 8px;
            }
        """)

    def load_config(self):
        # Load current env var
        current_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.env_key_input.setText(current_key if current_key else "Not set")
        
        config_file = 'config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Don't set the API key input - leave it empty for new keys only
                self.system_prompt.setText(config.get('additional_system_prompt', ''))
                screen_index = config.get('screen_index', 0)
                if screen_index < self.screen_combo.count():
                    self.screen_combo.setCurrentIndex(screen_index)

    def save_config(self):
        new_api_key = self.api_key_input.text().strip()
        
        config = {
            'additional_system_prompt': self.system_prompt.toPlainText(),
            'screen_index': self.screen_combo.currentIndex()
        }
        
        # Only update API key if a new one was entered
        if new_api_key:
            config['api_key'] = new_api_key
            # Update environment variable
            os.environ['ANTHROPIC_API_KEY'] = new_api_key
            # Save to .env file
            with open('.env', 'w') as f:
                f.write(f'ANTHROPIC_API_KEY={new_api_key}')
        
        # Save to config file
        with open('config.json', 'w') as f:
            json.dump(config, f)
        
        self.accept()
