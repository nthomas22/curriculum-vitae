import shutil

from pathlib import Path

import pytest

DATA_FILES = ["manifest.yaml", "contact.yaml"]
DATA_DIRS = ["sections", "variants", "templates"]

@pytest.fixture
def repo_root():
    return Path(__file__).parent.parent

@pytest.fixture
def cv_repo(tmp_path, repo_root):
    # A copy of the real CV data with no output/ directory, standing in for a
    # fresh clone - the renderer has to create output/ itself.
    for file in DATA_FILES:
        shutil.copy2(repo_root / file, tmp_path / file)
    for directory in DATA_DIRS:
        shutil.copytree(repo_root / directory, tmp_path / directory)
    return tmp_path

@pytest.fixture
def minimal_repo(tmp_path, repo_root):
    # A one-section CV used for cases the real data cannot express, such as a
    # variant that matches nothing at all.
    (tmp_path / "sections").mkdir()
    (tmp_path / "variants").mkdir()
    shutil.copy2(repo_root / "contact.yaml", tmp_path / "contact.yaml")
    (tmp_path / "manifest.yaml").write_text(
        "sections:\n"
        "  - name: summary\n"
        "    shape: free_text\n"
        "    file: summary.yaml\n"
    )
    (tmp_path / "sections" / "summary.yaml").write_text(
        'text: "A summary."\n'
        "tags: [niche]\n"
    )
    return tmp_path
