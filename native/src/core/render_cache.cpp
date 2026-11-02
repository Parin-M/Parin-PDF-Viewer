#include "core/render_cache.h"

#include "core/rust_ffi.h"

#include <limits>

namespace parin {

RenderCache::RenderCache(std::size_t maxBytes)
    : cache_(parin_cache_create(maxBytes))
{
}

RenderCache::~RenderCache()
{
    if (cache_ != nullptr)
        parin_cache_destroy(cache_);
}

QByteArray RenderCache::get(const QByteArray &key) const
{
    if (cache_ == nullptr || key.isEmpty())
        return {};

    const auto required = parin_cache_entry_size(cache_, key.constData());
    if (required <= 0 || required > std::numeric_limits<qsizetype>::max())
        return {};

    QByteArray result(static_cast<qsizetype>(required), '\0');
    if (!parin_cache_copy(cache_, key.constData(),
            reinterpret_cast<std::uint8_t *>(result.data()),
            static_cast<std::size_t>(result.size()))) {
        return {};
    }
    return result;
}

bool RenderCache::put(const QByteArray &key, const QByteArray &value)
{
    if (cache_ == nullptr || key.isEmpty())
        return false;
    return parin_cache_insert(
        cache_,
        key.constData(),
        reinterpret_cast<const std::uint8_t *>(value.constData()),
        static_cast<std::size_t>(value.size())
    ) != 0;
}

void RenderCache::clear() noexcept
{
    if (cache_ != nullptr)
        parin_cache_clear(cache_);
}

std::size_t RenderCache::usedBytes() const noexcept
{
    return cache_ != nullptr ? parin_cache_used_bytes(cache_) : 0u;
}

} // namespace parin
