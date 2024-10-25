from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, 
                             QPushButton, QLabel, QProgressBar, QSystemTrayIcon, QMenu, QApplication)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QFontDatabase
import qtawesome as qta

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
        
        self.setWindowTitle("Grunty 👨🏽‍💻")
        self.setGeometry(100, 100, 350, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        self.setup_ui()
        self.setup_tray()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Title bar
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout()
        title_bar.setLayout(title_bar_layout)
        title_bar.setStyleSheet("background-color: #2C2C2C;")
        
        title_label = QLabel("Grunty 👨🏽‍💻")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_bar_layout.addWidget(title_label)
        
        title_bar_layout.addStretch()
        
        minimize_button = QPushButton(qta.icon('fa5s.window-minimize', color='white'), "")
        minimize_button.setFlat(True)
        close_button = QPushButton(qta.icon('fa5s.times', color='white'), "")
        close_button.setFlat(True)
        title_bar_layout.addWidget(minimize_button)
        title_bar_layout.addWidget(close_button)
        
        layout.addWidget(title_bar)
        
        # Input area
        self.input_area = QTextEdit()
        self.input_area.setPlaceholderText("What can I do for you today?")
        self.input_area.setStyleSheet("""
            QTextEdit {
                background-color: #3A3A3A;
                border: 1px solid #4A4A4A;
                border-radius: 5px;
                color: white;
                padding: 10px;
                font-size: 14px;
            }
        """)
        self.input_area.textChanged.connect(self.update_run_button)
        layout.addWidget(self.input_area)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.run_button = QPushButton(qta.icon('fa5s.play', color='white'), "Let's Go")
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #808080;
            }
        """)
        self.run_button.setEnabled(False)
        self.stop_button = QPushButton(qta.icon('fa5s.stop', color='white'), "Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #808080;
            }
        """)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.run_button)
        control_layout.addWidget(self.stop_button)
        layout.addLayout(control_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #4A4A4A;
                border-radius: 5px;
                background-color: #3A3A3A;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Action log
        self.action_log = QTextEdit()
        self.action_log.setReadOnly(True)
        self.action_log.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                border: 1px solid #4A4A4A;
                border-radius: 5px;
                color: #CCCCCC;
                padding: 10px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.action_log)
        
        # Connect signals
        self.run_button.clicked.connect(self.run_agent)
        self.stop_button.clicked.connect(self.stop_agent)
        minimize_button.clicked.connect(self.showMinimized)
        close_button.clicked.connect(self.close)
        
        # Set window background
        self.setStyleSheet("background-color: #333333;")
        
    def update_run_button(self):
        self.run_button.setEnabled(bool(self.input_area.toPlainText().strip()))
        
    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(qta.icon('fa5s.robot'))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
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
        self.update_log("Agent run completed.")
        
    def update_log(self, message):
        if message.startswith("Assistant:"):
            self.action_log.append(f'<p style="color: #4CAF50;"><strong>{message}</strong></p>')
        elif message.startswith("Assistant action:"):
            self.action_log.append(f'<p style="color: #2196F3;"><em>{message}</em></p>')
        else:
            self.action_log.append(f'<p>{message}</p>')
        
        # Scroll to the bottom of the log
        self.action_log.verticalScrollBar().setValue(self.action_log.verticalScrollBar().maximum())
        
    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()
        
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Grunty 👨🏽‍💻",
            "Application minimized to tray. Click the tray icon to restore.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
        
    def quit_application(self):
        self.tray_icon.hide()
        QApplication.quit()
