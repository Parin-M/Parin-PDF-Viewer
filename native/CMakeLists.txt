find_package(Qt6 6.4 REQUIRED COMPONENTS Core Gui Widgets)
find_package(PkgConfig REQUIRED)
pkg_check_modules(MUPDF REQUIRED IMPORTED_TARGET mupdf)
pkg_check_modules(HARFBUZZ REQUIRED IMPORTED_TARGET harfbuzz)
pkg_check_modules(FREETYPE REQUIRED IMPORTED_TARGET freetype2)
pkg_check_modules(MUJS REQUIRED IMPORTED_TARGET mujs)
pkg_check_modules(GUMBO REQUIRED gumbo)
# MuPDF's static archive references Gumbo. Link its static archive so the
# resulting Parin package does not require a particular libgumbo SONAME/version
# on the user's machine (for example libgumbo1 on older LTS releases).
find_file(GUMBO_STATIC_LIBRARY
    NAMES libgumbo.a
    PATHS ${GUMBO_LIBRARY_DIRS}
    NO_DEFAULT_PATH
    REQUIRED
)
find_package(JPEG REQUIRED)
find_package(Threads REQUIRED)
find_package(ZLIB REQUIRED)
find_library(MUPDF_THIRD_LIBRARY NAMES mupdf-third REQUIRED)
find_library(JBIG2DEC_LIBRARY NAMES jbig2dec REQUIRED)
find_library(OPENJPEG_LIBRARY NAMES openjp2 REQUIRED)
find_library(LCMS2_LIBRARY NAMES lcms2 REQUIRED)
find_program(CARGO_EXECUTABLE cargo REQUIRED)

set(PARIN_RUST_TARGET_DIR "${CMAKE_BINARY_DIR}/rust-target")
set(PARIN_RUST_ARCHIVE "${PARIN_RUST_TARGET_DIR}/release/libparin_core.a")
set(PARIN_RUST_MANIFEST "${CMAKE_CURRENT_SOURCE_DIR}/rust/parin_core/Cargo.toml")

add_custom_command(
    OUTPUT "${PARIN_RUST_ARCHIVE}"
    COMMAND "${CMAKE_COMMAND}" -E env
        "CARGO_TARGET_DIR=${PARIN_RUST_TARGET_DIR}"
        "${CARGO_EXECUTABLE}" build --release --manifest-path "${PARIN_RUST_MANIFEST}"
    DEPENDS
        "${PARIN_RUST_MANIFEST}"
        "${CMAKE_CURRENT_SOURCE_DIR}/rust/parin_core/src/lib.rs"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/rust/parin_core"
    COMMENT "Building Parin's Rust core"
    VERBATIM
)
add_custom_target(parin_rust_build DEPENDS "${PARIN_RUST_ARCHIVE}")

add_library(parin_rust_core STATIC IMPORTED GLOBAL)
set_target_properties(parin_rust_core PROPERTIES IMPORTED_LOCATION "${PARIN_RUST_ARCHIVE}")
add_library(parin_pdf_engine STATIC
    src/pdf/mupdf_c_api.c
    src/pdf/mupdf_document.cpp
)
target_include_directories(parin_pdf_engine PUBLIC src)
target_link_libraries(parin_pdf_engine PUBLIC PkgConfig::MUPDF ${MUPDF_THIRD_LIBRARY} PkgConfig::HARFBUZZ PkgConfig::FREETYPE PkgConfig::MUJS ${GUMBO_STATIC_LIBRARY} JPEG::JPEG ${JBIG2DEC_LIBRARY} ${OPENJPEG_LIBRARY} ${LCMS2_LIBRARY} ZLIB::ZLIB Qt6::Core Qt6::Gui)
target_compile_options(parin_pdf_engine PRIVATE
    $<$<COMPILE_LANGUAGE:C>:-Wall;-Wextra;-Wpedantic>
    $<$<COMPILE_LANGUAGE:CXX>:-Wall;-Wextra;-Wpedantic>
)

add_library(parin_native_core STATIC
    src/core/render_cache.cpp
)
target_include_directories(parin_native_core PUBLIC src)
target_link_libraries(parin_native_core PUBLIC Qt6::Core parin_rust_core Threads::Threads ${CMAKE_DL_LIBS} m)
add_dependencies(parin_native_core parin_rust_build)

add_executable(parin-native
    src/main.cpp
    src/ui/main_window.cpp
)
target_include_directories(parin-native PRIVATE src)
target_link_libraries(parin-native PRIVATE
    Qt6::Core Qt6::Gui Qt6::Widgets
    parin_pdf_engine parin_native_core
)
target_compile_definitions(parin-native PRIVATE PARIN_APP_VERSION="${PROJECT_VERSION}")

if(BUILD_TESTING)
    find_package(Qt6 6.4 REQUIRED COMPONENTS Test)
    add_executable(parin-native-tests
        tests/native_tests.cpp
    )
    target_link_libraries(parin-native-tests PRIVATE
        Qt6::Core Qt6::Gui Qt6::Widgets Qt6::Test
        parin_pdf_engine parin_native_core
    )
    add_dependencies(parin-native-tests parin_rust_build)
    add_test(NAME parin-native-tests COMMAND parin-native-tests)
    set_tests_properties(parin-native-tests PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen")
endif()

install(TARGETS parin-native RUNTIME DESTINATION bin)
install(FILES packaging/parin-pdf.desktop DESTINATION share/applications)
install(FILES packaging/parin-pdf.svg DESTINATION share/icons/hicolor/scalable/apps)
