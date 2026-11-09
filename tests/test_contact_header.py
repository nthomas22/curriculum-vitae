import json

from renderer.models import Contact, Link
from renderer.render import build_html, load_contact_details, render

def contact(**extra):
    return Contact(
        name="Nathan Thomas",
        email="someone@example.com",
        links=[Link(text="LinkedIn", url="https://www.linkedin.com/in/example/")],
        **extra,
    )

def test_the_headline_and_location_appear_under_the_name(repo_root):
    html = build_html(contact(headline="Full Stack Developer", location="Manchester, UK"), [], repo_root)
    assert '<p class="headline">Full Stack Developer</p>' in html
    assert "Manchester, UK" in html
    assert html.index("Nathan Thomas") < html.index("Full Stack Developer") < html.index("Manchester, UK")

def test_a_contact_without_a_headline_or_location_leaves_no_empty_lines(repo_root):
    html = build_html(contact(), [], repo_root)
    assert 'class="headline"' not in html
    assert html.count('class="contact-details"') == 1

def test_the_real_contact_details_have_a_headline_and_location(repo_root):
    details = load_contact_details(repo_root)
    assert details.headline
    assert details.location

def test_the_json_feed_carries_the_headline_and_location(cv_repo):
    render("default", "json", cv_repo)
    data = json.loads((cv_repo / "output" / "default.json").read_text())
    assert data["contact"]["headline"]
    assert data["contact"]["location"]
