# Changelog

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
