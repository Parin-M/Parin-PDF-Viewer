#pragma once

#include <QByteArray>

#include <cstddef>

struct ParinCache;

namespace parin {

class RenderCache final {
public:
    explicit RenderCache(std::size_t maxBytes = 48u * 1024u * 1024u);
    ~RenderCache();

    RenderCache(const RenderCache &) = delete;
    RenderCache &operator=(const RenderCache &) = delete;

    [[nodiscard]] QByteArray get(const QByteArray &key) const;
    bool put(const QByteArray &key, const QByteArray &value);
    void clear() noexcept;
    [[nodiscard]] std::size_t usedBytes() const noexcept;

private:
    ParinCache *cache_ = nullptr;
};

} // namespace parin
