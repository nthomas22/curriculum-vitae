import json

import pytest

from pydantic import ValidationError

from renderer.models import Contact, Link, Variant
from renderer.render import apply_headline_override, load_contact_details, render

def contact(headline=None):
    return Contact(
        name="Nathan Thomas",
        headline=headline,
        email="someone@example.com",
        links=[Link(text="LinkedIn", url="https://www.linkedin.com/in/example/")],
    )

def test_a_variant_without_a_headline_keeps_the_shared_one():
    shared = contact("Full Stack Developer")
    assert apply_headline_override(shared, Variant(include_tags=[])) is shared

def test_a_variant_headline_replaces_the_shared_one():
    variant = Variant(include_tags=[], headline="Senior Developer | DevOps")
    assert apply_headline_override(contact("Full Stack Developer"), variant).headline == "Senior Developer | DevOps"

def test_a_variant_headline_is_used_even_when_there_is_no_shared_one():
    variant = Variant(include_tags=[], headline="Senior Developer")
    assert apply_headline_override(contact(), variant).headline == "Senior Developer"

def test_the_override_does_not_change_the_shared_contact_details():
    shared = contact("Full Stack Developer")
    apply_headline_override(shared, Variant(include_tags=[], headline="Senior Developer"))
    assert shared.headline == "Full Stack Developer"

def test_an_empty_headline_is_rejected():
    with pytest.raises(ValidationError):
        Variant(include_tags=[], headline="")

def test_the_variant_headline_reaches_the_rendered_cv(cv_repo):
    (cv_repo / "variants" / "senior.yaml").write_text(
        "include_tags: [core]\n"
        "headline: Senior Developer | DevOps\n"
    )
    render("senior", "json", cv_repo)
    data = json.loads((cv_repo / "output" / "senior.json").read_text())
    assert data["contact"]["headline"] == "Senior Developer | DevOps"

def test_other_variants_keep_the_shared_headline(cv_repo, repo_root):
    render("default", "json", cv_repo)
    data = json.loads((cv_repo / "output" / "default.json").read_text())
    assert data["contact"]["headline"] == load_contact_details(repo_root).headline
