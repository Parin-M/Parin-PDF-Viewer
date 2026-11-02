# Parin 10.2 — Native migration

## Target architecture

Parin 10.2 introduces a native application target. The executable is built from C, C++20 and Rust; Python is not invoked by the native build, runtime, test runner or Debian packaging script.

- **C++20 + Qt 6 Widgets:** desktop application, reader workspace, document session and UI state.
- **MuPDF C API:** document open/authentication, page geometry, raster rendering and page text search.
- **Rust static library:** bounded least-recently-used render cache, exposed through a small C ABI.
- **CMake + Ninja + Cargo:** reproducible native build and package pipeline.

The previous Python implementation remains in the repository as the 10.1 migration reference. It is not linked into `parin-native` and is not used by the native CI workflow.

## Implemented in this milestone

- Open local PDF files, including password-protected PDFs.
- Count pages and query page dimensions.
- Render pages through MuPDF's C API.
- Navigate to previous and next pages.
- Zoom, fit width and fit page.
- Search pages using MuPDF's page search API.
- Cache raster output with a byte-bounded Rust LRU cache.
- Build a native Debian package.

The native reader currently labels the document area as a read-only preview. It does not yet replace the 10.1 feature set.

## Not yet migrated

Annotations, text editing, encrypted save/export, Undo/Redo, Page Organizer, outlines/bookmarks, thumbnail navigation, multi-document tabs, Research Studio and Compare Studio remain on the legacy implementation until their native equivalents have regression coverage.

## Threading contract

The first native milestone serializes MuPDF operations through one document context on the UI thread. MuPDF contexts are not thread-safe. Background rendering must use MuPDF's documented locking and cloned-context model, and must not share a single context unsafely between threads.

## License notice

The open-source MuPDF distribution is licensed under AGPL-3.0-or-later; Artifex also offers a commercial license. Before distributing binaries, review the complete license obligations for the combined application and keep the corresponding source and notices available. If the product must be distributed under terms incompatible with AGPL, obtain an appropriate commercial license from Artifex before release.

References:
- https://mupdf.readthedocs.io/en/latest/license.html
- https://mupdf.readthedocs.io/en/latest/reference/c/fitz/api-overview.html
- https://mupdf.com/releases

This note is project documentation, not legal advice.
