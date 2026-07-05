import os, subprocess, urllib.request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bin_dir = os.path.join(PROJECT_ROOT, "backend", "bin")
exe_path = os.path.join(bin_dir, "wkhtmltopdf_installer.exe")
dest_path = os.path.join(bin_dir, "wkhtmltox")

os.makedirs(bin_dir, exist_ok=True)

url = "https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.msvc2015-win64.exe"

print("Downloading installer...")
urllib.request.urlretrieve(url, exe_path)

print(f"Installing silently to {dest_path} ...")
# /S for silent, /D sets directory (must be last without quotes)
cmd = [exe_path, "/S", f"/D={dest_path}"]
subprocess.run(cmd, check=True)
print("Done!")
