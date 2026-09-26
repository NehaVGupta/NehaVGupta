"""Storage abstraction. LocalStorageService is used by the prototype; S3/MinIO can replace it."""
import re
from abc import ABC, abstractmethod
from pathlib import Path

from app.utils.errors import UserError

_KEY = re.compile(r"^[A-Za-z0-9_\-./]+$")


class StorageService(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes) -> str: ...
    @abstractmethod
    def load(self, key: str) -> bytes: ...
    @abstractmethod
    def exists(self, key: str) -> bool: ...
    @abstractmethod
    def list(self, prefix: str) -> list[str]: ...
    @abstractmethod
    def delete(self, key: str) -> None: ...


class LocalStorageService(StorageService):
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not _KEY.match(key) or key.startswith("/") or ".." in key.split("/"):
            raise UserError("Invalid storage key.", "invalid_key")
        p = (self.root / key).resolve()
        if self.root not in p.parents:
            raise UserError("Invalid storage key.", "invalid_key")
        return p

    def save(self, key, data):
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return key

    def load(self, key):
        p = self._path(key)
        if not p.exists():
            raise UserError("The requested item was not found.", "not_found", 404)
        return p.read_bytes()

    def exists(self, key):
        return self._path(key).exists()

    def list(self, prefix):
        d = self._path(prefix.rstrip("/"))
        return sorted(f"{prefix.rstrip('/')}/{p.name}" for p in d.iterdir()) if d.exists() else []

    def delete(self, key):
        p = self._path(key)
        if p.exists():
            p.unlink()


class S3StorageService(StorageService):  # pragma: no cover - extension point
    """MinIO / AWS S3 adapter placeholder. Implement with boto3 (put_object/get_object/list_objects_v2)."""

    def __init__(self, *a, **k):
        raise NotImplementedError("S3/MinIO storage is a planned adapter; use STORAGE_BACKEND=local for the prototype.")
