import json
import xml.etree.ElementTree as ET

from dataclasses import asdict
from pathlib import Path

from .models import Event
from .data_service import LinkedObservation


def prepare_data(results, data_type):
    if data_type == "events":
        return [asdict(event) for event in results]

    if data_type == "observations":
        return [
            {
                "observation": asdict(record.observation),
                "event": asdict(record.event),
                "location": asdict(record.location),
            }
            for record in results
        ]

    raise ValueError(f"Unsupported export type: {data_type}")


def export_json(results, data_type, path: Path):
    data = {
        "type": data_type,
        "results": prepare_data(results, data_type),
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def add_xml_data(parent, data):
    for key, value in data.items():
        if key == "id":
            parent.set("id", str(value))
            continue

        element = ET.SubElement(parent, key)

        if isinstance(value, dict):
            add_xml_data(element, value)

        elif isinstance(value, list):
            item_tag = {"objects": "object"}.get(key, "element")
            for item in value:
                child = ET.SubElement(element, item_tag)
                child.text = str(item)

        elif value is not None:
            element.text = str(value)


def export_xml(results, data_type, path: Path):
    root = ET.Element("filtered", type=data_type)
    data = prepare_data(results, data_type)

    if data_type == "events":
        for event in data:
            element = ET.SubElement(root, "event")
            add_xml_data(element, event)

    elif data_type == "observations":
        for record in data:
            element = ET.SubElement(root, "observation")
            add_xml_data(element, record["observation"])

            event = ET.SubElement(element, "event")
            add_xml_data(event, record["event"])

            location = ET.SubElement(element, "location")
            add_xml_data(location, record["location"])

    else:
        raise ValueError(f"Unsupported export type: {data_type}")

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def export_results(results, data_type, directory: Path):
    export_json(results, data_type, directory / "filtrirano.json")
    export_xml(results, data_type, directory / "filtrirano.xml")
