<h1 align="center">curriculum-vitae</h1>

<p align="center">
  <strong>A structured, tag-driven CV that renders to PDF and JSON from a single source of truth.</strong>
</p>

## Summary

Applying for jobs is a time consuming task. This project aims to alleviate some of that by providing a simple version controlled way of constructing a CV using a set of existing CV data and customisable variants. Each variant could be job specific or role specific (your choice!). Simply add your data, specify the variants and let it do the rest of the work.

## Pre-requisites

- **Python 3.12+** - the exact version is pinned in `.python-version`.
- **uv** - manages the virtual environment and dependencies. Install with `curl -LsSf https://astral.sh/uv/install.sh | sh` (see the [uv docs](https://docs.astral.sh/uv/) for other platforms).

No other system-level packages are required - WeasyPrint (used for PDF output) is pure Python from v53 onwards, so `uv sync` installs everything needed.

## Setup

```bash
git clone https://github.com/nthomas22/curriculum-vitae.git
cd curriculum-vitae
uv sync
```

## Usage

```bash
uv run python -m renderer.render --variant <variant-name> --format <pdf|json|all>
```

- `--variant <variant-name>` - required. The name of a file under `variants/`, without the `.yaml` extension - e.g. `default` for `variants/default.yaml`. A variant is a list of tags to include; entries tagged `core` are always included regardless of variant.
- `--format` - one of `pdf`, `json`, or `all`. Defaults to `all`.

Example - render the default variant to both formats:

```bash
uv run python -m renderer.render --variant default --format all
```

This writes `output/default.json` and `output/default.pdf`. The PDF is built from `templates/cv.html.j2` and `templates/cv.css` - a single-column, black-and-white layout intended to parse cleanly in Applicant Tracking Systems.

## Structure

```bash
curriculum-vitae
├── .github
│   └── CODEOWNERS
├── README.md
├── contact.yaml
├── manifest.yaml
├── output
│   └── The CV files you generate
├── pyproject.toml
├── renderer
│   ├── __init__.py
│   ├── models.py
│   └── render.py
├── sections
│   ├── additional_info.yaml
│   ├── education.yaml
│   ├── experience.yaml
│   ├── projects.yaml
│   ├── skills.yaml
│   └── summary.yaml
├── templates
│   ├── cv.css
│   └── cv.html.j2
└── variants
    └── default.yaml
```