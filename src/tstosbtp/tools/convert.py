import argparse
import xml.etree.ElementTree as ET
import os
from pathlib import Path


def read_bytestr(file_descriptor, n):
    return file_descriptor.read(n).decode("utf8")


def write_str_to_file(file_descriptor, str_name, bytelen=1):
    # String length.
    str_name = str_name.encode("utf8")
    strlen = len(str_name)
    file_descriptor.write(strlen.to_bytes(bytelen))

    # String.
    file_descriptor.write(str_name)


def main():
    parser = argparse.ArgumentParser(
        description="""
        This tool allows you to convert sbtp (textpool) files to xml files back and forth from the game 'The Simpsons: Tapped Out'.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-r",
        "--reverse",
        help="If set, convert xml back to sbtp. If not set, convert sbtp to xml.",
        action="store_true",
    )

    parser.add_argument(
        "-k",
        "--keep",
        help="If set, do not delete the files that are being converted.",
        action="store_true",
    )

    parser.add_argument(
        "-i",
        "--indent",
        help="Indent level value used for xml files.",
        default=2,
        type=int,
    )

    parser.add_argument(
        "input_dir",
        help="List of directories containing the files.",
        nargs="+",
    )

    args = parser.parse_args()
    directories = [Path(item) for item in args.input_dir]

    ext = ["sbtp", "xml"]
    if args.reverse is True:
        ext.reverse()

    # Get total of files to convert.
    total = sum(
        [len(list(Path(directory).glob(f"**/*.{ext[0]}"))) for directory in directories]
    )

    if total == 0:
        print(f"\n\n(!) No {ext[0]} files found in any of the specified directories!")
        print("    If you need help, execute the following command:\n")
        print("(?) tstosbtp --help\n\n")
        return

    print("\n\n--- TEXTPOOL CONVERTER ---\n\n")
    print(f" * Operation: {ext[0].upper()} => {ext[1].upper()}")
    print(f" * Files: {total}")
    print(f" * Keep original files: {"Yes!" if args.keep is True else "No!"}\n")

    for directory in directories:
        # Process the files.
        if args.reverse is False:
            for file in directory.glob(f"**/*.{ext[0]}"):
                with open(file, "rb") as f:
                    if f.read(6) == b"\x53\x42\x54\x50\x01\x00":
                        # Prepare xml tree.
                        root = ET.Element("sbtp")
                        tree = ET.ElementTree(root)

                        # Start reading everything.
                        while True:
                            strlen = f.read(1)
                            if strlen == b"":
                                break

                            prefix = ET.SubElement(
                                root,
                                "group",
                                {"prefix": read_bytestr(f, int.from_bytes(strlen))},
                            )

                            suffixes = int.from_bytes(f.read(4))

                            for _ in range(suffixes):
                                strlen = int.from_bytes(f.read(1))
                                item = ET.SubElement(
                                    prefix, "item", {"suffix": read_bytestr(f, strlen)}
                                )

                                strlen = int.from_bytes(f.read(4))
                                text = read_bytestr(f, strlen)
                                item.text = text

                        # Store tree.
                        ET.indent(tree, " " * args.indent)
                        tree.write(
                            Path(file.parent, file.stem + ".xml"), encoding="utf8"
                        )

                    else:
                        continue

                # Only keep original files if requested.
                if args.keep is False:
                    os.remove(file)

        else:
            for file in directory.glob(f"**/*.{ext[0]}"):
                with open(file, "rb") as f:
                    root = ET.fromstring(f.read().decode("utf8"))

                    # If this xml file is not valid.
                    if root.tag != "sbtp":
                        continue

                    newfile = Path(file.parent, file.stem + f".{ext[1]}")

                    with open(newfile, "wb") as f:
                        # Write signature.
                        f.write(b"\x53\x42\x54\x50\x01\x00")

                        for group in root.findall("*"):
                            # Write prefix.
                            prefix = group.get("prefix")
                            write_str_to_file(f, prefix)

                            # Number of suffixes.
                            items = list(group.findall("*"))
                            f.write(int.to_bytes(len(items), 4))

                            # Write suffixes.
                            for item in items:
                                # Suffix name.
                                write_str_to_file(f, item.get("suffix"))

                                # Suffix content.
                                text = item.text
                                text = "" if text is None else text
                                write_str_to_file(f, text, 4)

                # Only keep original files if requested.
                if args.keep is False:
                    os.remove(file)

    print("\n\n--- JOB COMPLETED!!! ---\n\n")
