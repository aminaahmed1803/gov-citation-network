import os
import sys
from grobid_client.grobid_client import GrobidClient


def process_pdfs_with_grobid(pdf_dir, output_dir):
    """
    Process PDFs using GROBID to extract references.

    Args:
        pdf_dir (str): Path to the directory containing PDF files.
        output_dir (str): Path to the directory where GROBID output (TEI XML) will be saved.

    Returns:
        list: Paths to the generated TEI XML files.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Initialize the GROBID client
    client = GrobidClient(config_path="./config.json")

    # Process all PDFs in the directory
    pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in directory: {pdf_dir}")
        return []

    print(f"Processing {len(pdf_files)} PDFs with GROBID in {pdf_dir}...")
    client.process("processReferences", pdf_files, output_dir)

    # List all generated TEI XML files
    tei_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".tei.xml")]
    print(f"Successfully processed {len(tei_files)} PDFs. TEI XML files saved to: {output_dir}")
    return tei_files


def process_folder(input_folder):
    """
    Process all PDFs in a given folder structure.

    Args:
        input_folder (str): The main directory containing subdirectories with PDF files.
    """
    base_output_dir = os.path.join("grobid", input_folder, "folders")

    for subfolder in os.listdir(input_folder):
        subfolder_path = os.path.join(input_folder, subfolder)

        if os.path.isdir(subfolder_path):
            pdf_folder = os.path.join(subfolder_path, "pdf")

            if os.path.exists(pdf_folder):
                output_dir = os.path.join(base_output_dir, subfolder, "grobid")
                process_pdfs_with_grobid(pdf_folder, output_dir)


# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]

    if not os.path.exists(input_folder) or not os.path.isdir(input_folder):
        print(f"Error: The folder '{input_folder}' does not exist or is not a directory.")
        sys.exit(1)

    process_folder(input_folder)
