import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

project_root = Path(__file__).resolve().parents[2]  # .../job_notification_service
sys.path.insert(0, str(project_root))

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
