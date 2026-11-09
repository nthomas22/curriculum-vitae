import shutil

from pathlib import Path

from renderer.render import MAX_PAGES, render, warn_if_too_long

# No test here checks the real CV's length - that is left to the warning, by
# choice, so a deliberately longer CV never breaks the build.

def add_templates(repo, repo_root):
    shutil.copytree(repo_root / "templates", repo / "templates")

def test_a_cv_at_the_limit_gives_no_warning(capsys):
    warn_if_too_long(Path("output/default.pdf"), MAX_PAGES)
    assert capsys.readouterr().err == ""

def test_a_cv_over_the_limit_warns_with_its_file_and_page_count(capsys):
    warn_if_too_long(Path("output/default.pdf"), MAX_PAGES + 1)
    warning = capsys.readouterr().err
    assert "output/default.pdf" in warning
    assert str(MAX_PAGES + 1) + " pages" in warning

def test_a_short_rendered_cv_gives_no_warning(minimal_repo, repo_root, capsys):
    add_templates(minimal_repo, repo_root)
    (minimal_repo / "variants" / "niche.yaml").write_text("include_tags: [niche]\n")
    render("niche", "pdf", minimal_repo)
    assert capsys.readouterr().err == ""

def test_a_long_rendered_cv_warns_but_is_still_written(minimal_repo, repo_root, capsys):
    add_templates(minimal_repo, repo_root)
    long_summary = "A sentence that pads the summary out well past two pages. " * 400
    (minimal_repo / "variants" / "long.yaml").write_text(
        "include_tags: [niche]\n"
        "summary: " + long_summary + "\n"
    )
    render("long", "pdf", minimal_repo)
    assert "over the " + str(MAX_PAGES) + "-page limit" in capsys.readouterr().err
    assert (minimal_repo / "output" / "long.pdf").is_file()
