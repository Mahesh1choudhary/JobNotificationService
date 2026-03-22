from pathlib import Path
import logging
from typing import Union

# import the service from the package
from service.greenhouse_compressor_service import GreenhouseCompressorService  # type: ignore

logger = logging.getLogger(__name__)


def ensure_compressed(resources_dir: Union[str, Path] | None = None, force: bool = False) -> Path:
    """
    Ensure compressed JSON exists at <resources_dir>/greenhouse_client_compressed.json.

    - resources_dir: optional path to app_v1/resources (defaults to package resources directory)
    - force: if True, always re-generate even if output exists
    Returns the Path to the output file.
    """
    if resources_dir is None:
        resources_dir = Path(__file__).resolve().parent / "resources"
    resources_dir = Path(resources_dir)

    input_files = [
        resources_dir / "greenhouse_clients.json",
        resources_dir / "greenhouse_clients_page_1.json",
    ]
    output_path = resources_dir / "greenhouse_client_compressed.json"

    if output_path.exists() and not force:
        logger.info("Compressed file already present, skipping: %s", output_path)
        return output_path

    # only pass input files that exist
    resolved_inputs = [str(p) for p in input_files if p.exists()]
    if not resolved_inputs:
        logger.warning("No greenhouse input files found under %s; skipping compression.", resources_dir)
        return output_path

    svc = GreenhouseCompressorService(resolved_inputs)
    print(output_path)
    try:
        svc.compress_to(str(output_path))
        logger.info("Wrote compressed file: %s", output_path)
    except Exception:
        logger.exception("Failed to write compressed greenhouse file: %s", output_path)
        raise
    return output_path
