import py7zr
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bin_dir = os.path.join(PROJECT_ROOT, "backend", "bin")
archive_path = os.path.join(bin_dir, 'wkhtmltox-0.12.6-1.mxe-cross-win64.7z')

with py7zr.SevenZipFile(archive_path, mode='r') as z:
    z.extractall(path=bin_dir)
