import boto3
import os
from dotenv import load_dotenv
import logging
from logging.handlers import TimedRotatingFileHandler

s3_logger = logging.getLogger("s3_upload_files")
s3_logger.setLevel(logging.INFO)

log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "log_upload_s3.log")
s3_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=7)
s3_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
s3_handler.setFormatter(formatter)
s3_logger.addHandler(s3_handler)

dotenv_path = 'plugins/.env'
load_dotenv(dotenv_path, override=True)


def upload_json_to_s3():
    session = boto3.Session(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
    )
    s3 = session.client('s3')
    bucket_name = os.environ.get("AWS_BUCKET_NAME")
    print(f'bucket_name: {bucket_name}')
    folder_path = 'files/'

    files = os.listdir(folder_path)

    for file in files:
        file_path = os.path.join(folder_path, file)
        s3.upload_file(file_path, bucket_name, file)
        logging.info(f'Uploaded {file} to S3 bucket {bucket_name}')

        os.remove(file_path)
        logging.info(f'Deleted {file}')
