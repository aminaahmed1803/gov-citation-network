import os
import requests
import sys
import logging

sys.path.append(os.path.abspath('../'))

from dirstats import DirStats
from govinfo import GovInfo

BASE_URL = 'https://api.govinfo.gov/'
header_key = {'X-Api-key': 'ARqzwi0cCCjsdpdoeVv2Iv4I0FbhTVoSo7urYs1e'}

def ensure_folder(folder_path):
    """Ensure the existence of a folder."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def write_error(folder_path, error_message):
    """Write an error message to info.txt."""
    info_file = os.path.join(folder_path, "info.txt")
    with open(info_file, "w") as f:
        f.write(f"{error_message}\n")

def download_file(url, package_id, extension, folder_name):
    """
    Download the file from the given URL and save it locally.
    """
    try:
        # Ensure the folder exists
        ensure_folder(folder_name)

        file_path = os.path.join(folder_name, f"{package_id}{extension}")
        
        # Check if the file already exists
        if os.path.exists(file_path):
            return file_path

        response = GovInfo.get_file(url)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return file_path

    except requests.exceptions.RequestException as e:
        logging.error(f"Error during file download. URL: {url}, Error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error while downloading file. URL: {url}, Error: {str(e)}")
        return None

def download_collection(code, package_count):
    """
    Download all files for the given collection code.
    Ensure XML and PDF versions exist in their respective directories.
    """
    try:
        # Fetch data for the collection
        df = GovInfo.gpo_collections(collection=code, start_date="0000-00-00T00:00:00Z", api_key=header_key['X-Api-key'])

        # Ensure the DataFrame is valid
        if df is None or df.empty:
            return

        # Directories for XML and PDF files
        xml_folder = os.path.join("xml", code)
        pdf_folder = os.path.join("pdf", code)
        ensure_folder(xml_folder)
        ensure_folder(pdf_folder)

        # Check existing files
        xml_file_count = DirStats.count_xml_files(xml_folder)
        pdf_file_count = DirStats.count_pdf_files(pdf_folder)

        if xml_file_count == package_count and pdf_file_count == package_count:
            return

        # Iterate over each row in the DataFrame
        for _, row in df.iterrows():
            package_id = row['packageid']

            try:
                # Fetch package data
                summary = GovInfo.package_data(package_id)

                # Download XML file
                if "modsLink" in summary['download']:
                    download_file(summary['download']['modsLink'], package_id, ".mods.xml", xml_folder)
                elif "xmlLink" in summary['download']:
                    download_file(summary['download']['xmlLink'], package_id, ".xml", xml_folder)
                else:
                    error_message = f"No valid XML download links found for package ID: {package_id}."
                    write_error(xml_folder, error_message)

                # Download PDF file
                if "pdfLink" in summary['download']:
                    download_file(summary['download']['pdfLink'], package_id, ".pdf", pdf_folder)
                else:
                    error_message = f"No PDF download link available for package ID: {package_id}."
                    write_error(pdf_folder, error_message)

            except Exception as e:
                error_message = f"Error processing package ID: {package_id}. Error: {str(e)}"
                logging.error(error_message)
                write_error(xml_folder, error_message)
                write_error(pdf_folder, error_message)
                continue

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data for collection code: {code}. Error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error in download_collection for code: {code}. Error: {str(e)}")

def main():
    """
    Main function to process specified collections.
    """
    try:
        # Ensure codes are provided in command line arguments
        if len(sys.argv) < 2:
            sys.exit(1)

        collection_codes = sys.argv[1:]  # Collect collection codes from command line arguments
        joined_codes = "_".join(collection_codes)
        # Set up logging
        logging.basicConfig(
            filename= joined_codes + ".log",
            filemode="a",
            format="{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M",
            level=logging.INFO
        )
    
        # Fetch the list of collections
        code_data = GovInfo.gpo_collections(api_key=header_key['X-Api-key'])

        # Ensure the DataFrame is valid
        if code_data is None or code_data.empty:
            sys.exit(1)

        # Sort by package count for orderly processing
        code_data.sort_values('packagecount', inplace=True)

        # Process each collection
        for _, row in code_data.iterrows():
            collection_code = row['collectioncode']
            
            # Skip collections not in the command line argument list
            if collection_code not in collection_codes:
                continue

            package_count = row['packagecount']
            download_collection(collection_code, package_count)


    except Exception as e:
        logging.critical(f"Fatal error in main execution. Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
