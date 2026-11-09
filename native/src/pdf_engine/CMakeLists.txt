# Copyright (C) 2026 Parin Mashalchian
# SPDX-License-Identifier: GPL-3.0-only

cmake_minimum_required(VERSION 3.24)
project(ParinPdfEngineFoundation VERSION 0.1.0 LANGUAGES CXX)

add_library(parin_pdf_engine_foundation STATIC
    engine_contract.cpp
)
target_include_directories(parin_pdf_engine_foundation
    PUBLIC
        "${CMAKE_CURRENT_SOURCE_DIR}/../../include"
    PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
)
target_compile_features(parin_pdf_engine_foundation PUBLIC cxx_std_20)
set_target_properties(parin_pdf_engine_foundation PROPERTIES
    CXX_EXTENSIONS OFF
    POSITION_INDEPENDENT_CODE ON
)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(parin_pdf_engine_foundation PRIVATE
        -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion
    )
endif()
