// Copyright (C) 2026 Parin Mashalchian
// SPDX-License-Identifier: GPL-3.0-only
#pragma once

#include <cstddef>
#include <cstdint>
#include <span>

namespace parin::pdf::internal {

class ByteReader final {
public:
    explicit ByteReader(std::span<const std::uint8_t> bytes) noexcept : bytes_(bytes) {}

    [[nodiscard]] std::size_t position() const noexcept { return position_; }
    [[nodiscard]] std::size_t size() const noexcept { return bytes_.size(); }
    [[nodiscard]] std::size_t remaining() const noexcept { return bytes_.size() - position_; }
    [[nodiscard]] bool at_end() const noexcept { return position_ == bytes_.size(); }

    [[nodiscard]] bool seek(std::size_t offset) noexcept {
        if (offset > bytes_.size()) return false;
        position_ = offset;
        return true;
    }

    [[nodiscard]] bool skip(std::size_t count) noexcept {
        if (count > remaining()) return false;
        position_ += count;
        return true;
    }

    [[nodiscard]] bool read_byte(std::uint8_t& value) noexcept {
        if (at_end()) return false;
        value = bytes_[position_++];
        return true;
    }

    [[nodiscard]] bool peek_byte(std::uint8_t& value) const noexcept {
        if (at_end()) return false;
        value = bytes_[position_];
        return true;
    }

    [[nodiscard]] bool read(std::span<std::uint8_t> output) noexcept {
        if (output.size() > remaining()) return false;
        for (std::size_t i = 0; i < output.size(); ++i) {
            output[i] = bytes_[position_ + i];
        }
        position_ += output.size();
        return true;
    }

private:
    std::span<const std::uint8_t> bytes_;
    std::size_t position_{0};
};

} // namespace parin::pdf::internal
