import csv
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from pathlib import Path
from typing import Optional


def csv_to_alignment_api(
    input_csv_path: str,
    output_xml_path: str,
    relation: str = "=",
    measure: Optional[float] = None,
    onto1: Optional[str] = None,
    onto2: Optional[str] = None,
    type_value: str = "??",
) -> None:
    """
    Generate Alignment API RDF/XML with exact header:
    <?xml version="1.0" encoding="utf-8"?>
    <rdf:RDF xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment#"
             xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema#">
    """

    NS_ALIGN = "http://knowledgeweb.semanticweb.org/heterogeneity/alignment#"
    NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    NS_XSD = "http://www.w3.org/2001/XMLSchema#"

    # Manually build <rdf:RDF> with all namespace declarations
    rdf_root = Element(
        "rdf:RDF",
        {
            "xmlns": NS_ALIGN,
            "xmlns:rdf": NS_RDF,
            "xmlns:xsd": NS_XSD,
        },
    )

    alignment = SubElement(rdf_root, "Alignment")
    SubElement(alignment, "xml").text = "yes"
    SubElement(alignment, "level").text = "0"
    SubElement(alignment, "type").text = str(type_value)

    if onto1:
        SubElement(alignment, "onto1").text = str(onto1)
    if onto2:
        SubElement(alignment, "onto2").text = str(onto2)

    with open(input_csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or any(c not in reader.fieldnames for c in ("Entity1", "Entity2")):
            raise ValueError("CSV must have columns: Entity1, Entity2")

        for row in reader:
            e1 = (row.get("Entity1") or "").strip()
            e2 = (row.get("Entity2") or "").strip()
            if not e1 or not e2:
                continue

            map_el = SubElement(alignment, "map")
            cell = SubElement(map_el, "Cell")
            SubElement(cell, "entity1", {"rdf:resource": e1})
            SubElement(cell, "entity2", {"rdf:resource": e2})

            if measure is not None:
                SubElement(
                    cell,
                    "measure",
                    {"rdf:datatype": f"xsd:float"},
                ).text = f"{float(measure):.1f}"  # always one decimal place

            SubElement(cell, "relation").text = relation

    # Pretty print with exact XML header
    rough_xml = tostring(rdf_root, encoding="utf-8")
    pretty = minidom.parseString(rough_xml).toprettyxml(indent="  ", encoding="utf-8")

    with open(output_xml_path, "wb") as out:
        out.write(pretty)


def batch_convert_predict_csv_to_xml(
    root_dir: str,
    source_file: str,
    target_file: str,
    relation: str = "=",
    measure: Optional[float] = None,
    onto1: Optional[str] = None,
    onto2: Optional[str] = None,
):
    """
    Recursively find all predict.csv files under root_dir and generate predict.xml
    in the same directory using csv_to_alignment_api.
    """
    root = Path(root_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root folder not found: {root}")

    converted = 0
    for csv_path in root.rglob(source_file):
        xml_path = csv_path.with_name(target_file)
        try:
            print(f"[INFO] Converting: {csv_path} -> {xml_path}")
            csv_to_alignment_api(
                str(csv_path),
                str(xml_path),
                relation=relation,
                measure=measure,
                onto1=onto1,
                onto2=onto2,
            )
            converted += 1
        except Exception as e:
            print(f"[ERROR] Failed on {csv_path}: {e}")

    print(f"[DONE] Converted {converted} file(s).")
    return converted


# Example usage
if __name__ == "__main__":
    batch_convert_predict_csv_to_xml(
        root_dir="campaign/OAEI_2025",
        source_file="predict.csv",
        target_file="predict.xml",
        relation="=",
        # measure=0.9,
        # onto1="CMT",
        # onto2="Conference"
    )

    # csv_to_alignment_api(
    #     "predict.csv",
    #     "predict.xml",
    #     relation="=",
    #     # measure=0.9,
    #     # onto1="CMT",
    #     # onto2="Conference"
    #     )