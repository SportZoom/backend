import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from supabase import create_client


def _supabase_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise ImproperlyConfigured(
            'SUPABASE_URL and SUPABASE_SERVICE_KEY must be set to upload product images.'
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def upload_product_image(uploaded_file):
    bucket = settings.SUPABASE_STORAGE_BUCKET
    suffix = Path(uploaded_file.name).suffix.lower()
    file_path = f"productos/{uuid.uuid4().hex}{suffix}"
    content_type = getattr(uploaded_file, 'content_type', 'application/octet-stream')

    uploaded_file.seek(0)
    client = _supabase_client()
    client.storage.from_(bucket).upload(
        file_path,
        uploaded_file.read(),
        file_options={
            'content-type': content_type,
            'upsert': 'false',
        },
    )
    return client.storage.from_(bucket).get_public_url(file_path)
