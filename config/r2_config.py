import os
from dotenv import load_dotenv

load_dotenv()


class R2Config:
    """Cấu hình Cloudflare R2"""

    ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
    ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
    SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
    BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "manga-storage")

    # R2 endpoint
    ENDPOINT_URL = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"
    PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

    @classmethod
    def validate(cls):
        required = ["ACCOUNT_ID", "ACCESS_KEY_ID", "SECRET_ACCESS_KEY"]
        missing = [key for key in required if not getattr(cls, key)]

        if missing:
            raise ValueError(f"Thiếu cấu hình R2: {', '.join(missing)}")

        return True
