import argparse
import logging
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO)

out_directory = Path("out")


@dataclass
class ExtractedClass:
    name: str
    common_header: List[str]
    content: List[str]


def read_input_file(fname: str) -> List[str]:
    with open(fname, "r") as f:
        return f.read().split("\n")


def extract_class_name(value: str) -> Optional[str]:
    m = re.match(r"^class (\w*)", value)
    return m.group(1) if m is not None else None


def camel_to_snake(value: str) -> str:
    value = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", value).lower()


def process_file(content: List[str]) -> List[ExtractedClass]:
    current_class = list()
    current_class_name = ""
    common_header = list()
    classes = list()

    n = 0
    while n < len(content):
        if content[n].startswith("class "):
            current_class = [content[n]]
            break
        common_header.append(content[n])
        n += 1

    while n < len(content):
        current_class_name = extract_class_name(content[n])
        if not current_class_name:
            logging.error(f"Unable to extract class name from {content[n]}")

        n += 1

        while n < len(content) and not content[n].startswith("class "):
            current_class.append(content[n])
            n += 1

        if len(current_class):
            logging.info(f"Class finished: {current_class_name}")
            if current_class_name is not None:
                classes.append(
                    ExtractedClass(
                        name=current_class_name,
                        common_header=common_header,
                        content=current_class,
                    )
                )
            current_class = [content[n]] if n < len(content) else []

    return classes


def process_extracted_classes(class_list: List[ExtractedClass]):
    init_py_file = []

    if not os.path.exists(out_directory):
        os.makedirs(out_directory)

    for cls in class_list:
        snake_case_name = camel_to_snake(cls.name)
        out_fname = out_directory.joinpath(f"{snake_case_name}.py")
        init_py_file.append(f"from .{snake_case_name} import {cls.name}")

        logging.info(f"Writing class {cls.name} to {out_fname}")

        with open(out_fname, "w") as f:
            out = cls.common_header + cls.content
            f.write("\n".join(out))

    with open(out_directory.joinpath("__init__.py"), "w") as f:
        f.write("\n".join(sorted(init_py_file)))


def main():
    parser = argparse.ArgumentParser(description="Split massive class file into pieces")
    parser.add_argument("input_filename", type=str)
    args = parser.parse_args()

    try:
        content = read_input_file(args.input_filename)
    except FileNotFoundError:
        logging.error(f"File not found: {args.input_filename}")
        quit()

    class_list = process_file(content)
    process_extracted_classes(class_list)


if __name__ == "__main__":
    main()
