"""JSON repository over StorageService.

Prototype persistence. The entity model for PostgreSQL/PostGIS lives in app/models/db.py
and is what a production deployment would use instead of this class.
"""
import json


class Repository:
    def __init__(self, storage):
        self.s = storage

    def put(self, kind, id_, obj):
        self.s.save(f"{kind}/{id_}.json", json.dumps(obj).encode())

    def get(self, kind, id_):
        return json.loads(self.s.load(f"{kind}/{id_}.json"))

    def exists(self, kind, id_):
        return self.s.exists(f"{kind}/{id_}.json")

    def list(self, kind):
        out = []
        for k in self.s.list(kind):
            try:
                out.append(json.loads(self.s.load(k)))
            except Exception:  # noqa: BLE001
                continue
        return sorted(out, key=lambda o: o.get("created", ""), reverse=True)
