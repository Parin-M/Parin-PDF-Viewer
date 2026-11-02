#pragma once

#include "core/render_cache.h"
#include "pdf/mupdf_document.h"

#include <QMainWindow>

class QAction;
class QLabel;
class QLineEdit;
class QResizeEvent;
class QScrollArea;

namespace parin {

class MainWindow final : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    bool openDocumentPath(const QString &path);

protected:
    void resizeEvent(QResizeEvent *event) override;

private slots:
    void openDocument();
    void previousPage();
    void nextPage();
    void zoomIn();
    void zoomOut();
    void fitWidth();
    void fitPage();
    void findText();

private:
    void buildUi();
    void renderCurrentPage();
    void updateDocumentState();
    [[nodiscard]] QByteArray cacheKey() const;
    [[nodiscard]] QImage decodeCachedImage(const QByteArray &payload) const;
    [[nodiscard]] QByteArray encodeImage(const QImage &image) const;

    MupdfDocument document_;
    RenderCache renderCache_;
    int currentPage_ = 0;
    qreal zoom_ = 1.0;
    bool fitWidthMode_ = false;
    bool fitPageMode_ = false;

    QScrollArea *scrollArea_ = nullptr;
    QLabel *pageCanvas_ = nullptr;
    QLabel *pageStatus_ = nullptr;
    QLabel *documentInfo_ = nullptr;
    QLineEdit *searchEdit_ = nullptr;

    QAction *previousAction_ = nullptr;
    QAction *nextAction_ = nullptr;
    QAction *zoomOutAction_ = nullptr;
    QAction *zoomInAction_ = nullptr;
    QAction *fitWidthAction_ = nullptr;
    QAction *fitPageAction_ = nullptr;
};

} // namespace parin
