import os
from grobid_client.grobid_client import GrobidClient


def process_pdfs_with_grobid(pdf_dir, output_dir):
    """
    Process PDFs using GROBID to extract references.

    Args:
        pdf_dir (str): Path to the directory containing PDF files.
        output_dir (str): Path to the directory where GROBID output (TEI XML) will be saved.
        grobid_url (str): The URL of the running GROBID server. Default is "http://localhost:8070".

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
        raise FileNotFoundError(f"No PDF files found in directory: {pdf_dir}")

    print(f"Processing {len(pdf_files)} PDFs with GROBID...")
    client.process("processReferences", pdf_files, output_dir)


    # List all generated TEI XML files
    tei_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".tei.xml")]
    print(f"Successfully processed {len(tei_files)} PDFs. TEI XML files saved to: {output_dir}")
    return tei_files

# Example usage
if __name__ == "__main__":
    pdf_dir = "./ERP/ERP-1996/pdf"
    output_dir = "./results/ERP-1996/pdf"
    process_pdfs_with_grobid(pdf_dir, output_dir)
