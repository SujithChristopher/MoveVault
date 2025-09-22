
import zipfile
import boto3
from botocore.exceptions import ClientError
import os

from core.logger import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, AWS_BUCKET_NAME, BASE_FOLDER
from core.s3_upload_worker import device_name

def extract_subject_name_from_gt3x(gt3x_path):
    try:
        with zipfile.ZipFile(gt3x_path, 'r') as zf:
            for name in zf.namelist():
                if name.lower().endswith("info.txt"):
                    with zf.open(name) as info_file:
                        content = info_file.read().decode()
                        subject_name = "Unknown"
                        serial_number = "Unknown"
                        for line in content.splitlines():
                            if line.startswith("Subject Name:"):
                                subject_name = line.split(":", 1)[1].strip()
                            elif line.lower().startswith("serial number:"):
                                serial_number = line.split(":", 1)[1].strip()
                        return subject_name, serial_number#subject id,device unique id(serialnumber)
    except Exception as e:
        print(f"Error extracting subject name from {gt3x_path}: {e}")
        return "Unknown", "Unknown"

def get_existing_subjects_from_s3():
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )

        response = s3_client.list_objects_v2(
            Bucket=AWS_BUCKET_NAME,
            Prefix=f"{BASE_FOLDER}/",
            Delimiter="/"
        )

        subjects = []
        if 'CommonPrefixes' in response:
            for prefix in response['CommonPrefixes']:
                subject = prefix['Prefix'].replace(f"{BASE_FOLDER}/", "").rstrip("/")
                if subject and subject != "logs":
                    subjects.append(subject)
        return sorted(subjects)
    except Exception as e:
        print(f"Error fetching existing subjects from S3: {e}")
        return []
    
