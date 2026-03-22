import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ensure project root is on sys.path so we can import compress_greenhouse_clients
project_root = Path(__file__).resolve().parents[2]  # .../job_notification_service
sys.path.insert(0, str(project_root))

# from compress_greenhouse_clients import GreenhouseCompressor  # type: ignore


class GreenhouseCompressorService:
    def __init__(self, input_paths: List[str]):
        self.input_paths = input_paths

    def _load_json(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def extract_linkedin_entries(self) -> List[Dict[str, Any]]:
        results = []
        for path in self.input_paths:
            if not os.path.isfile(path):
                # skip missing files
                continue
            obj = self._load_json(path)
            for i, entry in enumerate(obj.get("data", [])):
                # iterate with variable i
                linkedin = entry.get("linkedin_url")
                if linkedin:
                    results.append({
                        "source_file": os.path.basename(path),
                        "index": i,
                        "id": entry.get("id"),
                        "name": entry.get("name"),
                        "domain": entry.get("domain"),
                        "linkedin_url": linkedin
                    })
        return results

    def compress_to(self, output_path: str):
        entries = self.extract_linkedin_entries()
        # determine final output path: if caller passed an absolute path, use it;
        # otherwise write into project_root so the output JSON lands at repo root.
        out_p = Path(output_path)
        if not out_p.is_absolute():
            out_p = project_root / out_p

        # ensure parent dirs exist
        # out_p.parent.mkdir(parents=True, exist_ok=True)

        # write compressed JSON
        with open(str(out_p), "w", encoding="utf-8") as out:
            json.dump({"data": entries}, out, indent=2, ensure_ascii=False)
        logging.info("Wrote compressed file: %s", out_p)


# class GreenhouseCompressorService:
#     """
#     Service wrapper around GreenhouseCompressor.

#     Usage:
#       svc = GreenhouseCompressorService(resources_dir="path/to/app_v1/resources")
#       await svc.compress(["greenhouse_clients.json", "greenhouse_clients_page_1.json"])
#     """

#     def __init__(self, resources_dir: str | Path | None = None):
#         if resources_dir is None:
#             resources_dir = Path(__file__).resolve().parents[1] / "resources"
#         self.resources_dir = Path(resources_dir)

#     async def compress(self, input_files: List[str], output_name: str = "greenhouse_clients_compressed.json") -> Path:
#         """
#         Compress the given input_files into <resources_dir>/<output_name>.

#         input_files may be absolute paths or filenames relative to resources_dir.
#         """
#         os.makedirs(self.resources_dir, exist_ok=True)

#         resolved_inputs: List[str] = []
#         for f in input_files:
#             p = Path(f)
#             if p.is_absolute():
#                 resolved_inputs.append(str(p))
#             elif p.parent == Path('.'):
#                 # treat as filename relative to resources_dir
#                 resolved_inputs.append(str(self.resources_dir / p.name))
#             else:
#                 # a relative path containing subdirs -> interpret relative to resources_dir
#                 resolved_inputs.append(str(self.resources_dir / p))

#         compressor = GreenhouseCompressor(resolved_inputs)
#         output_path = self.resources_dir / output_name
#         # call the existing synchronous API; keep method async for compatibility with other services
#         compressor.compress_to(str(output_path))
#         logging.info("Wrote compressed file: %s", output_path)
#         return output_path
