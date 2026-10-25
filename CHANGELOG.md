# Changelog

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
