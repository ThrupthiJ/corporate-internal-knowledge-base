import os
import io
import time
from datetime import datetime
from config import Config

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class BaseStorageProvider:
    def list_files(self, dept=None):
        raise NotImplementedError
    def upload_file(self, dept, filename, file_data, content_type='text/plain'):
        raise NotImplementedError
    def get_file(self, dept, filename):
        raise NotImplementedError
    def delete_file(self, dept, filename):
        raise NotImplementedError


class S3StorageProvider(BaseStorageProvider):
    def __init__(self, bucket_name, region_name):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.s3_client = boto3.client('s3', region_name=region_name)
        
    def list_files(self, dept=None):
        prefix = f"{dept}/" if dept else ""
        results = []
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            for item in response.get('Contents', []):
                key = item['Key']
                if key.endswith('/'):
                    continue
                parts = key.split('/', 1)
                file_dept = parts[0] if len(parts) > 1 else 'shared'
                name = parts[1] if len(parts) > 1 else parts[0]
                results.append({
                    'department': file_dept,
                    'filename': name,
                    'key': key,
                    'size': item['Size'],
                    'last_modified': item['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
                    'storage_tier': 'Amazon S3 Standard'
                })
        except Exception as e:
            print(f"[!] S3 list error: {e}")
        return results

    def upload_file(self, dept, filename, file_data, content_type='text/plain'):
        key = f"{dept}/{filename}"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=file_data,
            ContentType=content_type,
            ServerSideEncryption='AES256'
        )
        return key

    def get_file(self, dept, filename):
        key = f"{dept}/{filename}"
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return response['Body'].read(), response.get('ContentType', 'application/octet-stream')

    def delete_file(self, dept, filename):
        key = f"{dept}/{filename}"
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        return True


class LocalS3MirrorProvider(BaseStorageProvider):
    """
    Mirrors AWS S3 Object Storage bucket structure locally.
    Enforces identical prefix/folder isolation for demonstration and offline VM evaluation.
    """
    def __init__(self, base_dir, bucket_name):
        self.base_dir = base_dir
        self.bucket_name = bucket_name
        for dept in ['hr', 'it', 'sales', 'shared']:
            os.makedirs(os.path.join(self.base_dir, dept), exist_ok=True)

    def list_files(self, dept=None):
        results = []
        depts_to_scan = [dept] if dept else ['hr', 'it', 'sales', 'shared']
        for d in depts_to_scan:
            target_path = os.path.join(self.base_dir, d)
            if not os.path.exists(target_path):
                continue
            for fname in os.listdir(target_path):
                fpath = os.path.join(target_path, fname)
                if os.path.isfile(fpath):
                    stats = os.stat(fpath)
                    results.append({
                        'department': d,
                        'filename': fname,
                        'key': f"{d}/{fname}",
                        'size': stats.st_size,
                        'last_modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'storage_tier': f"S3-Emulated ({self.bucket_name})"
                    })
        return sorted(results, key=lambda x: x['last_modified'], reverse=True)

    def upload_file(self, dept, filename, file_data, content_type='text/plain'):
        target_dir = os.path.join(self.base_dir, dept)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, filename)
        with open(target_path, 'wb') as f:
            if isinstance(file_data, (bytes, bytearray)):
                f.write(file_data)
            else:
                f.write(file_data.read())
        return f"{dept}/{filename}"

    def get_file(self, dept, filename):
        target_path = os.path.join(self.base_dir, dept, filename)
        if not os.path.exists(target_path):
            return None, None
        with open(target_path, 'rb') as f:
            data = f.read()
        return data, 'application/octet-stream'

    def delete_file(self, dept, filename):
        target_path = os.path.join(self.base_dir, dept, filename)
        if os.path.exists(target_path):
            os.remove(target_path)
            return True
        return False


def get_storage():
    """
    Factory function returning the active storage engine.
    Tries AWS S3 first if configured; falls back to S3-Mirror Provider with full parity.
    """
    mode = Config.STORAGE_MODE
    if mode == 's3' and BOTO3_AVAILABLE:
        try:
            return S3StorageProvider(Config.S3_BUCKET_NAME, Config.AWS_REGION), "AWS S3 Cloud Object Storage"
        except Exception:
            pass

    # Default to Local S3 Mirror Provider
    return LocalS3MirrorProvider(Config.LOCAL_STORAGE_DIR, Config.S3_BUCKET_NAME), "Local S3 Mirror Storage Engine"
