from datetime import datetime
import logging
import re
import os
import xmltodict

log = logging.getLogger(__name__)


def get_list_items(d, key1, key2):
    x = d.get(key1)
    if x:
        items = x.get(key2)
        if items and not isinstance(items, list):
            items = [items]
        if items:
            return items
    return []


def import_bouwdossiers(dir: str, file: str, dest_dir: str):
    file_path = dir + os.sep + file
    with open(file_path) as fd:
        xml = xmltodict.parse(fd.read())

    xml_top = xml.get('overdracht_bouwdossier')
    overdracht_bouwdossier = {
        'id': xml_top['@id'],
        'classid' : xml_top['@classid'],
        'soort' : xml_top['@soort'],
        'datumpublicatie': datetime.fromisoformat(xml_top['datumpublicatie']['@valuecode']),
        'omschrijvingpublicatie': xml_top['omschrijvingpublicatie']['#text'],
    }
    print (overdracht_bouwdossier)

    for bouwdossier in get_list_items(xml_top, 'bouwdossiers', 'bouwdossier'):
        print(f"oId:{bouwdossier.get('@oId')}")


if __name__ == "__main__":
    dms_dir = '/Users/bart/tmp/NHA/Eerste overdracht 1875 - 1900'
    dms_xml_file = '000000636885001374942024.xml'
    import_bouwdossiers(dms_dir, dms_xml_file, 'sidecar')








