import urllib.request
import zipfile
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bin_dir = os.path.join(PROJECT_ROOT, "backend", "bin")
zip_path = os.path.join(bin_dir, "wkhtmltox.zip")
extract_path = os.path.join(bin_dir, "wkhtmltox")

os.makedirs(bin_dir, exist_ok=True)

url = "https://www.nuget.org/api/v2/package/wkhtmltopdf-msvc-64/0.12.6.1"

print("Downloading wkhtmltopdf nuget package...")
urllib.request.urlretrieve(url, zip_path)

print("Extracting...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

print("Extracted successfully.")
