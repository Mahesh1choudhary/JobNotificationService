import json
import os
import argparse
from typing import List, Dict, Any


class GreenhouseCompressor:
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
        # write compressed JSON
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump({"data": entries}, out, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compress greenhouse client JSONs to extract linkedin_url fields.")
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "resources/greenhouse_clients.json",
            "resources/greenhouse_clients_page_1.json",
        ],
        help="Input JSON files (space separated)."
    )
    parser.add_argument(
        "--output",
        default="resources/greenhouse_clients_compressed.json",
        help="Output compressed JSON path."
    )
    args = parser.parse_args()

    compressor = GreenhouseCompressor(args.inputs)
    compressor.compress_to(args.output)
    print(f"Wrote compressed file: {args.output}")
