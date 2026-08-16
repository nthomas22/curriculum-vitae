import argparse
import sys
import yaml
import json

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from renderer.models import Contact, Categorised, EntryListDated, FreeText, Manifest, TaggedList, Variant

# output/ is gitignored, so it does not exist in a fresh clone - both writers
# create it on demand rather than assuming it is already there.
OUTPUT_DIR = Path("./output")

SHAPE_MODELS = {
    "categorised": Categorised,
    "entry_list_dated": EntryListDated,
    "free_text": FreeText,
    "tagged_list": TaggedList
}

def matches(item_tags, include_tags):
    return bool(set(item_tags) & include_tags)

def filter_free_text(data, include_tags):
    if matches(data.tags, include_tags):
        return data
    return None

def filter_entry_list_dated(data, include_tags):
    filtered = [
        datum for datum in data.entries
        if matches(datum.tags, include_tags)
    ]
    if len(filtered) == 0:
        return None
    return EntryListDated(entries=sorted(filtered, key=lambda item: item.start_date, reverse=True)) 

def filter_categorised(data, include_tags):
    filtered = [
        datum for datum in data.categories
        if matches(datum.tags, include_tags)
    ]
    if len(filtered) == 0:
        return None
    return Categorised(categories=filtered) 

def filter_tagged_list(data, include_tags):
    filtered = [
        datum for datum in data.entries
        if matches(datum.tags, include_tags)
    ]
    if len(filtered) == 0:
        return None
    return TaggedList(entries=filtered) 

SHAPE_FILTERS = {
    Categorised: filter_categorised,
    EntryListDated: filter_entry_list_dated,
    FreeText: filter_free_text,
    TaggedList: filter_tagged_list,
}

def parse_args():
    parser = argparse.ArgumentParser(description="Render a CV variant to PDF and/or JSON.")
    parser.add_argument("--variant", required=True, help="Name of the variant file under variants/, without .yaml")
    parser.add_argument("--format", choices=["pdf", "json", "all"], default="all")
    return parser.parse_args()

def load_variant(variant):
    with open('./variants/' + variant + '.yaml', 'rt') as fs: variant_data_raw = yaml.safe_load(fs)
    return Variant(**variant_data_raw)

def load_contact_details():
    with open('./contact.yaml', 'rt') as fs: contact_data_raw = yaml.safe_load(fs)
    return Contact(**contact_data_raw)

def load_sections():
    with open('./manifest.yaml', 'rt') as fs: manifest_data_raw = yaml.safe_load(fs)
    sections = dict()
    manifest = Manifest(**manifest_data_raw)
    for section in manifest.sections:
        name = section.name
        file = section.file
        with open('./sections/' + file, 'rt') as fs: section_data_raw = yaml.safe_load(fs)
        model_class = SHAPE_MODELS[section.shape]
        section_data = model_class(**section_data_raw)
        sections[name] = section_data
    return sections, manifest

def write_to_file(variant, data):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / (variant + ".json"), "w") as file:
        json.dump(data, file, indent=2)

def render_json(variant, contact, filtered_sections):
    output = dict()
    output["contact"] = contact.model_dump(mode="json")
    for section in filtered_sections:
        output[section["name"]] = section["data"].model_dump(mode="json")
    write_to_file(variant, output)

def render_pdf(variant, contact, filtered_sections):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("cv.html.j2")
    html_content = template.render(contact=contact, sections=filtered_sections)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML(string=html_content, base_url="templates").write_pdf(
        OUTPUT_DIR / (variant + ".pdf"),
        stylesheets=["templates/cv.css"],
    )

def main():
    parsedArguments = parse_args()
    sections, manifest = load_sections()
    variant = load_variant(parsedArguments.variant)
    contact = load_contact_details()
    tagsToInclude = set(variant.include_tags) | {"core"}

    filtered_sections = []
    for section in manifest.sections:
        data = sections[section.name]
        filtered = SHAPE_FILTERS[type(data)](data, tagsToInclude)
        if filtered is not None:
            filtered_sections.append({"name": section.name, "shape": section.shape, "data": filtered})

    if len(filtered_sections) <= 0:
        sys.exit("Error: no sections matched the given tags - check your variant file.")

    if parsedArguments.format in ("json", "all"):
        render_json(parsedArguments.variant, contact, filtered_sections)
    if parsedArguments.format in ("pdf", "all"):
        render_pdf(parsedArguments.variant, contact, filtered_sections)


if __name__ == "__main__": main()