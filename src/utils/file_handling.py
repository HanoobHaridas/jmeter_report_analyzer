import os
import zipfile
import tempfile
from pathlib import Path
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_zip(uploaded_file):
    """Extract uploaded zip file to a temporary directory."""
    try:
        # Create a temp directory in the current working directory
        current_dir = os.path.abspath(os.getcwd())
        temp_dir_name = "temp_jmeter_reports"
        custom_temp_dir = os.path.abspath(os.path.join(current_dir, temp_dir_name))
        
        logger.debug(f"Current directory: {current_dir}")
        logger.debug(f"Custom temp directory: {custom_temp_dir}")
        
        # Ensure the directory exists
        os.makedirs(custom_temp_dir, exist_ok=True)
        
        # Create a unique subdirectory for this extraction
        with tempfile.TemporaryDirectory(dir=custom_temp_dir) as temp_dir:
            temp_dir = os.path.abspath(temp_dir)  # Convert to absolute path
            logger.debug(f"Created temp directory: {temp_dir}")
            
            # List contents of temp directory before extraction
            logger.debug("Contents before extraction:")
            for item in os.listdir(temp_dir):
                logger.debug(f"  - {item}")
            
            temp_zip_path = os.path.join(temp_dir, "uploaded.zip")
            logger.debug(f"Writing zip to: {temp_zip_path}")
            
            # Write the uploaded file
            with open(temp_zip_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Verify zip file was written
            if os.path.exists(temp_zip_path):
                logger.debug(f"Zip file written successfully: {temp_zip_path}")
            else:
                raise Exception(f"Failed to write zip file to {temp_zip_path}")
            
            # Extract the zip file
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                logger.debug("Extracting zip contents...")
                zip_ref.extractall(temp_dir)
            
            # List contents after extraction
            logger.debug("Contents after extraction:")
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    logger.debug(f"  - {os.path.join(root, file)}")
            
            # Find index.html
            index_path = None
            for root, _, files in os.walk(temp_dir):
                if 'index.html' in files:
                    index_path = os.path.abspath(os.path.join(root, 'index.html'))
                    logger.debug(f"Found index.html at: {index_path}")
                    break
            
            if not index_path:
                # List all files for debugging
                all_files = []
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        all_files.append(os.path.join(root, file))
                raise FileNotFoundError(
                    f"index.html not found in the uploaded zip file. Found files: {all_files}"
                )
            
            # Verify index.html exists
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"index.html path exists but file not found: {index_path}")
            
            # Create a persistent copy of the entire directory structure
            persistent_dir = os.path.join(custom_temp_dir, "persistent")
            os.makedirs(persistent_dir, exist_ok=True)
            
            # Copy the entire directory structure
            for root, dirs, files in os.walk(temp_dir):
                # Skip the uploaded.zip file
                if 'uploaded.zip' in files:
                    files.remove('uploaded.zip')
                
                # Create corresponding directories in persistent folder
                rel_path = os.path.relpath(root, temp_dir)
                persistent_path = os.path.join(persistent_dir, rel_path)
                os.makedirs(persistent_path, exist_ok=True)
                
                # Copy all files
                for file in files:
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(persistent_path, file)
                    shutil.copy2(src_path, dst_path)
                    logger.debug(f"Copied {src_path} to {dst_path}")
            
            # Get the path to index.html in the persistent directory
            persistent_index_path = os.path.join(persistent_dir, os.path.relpath(index_path, temp_dir))
            logger.debug(f"Created persistent copy at: {persistent_index_path}")
            
            return persistent_index_path, persistent_dir
            
    except Exception as e:
        logger.error(f"Error processing zip file: {str(e)}")
        raise Exception(f"Error processing zip file: {str(e)}") 