from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, 
                             QPushButton, QLabel, QProgressBar, QSystemTrayIcon, QMenu, QApplication, QDialog, QLineEdit, QMenuBar, QTextBrowser)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QThread, QUrl
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QAction, QTextCursor, QDesktopServices
from .store import Store
from .anthropic import AnthropicClient  
import logging
import qtawesome as qta

logger = logging.getLogger(__name__)

class AgentThread(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, store):
        super().__init__()
        self.store = store

    def run(self):
        self.store.run_agent(self.update_signal.emit)
        self.finished_signal.emit()

class MainWindow(QMainWindow):
    def __init__(self, store, anthropic_client):
        super().__init__()
        self.store = store
        self.anthropic_client = anthropic_client
        self.app = QApplication.instance()  # Get the QApplication instance
        
        # Check if API key is missing
        if self.store.error and "ANTHROPIC_API_KEY not found" in self.store.error:
            self.show_api_key_dialog()
        
        self.setWindowTitle("Grunty 👨💻")
        self.setGeometry(100, 100, 400, 600)
        self.setMinimumSize(400, 500)  # Increased minimum size for better usability
        
        # Set rounded corners and border
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_tray()
        self.setup_shortcuts()
        
    def show_api_key_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("API Key Required")
        dialog.setFixedWidth(400)
        
        layout = QVBoxLayout()
        
        # Icon and title
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('fa5s.key', color='#4CAF50').pixmap(32, 32))
        title_layout.addWidget(icon_label)
        title_label = QLabel("Anthropic API Key Required")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        title_layout.addWidget(title_label)
        layout.addLayout(title_layout)
        
        # Description
        desc_label = QLabel("Please enter your Anthropic API key to continue. You can find this in your Anthropic dashboard.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(desc_label)
        
        # API Key input
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-ant-...")
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.api_key_input)
        
        # Save button
        save_btn = QPushButton("Save API Key")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(lambda: self.save_api_key(dialog))
        layout.addWidget(save_btn)
        
        dialog.setLayout(layout)
        dialog.exec()

    def save_api_key(self, dialog):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            return
            
        # Save to .env file
        with open('.env', 'w') as f:
            f.write(f'ANTHROPIC_API_KEY={api_key}')
            
        # Reinitialize the store and anthropic client
        self.store = Store()
        self.anthropic_client = AnthropicClient()
        dialog.accept()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with padding for shadow
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        central_widget.setLayout(main_layout)
        
        # Container widget for rounded corners
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: #1a1a1a;
                border-radius: 12px;
                border: 1px solid #333333;
            }
        """)
        container_layout = QVBoxLayout()
        container_layout.setSpacing(0)  # Remove spacing between elements
        container.setLayout(container_layout)
        
        # Title bar
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout()
        title_bar.setLayout(title_bar_layout)
        
        title_label = QLabel("Grunty 👨🏽‍💻")
        title_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff; padding: 5px;")
        title_bar_layout.addWidget(title_label)
        
        title_bar_layout.addStretch()
        
        # Window controls
        github_button = QPushButton()
        github_button.setIcon(qta.icon('fa5b.github', color='white'))  # Using qtawesome for GitHub icon
        github_button.setFlat(True)
        github_button.setStyleSheet("""
            QPushButton {
                color: #ffffff;
                background-color: transparent;
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        github_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/suitedaces/computer-agent')))
        
        config_button = QPushButton()
        config_button.setIcon(qta.icon('fa5s.cog', color='white'))
        config_button.setFlat(True)
        config_button.setStyleSheet("""
            QPushButton {
                color: #ffffff;
                background-color: transparent;
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        config_button.clicked.connect(self.show_config_dialog)
        
        minimize_button = QPushButton("—")
        minimize_button.setFlat(True)
        minimize_button.setStyleSheet("""
            QPushButton {
                color: #ffffff;
                background-color: transparent;
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        
        close_button = QPushButton("×")
        close_button.setFlat(True)
        close_button.setStyleSheet("""
            QPushButton {
                color: #ffffff;
                background-color: transparent;
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #ff4444;
            }
        """)
        
        title_bar_layout.addWidget(github_button)
        title_bar_layout.addWidget(config_button)
        title_bar_layout.addWidget(minimize_button)
        title_bar_layout.addWidget(close_button)
        container_layout.addWidget(title_bar)
        
        # Action log with modern styling - Now at the top with flexible space
        self.action_log = QTextBrowser()
        self.action_log.setReadOnly(True)
        self.action_log.setOpenExternalLinks(False)  # Prevent automatic link handling
        self.action_log.anchorClicked.connect(self.handle_link_click)  # Connect link clicks
        self.action_log.setStyleSheet("""
            QTextBrowser {
                background-color: #262626;
                border: none;
                border-radius: 0;
                color: #ffffff;
                padding: 16px;
                font-family: Inter;
                font-size: 13px;
            }
        """)
        container_layout.addWidget(self.action_log, stretch=1)  # Give it flexible space
        
        # Progress bar - Now above input area
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #262626;
                height: 2px;
                margin: 0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        self.progress_bar.hide()
        container_layout.addWidget(self.progress_bar)

        # Input section container - Fixed height at bottom
        input_section = QWidget()
        input_section.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border-top: 1px solid #333333;
            }
        """)
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(12)
        input_section.setLayout(input_layout)

        # Input area with modern styling
        self.input_area = QTextEdit()
        self.input_area.setPlaceholderText("What can I do for you today?")
        self.input_area.setFixedHeight(100)  # Fixed height for input
        self.input_area.setStyleSheet("""
            QTextEdit {
                background-color: #262626;
                border: 1px solid #333333;
                border-radius: 8px;
                color: #ffffff;
                padding: 12px;
                font-family: Inter;
                font-size: 14px;
                selection-background-color: #4CAF50;
            }
            QTextEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
        input_layout.addWidget(self.input_area)

        # Control buttons with modern styling
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)
        
        self.run_button = QPushButton(qta.icon('fa5s.play', color='white'), "Start")
        self.stop_button = QPushButton(qta.icon('fa5s.stop', color='white'), "Stop")
        
        for button in (self.run_button, self.stop_button):
            button.setFixedHeight(40)
            if button == self.run_button:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 0 24px;
                        font-family: Inter;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QPushButton:disabled {
                        background-color: #333333;
                        color: #666666;
                    }
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #ff4444;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 0 24px;
                        font-family: Inter;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ff3333;
                    }
                    QPushButton:disabled {
                        background-color: #333333;
                        color: #666666;
                    }
                """)
        
        control_layout.addWidget(self.run_button)
        control_layout.addWidget(self.stop_button)
        input_layout.addLayout(control_layout)

        # Add input section to main container
        container_layout.addWidget(input_section)

        # Add the container to the main layout
        main_layout.addWidget(container)
        
        # Set window shadow and background
        self.setStyleSheet("""
            MainWindow {
                background-color: transparent;
            }
            QWidget#container {
                background-color: #1a1a1a;
                border-radius: 12px;
                border: 1px solid #333333;
            }
        """)
        
        # Connect signals
        self.run_button.clicked.connect(self.run_agent)
        self.stop_button.clicked.connect(self.stop_agent)
        minimize_button.clicked.connect(self.showMinimized)
        close_button.clicked.connect(self.close)
        
    def update_run_button(self):
        self.run_button.setEnabled(bool(self.input_area.toPlainText().strip()))
        
    def setup_menu_bar(self):
        # Create menu bar
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Add actions
        new_task = QAction('New Task', self)
        new_task.setShortcut('Ctrl+N')
        new_task.triggered.connect(self.show)
        
        quit_action = QAction('Quit', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.quit_application)
        
        file_menu.addAction(new_task)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        # Make the icon larger and more visible
        icon = qta.icon('fa5s.robot', scale_factor=1.5, color='white')
        self.tray_icon.setIcon(icon)
        
        # Create the tray menu
        tray_menu = QMenu()
        
        # Add a title item (non-clickable)
        title_action = tray_menu.addAction("Grunty 👨🏽‍💻")
        title_action.setEnabled(False)
        tray_menu.addSeparator()
        
        # Add "New Task" option with icon
        new_task = tray_menu.addAction(qta.icon('fa5s.plus', color='white'), "New Task")
        new_task.triggered.connect(self.show)
        
        # Add "Show/Hide" toggle with icon
        toggle_action = tray_menu.addAction(qta.icon('fa5s.eye', color='white'), "Show/Hide")
        toggle_action.triggered.connect(self.toggle_window)
        
        tray_menu.addSeparator()
        
        # Add Quit option with icon
        quit_action = tray_menu.addAction(qta.icon('fa5s.power-off', color='white'), "Quit")
        quit_action.triggered.connect(self.quit_application)
        
        # Style the menu for dark mode
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #333333;
                color: white;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px 8px 8px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
            QMenu::separator {
                height: 1px;
                background: #444444;
                margin: 5px 0px;
            }
        """)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Show a notification when the app starts
        self.tray_icon.showMessage(
            "Grunty is running",
            "Click the robot icon in the menu bar to get started!",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
        
        # Connect double-click to toggle window
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window()

    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def run_agent(self):
        instructions = self.input_area.toPlainText()
        if not instructions:
            self.update_log("Please enter instructions before running the agent.")
            return
        
        self.store.set_instructions(instructions)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.show()
        self.action_log.clear()
        
        self.agent_thread = AgentThread(self.store)
        self.agent_thread.update_signal.connect(self.update_log)
        self.agent_thread.finished_signal.connect(self.agent_finished)
        self.agent_thread.start()
        
    def stop_agent(self):
        self.store.stop_run()
        self.stop_button.setEnabled(False)
        
    def agent_finished(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.hide()
        
        # Yellow completion message with sparkle emoji
        completion_message = '''
            <div style="margin: 6px 0;">
                <span style="
                    display: inline-flex;
                    align-items: center;
                    background-color: rgba(45, 45, 45, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 100px;
                    padding: 4px 12px;
                    color: #FFD700;
                    font-family: Inter, -apple-system, system-ui, sans-serif;
                    font-size: 13px;
                    line-height: 1.4;
                    white-space: nowrap;
                ">✨ Agent run completed</span>
            </div>
        '''
        self.action_log.append(completion_message)
        
        
    def update_log(self, message):
        if message.startswith("Performed action:"):
            action_text = message.replace("Performed action:", "").strip()
            
            try:
                import json
                action_data = json.loads(action_text)
                action_type = action_data.get('type', '').lower()
                
                if action_type == "type":
                    text = action_data.get('text', '')
                    msg = f'⌨️ <span style="margin: 0 4px; color: #4CAF50;">Typed</span> <span style="color: #4CAF50">"{text}"</span>'
                    self.action_log.append(self._format_pill(msg))
                    
                elif action_type == "key":
                    key = action_data.get('text', '')
                    msg = f'⌨️ <span style="margin: 0 4px; color: #4CAF50;">Pressed</span> <span style="color: #4CAF50">{key}</span>'
                    self.action_log.append(self._format_pill(msg))
                    
                elif action_type == "mouse_move":
                    x = action_data.get('x', 0)
                    y = action_data.get('y', 0)
                    msg = f'🖱️ <span style="margin: 0 4px; color: #4CAF50;">Moved to</span> <span style="color: #4CAF50">({x}, {y})</span>'
                    self.action_log.append(self._format_pill(msg))
                    
                elif action_type == "screenshot":
                    msg = '''
                        <div style="margin: 6px 0;">
                            <a href="screenshot://" style="
                                display: inline-flex;
                                align-items: center;
                                background-color: rgba(45, 45, 45, 0.95);
                                border: 1px solid rgba(255, 255, 255, 0.1);
                                border-radius: 100px;
                                padding: 4px 12px;
                                color: #4CAF50;
                                text-decoration: none;
                                font-family: Inter, -apple-system, system-ui, sans-serif;
                                font-size: 13px;
                                line-height: 1.4;
                                white-space: nowrap;
                            ">📸 View Screenshot</a>
                        </div>
                    '''
                    self.action_log.append(msg)
                    
                elif "click" in action_type:
                    x = action_data.get('x', 0)
                    y = action_data.get('y', 0)
                    click_map = {
                        "left_click": "Left Click",
                        "right_click": "Right Click",
                        "middle_click": "Middle Click",
                        "double_click": "Double Click"
                    }
                    click_type = click_map.get(action_type, "Click")
                    msg = f'👆 <span style="margin: 0 4px; color: #4CAF50;">{click_type}</span> <span style="color: #4CAF50">({x}, {y})</span>'
                    self.action_log.append(self._format_pill(msg))
                    
            except json.JSONDecodeError:
                self.action_log.append(self._format_pill(action_text))

        # Clean assistant message style without green background
        elif message.startswith("Assistant:"):
            message_style = '''
                <div style="
                    border-left: 2px solid #666;
                    padding: 8px 16px;
                    margin: 8px 0;
                    font-family: Inter, -apple-system, system-ui, sans-serif;
                    font-size: 13px;
                    line-height: 1.5;
                    color: #e0e0e0;
                ">{}</div>
            '''
            clean_message = message.replace("Assistant:", "").strip()
            self.action_log.append(message_style.format(f'💬 {clean_message}'))

        # Subtle assistant action style
        elif message.startswith("Assistant action:"):
            action_style = '''
                <div style="
                    color: #666;
                    font-style: italic;
                    padding: 4px 0;
                    font-size: 12px;
                    font-family: Inter, -apple-system, system-ui, sans-serif;
                    line-height: 1.4;
                ">🤖 {}</div>
            '''
            clean_message = message.replace("Assistant action:", "").strip()
            self.action_log.append(action_style.format(clean_message))

        # Regular message style
        else:
            regular_style = '''
                <div style="
                    padding: 4px 0;
                    color: #e0e0e0;
                    font-family: Inter, -apple-system, system-ui, sans-serif;
                    font-size: 13px;
                    line-height: 1.4;
                ">{}</div>
            '''
            self.action_log.append(regular_style.format(message))

        # Scroll to bottom
        self.action_log.verticalScrollBar().setValue(
            self.action_log.verticalScrollBar().maximum()
        )

    def _format_pill(self, text):
        return f'''
            <div style="margin: 6px 0;">
                <span style="
                    display: inline-flex;
                    align-items: center;
                    background-color: rgba(45, 45, 45, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 100px;
                    padding: 4px 12px;
                    font-family: Inter, -apple-system, system-ui, sans-serif;
                    font-size: 13px;
                    line-height: 1.4;
                    white-space: nowrap;
                ">{text}</span>
            </div>
        '''

    def show_screenshot(self, screenshot_data):
        if not screenshot_data:
            return
            
        # Create a new dialog to show the screenshot
        dialog = QDialog(self)
        dialog.setWindowTitle("Screenshot")
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
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
        
        # Create layout
        layout = QVBoxLayout()
        
        # Convert base64 to QPixmap
        import base64
        from PyQt6.QtGui import QPixmap
        pixmap_data = base64.b64decode(screenshot_data)
        pixmap = QPixmap()
        pixmap.loadFromData(pixmap_data)
        
        # Create label and set pixmap
        label = QLabel()
        label.setPixmap(pixmap)
        label.setStyleSheet("background-color: #262626; padding: 8px;")
        
        # Add to layout
        layout.addWidget(label)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec()

    def handle_link_click(self, url):
        if url.scheme() == "screenshot":
            self.show_screenshot(self.store.last_screenshot)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()
        
    def closeEvent(self, event):
        # Override close event to minimize to tray instead of quitting
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Grunty 👨🏽‍💻",
            "Application minimized to tray",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
        
    def quit_application(self):
        # Actually quit the application
        QApplication.quit()

    def pixmap_to_base64(self, pixmap):
        from PyQt6.QtCore import QByteArray, QBuffer
        import base64
        
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, 'PNG')
        
        return base64.b64encode(byte_array.data()).decode()

    def setup_shortcuts(self):
        # Essential shortcuts
        close_window = QShortcut(QKeySequence("Ctrl+W"), self)
        close_window.activated.connect(self.close)
        
        # Add Ctrl+C to stop agent
        stop_agent = QShortcut(QKeySequence("Ctrl+C"), self)
        stop_agent.activated.connect(self.stop_agent)
        
        # Add Ctrl+Enter to send message
        send_message = QShortcut(QKeySequence("Ctrl+Return"), self)
        send_message.activated.connect(self.run_agent)
        
        # Allow tab for indentation
        self.input_area.setTabChangesFocus(False)
        
        # Custom text editing handlers
        self.input_area.keyPressEvent = self.handle_input_keypress

    def handle_input_keypress(self, event):
        # Handle Ctrl + Enter to send message
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.run_agent()
            return
        
        # Get cursor and text
        cursor = self.input_area.textCursor()
        text = self.input_area.toPlainText()
        position = cursor.position()
        
        # Handle Ctrl + Backspace (delete entire line)
        if event.key() == Qt.Key.Key_Backspace and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Find the start and end of the current line
            line_start = text.rfind('\n', 0, position)
            line_start = line_start + 1 if line_start != -1 else 0
            line_end = text.find('\n', position)
            line_end = line_end if line_end != -1 else len(text)
            
            # Select and delete the entire line
            cursor.setPosition(line_start)
            cursor.setPosition(line_end, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            
            # Remove the extra newline if we're not at the start of the document
            if line_start > 0 and cursor.position() == line_start:
                cursor.deletePreviousChar()
        # Default handling for other keys
        else:
            QTextEdit.keyPressEvent(self.input_area, event)

    def show_config_dialog(self):
        from .config_dialog import ConfigDialog
        dialog = ConfigDialog(self)
        dialog.exec()

