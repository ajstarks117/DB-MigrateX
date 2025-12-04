# hex_to_dbf.py
import os
import binascii

def hex_to_dbf(hex_path, dbf_path):
    with open(hex_path, "r") as f:
        hex_data = f.read().replace("\n", "").replace(" ", "")
    binary = binascii.unhexlify(hex_data)
    with open(dbf_path, "wb") as f:
        f.write(binary)
    print("Created:", dbf_path)

folder = "./data/foxpro"

for file in os.listdir(folder):
    if file.lower().endswith(".hex"):
        name = file[:-4] + ".dbf"
        hex_to_dbf(os.path.join(folder, file),
                   os.path.join(folder, name))
