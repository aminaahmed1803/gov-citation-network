import os
import sys
import json
from grobid_client.grobid_client import GrobidClient

def process_pdfs_with_grobid(pdf_dir, output_dir):
    """
    Process PDFs using GROBID to extract full-text information and log results.
    
    Args:
        pdf_dir (str): Path to the directory containing PDF files.
        output_dir (str): Path to the directory where GROBID output (TEI XML) will be saved.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize the GROBID client
    client = GrobidClient(config_path="./config.json")
    
    # Process all PDFs in the directory
    pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in directory: {pdf_dir}")
    
    
    client.process("processFulltextDocument", pdf_dir, output_dir)
    
    # List all generated TEI XML files
    tei_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".tei.xml")]
    print(f"Successfully processed {len(tei_files)} PDFs. TEI XML files saved to: {output_dir}")
    
    return tei_files

def process_folder(input_folder):
    """
    Process all PDFs in subdirectories and log results.
    
    Args:
        input_folder (str): The name of the main folder inside "zip".
    """
    zip_path = os.path.join("zip", input_folder)
    output_base = os.path.join("grobid", input_folder)
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{input_folder}_grobid.json")
    
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Input folder '{zip_path}' does not exist.")
    
    log_data = []
    success_count = 0
    failure_count = 0
    
    # Iterate through all subfolders inside the input folder
    for subfolder in os.listdir(zip_path):
        subfolder_path = os.path.join(zip_path, subfolder)
        if not os.path.isdir(subfolder_path):
            continue  # Skip non-directory files
        
        pdf_dir = os.path.join(subfolder_path, "pdf")
        output_dir = os.path.join(output_base, subfolder)
        os.makedirs(output_dir, exist_ok=True)
        
        status = "Success"
        reason = ""
        
        try:
            tei_files = process_pdfs_with_grobid(pdf_dir, output_dir)
            success_count += 1
        except Exception as e:
            status = "Failed"
            reason = str(e)
            failure_count += 1
        
        log_data.append({
            "subfolder": subfolder,
            "status": status,
            "reason": reason
        })
    
    # Add summary statistics
    log_data.append({
        "summary": {
            "total_processed": success_count + failure_count,
            "successful": success_count,
            "failed": failure_count
        }
    })
    
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=4)
    
    print(f"Log saved at: {log_file}")

# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_name>")
        sys.exit(1)
    
    folder_name = sys.argv[1]
    process_folder(folder_name)
