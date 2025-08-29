from pathlib import Path
from collections import Counter, defaultdict
from rdflib import Graph
from tqdm import tqdm

# folder to search
DATA_ROOT = Path("data")

SKOS_NS = "http://www.w3.org/2004/02/skos/core#"
OWL_NS  = "http://www.w3.org/2002/07/owl#"

def iter_component_xml(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and path.name in {"source.xml", "target.xml"}:
            yield path

def extract_terms_from_graph(g: Graph):
    skos_terms = set()
    owl_terms  = set()
    for s, p, o in g:
        for term in (s, p, o):
            iri = str(term)
            if iri.startswith(SKOS_NS):
                skos_terms.add(iri)
            elif iri.startswith(OWL_NS):
                owl_terms.add(iri)
    return skos_terms, owl_terms

def main():
    all_skos = set()
    all_owl  = set()
    skos_counts = Counter()
    owl_counts  = Counter()
    per_file = defaultdict(lambda: {"skos": set(), "owl": set()})

    files = sorted(iter_component_xml(DATA_ROOT))
    if not files:
        print(f"No source.xml or target.xml found under: {DATA_ROOT.resolve()}")
        return

    print(f"Found {len(files)} files. Parsing...\n")
    for f in tqdm(files, desc="Parsing RDF/XML files", unit="file"):
        g = Graph()
        try:
            # disable datatype normalization to avoid strict ISO 8601 parsing issues
            g.parse(f.as_posix(), format="xml", datatype_normalization=False)
        except Exception as e:
            tqdm.write(f"[WARN] Failed to parse {f}: {e}")
            continue

        skos_terms, owl_terms = extract_terms_from_graph(g)

        per_file[f]["skos"] = skos_terms
        per_file[f]["owl"]  = owl_terms

        all_skos |= skos_terms
        all_owl  |= owl_terms
        skos_counts.update(skos_terms)
        owl_counts.update(owl_terms)

    # summary
    print("=== SKOS terms (unique across all files) ===")
    for iri in sorted(all_skos):
        print(iri)
    print(f"\nTotal unique SKOS terms: {len(all_skos)}")

    print("\n=== OWL terms (unique across all files) ===")
    for iri in sorted(all_owl):
        print(iri)
    print(f"\nTotal unique OWL terms: {len(all_owl)}")

    # frequency (in how many files each term appears)
    if all_skos:
        print("\n=== SKOS term frequency (number of files containing the term) ===")
        for iri, cnt in skos_counts.most_common():
            print(f"{cnt:3d}  {iri}")
    if all_owl:
        print("\n=== OWL term frequency (number of files containing the term) ===")
        for iri, cnt in owl_counts.most_common():
            print(f"{cnt:3d}  {iri}")

    # optional: per-file listing
    # print("\n=== Per-file terms (brief) ===")
    # for f in files:
    #     sk = sorted(per_file[f]["skos"])
    #     ow = sorted(per_file[f]["owl"])
    #     print(f"\n{f}")
    #     print(f"  SKOS ({len(sk)}):")
    #     for iri in sk:
    #         print(f"    - {iri}")
    #     print(f"  OWL  ({len(ow)}):")
    #     for iri in ow:
    #         print(f"    - {iri}")

if __name__ == "__main__":
    main()