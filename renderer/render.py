import argparse
import sys
import yaml
import json

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from renderer.models import Contact, Categorised, EntryListDated, FreeText, Manifest, TaggedList, Variant

# Every path is resolved against a root rather than the process working directory
# so tests can point the renderer at a throwaway copy of the repo.
DEFAULT_ROOT = Path(".")

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

def filter_lines(lines, include_tags):
    # Untagged lines go wherever their parent entry goes; tagged lines must also
    # match the variant themselves. Either way only the text is kept, so the
    # template and JSON feed never see the tags.
    return [
        line if isinstance(line, str) else line.text
        for line in lines
        if isinstance(line, str) or matches(line.tags, include_tags)
    ]

def filter_entry_list_dated(data, include_tags):
    filtered = [
        datum.model_copy(update={"highlights": filter_lines(datum.highlights, include_tags)})
        for datum in data.entries
        if matches(datum.tags, include_tags)
    ]
    if len(filtered) == 0:
        return None
    return EntryListDated(entries=sorted(filtered, key=lambda item: item.start_date, reverse=True)) 

def filter_categorised(data, include_tags):
    filtered = [
        datum.model_copy(update={"items": filter_lines(datum.items, include_tags)})
        for datum in data.categories
        if matches(datum.tags, include_tags)
    ]
    # A category whose items were all filtered out would render as a bare heading.
    filtered = [datum for datum in filtered if len(datum.items) > 0]
    if len(filtered) == 0:
        return None
    return Categorised(categories=filtered) 

def filter_tagged_list(data, include_tags):
    filtered = [
        datum.model_copy(update={"details": filter_lines(datum.details, include_tags)})
        for datum in data.entries
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

def load_variant(variant, root=DEFAULT_ROOT):
    with open(root / "variants" / (variant + ".yaml"), 'rt') as fs: variant_data_raw = yaml.safe_load(fs)
    return Variant(**variant_data_raw)

def load_contact_details(root=DEFAULT_ROOT):
    with open(root / "contact.yaml", 'rt') as fs: contact_data_raw = yaml.safe_load(fs)
    return Contact(**contact_data_raw)

def load_sections(root=DEFAULT_ROOT):
    with open(root / "manifest.yaml", 'rt') as fs: manifest_data_raw = yaml.safe_load(fs)
    sections = dict()
    manifest = Manifest(**manifest_data_raw)
    for section in manifest.sections:
        name = section.name
        file = section.file
        with open(root / "sections" / file, 'rt') as fs: section_data_raw = yaml.safe_load(fs)
        model_class = SHAPE_MODELS[section.shape]
        section_data = model_class(**section_data_raw)
        sections[name] = section_data
    return sections, manifest

def resolve_tags(variant):
    # "core" is what every CV keeps no matter which variant is being rendered,
    # so it is added on top of whatever the variant itself asked for.
    return set(variant.include_tags) | {"core"}

def filter_sections(sections, manifest, include_tags):
    filtered_sections = []
    for section in manifest.sections:
        data = sections[section.name]
        filtered = SHAPE_FILTERS[type(data)](data, include_tags)
        if filtered is not None:
            filtered_sections.append({"name": section.name, "shape": section.shape, "data": filtered})
    return filtered_sections

def prepare_output_dir(root):
    # output/ is gitignored, so it does not exist in a fresh clone - it is created
    # on demand rather than assumed to be there.
    directory = root / "output"
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def write_to_file(variant, data, root=DEFAULT_ROOT):
    directory = prepare_output_dir(root)
    with open(directory / (variant + ".json"), "w") as file:
        json.dump(data, file, indent=2)

def render_json(variant, contact, filtered_sections, root=DEFAULT_ROOT):
    output = dict()
    output["contact"] = contact.model_dump(mode="json")
    for section in filtered_sections:
        output[section["name"]] = section["data"].model_dump(mode="json")
    write_to_file(variant, output, root)

def render_pdf(variant, contact, filtered_sections, root=DEFAULT_ROOT):
    templates = root / "templates"
    env = Environment(loader=FileSystemLoader(templates))
    template = env.get_template("cv.html.j2")
    html_content = template.render(contact=contact, sections=filtered_sections)
    directory = prepare_output_dir(root)
    HTML(string=html_content, base_url=str(templates)).write_pdf(
        directory / (variant + ".pdf"),
        stylesheets=[templates / "cv.css"],
    )

def render(variant_name, output_format, root=DEFAULT_ROOT):
    sections, manifest = load_sections(root)
    variant = load_variant(variant_name, root)
    contact = load_contact_details(root)
    tagsToInclude = resolve_tags(variant)

    filtered_sections = filter_sections(sections, manifest, tagsToInclude)

    if len(filtered_sections) <= 0:
        sys.exit("Error: no sections matched the given tags - check your variant file.")

    if output_format in ("json", "all"):
        render_json(variant_name, contact, filtered_sections, root)
    if output_format in ("pdf", "all"):
        render_pdf(variant_name, contact, filtered_sections, root)

def main():
    parsedArguments = parse_args()
    render(parsedArguments.variant, parsedArguments.format)


if __name__ == "__main__": main()
