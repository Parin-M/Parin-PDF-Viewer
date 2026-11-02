# Parin PDF Viewer

A PDF workspace for Debian-based desktop systems.

## Edition V10.2 — Native MuPDF preview

Parin 10.2 starts the native migration. The new `parin-native` application is built with C++20 and Qt 6, calls the MuPDF C API directly for PDF open/authentication/rendering/search, and uses a Rust static library for a bounded render cache. Its build and tests use CMake, Ninja and Cargo; Python is not part of the native executable or native packaging pipeline. Debian packages bundle the Qt runtime, Qt platform plugins and non-glibc shared-library dependencies under /opt/parin so users do not need to install Qt/MuPDF runtime packages separately. The host still supplies its base glibc and dynamic loader.

This is an incremental native preview, not a complete feature-for-feature replacement yet. Annotations, editing and save, Undo/Redo, page organization, bookmarks, multi-document tabs, Research and Compare are still being migrated from the 10.1 reference implementation. See [the 10.2 migration plan](docs/V10_2_NATIVE_MIGRATION.md).

**Licensing:** the open-source MuPDF build is AGPL-3.0-or-later. Review the combined application's distribution obligations before publishing binary packages; Artifex also offers a commercial license. See the migration document for references.

Website: https://parin-m.github.io/parin-pdf-viewer-site/

-----------------------------------------------------------------------------------------------------------------------------------------------------

Edition V10.1 — Application version 10.1.0:

The Precision Workspace update refines responsive panels, adds a user-controlled
document Inspector, bounds print raster memory, and makes Page Organizer edits
transactional through validated document candidates. The Hybrid Pro Reader,
Focus, Research, Compare and Document Hub workspaces remain the foundation.


-----------------------------------------------------------------------------------------------------------------------------------------------------

Edition V9.2:

<img width="1920" height="1050" alt="image" src="https://github.com/user-attachments/assets/bbfe0b0f-2637-4017-bddb-1e5f29d09845" />

-----------------------------------------------------------------------------------------------------------------------------------------------------


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
