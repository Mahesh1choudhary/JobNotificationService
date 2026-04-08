import hashlib


def compute_hash(description: str) -> str:
    return hashlib.sha256(description.encode("utf-8")).hexdigest()

