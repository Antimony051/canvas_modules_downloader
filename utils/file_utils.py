import os
import string
import unicodedata
import re
import requests


def make_valid_filename(input_str):
    """Convert string to valid filename."""
    if not input_str:
        return input_str
    
    # Normalize Unicode and whitespace
    input_str = unicodedata.normalize('NFKC', input_str)
    input_str = input_str.replace("\u00A0", " ")  # NBSP to space
    input_str = re.sub(r"\s+", " ", input_str)
    
    # Remove invalid characters
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    input_str = input_str.replace("+", " ")  # Canvas default for spaces
    input_str = input_str.replace(":", "-")
    input_str = input_str.replace("/", "-")
    input_str = "".join(c for c in input_str if c in valid_chars)
    
    # Remove leading and trailing whitespace
    input_str = input_str.lstrip().rstrip()
    
    # Remove trailing periods
    input_str = input_str.rstrip(".")
    
    return input_str


def download_file_from_url(url, file_path, filename):
    """Download a file from URL to specified path."""
    try:
        print(f"    Downloading: {filename}...")
        # TODO: use streaming download to avoid loading large files into memory
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        print(f"      ✓ Saved: {filename}")
        return True
    except Exception as e:
        print(f"      ❌ Failed to download {filename}: {e}")
        return False