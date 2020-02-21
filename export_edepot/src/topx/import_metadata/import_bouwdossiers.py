import argparse
from datetime import datetime
from jinja2 import Environment, PackageLoader
import logging
import os
from pathlib import Path
import shutil
import xmltodict

from topx.lib.utils import (
    get_list_items,
    find_first_file_extension,
    get_string_adres,
    import_bestand,
    import_archief,
    import_dossier,
)
from topx.settings import IGNORE_FILES

log = logging.getLogger(__name__)


def import_bouwdossiers_xml(dms_dir: str, dest_dir: str, template):
    """
    TopX structuur

    Archief
    Dossier
    Bestand

    Geen Serie of Record??
    """
    bestanden_processed = set()
    dms_xml_file = find_first_file_extension(dms_dir, ".xml")
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
        #        "aggregatie": "aggregatie",
        #        "aggregatie_niveau": "Archief",
        "identificatiekenmerk": identificatiekenmerk,
        "naam": xml_top["omschrijvingpublicatie"]["#text"],
        #        "omschrijving": "",
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
    archief_dir = import_archief(dms_dir, dest_dir, template, meta_data=archief_data)

    total_metadatafiles += 1
    for bouwdossier in get_list_items(xml_top, "bouwdossiers", "bouwdossier"):
        dossier_id = bouwdossier.get("@oId")
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

        dossier_dest_dir = import_dossier(
            archief_dir, archief_dir, template, meta_data=bouwdossier_data
        )
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
                "vorm": {"redactieGenre": bijlage["producthulpcategorie"].get("#text")},
                "openbaarheid": {
                    "openbaar": bijlage["vertrouwelijkheid"][
                        "#text"
                    ],  # ?? Vertrouwelijkheid bevat openbaarheid
                    "jaar": bouwdosjaar,  # ? gebruik bouwdosjaar
                },
            }
            import_bestand(
                bijlage_path, bestand_dest_dir, template, meta_data=meta_data
            )
            bestanden_processed.add(bijlage_path)
            total_metadatafiles += 1
    return total_metadatafiles, bestanden_processed, archief_dir


def import_bouwdossiers_rest(dms_dir, dest_dir, template, bestanden_processed):
    result = 0
    for root, subdirs, files in os.walk(dms_dir):
        for file in files:
            if file in IGNORE_FILES:
                continue
            fullpath = os.path.join(root, file)
            if fullpath not in bestanden_processed:
                import_bestand(fullpath, dest_dir, template)
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
    template = env.get_template("ToPX-2.3-template.xml")
    total_metadatafiles, bestanden_processed, archief_dir = import_bouwdossiers_xml(
        dms_dir, dest_dir, template
    )
    extra_metafiles = import_bouwdossiers_rest(
        dms_dir, archief_dir, template, bestanden_processed
    )
    total_metadatafiles += extra_metafiles
    log.info(f"Total metadata files : {total_metadatafiles}")
