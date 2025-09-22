import os
import json
from datetime import datetime
import base64
import boto3
from botocore.exceptions import ClientError

# AWS credentials - try embedded file first, then environment variables, then fallback
def get_aws_credentials():
    """Get AWS credentials from embedded file, environment variables, or fallback."""
    # Try embedded credentials file first (for distributed executables)
    try:
        import sys
        if getattr(sys, 'frozen', False):
            # Running as executable, look for embedded credentials in PyInstaller temp directory
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller creates a temp folder and stores the path in _MEIPASS
                credentials_file = os.path.join(sys._MEIPASS, '.credentials')
            else:
                # Fallback to executable directory
                app_dir = os.path.dirname(sys.executable)
                credentials_file = os.path.join(app_dir, '.credentials')
        else:
            # Running as script, look in current directory
            credentials_file = '.credentials'
            
        if os.path.exists(credentials_file):
            with open(credentials_file, 'r') as f:
                credentials = json.load(f)
                
                # Extract all credentials
                access_key = credentials.get('aws_access_key_id')
                secret_key = credentials.get('aws_secret_access_key')
                bucket_name = credentials.get('aws_bucket_name', 'homerclouds')
                region = credentials.get('aws_region', 'us-east-1')
                base_folder = credentials.get('base_folder', 'Ranipet')
                
                if access_key and secret_key:
                    return access_key, secret_key, bucket_name, region, base_folder
    except Exception as e:
        print(f"Failed to load embedded credentials: {e}")
    
    # Try environment variables as fallback
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('AWS_BUCKET_NAME', 'homerclouds')
    region = os.getenv('AWS_REGION', 'us-east-1')
    base_folder = os.getenv('AWS_BASE_FOLDER', 'Ranipet')
    
    if access_key and secret_key:
        return access_key, secret_key, bucket_name, region, base_folder
    
    # Return placeholder values if nothing is configured
    return "YOUR_ACCESS_KEY_HERE", "YOUR_SECRET_KEY_HERE", "homerclouds", "us-east-1", "Ranipet"

AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_BUCKET_NAME, AWS_REGION, BASE_FOLDER = get_aws_credentials()


class ApplicationLogger:
    def __init__(self, app_instance):
        self.app_instance = app_instance
        self.local_log_file = None
        self.session_start_time = datetime.now()
        self.session_id = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        self.s3_log_key = f"{BASE_FOLDER}/logs/actigraph_uploader_log.txt"
        self.init_local_log()

    def init_local_log(self):
        log_dir = os.path.join("actigraph_uploader_logs")
        os.makedirs(log_dir, exist_ok=True)
        log_filename = f"session_{self.session_id}.log"
        self.local_log_file = os.path.join(log_dir, log_filename)
        with open(self.local_log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== ActiGraph S3 Uploader Session Log ===\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Start Time: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Target S3 Bucket: {AWS_BUCKET_NAME}\n")
            f.write(f"Base Folder: {BASE_FOLDER}\n")
            f.write("="*50 + "\n\n")
        self.log_action("APPLICATION_START", "ActiGraph S3 Uploader started")
        self.test_aws_connection()

    def log_action(self, action_type, description, details=None):
        if not self.local_log_file:
            return
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.local_log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {action_type}: {description}\n")
            if details:
                f.write(f"  Details: {json.dumps(details, indent=2)}\n")
            f.write("\n")
        if hasattr(self.app_instance, 'log_text'):
            self.app_instance.log_text.append(f"[LOG] {action_type}: {description}")

    def test_aws_connection(self):
        """Test AWS S3 connection and log the result."""
        try:
            if AWS_ACCESS_KEY == "YOUR_ACCESS_KEY_HERE":
                self.log_action("AWS_CONNECTION", "No AWS credentials configured - using placeholder values")
                return False
            
            s3_client = boto3.client('s3',
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                region_name=AWS_REGION
            )
            
            # Test connection by checking if bucket exists and is accessible
            s3_client.head_bucket(Bucket=AWS_BUCKET_NAME)
            self.log_action("AWS_CONNECTION", "Successfully connected to HomerClouds S3", {
                "bucket": AWS_BUCKET_NAME,
                "region": AWS_REGION,
                "base_folder": BASE_FOLDER
            })
            
            # Display in UI if available
            if hasattr(self.app_instance, 'log_text'):
                self.app_instance.log_text.append("Connected to HomerClouds")
            
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            self.log_action("AWS_CONNECTION", f"Failed to connect to HomerClouds S3: {error_code}", str(e))
            
            if hasattr(self.app_instance, 'log_text'):
                self.app_instance.log_text.append(f"HomerClouds connection failed: {error_code}")
            
            return False
            
        except Exception as e:
            self.log_action("AWS_CONNECTION", f"AWS connection error: {str(e)}")
            
            if hasattr(self.app_instance, 'log_text'):
                self.app_instance.log_text.append(f"HomerClouds connection error: {str(e)}")
            
            return False

    def upload_log_to_s3(self):
        if not self.local_log_file or not os.path.exists(self.local_log_file):
            return False
        try:
            s3_client = boto3.client('s3',
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                region_name=AWS_REGION
            )
            with open(self.local_log_file, 'r', encoding='utf-8') as f:
                current_log = f.read()
            try:
                response = s3_client.get_object(Bucket=AWS_BUCKET_NAME, Key=self.s3_log_key)
                existing_log = response['Body'].read().decode('utf-8')
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchKey':
                    raise
                existing_log = ""
            combined_log = existing_log + "\n" + ("="*80) + "\n" + current_log
            s3_client.put_object(Bucket=AWS_BUCKET_NAME, Key=self.s3_log_key,
                                 Body=combined_log.encode('utf-8'), ContentType='text/plain')
            session_log_key = f"{BASE_FOLDER}/logs/session_{self.session_id}.log"
            s3_client.put_object(Bucket=AWS_BUCKET_NAME, Key=session_log_key,
                                 Body=current_log.encode('utf-8'), ContentType='text/plain')
            self.log_action("LOG_UPLOAD", "Successfully uploaded session log to S3", {
                "s3_key": self.s3_log_key,
                "session_log_key": session_log_key
            })
            return True
        except Exception as e:
            self.log_action("LOG_UPLOAD_ERROR", f"Failed to upload log to S3: {str(e)}")
            return False

    def finalize_session(self):
        end_time = datetime.now()
        duration = end_time - self.session_start_time
        self.log_action("APPLICATION_END", "Uploader session ended", {
            "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_seconds": int(duration.total_seconds()),
            "duration_formatted": str(duration)
        })
        return self.upload_log_to_s3()