# Parin PDF Viewer 10.3 — Native PDF Engine Migration

Copyright (C) 2026 Parin Mashalchian

This document defines the staged replacement of the V10.2 MuPDF-based native preview with an independently implemented PDF engine.

## Product decisions

- Target: Linux desktop; deliver DEB and AppImage.
- Implementation language: C++20.
- Project code license: GNU GPL version 3 only (GPL-3.0-only).
- UI and PDF engine must communicate through a stable, engine-independent C++ interface.
- Do not add MuPDF, PDFium, Poppler, or Qt PDF as the target engine.
- The new engine is an incremental implementation, not a claim of complete ISO 32000 conformance.
- Preserve the existing V10.2 implementation during migration. Do not remove the current engine until replacement capabilities pass acceptance tests.
- UI languages: English, Persian, Finnish, Danish, Norwegian Bokmål, Swedish, Swiss German, German, Polish, Ukrainian, Arabic, Hebrew, Italian, Korean, Japanese, and Hindi.
- About attribution: “Created by Parin Mashalchian” and link to https://github.com/Parin-M/Parin-PDF-Viewer.

## Licensing policy

The application-authored code is GPL-3.0-only. Third-party components must be individually audited for license compatibility with GPL-3.0, notices, source-offer/source-publication obligations, and redistribution conditions. A dependency's original license is not rewritten as GPL merely by linking it. Fonts may use GPL-compatible licenses including OFL, with their original notices preserved.

The host operating system, kernel, dynamic loader, compiler toolchain, and standard runtime are not treated as application-authored components. Any libraries bundled in DEB/AppImage must be inventoried and audited. No claim of “all components are exactly GPL-3.0” should be made for separately licensed third-party works.

## Architecture

1. `PdfEngine`: stable public API independent of parser/renderer implementation.
2. `PdfDocument`: document lifetime, authentication, page count and metadata.
3. `PdfPage`: page geometry and rendering requests.
4. `PdfTextPage`: text extraction and selection geometry.
5. `PdfSearch`: cancellable asynchronous search.
6. `PdfAnnotationStore`: annotation model and persistence capabilities.
7. `PdfWriter`: incremental/full save operations when implemented.
8. Core services: bounded cache, worker scheduling, cancellation and memory accounting.

The UI must not include parser-internal headers or manipulate PDF objects directly.

## Implementation milestones

### M0 — Repository and licensing baseline
- Create this migration specification and an SPDX-tagged source layout.
- Inventory V10.2 source, build dependencies, bundled runtime files and licenses.
- Record baseline build/test commands and current feature behavior.
- No removal of existing MuPDF/Rust/Qt code in this milestone.

### M1 — Engine contract and test harness
- Define engine-neutral document, page, geometry, render, text and error types.
- Add deterministic unit-test fixtures for malformed input, bounds checking and cancellation.
- Establish a parser security policy: checked arithmetic, bounded recursion, bounded allocations, no untrusted object deserialization.

### M2 — Parser foundation
- Implement byte source abstraction, lexer, primitive objects, dictionaries, arrays, names, strings and stream boundaries.
- Add xref/trailer parsing and object resolution.
- Reject or safely report unsupported/corrupt structures; never silently trust offsets or lengths.

### M3 — Document model and filters
- Page tree traversal, inherited page attributes, metadata and core stream filters.
- Add limits for decompression, recursion, object count and document size.

### M4 — Rendering
- Graphics state, paths, transforms, clipping, text operators and raster output.
- Add image decoding only after codec license and security review.
- Compare rendered output against a curated golden corpus.

### M5 — Text, search and fonts
- Unicode extraction, glyph mapping, selection geometry and asynchronous search.
- RTL and complex-script behavior must be tested separately from UI translation.
- Font shaping/rendering dependencies require a license audit before adoption.

### M6 — Editing and persistence
- Annotations, bookmarks, rotation persistence, writer, undo/redo.
- Save must be transactional: write to a temporary file, validate, then atomically replace where supported.

### M7 — UI integration and packaging
- Integrate through the engine contract.
- Preserve the existing V10.2 branch as fallback until parity criteria pass.
- Produce DEB/AppImage with corresponding source and notices.

## Initial acceptance criteria

- Parser unit tests pass under sanitizers.
- Malformed and adversarial fixtures fail safely without crashes or unbounded resource use.
- No UI-thread parsing, rendering, or full-document search.
- Document and page APIs have explicit ownership and cancellation semantics.
- Dependency inventory and license audit are part of CI/release checks.
- Memory target is measured against a documented corpus; 2 GiB is a ceiling for the defined stress profile, not a guarantee for every arbitrary file.

## Explicit non-goals for the first prototype

- Full PDF 2.0 conformance.
- Every legacy encryption/filter combination.
- Full font embedding/subsetting and advanced color management.
- Editing arbitrary PDF content streams.
- Claiming compatibility based on a successful build alone.
