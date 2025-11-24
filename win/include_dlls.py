#!/usr/bin/env python3
import argparse
import base64
import hashlib
import os
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument("wheel", type=str, help="The source wheel")
parser.add_argument("output_dir", type=str, help="The directory to save the updated wheel to")
parser.add_argument("dll_dir", type=str, help="The directory with the additional libraries")
parser.add_argument("--toplevel_directory", default=False, action="store_true", help="Copy to top-level directory")
args = parser.parse_args()

wheel_name = os.path.basename(args.wheel)
archive_dir = wheel_name.split("-")[0]
archive_dir = archive_dir.split("_")[0] if args.toplevel_directory else archive_dir.replace("_", "/")
output_wheel = os.path.join(args.output_dir, wheel_name)
if "PYTHON_ARCH" in args.dll_dir:
    args.dll_dir = args.dll_dir.replace("PYTHON_ARCH", os.environ["PYTHON_ARCH"])

records, records_path = [], None
with (
    zipfile.ZipFile(args.wheel, mode="r") as source_wheel_zip,
    zipfile.ZipFile(output_wheel, mode="w", compression=zipfile.ZIP_DEFLATED) as output_wheel_zip,
):
    for item in source_wheel_zip.infolist():
        buffer = source_wheel_zip.read(item.filename)
        if item.filename.endswith("/RECORD"):
            assert not records_path, "Multiple RECORD files found in the wheel"
            records_path = item.filename
            records = buffer.decode("utf-8").splitlines()
            assert f"{item.filename},," in records
        else:
            output_wheel_zip.writestr(item, buffer)
    assert records_path, "No RECORD file found in the wheel"

    for name in sorted(os.listdir(args.dll_dir)):
        if name.lower().endswith(".dll"):
            source_dll_path = os.path.join(args.dll_dir, name)
            archive_dll_path = os.path.join(archive_dir, name)
            assert not any(record.startswith(archive_dll_path + ",") for record in records)

            output_wheel_zip.write(source_dll_path, archive_dll_path)
            with open(source_dll_path, "rb") as source_dll_file:
                dll_contents = source_dll_file.read()
            sha256 = hashlib.sha256(dll_contents).digest()
            sha256 = base64.urlsafe_b64encode(sha256).rstrip(b"=").decode("ascii")
            records.append(f"{archive_dll_path},sha256={sha256},{len(dll_contents)}")

    output_wheel_zip.writestr(records_path, "".join(record + "\n" for record in records))
