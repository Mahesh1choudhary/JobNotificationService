# import os
# import time
# import argparse
# import logging
# from typing import List, Dict

# # imports the class from the existing module
# # from compress_greenhouse_clients import GreenhouseCompressor

# logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# def full_paths(resources_dir: str, filenames: List[str]) -> List[str]:
#     return [os.path.join(resources_dir, os.path.basename(f)) for f in filenames]


# def get_mtimes(paths: List[str]) -> Dict[str, float]:
#     mt = {}
#     for p in paths:
#         try:
#             mt[p] = os.path.getmtime(p)
#         except OSError:
#             mt[p] = 0.0
#     return mt


# def run_service(resources_dir: str, input_files: List[str], output_file: str, interval: float, once: bool):
#     inputs = full_paths(resources_dir, input_files)
#     # write output to parent of the resources directory (outside the service folder)
#     output_dir = os.path.abspath(os.path.join(resources_dir, os.pardir))
#     os.makedirs(output_dir, exist_ok=True)
#     output = os.path.join(output_dir, os.path.basename(output_file))
#     logging.info("Service starting. inputs=%s output=%s interval=%s once=%s", inputs, output, interval, once)

#     last_mtimes = get_mtimes(inputs)

#     # perform initial compression
#     compressor = GreenhouseCompressor(inputs)
#     try:
#         compressor.compress_to(output)
#         logging.info("Initial compression written to %s", output)
#         last_mtimes = get_mtimes(inputs)
#     except Exception as e:
#         logging.error("Initial compression failed: %s", e)

#     if once:
#         return

#     while True:
#         time.sleep(interval)
#         current_mtimes = get_mtimes(inputs)
#         changed = any(current_mtimes[p] != last_mtimes.get(p, 0.0) for p in inputs)
#         if changed:
#             logging.info("Change detected in inputs, recompressing...")
#             compressor = GreenhouseCompressor(inputs)
#             try:
#                 compressor.compress_to(output)
#                 logging.info("Recompression written to %s", output)
#                 last_mtimes = current_mtimes
#             except Exception as e:
#                 logging.error("Recompression failed: %s", e)


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Service to compress greenhouse client JSONs from resources folder.")
#     parser.add_argument("--resources", default="resources", help="Resources directory containing input files.")
#     parser.add_argument(
#         "--inputs",
#         nargs="+",
#         default=[
#             "resources/greenhouse_clients.json",
#             "resources/greenhouse_clients_page_1.json",
#         ],
#         help="Input filenames or paths (can be inside resources/)."
#     )
#     parser.add_argument("--output", default="greenhouse_clients_compressed.json", help="Output filename (will be placed outside the service/resources folder).")
#     parser.add_argument("--interval", type=float, default=10.0, help="Polling interval in seconds (ignored when --once).")
#     parser.add_argument("--once", action="store_true", help="Run one compression and exit.")
#     args = parser.parse_args()

#     run_service(args.resources, args.inputs, args.output, args.interval, args.once)


# class GreenhouseCompressor:
#     def __init__(self, input_paths: List[str]):
#         self.input_paths = input_paths

#     def _load_json(self, path: str) -> Dict[str, Any]:
#         with open(path, "r", encoding="utf-8") as f:
#             return json.load(f)

#     def extract_linkedin_entries(self) -> List[Dict[str, Any]]:
#         results = []
#         for path in self.input_paths:
#             if not os.path.isfile(path):
#                 # skip missing files
#                 continue
#             obj = self._load_json(path)
#             for i, entry in enumerate(obj.get("data", [])):
#                 # iterate with variable i
#                 linkedin = entry.get("linkedin_url")
#                 if linkedin:
#                     results.append({
#                         "source_file": os.path.basename(path),
#                         "index": i,
#                         "id": entry.get("id"),
#                         "name": entry.get("name"),
#                         "domain": entry.get("domain"),
#                         "linkedin_url": linkedin
#                     })
#         return results

#     def compress_to(self, output_path: str):
#         entries = self.extract_linkedin_entries()
#         # write compressed JSON
#         with open(output_path, "w", encoding="utf-8") as out:
#             json.dump({"data": entries}, out, indent=2, ensure_ascii=False)

