# hex_to_dbf.py
import os
import binascii
from pathlib import Path

def hex_to_dbf(hex_path, dbf_path):
    with open(hex_path, "r") as f:
        hex_data = f.read().replace("\n", "").replace(" ", "")
    binary = binascii.unhexlify(hex_data)
    with open(dbf_path, "wb") as f:
        f.write(binary)
    print("Created:", dbf_path)

BASE_DIR = Path(__file__).resolve().parent
folder = BASE_DIR / "data" / "foxpro"

if not folder.exists():
    print(f"Error: folder not found: {folder}")
    print("Make sure you're running the script from the project or that the `data/foxpro` directory exists.")
    raise SystemExit(1)

for entry in folder.iterdir():
    if entry.is_file() and entry.suffix.lower() == ".hex":
        name = entry.with_suffix('.dbf')
        hex_to_dbf(str(entry), str(name))
