# Native PDF Engine

Copyright (C) 2026 Parin Mashalchian

SPDX-License-Identifier: GPL-3.0-only

This directory is the home of Parin's independently implemented PDF engine.

The engine must remain independent of the current V10.2 MuPDF adapter and of UI toolkit headers. Public contracts belong in `native/include/parin/pdf`; implementation details belong under this directory.

## Current foundation

- `engine_contract.cpp`: compiles the public, engine-neutral API contract.
- `byte_reader.h`: bounded, non-owning byte reader. All read/skip/seek operations check bounds before advancing.

## Implementation order

1. byte source and bounded reader;
2. lexer and primitive object parser;
3. xref/trailer and indirect object resolution;
4. page tree and document model;
5. stream filters;
6. graphics interpreter and renderer;
7. text extraction/search;
8. annotations and writer.

Do not copy code from incompatible projects. Every new third-party dependency requires a recorded version, license, notices, and redistribution review before it enters the build.
