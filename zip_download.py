
import os
import sys
import json
import time
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.abspath(os.getcwd()))

from govinfo import GovInfo  # Assuming GovInfo is a custom library

# Constants
MAX_CONCURRENT_DOWNLOADS = 1000
MAX_RETRIES = 5
LOGS_FOLDER = "logs"
COLLECTION_CODE = "PPP"
DOWNLOAD_FOLDER = "zip/PPP"


def ensure_folder(folder_path):
    """Ensure the existence of a folder."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def download_file(url, package_id, folder_name, extension=".zip"):
    """
    Download the zipped folder from the given URL and save it in the specified folder.
    Retry up to MAX_RETRIES times if the download fails.
    """
    ensure_folder(folder_name)
    file_path = os.path.join(folder_name, f"{package_id}{extension}")
    if os.path.exists(file_path):
        return file_path

    for attempt in range(MAX_RETRIES):
        try:
            response = GovInfo.get_file(url)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return file_path
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(15)
                print(f"Retrying download for {package_id} (Attempt {attempt + 2})...")
            else:
                print(f"Failed to download {package_id} after {MAX_RETRIES} attempts: {e}")
    return None


def process_package(package, counters, output_file):
    """
    Process each package: fetch metadata and download the file if a zipLink exists.
    Updates counters and writes results to the output file incrementally.
    """
    package_id = package.get("packageid")
    url = package.get("packagelink")

    if not package_id or not url:
        counters["missing_packageid"] += 1
        result = {
            "packageid": package_id,
            "status": "ERROR",
            "message": "Missing packageid or packagelink"
        }
    else:
        try:
            # Fetch package metadata
            summary = GovInfo.package_data(package_id)

            # Check for zipLink and download file
            if "zipLink" in summary.get("download", {}):
                zip_link = summary["download"]["zipLink"]
                file_path = download_file(zip_link, package_id, "zip/PPP")
                if file_path:
                    counters["success"] += 1
                    result = {
                        "packageid": package_id,
                        "status": "SUCCESS",
                        "message": "Metadata fetched and file downloaded",
                        "file_path": file_path
                    }
                else:
                    counters["download_failed"] += 1
                    result = {
                        "packageid": package_id,
                        "status": "ERROR",
                        "message": "Failed to download file"
                    }
            else:
                counters["missing_ziplink"] += 1
                result = {
                    "packageid": package_id,
                    "status": "ERROR",
                    "message": "Missing or invalid zipLink in metadata"
                }
        except Exception as e:
            counters["http_errors"] += 1
            result = {
                "packageid": package_id,
                "status": "ERROR",
                "message": f"HTTP error: {str(e)}"
            }

    # Write result to file incrementally
    with open(output_file, "a") as outfile:
        outfile.write(json.dumps(result) + "\n")
    return result


def read_packages(filename):
    """
    Read package data from an input file.
    Each line is a JSON object, not comma-separated.
    """
    with open(filename, "r") as infile:
        for line in infile:
            yield json.loads(line.strip())



def download_collection(collection_code):
    """
    Download all packages in the specified collection.
    """
    try:
        input_file = f"collections/{collection_code}.txt"
        output_file = f"{LOGS_FOLDER}/{collection_code}_result.jsonl"
        ensure_folder(LOGS_FOLDER)

        results = []

        # Initialize counters
        counters = {
            "success": 0,
            "missing_packageid": 0,
            "missing_ziplink": 0,
            "download_failed": 0,
            "http_errors": 0
        }

        # Process packages line by line
        with open(output_file, "a") as outfile:
            for package in read_packages(input_file):
                try:
                    result = process_package(package, counters, output_file)
                    results.append(result)
                    outfile.write(json.dumps(result) + "\n")
                except Exception as e:
                    counters["download_failed"] += 1
                    error_result = {
                        "package": package,
                        "status": "failure",
                        "error": str(e)
                    }
                    results.append(error_result)
                    outfile.write(json.dumps(error_result) + "\n")

        # Update counters at the end of the file
        with open(output_file, "a") as outfile:
            outfile.write("\n" + json.dumps({"final_summary": counters}, indent=4))

        print(f"Processing completed. Results saved to {output_file}.")
    except Exception as e:
        print(f"Error processing collection {collection_code}: {str(e)}")
        sys.exit(1)

def main():
    """
    Main function to process specified collections.
    """
    download_collection(COLLECTION_CODE)


if __name__ == "__main__":
    main()
                          