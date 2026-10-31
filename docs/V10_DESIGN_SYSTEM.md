# Parin v10 — Hybrid Pro foundations

This document describes the first implementation slice on `feature/v10-hybrid-pro`.

## Implemented in this slice

- **Parin Aurora tokens:** semantic dark and light palettes, with text, surface, border, accent and status roles.
- **Density profiles:** high-density is the default; comfortable and compact profiles are available for responsive layouts.
- **Theme engine:** a small Qt stylesheet adapter that consumes semantic tokens.
- **Workspace shell:** a modular five-zone shell with header, main toolbar, context toolbar, navigation, replaceable canvas, inspector and status strip.
- **Command palette:** searchable command registry, keyboard-friendly dialog, and a `Ctrl+K` shortcut in the workspace shell.
- **Responsive panels:** the inspector collapses below the compact breakpoint; navigation collapses below the narrow breakpoint.

## Workspace zones

| Zone | High-density target |
|---|---:|
| Header | 54 px |
| Main toolbar | 50 px |
| Context toolbar | 40 px |
| Navigation | 224 px |
| Inspector | 288 px |
| Status strip | 28 px |

## Migration boundary

The v10 shell is now the main application window and hosts the existing PDF reader,
toolbar, navigation tabs, welcome page, settings and language controls. The proven
PDF renderer and document lifecycle remain in `parin_pdf_viewer.py`; the new workspaces
are separate modules mounted into the central workspace. This incremental boundary
keeps the renderer fixes isolated while the remaining legacy services are migrated.


## Reader integration update

The v10 workspace shell is now mounted as the main central widget of the application.
The existing PDF welcome page, scroll area, toolbar actions, search field, settings and
language controls are hosted inside the new shell rather than duplicated. The existing
outline and page-thumbnail tabs are mounted in the left navigation panel. The right
Inspector reports the open file, page count, current page, page dimensions, title,
author, subject and save state, and exposes quick actions routed to the existing PDF
operations.

Focus Studio, Research Studio and Compare Studio are now functional
workspace modules. Document Hub reuses the recent-document welcome view. Switching
between workspaces does not close the Reader's open PDF; Compare Studio maintains its
own two independent, read-only PDF handles and releases them when the application closes.


## Focus Studio

Focus Studio is now a functional reader mode. It reuses the currently open PDF
viewport, collapses the main action toolbar, navigation and inspector panels, and
keeps the compact context strip with an explicit **Exit Focus** action. Returning
to Reader Studio restores the responsive panels and the same document widget.


## Document Hub

Document Hub now reuses the localized welcome view and its recent-document cards
and page-one previews. Opening a PDF from the Hub returns to Reader Studio; moving
between Hub and Reader does not close the in-memory PDF document.


## Research Studio

Research Studio now provides document-scoped local research notes and references.
Notes are stored as atomic JSON sidecars under the application's private data
directory, keyed by the canonical local PDF path. Each note stores its page number,
text and timestamps. Save As copies the note set to the new PDF identity while
retaining the original sidecar.

The studio also reads PDF Highlight annotations and Parin's translucent ink
highlighter strokes from the open document. Selecting a note or highlight navigates
the existing Reader to its referenced page. Research data remains local; no document
content or notes are sent to a remote service.


## Compare Studio

Compare Studio now hosts two independent local PDF documents side by side.
Each pane validates a candidate file before replacing its current document,
renders pages inside a bounded scrollable viewport, and exposes its own page
selector. Page synchronization is enabled by default and can be switched off;
when enabled, page numbers are matched and clamped to the available range of
the other document. Closing the main application releases both comparison
documents. Compare mode is read-only and does not modify either PDF.


### Page text comparison

The comparison toolbar also offers a read-only unified text diff for the currently
selected pages. Added and removed lines are counted and shown with context. To keep
comparison responsive on very long or malformed pages, extracted text and displayed
diff output are bounded before presentation.


### Navigation panel and thumbnail controller

The navigation dock, PDF outline projection, page-list synchronization, lazy thumbnail
rendering and bounded LRU cache are managed by
`src/parin_ui/navigation_panel.py`. The main viewer remains responsible for document
lifecycle and page navigation; the controller keeps compatibility aliases on the
viewer while owning the navigation widgets and refresh timer.

### Navigation localization boundary

The navigation panel's labels are stored in the Qt-independent
`src/parin_ui/navigation_i18n.py`. The main viewer imports the data and keeps
the existing language fallback and page-label formatting behavior.

### Settings module boundary

The settings dialog UI lives in `src/parin_ui/settings_dialog.py`. Its language data and
label normalization are isolated in the Qt-independent
`src/parin_ui/settings_i18n.py`; the main viewer supplies appearance resources through
`SettingsDialogResources`. The existing PDF rendering and document lifecycle remain
in the legacy main module during the staged migration.

### Document history service

Undo/redo checkpoint storage is managed by the Qt-independent
`src/parin_ui/document_history.py`. The service enforces snapshot-size and
checkpoint-count bounds, clears redo history after a new edit, and only advances
history stacks after the Reader confirms a snapshot restore. PDF serialization,
encryption handling and UI refresh remain at the main-reader boundary.



### PDF document service

PDF opening and validation are now isolated in the Qt-free
`src/parin_ui/document_service.py`. It normalizes and checks the input path,
opens a candidate, handles password authentication outcomes, verifies that at
least one page is readable, and rasterizes a bounded page-one sample. Failed
candidates are closed by the service. The Reader retains the password prompt,
unsaved-change decision and final active-document replacement, so an invalid,
locked or cancelled candidate cannot displace the currently open PDF.


### PDF document save service

Transactional PDF saving is isolated in the Qt-free
src/parin_ui/document_save_service.py. The service serializes to a temporary
file in the destination directory, applies the requested encryption policy,
reopens and validates the candidate, authenticates it when required, and only
then replaces the target with an atomic same-filesystem operation. It returns
the validated open document and its encryption/page metadata. The Reader owns
the UI handoff, closes the previous in-memory document after success, updates
reading state, and copies local Research notes for Save As. Failed writes do
not close or mutate the current source document.


### PDF page operations service

Page-plan validation, page ordering/removal/rotation, PDF-to-PDF insertion and
page extraction are now owned by the Qt-free
`src/parin_ui/page_operations.py`. The Page Organizer remains responsible for
the list and dialogs, but submits a validated plan to the service. Extraction
writes through the transactional save service, so an existing destination is
replaced only after the extracted PDF has been reopened and validated. The
Reader continues to own undo checkpoints, active-page selection and UI refresh.
