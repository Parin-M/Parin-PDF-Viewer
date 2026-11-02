# Parin PDF Viewer

## Parin 10.2.01 — Persian Grand Edition

Native PDF workspace built with C++20, Qt 6, MuPDF C API and a Rust render cache.

### Persian Grand Edition interface
- Midnight/lapis workspace with turquoise and saffron-gold accents, Persian-inspired geometric identity and a redesigned app icon.
- 500 generated accent palettes in Appearance settings.
- Preferences atelier with General, Appearance, Reader, Audio and Advanced tabs.
- Language selector for Persian, English, Danish, Swedish, Arabic, Norwegian, German, Greek, Ukrainian, Turkish, Japanese, Italian, Korean, Mongolian, Hindi and Urdu. Selector and preference persistence are implemented; complete UI translation coverage remains ongoing.
- Lo-fi Listening Room with local audio playback, play/pause, stop and volume. No copyrighted music is bundled.
- About credits Parin Mashalchian (پــَــرین مشعلچیان).

### Native stack
C++20 / Qt 6 Widgets and Multimedia, MuPDF C API, Rust static render cache, CMake, Ninja and Cargo. Python is not part of the native executable or native build/test/package workflow.

### Current scope
This is an incremental native reader preview. Native page navigation, zoom, fit modes, document search, password opening and inspector are retained. Annotation/editing, save/export, undo/redo, organizer, bookmarks and full localization remain future migration work.

### Build
```bash
cmake -S . -B build/native -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build/native --parallel
ctest --test-dir build/native --output-on-failure
bash native/scripts/build-deb.sh
```

MuPDF open-source distribution is AGPL-3.0-or-later. Review combined-work distribution obligations or obtain an appropriate Artifex commercial license before distributing binaries.
