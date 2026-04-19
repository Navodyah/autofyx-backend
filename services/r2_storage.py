import os
import re
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import boto3
from botocore.config import Config


class R2StorageService:
    def __init__(self) -> None:
        self.bucket_name = os.getenv("R2_BUCKET_NAME", "").strip()
        self.public_base_url = os.getenv("R2_PUBLIC_BASE_URL", "").strip().rstrip("/")
        account_id = os.getenv("R2_ACCOUNT_ID", "").strip()
        endpoint_url = os.getenv("R2_S3_clients", "").strip() or (
            f"https://{account_id}.r2.cloudflarestorage.com" if account_id else ""
        )

        if not self.bucket_name:
            raise RuntimeError("R2_BUCKET_NAME is not configured")
        if not self.public_base_url:
            raise RuntimeError("R2_PUBLIC_BASE_URL is not configured")
        if not endpoint_url:
            raise RuntimeError("R2_S3_clients or R2_ACCOUNT_ID is not configured")

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=os.getenv("R2_Access_Key_ID", "").strip(),
            aws_secret_access_key=os.getenv("R2_Secret_Access_Key", "").strip(),
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        name = Path(filename).name or "image"
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("._-")
        return name or "image"

    def build_vehicle_key(self, vehicle_id: int, filename: str) -> str:
        safe_filename = self._sanitize_filename(filename)
        return f"images/vehicles/{vehicle_id}/{uuid.uuid4().hex}-{safe_filename}"

    def public_url(self, key: str) -> str:
        return f"{self.public_base_url}/{key.lstrip('/')}"

    def upload_bytes(self, *, key: str, body: bytes, content_type: Optional[str]) -> str:
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=body,
            ContentType=content_type or "application/octet-stream",
        )
        return self.public_url(key)

    def delete_key(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket_name, Key=key)

    def extract_key_from_url(self, image_url: Optional[str]) -> Optional[str]:
        if not image_url:
            return None

        normalized_base = self.public_base_url.rstrip("/")
        normalized_url = image_url.rstrip("/")
        if normalized_url.startswith(f"{normalized_base}/"):
            return normalized_url[len(normalized_base) + 1 :]

        parsed_url = urlparse(image_url)
        if parsed_url.scheme and parsed_url.netloc:
            return parsed_url.path.lstrip("/") or None

        return image_url.lstrip("/") or None


r2_storage = R2StorageService()