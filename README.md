<h1 align="center">curriculum-vitae</h1>

<p align="center">
  <strong>A structured, tag-driven CV that renders to PDF and JSON from a single source of truth.</strong>
</p>

## Summary

Applying for jobs is a time consuming task. This project aims to alleviate some of that by providing a simple version controlled way of constructing a CV using a set of existing CV data and customisable variants. Each variant could be job specific or role specific (your choice!). Simply add your data, specify the variants and let it do the rest of the work.

## Pre-requisites

- **Python 3.12+** - the exact version is pinned in `.python-version`.
- **uv** - manages the virtual environment and dependencies. Install with `curl -LsSf https://astral.sh/uv/install.sh | sh` (see the [uv docs](https://docs.astral.sh/uv/) for other platforms).
- **Pango** - a text layout library that WeasyPrint (used for PDF output) calls into. It is not a Python package, so `uv sync` cannot install it. Most Linux desktop installations already have it; on a bare server or a CI runner, install `libpango-1.0-0` and `libpangoft2-1.0-0`. On macOS, `brew install pango`. JSON output does not touch it, but the module is imported either way, so it must be present to run the renderer at all.

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

### Tagging individual lines

Tags normally apply to a whole entry - a job, a project or a skill category. Inside an entry, a bullet point or skill can also carry its own tags, so the repo can hold more facts than fit on one CV and each variant picks the ones it wants:

```yaml
highlights:
  - Founding developer on Fusion.          # plain text - shown whenever the job is shown
  - text: Support DevOps work, including GitHub Actions CI and continuous delivery to AWS.
    tags: [devops]                         # shown only when the variant asks for devops
```

A plain line appears whenever its entry does. A tagged line appears only if its entry is included *and* one of its tags is in the variant - `core` on the entry keeps the job, not every bullet inside it. This works for `highlights` (experience, education), `details` (projects, additional info) and skill `items`. A skill category left with no items is dropped; a job or project left with no bullets still shows its heading. Untagged lines end up on every CV, including `default`, which is published publicly - so keep anything extra tagged.

## Testing

```bash
uv run pytest
```

The suite is deliberately small. It covers the logic that could produce a *wrong* CV without anything crashing - a silent error you would only notice after sending the file to an employer:

- **Tag filtering** - each shape keeps only the entries carrying a wanted tag, and a section with nothing left is dropped rather than rendered empty. Inside each entry, tagged bullet points and skills are filtered the same way, and come out as plain text so the template and JSON feed never see tags.
- **The `core` tag** - entries tagged `core` are added to every variant automatically, so they can never fall off a CV.
- **Date ordering** - roles come back newest first, and an ongoing role (one with no end date) is placed by when it started rather than floating to the top.
- **Parsing** - every `sections/*.yaml` file matches the model its shape names, and no field in the YAML is quietly discarded on the way in. This last check exists because an optional field whose name does not match its model is dropped without any error at all.
- **A real render** - the renderer is run end-to-end against a copy of the CV data with no `output/` folder, standing in for a fresh clone, and the resulting JSON and PDF are inspected.

## Continuous Integration

`.github/workflows/ci.yaml` runs automatically on GitHub using GitHub Actions - GitHub's built-in automation service, which starts a temporary machine and runs the steps in that file.

- **On every pull request, and on every push to `main`** - installs the dependencies and runs the test suite. A broken YAML file or a failing test is caught here rather than the next time you generate a CV. A pull request is tested as if it were already merged into `main`. Pushing to a branch on its own does not run the tests - open a pull request for it, and every later push to that branch is tested.

The workflow is read-only (`contents: read`) - it can check out the code but cannot change anything in the repository.

## Structure

```bash
curriculum-vitae
├── .github
│   ├── CODEOWNERS
│   └── workflows
│       └── ci.yaml
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
├── tests
│   ├── conftest.py
│   ├── test_filtering.py
│   ├── test_parsing.py
│   ├── test_render.py
│   └── test_sorting.py
└── variants
    └── default.yaml
```