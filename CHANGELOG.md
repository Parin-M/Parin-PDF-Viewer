# Changelog

## 9.2.0 — Python-only core and interface refresh

- Remove the PyO3/Rust extension and the entire `rust-core` project; all runtime helpers are implemented directly in Python.
- Remove Rust setup, Cargo tests and maturin build/install steps from CI and Debian packaging.
- Refresh the interface with a consistent surface system, more legible typography, refined spacing, clearer button states and improved light/dark contrast.
- Refine toolbar density, primary actions, page-navigation controls, recent-document cards and responsive welcome layout.
- Expand regression coverage for the pure-Python zoom helper and key interface styling.


## 9.1.4 — Full audit fixes

- Preserve encryption for PDFs with an empty user password, validate temporary output before replacing the open file, and keep the previous document usable when saving fails.
- Preserve encryption in undo/redo snapshots and keep history stacks unchanged if restoration fails.
- Apply 100% zoom and selected page rotation/alignment settings correctly.
- Reset all Settings controls and stored values together.
- Respect the audio-enabled preference and synchronize the native module version with the Cargo package version.
- Make Python and Rust zoom normalization agree for non-finite values and custom bounds.
- Expand regression coverage for upward/downward wheel transitions, Ctrl+wheel zoom, encrypted saves, settings reset, and fit-mode changes.


## 9.1.3 — Fix wheel routing and stale scroll ranges

- Handle wheel input centrally for the page label, the scroll area's own surface, and its viewport, including blank margins around fitted pages.
- Recalculate the target scroll offset after page changes and scrollbar range updates, with a generation guard that prevents stale delayed callbacks from moving a newer page.
- Add a regression assertion that scrolling over the viewport advances to the next page and keeps real rendered page pixels visible.
- Bump application, native-core, Debian package, and workflow artifact versions to 9.1.3.

## 9.1.2 — PDF scrolling and page transitions

- Handle mouse-wheel and touchpad scrolling directly on the PDF canvas, including Ctrl+wheel zoom.
- Continue into adjacent pages at the scroll boundaries while carrying over scroll distance.
- Reset the scroll offset when the displayed page changes, avoiding stale offsets and blank-looking views.
- Add a regression test for vertical scrolling and cross-page navigation, and bump package/CI versions to 9.1.2.

## 9.1.1 — PDF rendering fix

- Keep the PDF canvas at the exact dimensions of the rendered pixmap instead of allowing the scroll area to resize the page label independently.
- Re-render the active page after the stacked workspace completes layout, preventing fit-to-width calculations from using a hidden or zero-sized viewport during startup.
- Add a GUI regression test that asserts a rendered page bitmap exists, is sized to the canvas, and contains expected non-white page pixels.
- Carry forward the fixes for desktop file URLs, uppercase `.PDF` extensions, and safer recovery after failed opens.
- Bump application, native-core, Debian package, and CI artifact versions to 9.1.1.

## 9.1.0 — Development branch

Continues from `feature/v9.0` without changing `main`.

### Interface refresh
- Redesign the welcome screen with an Open PDF call to action, recent-document cards, first-page thumbnail previews, a clear-recent action, and PDF drag-and-drop support.
- Refine the main workspace with a deep navy header, compact monochrome toolbar glyphs, grouped tool surfaces, a coordinated search field, a neutral PDF canvas, and a more useful persistent page/zoom/save-status strip.
- Add a persistent Light/Dark appearance choice across the main window, menus, navigation dock, and Settings while preserving PDF page colours and the existing theme accent selection.
- Improve the navigation dock and page thumbnail spacing, and apply the existing page-shadow preference to the rendered page.
- Keep all existing PDF workflows and localization intact while applying the new styles.
- Add a live pen/highlighter preview while the pointer or stylus moves, then commit the stroke to the PDF on release.
- Add optional offline Smart Ink smoothing that adapts to stroke geometry, preserves endpoints and stronger turns, and reports a simple stroke-shape profile without uploading document content.
- Add font-family and 6–72 pt size controls for new text annotations; keep the selected Smart Ink preference between launches.
- Document the limitation explicitly: this lightweight helper stabilizes ink paths but does not claim handwriting-to-text recognition.
- Fix opening PDFs passed by the Linux desktop launcher (`%U` file URLs), include uppercase `.PDF` in the file picker, and retry password prompts without discarding the current document on cancellation/failure.
- Add headless integration regressions for local file URLs, valid PDF loading, uppercase extensions, and failed-open recovery.
- Fix a canvas sizing issue by keeping the scroll-area child at the exact rendered pixmap size instead of allowing `QScrollArea` to resize the PDF `QLabel` independently. This also keeps pen/highlighter preview coordinates aligned with the rendered page.
- Add a rendered-content regression test that verifies the PDF bitmap is non-empty, correctly sized for the canvas, and contains the expected page pixels.

### Python + Rust architecture
- Add an optional PyO3-based Rust native extension for zoom normalization.
- Keep the Python implementation as a compatibility fallback for source runs where the extension is not installed.
- Add Rust unit tests and CI checks; CI builds and installs the extension wheel directly, while the Debian build installs the Rust extension in its dedicated virtual environment before freezing the app.
- Align application and Debian package versioning and workflow artifact names at 9.1.0.


## 9.0.0 — Development branch

Version 9.0.0 continues the 8.9 reliability work and adds a localized About page, page organization, and bounded annotation/document undo history. This is a development build until CI, package installation, and GUI smoke tests have been reviewed.

### About and identity
- Add an About section under Settings with the version, GitHub repository, GPL-3.0 license information, and a version-copy action.
- Preserve the requested attribution verbatim: "This project was created by Parin Mashalchian and ChatGPT also contributed to this project."

### PDF page workflow
- Add a drag-and-drop page organizer to reorder pages, remove selected pages, rotate selected pages, or extract selected pages to a separate PDF.
- Insert pages from another PDF at the current page position.
- Refresh page navigation and thumbnails after page-structure edits.

### Editing history
- Add Ctrl+Z undo and Ctrl+Y redo for annotation edits and supported page operations.
- Keep history bounded to five snapshots and 16 MiB per snapshot; disable history when a snapshot would exceed the size limit to avoid unbounded memory use.

### Packaging
- Align application and Debian package versioning at 9.0.0.
- Extend CI to compile/test the project, build the Debian package, and upload it as a workflow artifact.

## 8.9.0 — Development branch

## 8.9.0 — Development branch

This entry describes the changes in the `feature/v8.9` development branch. It is not a release announcement; validation and maintainer review are still required.

### Reliability
- Open a replacement PDF only after it has been opened and, where required, authenticated successfully, so a bad file or password does not close the current document.
- Save through a temporary PDF in the destination directory, then atomically replace the target after serialization succeeds.
- Handle render, search, save, and print errors without silently swallowing them.
- Track unsaved annotation changes and ask before replacing a document or exiting.
- Clamp zoom values safely when the stored value is invalid.

### Reading and navigation
- Add a navigation dock with the PDF outline and page list.
- Render page thumbnails on demand and keep a bounded thumbnail cache for large documents.
- Cycle through text matches, including multiple matches on the same page, and highlight the selected result.
- Remember recently opened PDFs and allow reopening or clearing the recent-file list.
- Restore the last opened PDF, page, and zoom when the corresponding preferences are enabled.
- Print all pages instead of printing only the currently viewed page.

### Packaging and quality
- Add explicit runtime and development requirements.
- Add dependency-free helper tests and a GitHub Actions syntax/test workflow.
- Align Debian package version and artifact name with 8.9.0.

### Limitations for this development iteration
- No claim is made that the Linux GUI has been manually exercised on every Debian desktop environment.
- OCR for scanned PDFs, PDF page rearrangement, and true undo/redo history are not implemented in this iteration.
