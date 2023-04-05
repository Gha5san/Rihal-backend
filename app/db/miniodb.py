from minio import Minio

db_name = "minio-test-tmp"

client = Minio(
    "play.min.io",
    access_key="9aWNcZJObWlA9QLl",
    secret_key="rArfgmcEr4oSW2r7DAmYK2e7RRxwdxBn",
    secure=True
)

found = client.bucket_exists(db_name)
if not found:
    client.make_bucket(db_name)

def upload_file_minio(filepath, filename):
    client.fput_object(
        db_name, filename, filepath,
    )

def download_file_minio(filepath, filename):
    client.fget_object(
        db_name, filename, filepath
    )

def delete_file_minio(filename):
    client.remove_object(
        db_name, filename
    )