import yaml

import pytest

from renderer.render import SHAPE_MODELS, load_contact_details, load_sections

def missing_keys(raw, parsed, path=""):
    """Every key present in the YAML must survive into the parsed model.

    A field name that does not match its model is silently dropped when the
    field is optional, which quietly removes real content from the CV instead
    of failing - this walks both structures and reports where that happened.
    """
    missing = []
    if isinstance(raw, dict) and isinstance(parsed, dict):
        for key, value in raw.items():
            if key not in parsed:
                missing.append(path + "/" + key)
                continue
            missing += missing_keys(value, parsed[key], path + "/" + key)
    elif isinstance(raw, list) and isinstance(parsed, list) and len(raw) == len(parsed):
        for index, value in enumerate(raw):
            missing += missing_keys(value, parsed[index], path + "[" + str(index) + "]")
    return missing

def manifest_sections(repo_root):
    _, manifest = load_sections(repo_root)
    return manifest.sections

def test_every_shape_named_in_the_manifest_has_a_model(repo_root):
    shapes = {section.shape for section in manifest_sections(repo_root)}
    assert shapes <= set(SHAPE_MODELS)

def test_every_section_file_parses_into_the_model_its_shape_names(repo_root):
    sections, manifest = load_sections(repo_root)
    for section in manifest.sections:
        assert isinstance(sections[section.name], SHAPE_MODELS[section.shape]), section.name

def test_no_section_is_empty_after_parsing(repo_root):
    sections, manifest = load_sections(repo_root)
    for section in manifest.sections:
        assert sections[section.name].model_dump(), section.name

def test_no_yaml_field_is_silently_dropped_during_parsing(repo_root):
    sections, manifest = load_sections(repo_root)
    for section in manifest.sections:
        with open(repo_root / "sections" / section.file, "rt") as fs:
            raw = yaml.safe_load(fs)
        parsed = sections[section.name].model_dump(mode="json")
        dropped = missing_keys(raw, parsed)
        assert dropped == [], section.name + " dropped " + ", ".join(dropped)

def test_contact_details_parse(repo_root):
    contact = load_contact_details(repo_root)
    assert contact.name
    assert contact.email
    assert contact.links

def test_an_unknown_shape_fails_loudly(minimal_repo):
    (minimal_repo / "manifest.yaml").write_text(
        "sections:\n"
        "  - name: summary\n"
        "    shape: not_a_real_shape\n"
        "    file: summary.yaml\n"
    )
    with pytest.raises(KeyError):
        load_sections(minimal_repo)
