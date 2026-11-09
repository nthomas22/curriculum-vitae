import json
import subprocess

import pytest

from pydantic import ValidationError

from renderer.models import FreeText, Variant
from renderer.render import apply_summary_override, render

def render_json(repo, variant):
    render(variant, "json", repo)
    return json.loads((repo / "output" / (variant + ".json")).read_text())

def test_a_variant_without_a_summary_leaves_the_sections_untouched():
    sections = {"summary": FreeText(text="Shared summary.", tags=["core"])}
    assert apply_summary_override(sections, "default", Variant(include_tags=[])) is sections

def test_a_variant_summary_replaces_the_shared_one():
    sections = {"summary": FreeText(text="Shared summary.", tags=["core"])}
    variant = Variant(include_tags=[], summary="Tailored summary.")
    assert apply_summary_override(sections, "devops", variant)["summary"].text == "Tailored summary."

def test_the_override_does_not_change_the_shared_sections():
    # The loaded sections are reused, e.g. across tests, so overriding must
    # build a new dictionary rather than editing the one it was given.
    sections = {"summary": FreeText(text="Shared summary.", tags=["core"])}
    apply_summary_override(sections, "devops", Variant(include_tags=[], summary="Tailored summary."))
    assert sections["summary"].text == "Shared summary."

def test_an_empty_summary_is_rejected_rather_than_rendering_a_blank_one():
    with pytest.raises(ValidationError):
        Variant(include_tags=[], summary="")

def test_the_tailored_summary_reaches_the_rendered_cv(cv_repo):
    (cv_repo / "variants" / "devops.yaml").write_text(
        "include_tags: [core]\n"
        "summary: A tailored summary for a DevOps role.\n"
    )
    data = render_json(cv_repo, "devops")
    assert data["summary"]["text"] == "A tailored summary for a DevOps role."

def test_the_tailored_summary_appears_even_when_the_shared_one_would_not(minimal_repo):
    # minimal_repo's shared summary is tagged niche, so a backend variant would
    # normally render nothing at all.
    (minimal_repo / "variants" / "backend.yaml").write_text(
        "include_tags: [backend]\n"
        "summary: A tailored summary.\n"
    )
    data = render_json(minimal_repo, "backend")
    assert data["summary"]["text"] == "A tailored summary."

def test_a_summary_with_no_summary_section_to_replace_stops_the_render(minimal_repo):
    (minimal_repo / "manifest.yaml").write_text(
        "sections:\n"
        "  - name: profile\n"
        "    shape: free_text\n"
        "    file: summary.yaml\n"
    )
    (minimal_repo / "variants" / "backend.yaml").write_text(
        "include_tags: [niche]\n"
        "summary: A tailored summary.\n"
    )
    with pytest.raises(SystemExit) as exit_info:
        render("backend", "json", minimal_repo)
    assert "no section named summary" in str(exit_info.value)
    assert not (minimal_repo / "output").exists()

def is_ignored_by_git(repo_root, path):
    result = subprocess.run(["git", "check-ignore", "--quiet", path], cwd=repo_root)
    return result.returncode == 0

def test_local_variants_are_kept_out_of_the_public_repo(repo_root):
    assert is_ignored_by_git(repo_root, "variants/local-acme-backend.yaml")

def test_ordinary_variants_are_still_committed(repo_root):
    assert not is_ignored_by_git(repo_root, "variants/default.yaml")
    assert not is_ignored_by_git(repo_root, "variants/devops.yaml")
