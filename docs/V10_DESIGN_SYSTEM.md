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

The existing PDF renderer and document lifecycle remain in `parin_pdf_viewer.py` for this first slice. The new shell exposes `set_workspace_widget()` so the proven PDF viewport can be mounted into the central canvas after the next integration step. This keeps the renderer fixes isolated while the UI is modularized.

The new shell is a component foundation; it does not replace the current application entry point yet.


## Reader integration update

The v10 workspace shell is now mounted as the main central widget of the application.
The existing PDF welcome page, scroll area, toolbar actions, search field, settings and
language controls are hosted inside the new shell rather than duplicated. The existing
outline and page-thumbnail tabs are mounted in the left navigation panel. The right
Inspector reports the open file, page count, current page, page dimensions, title,
author, subject and save state, and exposes quick actions routed to the existing PDF
operations.

Focus Studio, Research Studio, Compare Studio and Document Hub currently show an
explicit **IN DEVELOPMENT** state. Switching away from Reader Studio does not close
or discard the open PDF; returning to Reader restores the existing reader widget.


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
