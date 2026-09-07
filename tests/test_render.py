import json

import pytest

from renderer.render import render

def render_default(repo, output_format="all"):
    render("default", output_format, repo)
    return repo / "output"

def test_a_fresh_checkout_has_no_output_directory(cv_repo):
    # Guards the fixture itself: if output/ were copied in, the test below
    # would pass without the renderer ever having to create the directory.
    assert not (cv_repo / "output").exists()

def test_rendering_creates_the_output_directory_and_both_files(cv_repo):
    output = render_default(cv_repo)
    assert (output / "default.json").is_file()
    assert (output / "default.pdf").is_file()

def test_the_pdf_is_a_real_pdf_with_content(cv_repo):
    pdf = render_default(cv_repo) / "default.pdf"
    assert pdf.read_bytes().startswith(b"%PDF")
    assert pdf.stat().st_size > 1000

def test_the_json_carries_contact_details_and_every_section(cv_repo, repo_root):
    from renderer.render import load_sections

    _, manifest = load_sections(repo_root)
    output = render_default(cv_repo)
    data = json.loads((output / "default.json").read_text())
    assert data["contact"]["name"]
    assert list(data) == ["contact"] + [section.name for section in manifest.sections]

def test_asking_for_json_only_does_not_write_a_pdf(cv_repo):
    output = render_default(cv_repo, "json")
    assert (output / "default.json").is_file()
    assert not (output / "default.pdf").exists()

def test_asking_for_pdf_only_does_not_write_json(cv_repo):
    output = render_default(cv_repo, "pdf")
    assert (output / "default.pdf").is_file()
    assert not (output / "default.json").exists()

def test_rendering_twice_overwrites_rather_than_failing(cv_repo):
    render_default(cv_repo)
    first = (cv_repo / "output" / "default.json").read_text()
    render_default(cv_repo)
    assert (cv_repo / "output" / "default.json").read_text() == first

def test_a_variant_matching_nothing_stops_instead_of_writing_an_empty_cv(minimal_repo):
    (minimal_repo / "variants" / "empty.yaml").write_text("include_tags: [backend]\n")
    with pytest.raises(SystemExit) as exit_info:
        render("empty", "json", minimal_repo)
    assert "no sections matched" in str(exit_info.value)
    assert not (minimal_repo / "output").exists()

def test_a_missing_variant_file_is_not_silently_ignored(cv_repo):
    with pytest.raises(FileNotFoundError):
        render("does-not-exist", "json", cv_repo)
