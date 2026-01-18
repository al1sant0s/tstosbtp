import argparse
import xml.etree.ElementTree as ET
import os
from pathlib import Path
from natsort import natsorted


def read_bytestr(file_descriptor, n):
    return file_descriptor.read(n).rstrip(b"\x00").decode("utf8")


def write_str_to_file(file_descriptor, str_name, bytelen=1, null_terminated=False):
    # String length.
    str_name = str_name.encode("utf8")
    strlen = len(str_name) + null_terminated
    file_descriptor.write(strlen.to_bytes(bytelen))

    # String.
    file_descriptor.write(str_name)

    if null_terminated is True:
        file_descriptor.write(b"\x00")


def main():
    parser = argparse.ArgumentParser(
        description="""
        This tool allows you to convert sbtp/btp (textpool) files to xml files back and forth from the game 'The Simpsons: Tapped Out'.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-r",
        "--reverse",
        help="If set, convert xml back to sbtp/btp. If not set, convert sbtp/btp to xml.",
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

    ext = [["sbtp", "btp"], ["xml"]]
    if args.reverse is True:
        ext.reverse()

    ext_origin = [item for item in ext[0]]
    ext_dest = [item for item in ext[1]]

    # Get a flat list of files.
    files = [
        directory
        for glob in [
            Path(directory).glob(f"**/*.{item}")
            for item in ext_origin
            for directory in directories
        ]
        for directory in glob
    ]

    # Get total of files to convert.
    total = len(files)

    if total == 0:
        print(
            f"\n\n(!) No {'/'.join(ext_origin)} files found in any of the specified directories!"
        )
        print("    If you need help, execute the following command:\n")
        print("(?) tstosbtp --help\n\n")
        return

    print("\n\n--- TEXTPOOL CONVERTER ---\n\n")
    print(
        f" * Operation: {'/'.join(ext_origin).upper()} => {'/'.join(ext_dest).upper()}"
    )
    print(f" * Files: {total}")
    print(f" * Keep original files: {'Yes!' if args.keep is True else 'No!'}\n")

    # Process the files.
    if args.reverse is False:
        for file in files:
            try:
                if file.suffix == ".sbtp":
                    with open(file, "rb") as f:
                        if f.read(6) == b"\x53\x42\x54\x50\x01\x00":
                            # Start reading everything.
                            data = dict()
                            while True:
                                strlen = f.read(1)
                                if strlen == b"":
                                    break

                                # Add prefix.
                                prefix_key = read_bytestr(f, int.from_bytes(strlen))
                                data[prefix_key] = dict()

                                suffixes = int.from_bytes(f.read(4))

                                for _ in range(suffixes):
                                    strlen = int.from_bytes(f.read(1))
                                    suffix_key = read_bytestr(f, strlen)
                                    strlen = int.from_bytes(f.read(4))
                                    text = read_bytestr(f, strlen)

                                    # Add suffix within this group.
                                    data[prefix_key][suffix_key] = text

                            # Prepare xml tree.
                            root = ET.Element("sbtp")
                            tree = ET.ElementTree(root)

                            # Build tree in alphabetical order according to prefixes and suffixes.
                            for prefix_key in natsorted(data.keys()):
                                group = ET.SubElement(
                                    root, "group", {"prefix": prefix_key}
                                )
                                for suffix_key in natsorted(data[prefix_key].keys()):
                                    item = ET.SubElement(
                                        group, "item", {"suffix": suffix_key}
                                    )
                                    item.text = data[prefix_key][suffix_key]

                            # Store tree.
                            ET.indent(tree, " " * args.indent)
                            tree.write(
                                Path(file.parent, file.stem + ".xml"), encoding="utf8"
                            )


                    # Only keep original files if requested.
                    if args.keep is False:
                        os.remove(file)


                elif file.suffix == ".btp":
                    with open(file, "rb") as f:
                        if f.read(8) == b"\x42\x54\x50\x00\x04\x00\x10\x00":
                            # We are making the assumption the file size is written as 32 bit format.
                            # Ignore 32 bit file size.
                            f.read(4)

                            items = int.from_bytes(f.read(4))

                            # Ignore maximum block size.
                            f.read(4)

                            data = dict()

                            for _ in range(items):
                                # Ignore size of the block.
                                f.read(4)

                                strlen = int.from_bytes(f.read(1))
                                suffix_key = read_bytestr(f, strlen)
                                strlen = int.from_bytes(f.read(4))
                                text = read_bytestr(f, strlen)

                                # Add suffix.
                                data[suffix_key] = text

                            # Prepare xml tree.
                            root = ET.Element("btp")
                            tree = ET.ElementTree(root)

                            # Build tree in alphabetical order according to suffixes.
                            for suffix_key in natsorted(data.keys()):
                                item = ET.SubElement(
                                    root, "item", {"suffix": suffix_key[1:]}
                                )
                                item.text = data[suffix_key]

                            # Store tree.
                            ET.indent(tree, " " * args.indent)
                            tree.write(
                                Path(file.parent, file.stem + ".xml"), encoding="utf8"
                            )


                    # Only keep original files if requested.
                    if args.keep is False:
                        os.remove(file)


                else:
                    continue


            except Exception as e:
                print(f"ERROR! File {file.name} could not be converted! Reason: {e}")

    else:
        for file in files:
            try:
                if file.suffix == ".xml":
                    with open(file, "rb") as f:
                        root = ET.fromstring(f.read().decode("utf8"))

                    # Check type of revert conversion.
                    newfile = Path(file.parent, file.stem + f".{root.tag}")
                    if root.tag == "sbtp":
                        with open(newfile, "wb") as f:
                            # Write signature.
                            f.write(b"\x53\x42\x54\x50\x01\x00")

                            for group in root.findall("*"):
                                # Write prefix.
                                prefix = group.get("prefix")
                                write_str_to_file(f, prefix)

                                # Number of suffixes.
                                items = list(group.findall("*"))
                                f.write(len(items).to_bytes(4))

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


                    elif root.tag == "btp":
                        with open(newfile, "wb") as f:
                            # Write signature and unknown part.
                            f.write(b"\x42\x54\x50\x00\x04\x00\x10\x00")

                            # Reserve 32 bits for file size.
                            # Fill it up later!
                            file_size_seek = f.tell()
                            f.write(b"\x00\x00\x00\x00")

                            # Number of suffixes.
                            items = list(root.findall("item"))
                            f.write(len(items).to_bytes(4))

                            # Maximum block size.
                            # Fill it up later.
                            max_block_size_seek = f.tell()
                            f.write(b"\x00\x00\x00\x00")
                            max_block_size = 0

                            # Write suffixes.
                            for item in items:
                                # Get suffix content.
                                suffix_name = item.get("suffix")
                                suffix_name = "" if suffix_name is None else suffix_name
                                text = item.text
                                text = "" if text is None else text
                                block_size = (
                                    len(suffix_name.encode(("utf8")))
                                    + len(text.encode("utf8"))
                                    + 7
                                )
                                max_block_size = max(max_block_size, block_size)

                                # Write block size.
                                f.write(block_size.to_bytes(4))

                                # Write suffix name and suffix text.
                                write_str_to_file(f, suffix_name, null_terminated=True)
                                write_str_to_file(f, text, 4, True)

                            # Write file size.
                            file_size = f.tell()
                            f.seek(file_size_seek)
                            f.write(file_size.to_bytes(4))

                            # Write maximum block size.
                            f.seek(max_block_size_seek)
                            f.write(max_block_size.to_bytes(4))


                        # Only keep original files if requested.
                        if args.keep is False:
                            os.remove(file)


                    else:
                        continue


                else:
                    continue


            except Exception as e:
                print(f"ERROR! File {file.name} could not be converted! Reason: {e}")

    print("\n\n--- JOB COMPLETED!!! ---\n\n")
