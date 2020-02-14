import argparse
from datetime import datetime
from jinja2 import Environment, PackageLoader
import hashlib
import logging
import os
from pathlib import Path
import shutil
import xmltodict

log = logging.getLogger(__name__)

IGNORE_FILES = {".DS_Store"}


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


def find_first_xml_file(dms_dir: str):
    dms_xml_file = None
    for file in os.listdir(dms_dir):
        if file.endswith(".xml"):
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


def import_bestand(bestand_path, bestand_dest_dir, meta_data=None):
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
    new_meta_data.update(meta_data)
    bestand_template = env.get_template("ToPX-2.3-template.xml")
    bestand_meta_data = bestand_template.render(data=new_meta_data)
    bestand_metadata_path = os.path.join(bestand_dest_dir, document + ".metadata")
    with open(bestand_metadata_path, "w") as output:
        output.write(bestand_meta_data)


def import_bouwdossiers_xml(env, dms_dir: str, dest_dir: str):
    """
    TopX structuur

    Archief
    Dossier
    Bestand

    Geen Serie of Record??
    """
    bestanden_processed = set()
    dms_xml_file = find_first_xml_file(dms_dir)
    if not dms_xml_file:
        log.error("Geen XML gevonden in {dms_dir}")
        return

    total_metadatafiles = 0
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    file_path = dms_dir + os.sep + dms_xml_file
    with open(file_path) as fd:
        xml = xmltodict.parse(fd.read())

    file_base = os.path.splitext(dms_xml_file)[0]
    xml_top = xml.get("overdracht_bouwdossier")
    identificatiekenmerk = xml_top["@id"]
    archief_data = {
        "aggregatie": "aggregatie",
        "aggregatie_niveau": "Archief",
        "identificatiekenmerk": identificatiekenmerk,
        "naam": xml_top["omschrijvingpublicatie"]["#text"],
        "omschrijving": "",
        "classificatie": {
            "code": xml_top["@classid"],
            "omschrijving": xml_top["action"],  # ??
            "datum": datetime.fromisoformat(
                xml_top["datumpublicatie"]["@valuecode"]
            ).strftime(
                "%Y-%m-%d"
            ),  # ???
            "bron": xml_top["@soort"],  # ??
        },
    }
    archief_template = env.get_template("ToPX-2.3-template.xml")
    archief_metadata = archief_template.render(data=archief_data)
    archief_dir = dest_dir + os.sep + identificatiekenmerk + os.sep
    Path(archief_dir).mkdir(parents=True, exist_ok=True)
    archief_metadata_path = archief_dir + identificatiekenmerk + ".metadata"
    with open(archief_metadata_path, "w") as output:
        output.write(archief_metadata)
    total_metadatafiles += 1
    for bouwdossier in get_list_items(xml_top, "bouwdossiers", "bouwdossier"):
        dossier_id = bouwdossier.get("@oId")
        dossier_template = env.get_template("ToPX-2.3-template.xml")
        bouwdosjaar = bouwdossier.get("bouwdosjaar", {}).get("#text")
        omschrijving = " ".join(
            [
                bouwdossier["bouwdoscategorie"].get("#text", ""),
                bouwdossier["bouwdosomschrijving"].get("#text", ""),
                bouwdossier["omschrijving"].get("#text", ""),
            ]
        )

        bouwdossier_data = {
            "aggregatie": "aggregatie",
            "aggregatie_niveau": "Dossier",
            "identificatiekenmerk": dossier_id,
            "naam": bouwdossier["dossiernummer"]["#text"],  # ?? what is naam
            "omschrijving": omschrijving,
            "openbaarheid": {
                "openbaar": bouwdossier["vertrouwelijkheid"][
                    "#text"
                ],  # ?? Vertrouwelijkheid bevat openbaarheid
                "jaar": bouwdosjaar,
            },
            "externIdentificatiekenmerk": {
                "nummerBinnenSysteem": bouwdossier["bouwvergnummer"]["#text"],
                "kenmerkSysteem": "Bouwvergunningnummer",
            },
        }
        dekking = None
        if bouwdosjaar:
            dekking = {
                "intijd": {
                    "begin": {"jaar": bouwdosjaar},
                    "eind": {"jaar": bouwdosjaar},
                }
            }
        adressen = [
            get_string_adres(adres)
            for adres in get_list_items(bouwdossier, "adressen", "adres")
        ]
        if adressen:
            dekking["geografischgebied"] = {"adressen": adressen}
        if dekking:
            bouwdossier_data["dekking"] = dekking

        dossier_meta_data = dossier_template.render(data=bouwdossier_data)
        dossier_dest_dir = archief_dir + dossier_id + os.sep
        dossier_metadata_path = dossier_dest_dir + dossier_id + ".metadata"
        Path(dossier_dest_dir).mkdir(parents=True, exist_ok=True)
        with open(dossier_metadata_path, "w") as output:
            output.write(dossier_meta_data)
        total_metadatafiles += 1
        bestand_dest_dir = dossier_dest_dir
        Path(bestand_dest_dir).mkdir(parents=True, exist_ok=True)
        for bijlage in get_list_items(bouwdossier, "bijlagen", "bijlage"):
            bestand_id = bijlage["@oId"]
            document = bijlage["document"]["#text"]
            onderwerp = bijlage.get("onderwerp", {}).get("#text", "")
            bijlage_path = os.path.join(dms_dir, document)

            meta_data = {
                "identificatiekenmerk": bestand_id,
                "naam": onderwerp,
                # 'omschrijving': onderwerp,
                "vorm": {"redactieGenre": bijlage["producthulpcategorie"].get("#text")},
                "openbaarheid": {
                    "openbaar": bijlage["vertrouwelijkheid"][
                        "#text"
                    ],  # ?? Vertrouwelijkheid bevat openbaarheid
                    "jaar": bouwdosjaar,  # ? gebruik bouwdosjaar
                },
            }
            import_bestand(bijlage_path, bestand_dest_dir, meta_data=meta_data)
            bestanden_processed.add(bijlage_path)
            total_metadatafiles += 1
    return total_metadatafiles, bestanden_processed


def import_bouwdossiers_rest(env, dms_dir, dest_dir, bestanden_processed):
    result = 0
    for root, subdirs, files in os.walk(dms_dir):
        for file in files:
            if file in IGNORE_FILES:
                continue
            fullpath = os.path.join(root, file)
            if fullpath not in bestanden_processed:
                import_bestand(fullpath, dest_dir)
                result += 1
    return result


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
    total_metadatafiles, bestanden_processed = import_bouwdossiers_xml(
        env, dms_dir, dest_dir
    )
    extra_metafiles = import_bouwdossiers_rest(
        env, dms_dir, dest_dir, bestanden_processed
    )
    total_metadatafiles += extra_metafiles
    log.info(f"Total metadata files : {total_metadatafiles}")
