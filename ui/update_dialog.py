"""
Update dialog for ActiGraph S3 Uploader application.
Simple dialog for handling application updates similar to mars_calibration.
"""

import sys
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QProgressBar, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from core.autoupdate import ApplicationUpdater
from version import __version__


class UpdateThread(QThread):
    """Thread for handling update download and installation."""
    
    progress_update = Signal(int)
    status_update = Signal(str)
    update_complete = Signal()
    update_failed = Signal(str)
    
    def __init__(self, update_info):
        super().__init__()
        self.update_info = update_info
        self.updater = ApplicationUpdater(__version__)
        
    def run(self):
        """Download and install the update."""
        try:
            self.status_update.emit("Downloading update...")
            
            # Download the update
            download_path = self.updater.download_update(
                self.update_info["download_url"],
                progress_callback=self.progress_update.emit
            )
            
            if not download_path:
                self.update_failed.emit("Failed to download update")
                return
                
            self.status_update.emit("Extracting update...")
            self.progress_update.emit(90)
            
            # Extract the update
            executable_path = self.updater.extract_and_prepare_update(download_path)
            
            if not executable_path:
                self.update_failed.emit("Failed to extract update")
                return
                
            self.status_update.emit("Installing update...")
            self.progress_update.emit(95)
            
            # Install the update
            if self.updater.install_update(executable_path):
                self.update_complete.emit()
            else:
                self.update_failed.emit("Failed to install update")
                
        except Exception as e:
            self.update_failed.emit(f"Update failed: {str(e)}")


class UpdateDialog(QDialog):
    """Dialog for displaying and handling application updates."""
    
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.update_thread = None
        
        self.setWindowTitle("Update Available")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the update dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"ActiGraph S3 Uploader v{self.update_info['version']} is available!")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Current version info
        current_label = QLabel(f"Current version: {__version__}")
        layout.addWidget(current_label)
        
        # Release notes
        notes_label = QLabel("Release Notes:")
        notes_font = QFont()
        notes_font.setBold(True)
        notes_label.setFont(notes_font)
        layout.addWidget(notes_label)
        
        self.release_notes = QTextEdit()
        self.release_notes.setPlainText(self.update_info.get("release_notes", "No release notes available."))
        self.release_notes.setMaximumHeight(150)
        self.release_notes.setReadOnly(True)
        layout.addWidget(self.release_notes)
        
        # Progress bar (hidden initially) 
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label (hidden initially)
        self.status_label = QLabel()
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.install_button = QPushButton("Install Update")
        self.install_button.clicked.connect(self.start_update)
        
        self.later_button = QPushButton("Later")
        self.later_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.later_button)
        button_layout.addWidget(self.install_button)
        
        layout.addLayout(button_layout)
        
    def start_update(self):
        """Start the update process."""
        # Hide buttons and show progress
        self.install_button.setEnabled(False)
        self.later_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        
        # Start update thread
        self.update_thread = UpdateThread(self.update_info)
        self.update_thread.progress_update.connect(self.progress_bar.setValue)
        self.update_thread.status_update.connect(self.status_label.setText)
        self.update_thread.update_complete.connect(self.on_update_complete)
        self.update_thread.update_failed.connect(self.on_update_failed)
        self.update_thread.start()
        
    def on_update_complete(self):
        """Handle successful update completion."""
        QMessageBox.information(
            self,
            "Update Complete",
            "The application will now restart with the new version."
        )
        # The updater will handle restarting the application
        sys.exit(0)
        
    def on_update_failed(self, error_message):
        """Handle update failure."""
        QMessageBox.critical(
            self,
            "Update Failed", 
            f"Failed to update the application:\n{error_message}"
        )
        
        # Re-enable buttons
        self.install_button.setEnabled(True)
        self.later_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)