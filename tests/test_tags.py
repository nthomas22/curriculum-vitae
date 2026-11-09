import pytest

from pydantic import ValidationError

from renderer.models import TagVocabulary
from renderer.render import (
    collect_tags,
    find_unknown_tags,
    load_sections,
    load_tag_vocabulary,
    load_variant,
    render,
)

def write_experience(repo, highlight_tags, entry_tags):
    (repo / "manifest.yaml").write_text(
        "sections:\n"
        "  - name: experience\n"
        "    shape: entry_list_dated\n"
        "    file: experience.yaml\n"
    )
    (repo / "sections" / "experience.yaml").write_text(
        "entries:\n"
        "  - title: Developer\n"
        "    organisation: Crown Gas & Power\n"
        "    start_date: 2020-01-01\n"
        "    highlights:\n"
        "      - Untagged.\n"
        "      - text: Tagged.\n"
        "        tags: " + highlight_tags + "\n"
        "    tags: " + entry_tags + "\n"
    )
    (repo / "variants" / "devops.yaml").write_text("include_tags: [devops]\n")

def render_and_expect_failure(repo, variant):
    with pytest.raises(SystemExit) as exit_info:
        render(variant, "all", repo)
    assert not (repo / "output").exists()
    return str(exit_info.value)

def test_the_real_tag_list_parses_and_includes_core(repo_root):
    vocabulary = load_tag_vocabulary(repo_root)
    assert "core" in vocabulary
    assert all(meaning.strip() for meaning in vocabulary.values())

def test_the_real_sections_and_every_variant_only_use_listed_tags(repo_root):
    sections, _ = load_sections(repo_root)
    vocabulary = load_tag_vocabulary(repo_root)
    for variant_file in (repo_root / "variants").glob("*.yaml"):
        variant = load_variant(variant_file.stem, repo_root)
        assert find_unknown_tags(sections, variant_file.stem, variant, vocabulary) == []

def test_a_tag_with_no_meaning_is_rejected():
    with pytest.raises(ValidationError):
        TagVocabulary({"core": None})

def test_tags_are_collected_from_entries_and_lines_with_their_location():
    data = {
        "entries": [
            {"highlights": ["Plain.", {"text": "Tagged.", "tags": ["devops"]}], "tags": ["core"]},
        ]
    }
    assert sorted(collect_tags(data, "experience")) == [
        ("experience.entries[0]", "core"),
        ("experience.entries[0].highlights[1]", "devops"),
    ]

def test_an_unknown_tag_on_an_entry_stops_the_render(minimal_repo):
    write_experience(minimal_repo, highlight_tags="[devops]", entry_tags="[core, devosp]")
    message = render_and_expect_failure(minimal_repo, "devops")
    assert "experience.entries[0]: devosp" in message

def test_an_unknown_tag_on_a_single_line_stops_the_render(minimal_repo):
    write_experience(minimal_repo, highlight_tags="[devosp]", entry_tags="[core]")
    message = render_and_expect_failure(minimal_repo, "devops")
    assert "experience.entries[0].highlights[1]: devosp" in message

def test_an_unknown_tag_in_the_variant_stops_the_render(minimal_repo):
    (minimal_repo / "variants" / "typo.yaml").write_text("include_tags: [nihce]\n")
    message = render_and_expect_failure(minimal_repo, "typo")
    assert "variants/typo.yaml: nihce" in message

def test_unknown_tags_are_reported_even_on_content_the_variant_would_leave_out(minimal_repo):
    # The check covers the whole bank, not just what this variant renders, so a
    # typo is caught the first time anything is rendered rather than the day a
    # variant finally asks for that tag.
    write_experience(minimal_repo, highlight_tags="[frontedn]", entry_tags="[core]")
    message = render_and_expect_failure(minimal_repo, "devops")
    assert "frontedn" in message

def test_every_unknown_tag_is_reported_at_once(minimal_repo):
    write_experience(minimal_repo, highlight_tags="[devosp]", entry_tags="[croe]")
    message = render_and_expect_failure(minimal_repo, "devops")
    assert "devosp" in message and "croe" in message

def test_a_missing_tag_list_is_not_silently_ignored(cv_repo):
    (cv_repo / "tags.yaml").unlink()
    with pytest.raises(FileNotFoundError):
        render("default", "json", cv_repo)
