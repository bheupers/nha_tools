import argparse
from lxml import etree
import os


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", help="Directory")
    args = parser.parse_args()
    dir = args.dir

    schema_root = etree.parse("xsd/topx-2.3_1.xsd")
    schema = etree.XMLSchema(schema_root)
    parser = etree.XMLParser(schema = schema)
    total_errors = 0
    for root, subdirs, files in os.walk(dir):
        for file in files:
            if not file.endswith('.metadata'):
                continue
            fullpath = os.path.join(root, file)
            print(f"Validating {fullpath}")
            proot = etree.parse(fullpath, parser)
            total_errors += len(parser.error_log)
            if parser.error_log:
                print(parser.error_log)

    print(f"Total errors: {total_errors}")
