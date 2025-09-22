from PySide6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout,
    QLineEdit, QFileDialog, QGroupBox, QTextEdit, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QMenuBar, QMenu
)
from PySide6.QtGui import QFont, QTextCursor, QColor, QBrush, QAction
from PySide6.QtCore import Qt, QTimer
import os
from pathlib import Path

from core.logger import ApplicationLogger
from core.network_utils import is_internet_available
from core.s3_utils import extract_subject_name_from_gt3x, get_existing_subjects_from_s3
from core.email_utils import send_upload_report
from core.s3_upload_worker import S3UploadWorker, is_file_already_uploaded
from core.autoupdate import ApplicationUpdater
from ui.update_dialog import UpdateDialog
from ui.subject_mapping_dialog import SubjectMappingDialog
# AWS Config Dialog removed - credentials are now embedded in the executable
from version import __version__, __app_name__
class ActiGraphS3Uploader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__app_name__} v{__version__} - HomeClouds")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)

        self.selected_folder = ""
        self.file_data = []
        self.existing_subjects = []
        self.upload_worker = None

        self.logger = ApplicationLogger(self)
        self.updater = ApplicationUpdater(__version__)
        
        self.init_ui()
        self.init_network_timer()
        self.init_auto_update_check()

        self.logger.log_action("UI_INITIALIZED", "User interface initialized")

    def init_ui(self):
        # Create menu bar
        self.create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        header_layout = QHBoxLayout()
        title_label = QLabel("ActiGraph Files S3 Uploader")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addStretch(1)
        header_layout.addWidget(title_label, stretch=2)

        self.network_status_icon = QLabel()
        self.network_status_icon.setFixedSize(20, 20)
        self.network_status_icon.setAlignment(Qt.AlignRight)

        self.network_status_label = QLabel("Checking...")
        self.network_status_label.setStyleSheet("color: orange; font-weight: bold;")

        network_layout = QHBoxLayout()
        network_layout.setSpacing(5)
        network_layout.addWidget(self.network_status_icon)
        network_layout.addWidget(self.network_status_label)

        network_widget = QWidget()
        network_widget.setLayout(network_layout)

        header_layout.addWidget(network_widget)

        exit_button = QPushButton("Quit")
        exit_button.setMinimumSize(80, 30)
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        exit_button.clicked.connect(self.close)
        header_layout.addWidget(exit_button)
        main_layout.addLayout(header_layout)

        # Folder selection
        folder_group = QGroupBox("1. Select ActiGraph Files Folder")
        folder_layout = QHBoxLayout(folder_group)
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setReadOnly(True)
        self.select_folder_btn = QPushButton("Browse Folder")
        self.select_folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_path_edit)
        folder_layout.addWidget(self.select_folder_btn)
        main_layout.addWidget(folder_group)

         # Subject mapping
        self.mapping_btn = QPushButton("Check Subject Mapping")
        self.mapping_btn.setFixedSize(150, 28)
        self.mapping_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: black;
                font-weight: bold;
                border: 1px solid #E65100;
                border-radius: 4px;
                padding: 2px 6px;
            }
            QPushButton:disabled {
                background-color: #FFD180;
                color: #EEEEEE;
                border: 1px solid #FFB74D;
            }
            QPushButton:hover:!disabled {
                background-color: #FB8C00;
            }
        """)
        self.mapping_btn.setEnabled(False)
        self.mapping_btn.clicked.connect(self.check_subject_mapping)
        main_layout.addWidget(self.mapping_btn)

        # Files table
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["File Name", "Subject", "Size (MB)", "Status"])
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.files_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.files_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.files_table)

        # Upload buttons and progress
        upload_layout = QHBoxLayout()
        self.upload_btn = QPushButton("Start Upload")
        self.upload_btn.setFixedSize(120, 28)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: black;
                font-weight: bold;
                border: 1px solid #388E3C;
                border-radius: 4px;
                padding: 2px 6px;
            }
            QPushButton:disabled {
                background-color: #A5D6A7;
                color: #EEEEEE;
                border: 1px solid #81C784;
            }
            QPushButton:hover:!disabled {
                background-color: #43A047;
            }
        """)
        self.upload_btn.clicked.connect(self.start_upload)
        self.upload_btn.setEnabled(False)


        self.cancel_btn = QPushButton("Cancel Upload")
        self.cancel_btn.clicked.connect(self.cancel_upload)
        self.cancel_btn.setVisible(False)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        upload_layout.addWidget(self.upload_btn)
        upload_layout.addWidget(self.cancel_btn)
        upload_layout.addWidget(self.progress_bar)
        main_layout.addLayout(upload_layout)

        

        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        main_layout.addWidget(self.log_text)
        self.log_text.append("Application started")

    def check_and_enable_mapping(self):
        unique_subjects = {s for _, s, _, _ in self.file_data}
        self.existing_subjects = get_existing_subjects_from_s3()
        has_new_subjects = any(s not in self.existing_subjects for s in unique_subjects)
        self.mapping_btn.setEnabled(has_new_subjects)

    def check_subject_mapping(self):
        self.logger.log_action("SUBJECT_MAPPING", "Checking for unmapped subjects")
        mismatched = {}
        unique_subjects = {s for _, s, _, _ in self.file_data}
        self.existing_subjects = get_existing_subjects_from_s3()

        for subject in unique_subjects:
            if subject not in self.existing_subjects:
                mismatched[subject] = sum(1 for _, s, _, _ in self.file_data if s == subject)

        if mismatched:
            dialog = SubjectMappingDialog(mismatched, self.existing_subjects, self)
            if dialog.exec():
                mapping = dialog.get_mapping()
                if mapping:
                    for i, (file_path, subject, size, serial) in enumerate(self.file_data):
                        if subject in mapping:
                            self.file_data[i] = (file_path, mapping[subject], size, serial)
                    self.logger.log_action("MAPPING_APPLIED", "Mapping applied", str(mapping))
                    self.update_files_table()
                    self.logger.log_action("SUBJECT_MAPPING", "Subject mapping updated")
                    self.log_text.append("Subject mapping updated.")
        else:
            QMessageBox.information(self, "No Mapping Needed", "All subjects already exist in S3.")

    def init_network_timer(self):
        self.current_network_status = None
        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(self.update_network_status_if_changed)
        self.network_timer.start(10000)
        self.update_network_status_if_changed()

    def update_network_status_if_changed(self):
        new_status = is_internet_available()
        if new_status != getattr(self, "current_network_status", None):
            self.current_network_status = new_status
            if new_status:
                self.network_status_label.setText("✅--ONLINE--")
                self.network_status_label.setStyleSheet("color: green; font-weight: bold;")
                self.logger.log_action("NETWORK_STATUS", "ONLINE")
            else:
                self.network_status_label.setText("❌***OFFLINE***")
                self.network_status_label.setStyleSheet("color: red; font-weight: bold;")
                self.logger.log_action("NETWORK_STATUS", "OFFLINE")


    def closeEvent(self, event):
        try:
            self.logger.log_action("APPLICATION_CLOSING", "User requested application close")
            if self.logger.upload_log_to_s3():
                self.log_text.append("Session logs uploaded to S3 successfully")
            else:
                self.log_text.append("Warning: Failed to upload session logs to S3")
            self.logger.finalize_session()
        except Exception as e:
            print(f"Error during application close: {e}")
        event.accept()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path_edit.setText(folder)
            self.selected_folder = folder
            self.scan_files()

    def scan_files(self):
        self.file_data = []
        folder_path = Path(self.selected_folder)
        for file_path in folder_path.rglob("*.gt3x"):
            if file_path.is_file():
                subject_name, serial_number = extract_subject_name_from_gt3x(str(file_path))
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                self.file_data.append((str(file_path), subject_name, file_size, serial_number))
        self.update_files_table()

    def update_files_table(self):
        self.files_table.setRowCount(len(self.file_data))
        self.uploadable_files = []
        self.needtomap_files = []
        self.existing_subjects = get_existing_subjects_from_s3()
     

        for row, (file_path, subject_name, file_size, serial_number) in enumerate(self.file_data):
            self.files_table.setItem(row, 0, QTableWidgetItem(os.path.basename(file_path)))
            self.files_table.setItem(row, 1, QTableWidgetItem(subject_name))
            self.files_table.setItem(row, 2, QTableWidgetItem(f"{file_size:.2f}"))

            if subject_name not in self.existing_subjects:
                status = "NEEDS_MAPPING"
                # self.logger.log_action("MAPPING",f"STATUS-{subject_name}",{status})
                self.needtomap_files.append((file_path, subject_name, file_size, serial_number))
          
            #     # self.logger.log_action("MAPPING",f"STATUS-{subject_name}","Mapped")
            # elif is_file_already_uploaded(subject_name,os.path.basename(file_path),serial_number):
            #     status = "ALREADY_UPLOADED"
            else:
                status = "READY_TO_UPLOAD"
                self.uploadable_files.append((file_path, subject_name, file_size, serial_number))
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QBrush(Qt.white))
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)

            if status == "ALREADY_UPLOADED":
                status_item.setBackground(QBrush(QColor("green")))
            elif status == "NEEDS_MAPPING":
                status_item.setBackground(QBrush(QColor("red")))
            elif status == "READY_TO_UPLOAD":
                status_item.setBackground(QBrush(QColor("blue")))

            self.files_table.setItem(row, 3, status_item)
            # self.logger.log_action("FILE_STATUS", f"{file_path} -> {status}")

        self.upload_btn.setEnabled(bool(self.uploadable_files)and not bool(self.needtomap_files))
        self.check_and_enable_mapping()


    def start_upload(self):
        if not self.uploadable_files:
            QMessageBox.warning(self, "No Files to Upload", "Please select a folder containing .gt3x files to upload.")
            return

        self.upload_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.upload_worker = S3UploadWorker(self.uploadable_files, self.logger)
        self.upload_worker.progress_updated.connect(self.progress_bar.setValue)
        self.upload_worker.file_uploaded.connect(self.file_uploaded)
        self.upload_worker.upload_complete.connect(self.upload_finished)
        self.upload_worker.error_occurred.connect(self.upload_error)
        self.upload_worker.start()

    def cancel_upload(self):
        if self.upload_worker:
            self.upload_worker.cancel()
            self.log_text.append("Upload canceled by user.")
        self.reset_upload_ui()

    def file_uploaded(self, filename, subject_name, status, use_hand):
        self.log_text.append(f"[{subject_name}][{use_hand}] {filename}: {status}")
        for row in range(self.files_table.rowCount()):
            if self.files_table.item(row, 0).text() == filename:
                self.files_table.setItem(row, 3, QTableWidgetItem(status))
                break
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        

    def upload_finished(self, summary):
        self.log_text.append("\n" + "="*50)
        self.log_text.append(summary)
        self.logger.log_action("UPLOAD_COMPLETED","Upload summary",summary)
        QMessageBox.information(self, "Upload Complete", summary)
        
        #send email
        subject = "Upload Report - ActiGraph"
        send_upload_report(subject, summary)
        self.reset_upload_ui()

    def upload_error(self, error_message):
        self.log_text.append(f"\nERROR: {error_message}")
        QMessageBox.critical(self, "Upload Error", error_message)
        self.logger.log_action("UPLOAD_ERROR","Upload error details",error_message)
        self.reset_upload_ui()

    def reset_upload_ui(self):
        self.upload_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.progress_bar.setVisible(False)
        self.upload_btn.setEnabled(len(self.file_data) > 0)

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # Help menu (AWS configuration removed - credentials are embedded)
        help_menu = menubar.addMenu('Help')
        
        # Check for updates action
        check_updates_action = QAction('Check for Updates...', self)
        check_updates_action.triggered.connect(self.check_for_updates_manual)
        help_menu.addAction(check_updates_action)
        
        # About action
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_auto_update_check(self):
        """Initialize automatic update checking on startup."""
        # Check for updates 5 seconds after startup (non-intrusive)
        QTimer.singleShot(5000, self.check_for_updates_startup)

    def check_for_updates_startup(self):
        """Check for updates at startup (silent if no updates)."""
        if is_internet_available():
            try:
                update_info = self.updater.check_for_updates()
                if update_info:
                    self.show_update_dialog(update_info)
                self.logger.log_action("AUTO_UPDATE_CHECK", "Automatic update check performed at startup")
            except Exception as e:
                self.logger.log_action("UPDATE_CHECK_ERROR", f"Startup update check failed: {e}")

    def check_for_updates_manual(self):
        """Manually check for updates (show result message)."""
        if not is_internet_available():
            QMessageBox.warning(
                self,
                "No Internet Connection",
                "Please check your internet connection and try again."
            )
            return
        
        try:
            update_info = self.updater.check_for_updates()
            if update_info:
                self.show_update_dialog(update_info)
            else:
                QMessageBox.information(
                    self,
                    "No Updates",
                    f"You are running the latest version ({__version__})."
                )
            self.logger.log_action("MANUAL_UPDATE_CHECK", "Manual update check requested by user")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Update Check Failed",
                f"Could not check for updates:\n{str(e)}"
            )
            
    def show_update_dialog(self, update_info):
        """Show the update dialog."""
        dialog = UpdateDialog(update_info, self)
        dialog.exec()

    # AWS configuration removed - credentials are now embedded in the executable

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About",
            f"{__app_name__}\nVersion: {__version__}\n\n"
            f"A GUI application for uploading ActiGraph files to AWS S3 with "
            f"subject name mapping functionality.\n\n"
            f"Built with PySide6 and boto3."
        )
