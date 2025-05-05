import os
import requests
import sys
import logging
import json
import pandas as pd

sys.path.append(os.path.abspath('../'))

from govinfo import GovInfo

def save_collection_to_file(collection_code, df):
    """
    Save the collection DataFrame to a file in JSON format, where each line
    is a JSON object representing a package from the collection.
    """
    try:
        file_name = f"collections/{collection_code}.txt"
        os.makedirs("collections", exist_ok=True)  # Ensure the directory exists
        with open(file_name, "w", encoding="utf-8") as file:
            for _, row in df.iterrows():
                file.write(json.dumps(row.to_dict()) + "\n")
        logging.info(f"Saved collection {collection_code} to {file_name}.")
    except Exception as e:
        logging.error(f"Failed to save collection {collection_code} to file. Error: {str(e)}")


def download_collection(code):
    """
    Get collection data and save it.
    """
    try:
        logging.info(f"Fetching data for collection: {code}")
        df = GovInfo.gpo_collections(collection=code, start_date="0000-00-00T00:00:00Z")

        if df is None or df.empty:
            logging.warning(f"No data found for collection: {code}")
            return

        save_collection_to_file(code, df)
    except Exception as e:
        logging.error(f"Error processing collection {code}. Error: {str(e)}")


def main():
    """
    Main function to process specified collections or all if no input.
    """
    try:
        # Set up logging
        logging.basicConfig(
            filename="get-collection.log",
            filemode="a",
            format="{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M",
            level=logging.INFO
        )

        logging.info("Starting processing of collections.")

        # Check for command-line arguments
        if len(sys.argv) > 1:
            collections_to_process = sys.argv[1:]
            logging.info(f"Processing specified collections: {collections_to_process}")
        else:
            logging.info("Fetching list of available collections.")
            code_data = GovInfo.gpo_collections()
            
            if code_data is None or code_data.empty:
                logging.critical("No collections data retrieved. Exiting.")
                sys.exit(1)
            
            code_data.sort_values('packagecount', inplace=True)
            collections_to_process = code_data['collectioncode'].tolist()
            logging.info("Processing all available collections.")

        # Process each collection
        for collection_code in collections_to_process:
            download_collection(collection_code)

        logging.info("Completed processing of collections.")
    except Exception as e:
        logging.critical(f"Fatal error in main execution. Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

