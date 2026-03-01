"""
Script to manually download model artifacts from DagHub with robust retry logic.
This bypasses MLflow API issues.
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import time
from tqdm import tqdm

load_dotenv()

# Configuration
DAGSHUB_USER = os.getenv("DAGSHUB_USER", "MarcoSrhl")
DAGSHUB_TOKEN = os.getenv("DAGSHUB_TOKEN")
DAGSHUB_REPO = os.getenv("DAGSHUB_REPO", "MarcoSrhl/NLP-Fact-checking")
RUN_ID = "83c07187e08644c590e3cd92358ac4a4"  # mini_test_run_6

# Files to download (from the screenshot you showed)
FILES_TO_DOWNLOAD = [
    "components/tokenizer/tokenizer.json",
    "components/tokenizer/tokenizer_config.json",
    "components/model/config.json",
    "components/model/model.safetensors",
    "LICENSE.txt",
    "MLmodel",
    "conda.yaml",
    "python_env.yaml",
    "requirements.txt"
]

CACHE_DIR = Path(".model_cache") / RUN_ID


def download_file(url, output_path, max_retries=5):
    """Download a file with retry logic and progress bar"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    session = requests.Session()
    
    for attempt in range(max_retries):
        try:
            print(f"  Attempt {attempt + 1}/{max_retries}: {output_path.name}")
            
            # Stream download with progress
            response = session.get(
                url,
                auth=(DAGSHUB_USER, DAGSHUB_TOKEN),
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=output_path.name
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            print(f"  ✓ Downloaded {output_path.name}")
            return True
            
        except Exception as e:
            print(f"  ✗ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"  ✗ Failed to download {output_path.name} after {max_retries} attempts")
                return False


def main():
    print("="*60)
    print("DagHub Model Artifact Downloader")
    print("="*60)
    print(f"Repository: {DAGSHUB_REPO}")
    print(f"Run ID: {RUN_ID}")
    print(f"Cache directory: {CACHE_DIR}")
    print("="*60)
    
    if not DAGSHUB_TOKEN:
        print("ERROR: DAGSHUB_TOKEN not found in .env file")
        return
    
    # Download each file
    success_count = 0
    for file_path in FILES_TO_DOWNLOAD:
        url = f"https://dagshub.com/{DAGSHUB_REPO}.mlflow/api/2.0/mlflow-artifacts/artifacts/{RUN_ID}/artifacts/{file_path}"
        output_path = CACHE_DIR / file_path
        
        print(f"\n📥 Downloading: {file_path}")
        
        if download_file(url, output_path):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"Download complete: {success_count}/{len(FILES_TO_DOWNLOAD)} files")
    
    if success_count == len(FILES_TO_DOWNLOAD):
        print("✅ All files downloaded successfully!")
        print(f"Model cache location: {CACHE_DIR.absolute()}")
    else:
        print(f"⚠️  Some files failed to download ({len(FILES_TO_DOWNLOAD) - success_count} failed)")
    print("="*60)


if __name__ == "__main__":
    main()
