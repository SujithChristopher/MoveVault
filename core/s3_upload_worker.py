# core/s3_upload_worker.py
from PySide6.QtCore import QThread, Signal
import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError
from core.logger import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_BUCKET_NAME, AWS_REGION, BASE_FOLDER
from core.email_utils import send_upload_report
from botocore.config import Config
right_id = ["MOS2E19231076", 
            "MOS2E49240956",
            "MOS2E49240931",
            "MOS2E49240937",
            "MOS2E49240948",
            "MOS2E49240985",
            "MOS2E49240978",
            "MOS2E49240949",
	        "MOS2E49240871",
	        "MOS2E49240982",
	        "MOS2E49240916",
	        "MOS2E49240934"]
left_id = ["MOS2E50240763"
            ,"MOS2E50240769"
            ,"MOS2E50240770"
            ,"MOS2E50240761"
            ,"MOS2E50240771"
            ,"MOS2E50240754"
            ,"MOS2E50240768"
            ,"MOS2E50240756"
            ,"MOS2E49240899"
            ,"MOS2E49240890"
            ,"MOS2E46240317"
            ,"MOS2E49240927"
            ,"MOS2E49240942"]
device_name = "actilife"
class S3UploadWorker(QThread):
    progress_updated = Signal(int)
    file_uploaded = Signal(str, str, str, str)
    upload_complete = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, file_data, logger):
        super().__init__()
        self.file_data = file_data
        self.is_cancelled = False
        self.logger = logger

    def cancel(self):
        self.is_cancelled = True
        self.logger.log_action("UPLOAD_CANCELLED", "Upload process canceled by user")

    def run(self):
        try:
            config = Config(
                connect_timeout=120,
                read_timeout=300,
                retries={'max_attempts': 10, 'mode': 'standard'}
            )
            s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                region_name=AWS_REGION,
                config=config
            )

            total_files = len(self.file_data)
            uploaded_count = 0
            skipped_count = 0
            failed_files = []
            file_statuses = []

            for i, (file_path, subject_name, _, serial_number) in enumerate(self.file_data):
                if self.is_cancelled:
                    break

                file_name = os.path.basename(file_path)
                use_hand = 'Left' if serial_number not in right_id else 'Right'
                s3_key = f"{BASE_FOLDER}/{subject_name}/{device_name}/{use_hand}/{file_name}"

                try:
                    s3_client.head_object(Bucket=AWS_BUCKET_NAME, Key=s3_key)
                    skipped_count += 1
                    self.file_uploaded.emit(file_name, subject_name, "✓ Already uploaded (Skipped)", use_hand)
                    file_statuses.append(f"{file_name} - Skipped")
                except ClientError as e:
                    if int(e.response['Error']['Code']) == 404:
                        from boto3.s3.transfer import TransferConfig

                        config = TransferConfig(
                            multipart_threshold=50 * 1024 * 1024,  # 50 MB
                            multipart_chunksize=10 * 1024 * 1024,  # 10 MB
                            max_concurrency=5,
                            use_threads=True
                        )

                        s3_client.upload_file(file_path, AWS_BUCKET_NAME, s3_key, Config=config)

                        # s3_client.upload_file(file_path, AWS_BUCKET_NAME, s3_key)
                        uploaded_count += 1
                        self.file_uploaded.emit(file_name, subject_name, "✓ Uploaded", use_hand)
                        file_statuses.append(f"{file_name} - Uploaded")
                    else:
                        raise
                except Exception as e:
                    self.file_uploaded.emit(file_name, subject_name, f"✗ Failed: {str(e)}", use_hand)
                    failed_files.append(file_name)

                progress = int((i + 1) / total_files * 100)
                self.progress_updated.emit(progress)

            if not self.is_cancelled:
                summary = (
                    f"✓ Uploaded: {uploaded_count}\n→ Skipped: {skipped_count}\n✗ Failed: {len(failed_files)}\n\n"
                    + "\n".join(file_statuses)
                )
                self.upload_complete.emit(summary)
                

        except NoCredentialsError:
            error_msg = "AWS credentials error. Check credentials."
            self.error_occurred.emit(error_msg)
        except ClientError as e:
            self.error_occurred.emit(f"AWS Client Error: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")

def is_file_already_uploaded(subject_name, file_name,serial_number):
    s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                region_name=AWS_REGION
            )
    use_hand ="Left" if serial_number not in right_id else "Right"
    s3_key = f"{BASE_FOLDER}/{subject_name}/{device_name}/{use_hand}/{file_name}"
    # Debug: print(s3_key)
    try:
        s3_client.head_object(Bucket=AWS_BUCKET_NAME, Key=s3_key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        raise  # Let other errors bubble up