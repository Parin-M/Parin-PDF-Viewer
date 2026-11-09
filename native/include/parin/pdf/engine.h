// Copyright (C) 2026 Parin Mashalchian
// SPDX-License-Identifier: GPL-3.0-only
#pragma once

#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <variant>
#include <vector>

namespace parin::pdf {

struct Error {
    enum class Code {
        io,
        malformed_document,
        unsupported_feature,
        password_required,
        invalid_password,
        page_out_of_range,
        cancelled,
        resource_limit,
        internal
    };

    Code code{Code::internal};
    std::string message;
};

template <typename T>
using Result = std::variant<T, Error>;

struct DocumentInfo {
    std::uint32_t page_count{0};
    std::string title;
    std::string author;
    std::string language;
    bool encrypted{false};
};

struct PageSize {
    double width_points{0.0};
    double height_points{0.0};
};

struct RenderOptions {
    double scale{1.0};
    int rotation_degrees{0};
    std::uint32_t background_rgba{0xFFFFFFFFu};
};

struct RenderedPage {
    std::uint32_t width{0};
    std::uint32_t height{0};
    std::uint32_t stride_bytes{0};
    // RGBA8 pixel storage. Ownership is shared so UI/cache consumers can
    // retain a completed render without depending on engine internals.
    std::shared_ptr<const std::vector<std::uint8_t>> pixels;
};

struct TextRun {
    std::string utf8;
    // Bounding box in PDF points: x0, y0, x1, y1.
    double x0{0.0};
    double y0{0.0};
    double x1{0.0};
    double y1{0.0};
};

struct SearchOptions {
    bool case_sensitive{false};
    bool whole_word{false};
};

struct SearchHit {
    std::uint32_t page_index{0};
    double x0{0.0};
    double y0{0.0};
    double x1{0.0};
    double y1{0.0};
    std::string matched_text;
};

class CancellationToken {
public:
    virtual ~CancellationToken() = default;
    [[nodiscard]] virtual bool is_cancelled() const noexcept = 0;
};

class Document {
public:
    virtual ~Document() = default;
    [[nodiscard]] virtual DocumentInfo info() const = 0;
    [[nodiscard]] virtual Result<PageSize> page_size(std::uint32_t page_index) const = 0;
    [[nodiscard]] virtual Result<RenderedPage> render(
        std::uint32_t page_index,
        const RenderOptions& options,
        const CancellationToken* cancellation = nullptr) const = 0;
    [[nodiscard]] virtual Result<std::vector<TextRun>> extract_text(
        std::uint32_t page_index,
        const CancellationToken* cancellation = nullptr) const = 0;
    [[nodiscard]] virtual Result<std::vector<SearchHit>> search(
        const std::string& utf8_query,
        const SearchOptions& options,
        const CancellationToken* cancellation = nullptr) const = 0;
};

struct OpenOptions {
    std::optional<std::string> password;
    std::uint64_t max_file_bytes{2ull * 1024ull * 1024ull * 1024ull};
    std::uint32_t max_pages{1'000'000};
    std::uint32_t max_object_nesting{128};
};

class Engine {
public:
    virtual ~Engine() = default;
    [[nodiscard]] virtual Result<std::shared_ptr<Document>> open(
        const std::filesystem::path& path,
        const OpenOptions& options = {}) = 0;
    [[nodiscard]] virtual std::string name() const = 0;
    [[nodiscard]] virtual std::string version() const = 0;
};

} // namespace parin::pdf
