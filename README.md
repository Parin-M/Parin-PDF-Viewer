# Parin PDF Viewer

## Development branch: 9.1.0

This branch contains development work for the next Parin PDF Viewer iteration. It is **not a published release** until the automated checks pass and the maintainer reviews the changes.

### What is changing in 9.1

- Everything from `feature/v9.0`, including page organization, undo/redo, safer loading/saving, navigation, search, recent files, session restoration, and full-document printing.
- Redesign the welcome screen with Open PDF, recent-document cards and page-one previews, plus PDF drag-and-drop.
- Use a minimalist navy-header workspace with monochrome toolbar glyphs, grouped actions, a refined navigation dock, a page/zoom/save status strip, and a neutral PDF canvas with optional page shadow.
- Add a persistent Light/Dark appearance mode throughout the application and Settings; the PDF page content keeps its original colours.
- Preserve the existing PDF features and localized interface while modernizing the surrounding controls.
- Preview pen and highlighter strokes in real time and save the completed path to the PDF on release.
- Use the optional offline Smart Ink assistant to smooth small writing jitters while preserving stroke endpoints and stronger direction changes; it does not upload document content or perform handwriting-to-text recognition.
- Choose Sans serif, Serif or Monospace and a 6–72 pt font size before inserting text annotations.
- Add a Rust native extension (PyO3) for defensive zoom normalization, with the existing Python fallback retained when the extension is unavailable.
- A localized About page under Settings, with the exact project credit, application version, GitHub repository, GPL-3.0 license, and a copy-version button.
- A drag-and-drop page organizer to reorder, rotate, delete, and extract pages, plus insertion from another PDF.
- Ctrl+Z / Ctrl+Y undo and redo for annotations and supported page operations, with bounded history to limit memory use.
- CI regression tests and a Debian package artifact built by GitHub Actions.

### Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```

GitHub Actions builds the `.deb` file as `parin-pdf_9.1.0_amd64.deb` and uploads it as the `parin-pdf-9.1.0-deb` workflow artifact. To build locally on a compatible Debian-based system, follow scripts/build-deb.sh. GUI rendering and printing should still be smoke-tested on the target desktop before publishing a release. See CHANGELOG.md for details and known limitations.

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
