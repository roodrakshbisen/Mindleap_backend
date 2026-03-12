"""
Supabase Storage integration for file uploads (e.g., resource hub videos, PDFs).

Usage:
    from app.services.storage import upload_file, get_public_url, delete_file
    
    # Upload a file
    path = upload_file(file_bytes, "resources/anxiety-guide.pdf", "application/pdf")
    
    # Get the public URL
    url = get_public_url("resources/anxiety-guide.pdf")
"""

from typing import Optional
from supabase import create_client, Client
from app.core.config import settings


def _get_storage_client() -> Client:
    """Create a Supabase client using the service role key (full access)."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env "
            "for storage operations."
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def upload_file(
    file_bytes: bytes,
    file_path: str,
    content_type: str = "application/octet-stream",
    bucket: Optional[str] = None,
) -> str:
    """
    Upload a file to Supabase Storage.

    Args:
        file_bytes: Raw file content.
        file_path: Path within the bucket (e.g., "videos/session1.mp4").
        content_type: MIME type of the file.
        bucket: Override the default bucket name.

    Returns:
        The storage path of the uploaded file.
    """
    client = _get_storage_client()
    target_bucket = bucket or settings.SUPABASE_STORAGE_BUCKET

    client.storage.from_(target_bucket).upload(
        path=file_path,
        file=file_bytes,
        file_options={"content-type": content_type},
    )
    return file_path


def get_public_url(
    file_path: str,
    bucket: Optional[str] = None,
) -> str:
    """
    Get the public URL for a file stored in Supabase Storage.

    Args:
        file_path: Path within the bucket.
        bucket: Override the default bucket name.

    Returns:
        Public URL string.
    """
    client = _get_storage_client()
    target_bucket = bucket or settings.SUPABASE_STORAGE_BUCKET
    res = client.storage.from_(target_bucket).get_public_url(file_path)
    return res


def delete_file(
    file_path: str,
    bucket: Optional[str] = None,
) -> None:
    """
    Delete a file from Supabase Storage.

    Args:
        file_path: Path within the bucket.
        bucket: Override the default bucket name.
    """
    client = _get_storage_client()
    target_bucket = bucket or settings.SUPABASE_STORAGE_BUCKET
    client.storage.from_(target_bucket).remove([file_path])
