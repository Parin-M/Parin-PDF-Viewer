#include "pdf/mupdf_document.h"

#include "pdf/mupdf_c_api.h"

#include <QFileInfo>

#include <utility>

namespace parin {

MupdfDocument::~MupdfDocument()
{
    close();
}

MupdfDocument::MupdfDocument(MupdfDocument &&other) noexcept
    : document_(std::exchange(other.document_, nullptr)),
      path_(std::move(other.path_))
{
}

MupdfDocument &MupdfDocument::operator=(MupdfDocument &&other) noexcept
{
    if (this != &other) {
        close();
        document_ = std::exchange(other.document_, nullptr);
        path_ = std::move(other.path_);
    }
    return *this;
}

bool MupdfDocument::open(const QString &path, const QString &password, QString *error)
{
    close();
    const QByteArray utf8Path = QFileInfo(path).absoluteFilePath().toUtf8();
    const QByteArray utf8Password = password.toUtf8();
    char errorBuffer[512] = {};
    document_ = parin_mupdf_open(
        utf8Path.constData(),
        utf8Password.constData(),
        errorBuffer,
        sizeof(errorBuffer)
    );
    if (document_ == nullptr) {
        if (error != nullptr)
            *error = QString::fromUtf8(errorBuffer);
        return false;
    }
    path_ = QFileInfo(path).absoluteFilePath();
    return true;
}

void MupdfDocument::close() noexcept
{
    if (document_ != nullptr) {
        parin_mupdf_close(document_);
        document_ = nullptr;
    }
    path_.clear();
}

bool MupdfDocument::isOpen() const noexcept
{
    return document_ != nullptr;
}

int MupdfDocument::pageCount() const noexcept
{
    return parin_mupdf_page_count(document_);
}

QSizeF MupdfDocument::pageSize(int pageIndex, QString *error) const
{
    float width = 0.0f;
    float height = 0.0f;
    char errorBuffer[512] = {};
    if (!parin_mupdf_page_size(document_, pageIndex, &width, &height,
            errorBuffer, sizeof(errorBuffer))) {
        if (error != nullptr)
            *error = QString::fromUtf8(errorBuffer);
        return {};
    }
    return QSizeF(width, height);
}

QImage MupdfDocument::renderPage(int pageIndex, qreal scale, QString *error) const
{
    uint8_t *pixels = nullptr;
    int width = 0;
    int height = 0;
    int stride = 0;
    char errorBuffer[512] = {};

    if (!parin_mupdf_render_page(document_, pageIndex, static_cast<float>(scale),
            &pixels, &width, &height, &stride, errorBuffer, sizeof(errorBuffer))) {
        if (error != nullptr)
            *error = QString::fromUtf8(errorBuffer);
        return {};
    }

    const QImage borrowed(pixels, width, height, stride, QImage::Format_RGB888);
    QImage owned = borrowed.copy();
    parin_mupdf_free_buffer(pixels);
    return owned;
}

int MupdfDocument::searchPage(int pageIndex, const QString &query, QString *error) const
{
    const QByteArray utf8Query = query.toUtf8();
    char errorBuffer[512] = {};
    const int hits = parin_mupdf_search_page(
        document_, pageIndex, utf8Query.constData(), errorBuffer, sizeof(errorBuffer));
    if (hits < 0 && error != nullptr)
        *error = QString::fromUtf8(errorBuffer);
    return hits;
}

QString MupdfDocument::path() const
{
    return path_;
}

} // namespace parin
