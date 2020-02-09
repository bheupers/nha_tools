from datetime import datetime
from jinja2 import Environment, PackageLoader
import hashlib
import logging
import os
from pathlib import Path
import shutil
import xmltodict


log = logging.getLogger(__name__)


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def sha256(fname):
    sha256_hash = hashlib.sha256()
    with open(fname,"rb") as f:
        for chunk in iter(lambda: f.read(4096),b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


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

def get_string_adres(adres: dict):
    straatnaam = adres['adresstraatnaam'].get('#text','')
    aanduiding = adres['adresaanduiding'].get('#text','')
    huisnummer = adres['adreshuisnummer'].get('#text','')
    huisletter = adres['adreshuisletter'].get('#text','')
    huisnummertoevoeging = adres['adreshuisnummertoevoeging'].get('#text','')
    postcode = adres['adrespostcode'].get('#text','')
    woonplaats = adres['adreswoonplaats'].get('#text','')

    res = ''
    if aanduiding:
        res += aanduiding + ' '
    if straatnaam:
        res += straatnaam
    if huisnummer:
        res += ' ' + huisnummer
    if huisletter:
        res += huisletter
    if huisnummertoevoeging:
        res += ' ' + huisnummertoevoeging
    if postcode or woonplaats:
        res += ','
    if postcode:
        res += ' ' + postcode
    if woonplaats:
        res += ' ' + woonplaats
    return res


def import_bouwdossiers(env, dms_dir: str, dest_dir: str):
    """
    TopX structuur

    Archief
    Dossier
    Bestand

    Geen Serie of Record??
    """
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
    identificatiekenmerk = xml_top['@id']
    archief_data = {
        'identificatiekenmerk': identificatiekenmerk,
        'naam': xml_top['omschrijvingpublicatie']['#text'],
        'omschrijving': '',
        'classificatie' : {
            'code': xml_top['@classid'],
            'omschrijving': xml_top['action'],  # ??
            'datum': datetime.fromisoformat(xml_top['datumpublicatie']['@valuecode']).strftime("%Y-%m-%d"),  # ???
            'bron': xml_top['@soort'],  # ??

        },
    }
    archief_template = env.get_template('ToPX-2.3_Archief_max.xml.jinja')
    archief_metadata = archief_template.render(data=archief_data)
    archief_metadata_path = dest_dir + os.sep + identificatiekenmerk + '.metadata'
    with open(archief_metadata_path, "w") as output:
        output.write(archief_metadata)
    # print (overdracht_bouwdossier)
    for bouwdossier in get_list_items(xml_top, 'bouwdossiers', 'bouwdossier'):
        dossier_id = bouwdossier.get('@oId')
        # print(f"oId:{dossier_id}")
        dossier_template = env.get_template('ToPX-2.3_Dossier_max.xml.jinja')
        bouwdossier_data = {
            'identificatiekenmerk': dossier_id,
            'naam': bouwdossier['dossiernummer']['#text'],  # ?? what is naam
            'omschrijving': bouwdossier['omschrijving']['#text'],
        }
        bouwdosjaar = bouwdossier.get('bouwdosjaar', {}).get('#text')
        dekking = None
        if bouwdosjaar:
            dekking = {
                'intijd': {
                    'begin': {
                        'jaar': bouwdosjaar
                    },
                    'eind': {
                        'jaar': bouwdosjaar
                    }
                }
            }
        adressen = [get_string_adres(adres) for adres in get_list_items(bouwdossier, 'adressen', 'adres')]
        if adressen:
            dekking['geografischgebied'] = {
                'adressen': adressen
            }
        if dekking:
            bouwdossier_data['dekking'] = dekking

        dossier_meta_data = dossier_template.render(data=bouwdossier_data)
        dossier_dest_dir = dest_dir + os.sep + identificatiekenmerk + os.sep
        dossier_metadata_path = dossier_dest_dir + dossier_id + '.metadata'
        Path(dossier_dest_dir).mkdir(parents=True, exist_ok=True)
        with open(dossier_metadata_path, "w") as output:
            output.write(dossier_meta_data)
        bestand_dest_dir = dossier_dest_dir + dossier_id + os.sep
        Path(bestand_dest_dir).mkdir(parents=True, exist_ok=True)
        for bijlage in get_list_items(bouwdossier, 'bijlagen', 'bijlage'):
            bestand_id = bijlage['@oId']
            document = bijlage['document']['#text']
            onderwerp = bijlage.get('onderwerp', {}).get('#text', '')
            bijlage_path = os.path.join(dms_dir, document)
            statinfo = os.stat(bijlage_path)
            bestand_size = statinfo.st_size
            if bestand_size == 0:
                log.error(f"Bestand with size 0 : {document}")
                continue
            sha256value = sha256(bijlage_path)

            if not os.path.exists(bijlage_path):
                log.error(f"Missing : {bijlage_path}")
                continue
            shutil.copyfile(bijlage_path, os.path.join(bestand_dest_dir, document))
            basename, extension = os.path.splitext(document)
            bestand_data = {
                'identificatiekenmerk': bestand_id,
                'naam' : document,
                'omschrijving': onderwerp,
                'vorm': 1,
                'formaat' : {
                    'identificatiekenmerk' : bestand_id,  # formaat identificatiekenmerk ????
                    'bestandsnaam' : {
                        'naam' : basename,
                        'extensie': extension
                    },
                    'omvang': bestand_size,
                    'fysiekeintegriteit' : {
                        'algoritme' : 'sha256',
                        'waarde': sha256value,
                        'datumentijd': datetime.now().isoformat()
                    }
                }
            }
            bestand_template = env.get_template('ToPX-2.3_Bestand_max.xml.jinja')
            bestand_meta_data = bestand_template.render(data=bestand_data)
            bestand_metadata_path = bestand_dest_dir + document + '.metadata'
            with open(bestand_metadata_path, "w") as output:
                output.write(bestand_meta_data)


if __name__ == "__main__":
    dms_dir = '/Users/bart/tmp/NHA/Eerste overdracht 1875 - 1900'
    dest_dir = dms_dir + '.sidecar'
    env = Environment(loader=PackageLoader('topx', 'templates'), trim_blocks=True, lstrip_blocks=True)
    import_bouwdossiers(env, dms_dir, dest_dir)








