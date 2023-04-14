from minio import Minio


class MinIOClient:

    def __init__(self, bucket_name):
        self.name = bucket_name

        # secure is false to overcome to avoid ssl error
        self.client = Minio(
            "miniodb:9000",
            access_key="root",
            secret_key="password",
            secure=False
        ) 
        found = self.client.bucket_exists(self.name)
        if not found:
            self.client.make_bucket(self.name)

    def upload_file(self, filepath, filename):
        self.client.fput_object(
            self.name, filename, filepath,
        )

    def download_file(self, filepath, filename):
        self.client.fget_object(
            self.name, filename, filepath
        )

    def delete_file(self, filename):
        self.client.remove_object(
            self.name, filename
        )

    def get_file_tmp(self, filname):
        return self.client.get_object(
            self.name, filname
        )


miniodb = MinIOClient("minio-test-tmp")