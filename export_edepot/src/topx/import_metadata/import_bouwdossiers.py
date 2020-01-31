from datetime import datetime
from jinja2 import Environment, PackageLoader
import logging
import os
from pathlib import Path
import shutil
import sys
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


def find_first_xml_file(dms_dir:str):
    dms_xml_file = None
    for file in os.listdir(dms_dir):
        if file.endswith(".xml"):
            dms_xml_file = file
            break

    return dms_xml_file


def import_bouwdossiers(env, dms_dir: str, dest_dir: str):
    dms_xml_file = find_first_xml_file(dms_dir)
    if not dms_xml_file:
        log.error('Geen XML gevonden in {dms_dir}')
        return

    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    file_path = dms_dir + os.sep + dms_xml_file
    with open(file_path) as fd:
        xml = xmltodict.parse(fd.read())

    file_base = os.path.splitext(dms_xml_file)[0]
    xml_top = xml.get('overdracht_bouwdossier')
    overdracht_bouwdossier = {
        'identificatiekenmerk': xml_top['@id'],
        'naam': xml_top['omschrijvingpublicatie']['#text'],
        'omschrijving': '',
        'classificatie' : {
            'code': xml_top['@classid'],
            'omschrijving': xml_top['action'],  # ??
            'datum': datetime.fromisoformat(xml_top['datumpublicatie']['@valuecode']).strftime("%Y-%m-%d"),  # ???
            'bron': xml_top['@soort'],  # ??

        },
    }
    template = env.get_template('ToPX-2.3_Archief_max.xml.jinja')
    archief_xml = template.render(data=overdracht_bouwdossier)
    archief_xml_path = dest_dir + os.sep + overdracht_bouwdossier['identificatiekenmerk'] + '.xml'
    with open(archief_xml_path, "w") as output:
        output.write(archief_xml)
    # print (overdracht_bouwdossier)
    for bouwdossier in get_list_items(xml_top, 'bouwdossiers', 'bouwdossier'):
        print(f"oId:{bouwdossier.get('@oId')}")
        for bijlage in get_list_items(bouwdossier, 'bijlagen', 'bijlage'):
            document = bijlage['document']['#text']
            bijlage_path = os.path.join(dms_dir, document)
            if not os.path.exists(bijlage_path):
                print(f"Missing : {bijlage_path}")
            # else:
            #    print(bijlage_path)


if __name__ == "__main__":
    dms_dir = '/Users/bart/tmp/NHA/Eerste overdracht 1875 - 1900'
    dest_dir = dms_dir + '.sidecar'
    env = Environment(loader=PackageLoader('topx', 'templates'), trim_blocks=True, lstrip_blocks=True)
    import_bouwdossiers(env, dms_dir, dest_dir)








