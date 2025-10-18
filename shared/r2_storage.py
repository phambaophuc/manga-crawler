from typing import Optional, Tuple
import boto3
from botocore.exceptions import ClientError
from config.r2_config import R2Config
from shared.logger import logging


class R2Storage:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        R2Config.validate()

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=R2Config.ENDPOINT_URL,
            aws_access_key_id=R2Config.ACCESS_KEY_ID,
            aws_secret_access_key=R2Config.SECRET_ACCESS_KEY,
            region_name="auto",
        )
        self.bucket_name = R2Config.BUCKET_NAME
        self.public_url = R2Config.PUBLIC_URL

    def upload_file(
        self, file_data: bytes, object_key: str, content_type: str = "image/webp"
    ) -> Tuple[bool, Optional[str]]:
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                ContentType=content_type,
                CacheControl="public, max-age=31536000",
            )

            public_url = f"{self.public_url}/{object_key}"
            self.logger.debug(f"✅ Uploaded: {object_key}")
            return True, public_url

        except ClientError as e:
            self.logger.error(f"❌ R2 upload error [{object_key}]: {e}")
            return False, None
        except Exception as e:
            self.logger.error(f"❌ Unexpected error [{object_key}]: {e}")
            return False, None

    def get_public_url(self, object_key: str) -> str:
        return f"{self.public_url}/{object_key}"
