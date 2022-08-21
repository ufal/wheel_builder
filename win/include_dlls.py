#!/usr/bin/env python3
import argparse
import os
import shutil
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument("wheel", type=str, help="The source wheel")
parser.add_argument("output_dir", type=str, help="The directory to save the updated wheel to")
parser.add_argument("dll_dir", type=str, help="The directory with the additional libraries")
args = parser.parse_args()

wheel_name = os.path.basename(args.wheel)
archive_dir = wheel_name.split("-")[0].replace(".", "/")
output_wheel = os.path.join(args.output_dir, wheel_name)
if "PYTHON_ARCH" in args.dll_dir:
    args.dll_dir = args.dll_dir.replace("PYTHON_ARCH", os.environ["PYTHON_ARCH"])

shutil.copy(args.wheel, output_wheel)
with zipfile.ZipFile(output_wheel, mode="a", compression=zipfile.ZIP_DEFLATED) as output_wheel_zip:
    for name in sorted(os.listdir(args.dll_dir)):
        if name.lower().endswith(".dll"):
            source_dll_path = os.path.join(args.dll_dir, name)
            archive_dll_path = os.path.join(archive_dir, name)
            if archive_dll_path not in output_wheel_zip.namelist():
                output_wheel_zip.write(source_dll_path, archive_dll_path)
