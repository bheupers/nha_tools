import argparse
from datetime import datetime
from jinja2 import Environment, PackageLoader
import logging
import os
from pathlib import Path
import shutil
from xlrd import open_workbook, xldate_as_tuple, XL_CELL_NUMBER

from topx.lib.utils import (
    get_list_items,
    find_first_file_extension,
    get_string_adres,
    import_bestand,
)
from topx.settings import IGNORE_FILES

log = logging.getLogger(__name__)


def read_decos_excelfile(file_path: str) -> dict:
    global datemode
    result = {}
    wb = open_workbook(file_path)
    datemode = wb.datemode
    col_title_map = {}
    for s in wb.sheets():
        result[s.name] = {"count": s.nrows - 1}
        sheet = result[s.name]
        for row in range(s.nrows):
            for col in range(s.ncols):
                cell = s.cell(row, col)
                value = cell.value
                ctype = cell.ctype
                if ctype == XL_CELL_NUMBER and value == int(value):
                    value = int(value)
                str_col = str(col)
                if row == 0:
                    value = value.lower()
                    col_title_map[str_col] = value
                    sheet[value] = []
                else:
                    sheet[col_title_map[str_col]].append(value)
    return result


def import_decos_xlsx(dms_dir: str, dest_dir: str, template):
    xlsx_file = find_first_file_extension(dms_dir, ".xlsx")
    xlsx_path = os.path.join(dms_dir, xlsx_file)
    result = read_decos_excelfile(xlsx_path)
    zaken = result["Zaken"]
    documenten = result["Documenten"]
    bestanden = result["Bestanden"]
    print(f"{len(zaken)}, {len(documenten)}, {len(bestanden)}")

    return 0, {}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--idir", help="Input directory")
    parser.add_argument("-o", "--odir", help="Output directory")
    args = parser.parse_args()
    dms_dir = args.idir
    dest_dir = args.odir or dms_dir + ".sidecar"
    env = Environment(
        loader=PackageLoader("topx", "templates"), trim_blocks=True, lstrip_blocks=True
    )
    template = env.get_template("ToPX-2.3-template.xml")
    total_metadatafiles, bestanden_processed = import_decos_xlsx(
        dms_dir, dest_dir, template
    )
    log.info(f"Total metadata files : {total_metadatafiles}")
