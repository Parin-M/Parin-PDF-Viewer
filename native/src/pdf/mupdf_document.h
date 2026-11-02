#pragma once

#include <QImage>
#include <QSizeF>
#include <QString>

#include <memory>

struct parin_mupdf_document;

namespace parin {

class MupdfDocument final {
public:
    MupdfDocument() = default;
    ~MupdfDocument();

    MupdfDocument(const MupdfDocument &) = delete;
    MupdfDocument &operator=(const MupdfDocument &) = delete;
    MupdfDocument(MupdfDocument &&other) noexcept;
    MupdfDocument &operator=(MupdfDocument &&other) noexcept;

    bool open(const QString &path, const QString &password, QString *error = nullptr);
    void close() noexcept;
    [[nodiscard]] bool isOpen() const noexcept;
    [[nodiscard]] int pageCount() const noexcept;
    [[nodiscard]] QSizeF pageSize(int pageIndex, QString *error = nullptr) const;
    [[nodiscard]] QImage renderPage(int pageIndex, qreal scale, QString *error = nullptr) const;
    [[nodiscard]] int searchPage(int pageIndex, const QString &query, QString *error = nullptr) const;
    [[nodiscard]] QString path() const;

private:
    parin_mupdf_document *document_ = nullptr;
    QString path_;
};

} // namespace parin
