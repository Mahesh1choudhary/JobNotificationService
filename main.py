from pathlib import Path
import logging

# ensure the package is importable
from app_v1.startup import ensure_compressed  # type: ignore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main() -> None:
    # ensure compressed greenhouse JSON exists before other services start
    try:
        resources_dir = Path(__file__).resolve().parent / "app_v1" / "resources"
        ensure_compressed(resources_dir=resources_dir)
    except Exception:
        logger.exception("Failed to ensure greenhouse compressed file; continuing startup.")

    # ...existing code...
    # start your application (replace with your real startup logic)
    # e.g. import and start your web server, scheduler, workers, etc.
    # from app_v1.server import run_server
    # run_server()
    print("Application startup continues...")
    # ...existing code...


if __name__ == "__main__":
    main()
