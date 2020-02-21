import hashlib
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def sha256(fname):
    sha256_hash = hashlib.sha256()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
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


def find_first_file_extension(dms_dir: str, extension: str):
    dms_xml_file = None
    for file in os.listdir(dms_dir):
        if file.lower().endswith(extension):
            dms_xml_file = file
            break

    return dms_xml_file


def get_string_adres(adres: dict):
    straatnaam = adres["adresstraatnaam"].get("#text", "")
    aanduiding = adres["adresaanduiding"].get("#text", "")
    huisnummer = adres["adreshuisnummer"].get("#text", "")
    huisletter = adres["adreshuisletter"].get("#text", "")
    huisnummertoevoeging = adres["adreshuisnummertoevoeging"].get("#text", "")
    postcode = adres["adrespostcode"].get("#text", "")
    woonplaats = adres["adreswoonplaats"].get("#text", "")

    res = ""
    if aanduiding:
        res += aanduiding + " "
    if straatnaam:
        res += straatnaam
    if huisnummer:
        res += " " + huisnummer
    if huisletter:
        res += huisletter
    if huisnummertoevoeging:
        res += " " + huisnummertoevoeging
    if postcode or woonplaats:
        res += ","
    if postcode:
        res += " " + postcode
    if woonplaats:
        res += " " + woonplaats
    return res


def import_bestand(
    bestand_path, bestand_dest_dir, template, meta_data=None, relatie=None
):
    if meta_data is None:
        meta_data = {}

    path, document = os.path.split(bestand_path)
    basename, extension = os.path.splitext(document)
    extension = extension.lstrip(".")
    bestand_id = basename
    statinfo = os.stat(bestand_path)
    bestand_size = statinfo.st_size
    if not os.path.exists(bestand_path):
        log.error(f"Missing : {bestand_path}")
        return
    if bestand_size == 0:
        log.error(f"Bestand with size 0 : {document}")
        return
    sha256value = sha256(bestand_path)
    shutil.copyfile(bestand_path, os.path.join(bestand_dest_dir, document))
    new_meta_data = {
        "aggregatie": "bestand",
        "aggregatie_niveau": "Bestand",
        "identificatiekenmerk": bestand_id,
        "naam": basename,
        # 'omschrijving': onderwerp,
        "vorm": 1,
        "formaat": {
            "identificatiekenmerk": bestand_id,  # formaat identificatiekenmerk ????
            "bestandsnaam": {"naam": basename, "extensie": extension},
            "omvang": bestand_size,
            "fysiekeintegriteit": {
                "algoritme": "sha256",
                "waarde": sha256value,
                "datumentijd": datetime.now().isoformat(),
            },
        },
    }
    if relatie:
        new_meta_data["relatie"] = {
            "relatieID": relatie,
            "typeRelatie": "Maakt deel uit van",
        }

    new_meta_data.update(meta_data)
    bestand_meta_data = template.render(data=new_meta_data)
    bestand_metadata_path = os.path.join(bestand_dest_dir, document + ".metadata")
    with open(bestand_metadata_path, "w") as output:
        output.write(bestand_meta_data)


def import_archief(archief_path, dest_dir, template, meta_data=None):
    if meta_data is None:
        meta_data = {}

    path = os.path.split(archief_path)
    # Determine defaults

    new_meta_data = {
        "aggregatie": "aggregatie",
        "aggregatie_niveau": "Archief",
        "identificatiekenmerk": path[-1],
        "naam": path[-1],
    }
    new_meta_data.update(meta_data)
    identificatiekenmerk = new_meta_data["identificatiekenmerk"]
    archief_metadata = template.render(data=new_meta_data)
    archief_dir = dest_dir + os.sep + identificatiekenmerk + os.sep
    Path(archief_dir).mkdir(parents=True, exist_ok=True)
    archief_metadata_path = archief_dir + identificatiekenmerk + ".metadata"
    with open(archief_metadata_path, "w") as output:
        output.write(archief_metadata)
    return archief_dir


def import_dossier(dossier_path, dest_dir, template, meta_data=None, relatie=None):
    if meta_data is None:
        meta_data = {}

    path = os.path.split(dossier_path)
    # Determine defaults
    new_meta_data = {
        "aggregatie": "aggregatie",
        "aggregatie_niveau": "Dossier",
        "identificatiekenmerk": path[-1],
        "naam": path[-1],
    }
    if relatie:
        new_meta_data["relatie"] = {
            "relatieID": relatie,
            "typeRelatie": "Maakt deel uit van",
        }

    new_meta_data.update(meta_data)
    identificatiekenmerk = new_meta_data["identificatiekenmerk"]
    dossier_metadata = template.render(data=new_meta_data)
    dossier_dir = dest_dir + os.sep + identificatiekenmerk + os.sep
    Path(dossier_dir).mkdir(parents=True, exist_ok=True)
    archief_metadata_path = dossier_dir + identificatiekenmerk + ".metadata"
    with open(archief_metadata_path, "w") as output:
        output.write(dossier_metadata)
    return dossier_dir
