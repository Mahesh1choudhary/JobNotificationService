# ensure compressed greenhouse JSON is available at startup for other services
try:
    from .startup import ensure_compressed  # type: ignore
    # call without force so we avoid re-generating every import; will create file if missing
    ensure_compressed()
except Exception:
    # don't raise during package import; logging in startup already records failures
    pass
