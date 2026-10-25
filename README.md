# Parin PDF Viewer

## Development branch: 8.9.0

This branch contains development work for the next Parin PDF Viewer iteration. It is **not a published release** until the automated checks pass and the maintainer reviews the changes.

### What is changing in 8.9

- Safer PDF loading and atomic saves to reduce the risk of losing a document when an open, password, or write operation fails.
- Full-document printing with per-page rendering and error reporting.
- A navigation dock with the PDF's outline and an on-demand page-thumbnail list.
- Search navigation across individual matches, including repeated matches on the same page.
- A persistent recent-file menu and warnings for unsaved annotation changes.
- Explicit runtime dependencies, regression tests, CI checks, and aligned Debian package versioning.

### Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```

To build the Debian package on a compatible Debian-based system, follow scripts/build-deb.sh. GUI rendering and printing should still be smoke-tested on the target desktop before publishing a release. See CHANGELOG.md for details and known limitations.

---

A PDF viewer that you can install on Debian and Debian Base OS

Website: https://parin-m.github.io/parin-pdf-viewer-site/

Edition V8.7:

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/6ba5411f-a55c-4492-8579-eed11cdcb35f" />
in English 

------------------

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/4f69a5ca-9f55-4336-8932-ba87cb890690" />
in Persian


-----------------------------------------------------------------------------------------------------------------------------------------------------

Edition V6.0:

<img width="1920" height="1050" alt="image" src="https://github.com/user-attachments/assets/4a9f6f96-199e-4bca-9bae-3969ae35e76d" />
in Persian 

------------------

<img width="1920" height="1050" alt="image" src="https://github.com/user-attachments/assets/136593e1-5a25-43f4-a001-e5804afd76d1" />
in English
