from __future__ import annotations

import json
import uuid

# we use this simple wrapper for json to handle UUID serialization,
# as well as nested objects without requiring all of our json calls to include this


def serializer(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return obj.__dict__


def loads(data: str) -> dict:
    return json.loads(data)


def dumps(data: dict) -> str:
    return json.dumps(data, default=serializer, ensure_ascii=False)
