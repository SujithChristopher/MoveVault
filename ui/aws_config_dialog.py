"""AWS Configuration Dialog for ActiGraph S3 Uploader."""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QFormLayout, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class AWSConfigDialog(QDialog):
    """Dialog for configuring AWS credentials and settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AWS Configuration")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        self.init_ui()
        self.load_existing_config()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("AWS S3 Configuration")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Configure your AWS credentials and S3 settings for uploading ActiGraph files.\n"
            "These credentials will be stored as environment variables for this session."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(desc_label)
        
        # AWS Credentials Group
        creds_group = QGroupBox("AWS Credentials")
        creds_layout = QFormLayout(creds_group)
        
        self.access_key_edit = QLineEdit()
        self.access_key_edit.setPlaceholderText("Your AWS Access Key ID")
        creds_layout.addRow("Access Key ID:", self.access_key_edit)
        
        self.secret_key_edit = QLineEdit()
        self.secret_key_edit.setEchoMode(QLineEdit.Password)
        self.secret_key_edit.setPlaceholderText("Your AWS Secret Access Key")
        creds_layout.addRow("Secret Access Key:", self.secret_key_edit)
        
        layout.addWidget(creds_group)
        
        # S3 Settings Group
        s3_group = QGroupBox("S3 Settings")
        s3_layout = QFormLayout(s3_group)
        
        self.bucket_edit = QLineEdit()
        self.bucket_edit.setPlaceholderText("S3 bucket name")
        s3_layout.addRow("Bucket Name:", self.bucket_edit)
        
        self.region_edit = QLineEdit()
        self.region_edit.setPlaceholderText("AWS region (e.g., us-east-1)")
        s3_layout.addRow("Region:", self.region_edit)
        
        self.base_folder_edit = QLineEdit()
        self.base_folder_edit.setPlaceholderText("Base folder in S3 (e.g., Ranipet)")
        s3_layout.addRow("Base Folder:", self.base_folder_edit)
        
        layout.addWidget(s3_group)
        
        # Test Connection Button
        test_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        test_layout.addStretch()
        test_layout.addWidget(self.test_btn)
        test_layout.addStretch()
        layout.addLayout(test_layout)
        
        # Dialog Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        button_box.accepted.connect(self.accept_config)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_existing_config(self):
        """Load existing configuration from environment variables."""
        self.access_key_edit.setText(os.getenv('AWS_ACCESS_KEY_ID', ''))
        self.secret_key_edit.setText(os.getenv('AWS_SECRET_ACCESS_KEY', ''))
        self.bucket_edit.setText(os.getenv('AWS_BUCKET_NAME', 'homerclouds'))
        self.region_edit.setText(os.getenv('AWS_REGION', 'us-east-1'))
        self.base_folder_edit.setText(os.getenv('AWS_BASE_FOLDER', 'Ranipet'))
    
    def test_connection(self):
        """Test the AWS connection with provided credentials."""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            access_key = self.access_key_edit.text().strip()
            secret_key = self.secret_key_edit.text().strip()
            region = self.region_edit.text().strip() or 'us-east-1'
            bucket = self.bucket_edit.text().strip()
            
            if not access_key or not secret_key:
                QMessageBox.warning(self, "Missing Credentials", 
                                  "Please enter both Access Key ID and Secret Access Key.")
                return
            
            if not bucket:
                QMessageBox.warning(self, "Missing Bucket", 
                                  "Please enter the S3 bucket name.")
                return
            
            # Test S3 connection
            s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Try to list bucket contents (this will validate credentials and bucket access)
            s3_client.head_bucket(Bucket=bucket)
            
            QMessageBox.information(self, "Connection Successful", 
                                  f"Successfully connected to S3 bucket '{bucket}' in region '{region}'.")
            
        except NoCredentialsError:
            QMessageBox.critical(self, "Authentication Failed", 
                               "Invalid AWS credentials. Please check your Access Key ID and Secret Access Key.")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                QMessageBox.critical(self, "Access Denied", 
                                   f"Access denied to bucket '{bucket}'. Please check your permissions.")
            elif error_code == '404':
                QMessageBox.critical(self, "Bucket Not Found", 
                                   f"Bucket '{bucket}' not found. Please check the bucket name.")
            else:
                QMessageBox.critical(self, "Connection Failed", 
                                   f"Failed to connect to AWS S3: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", 
                               f"Unexpected error: {str(e)}")
    
    def accept_config(self):
        """Accept and save the configuration."""
        access_key = self.access_key_edit.text().strip()
        secret_key = self.secret_key_edit.text().strip()
        bucket = self.bucket_edit.text().strip()
        region = self.region_edit.text().strip()
        base_folder = self.base_folder_edit.text().strip()
        
        if not access_key or not secret_key:
            QMessageBox.warning(self, "Missing Credentials", 
                              "Please enter both Access Key ID and Secret Access Key.")
            return
        
        if not bucket:
            QMessageBox.warning(self, "Missing Bucket", 
                              "Please enter the S3 bucket name.")
            return
        
        # Set environment variables for this session
        os.environ['AWS_ACCESS_KEY_ID'] = access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        os.environ['AWS_BUCKET_NAME'] = bucket
        os.environ['AWS_REGION'] = region or 'us-east-1'
        os.environ['AWS_BASE_FOLDER'] = base_folder or 'Ranipet'
        
        self.accept()
    
    def get_config(self):
        """Get the current configuration as a dictionary."""
        return {
            'access_key': self.access_key_edit.text().strip(),
            'secret_key': self.secret_key_edit.text().strip(),
            'bucket': self.bucket_edit.text().strip(),
            'region': self.region_edit.text().strip() or 'us-east-1',
            'base_folder': self.base_folder_edit.text().strip() or 'Ranipet'
        }