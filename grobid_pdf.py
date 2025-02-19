import os
import sys
from grobid_client.grobid_client import GrobidClient

def process_pdfs_with_grobid(input_folder):
    """
    Process PDFs using GROBID to extract references.
    
    Args:
        input_folder (str): The name of the main folder inside "zip".
    """
    zip_path = os.path.join("zip", input_folder)
    output_base = os.path.join("grobid", input_folder)
    
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Input folder '{zip_path}' does not exist.")
    
    # Initialize the GROBID client
    client = GrobidClient(config_path="./config.json")
    
    # Iterate through all subfolders inside the input folder
    for subfolder in os.listdir(zip_path):
        subfolder_path = os.path.join(zip_path, subfolder)
        if not os.path.isdir(subfolder_path):
            continue  # Skip non-directory files
        
        pdf_dir = os.path.join(subfolder_path, "pdf")
        output_dir = os.path.join(output_base, subfolder, "grobid")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process PDFs if the pdf directory exists
        if os.path.exists(pdf_dir):
            pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
            
            if pdf_files:
                print(f"Processing {len(pdf_files)} PDFs in {pdf_dir}...")
                client.process("processReferences", pdf_files, output_dir)
                print(f"TEI XML files saved in: {output_dir}")
            else:
                print(f"No PDFs found in {pdf_dir}, skipping...")
        else:
            print(f"No 'pdf' folder found in {subfolder_path}, skipping...")

# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_name>")
        sys.exit(1)
    
    folder_name = sys.argv[1]
    process_pdfs_with_grobid(folder_name)
