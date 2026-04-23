import asyncio
from supabase import create_client, Client
from app.config import get_settings


class StorageService:
    def __init__(self):
        settings = get_settings()
        self._client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        self._bucket = settings.SUPABASE_BUCKET

    async def upload(self, file_key: str, file_bytes: bytes, mime_type: str) -> str:
        def _upload():
            self._client.storage.from_(self._bucket).upload(
                path=file_key,
                file=file_bytes,
                file_options={"content-type": mime_type, "upsert": "false"},
            )
        await asyncio.to_thread(_upload)
        return file_key

    async def download(self, file_key: str) -> bytes:
        def _download():
            return self._client.storage.from_(self._bucket).download(file_key)
        return await asyncio.to_thread(_download)

    async def delete(self, file_key: str) -> None:
        def _delete():
            self._client.storage.from_(self._bucket).remove([file_key])
        await asyncio.to_thread(_delete)
