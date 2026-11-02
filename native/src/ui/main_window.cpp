#include "ui/main_window.h"

#include <QAction>
#include <QApplication>
#include <QBuffer>
#include <QDataStream>
#include <QKeySequence>
#include <QFileDialog>
#include <QFileInfo>
#include <QFrame>
#include <QHBoxLayout>
#include <QInputDialog>
#include <QLabel>
#include <QLineEdit>
#include <QMessageBox>
#include <QPixmap>
#include <QResizeEvent>
#include <QScrollArea>
#include <QScrollBar>
#include <QSplitter>
#include <QStyle>
#include <QToolBar>
#include <QVBoxLayout>
#include <QWidget>

#include <algorithm>
#include <cmath>

namespace parin {

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
{
    buildUi();
    updateDocumentState();
    resize(1440, 900);
}

void MainWindow::buildUi()
{
    setWindowTitle(QStringLiteral("Parin 10.2 — Native PDF Workspace"));
    setMinimumSize(900, 600);
    setStyleSheet(QStringLiteral(
        "QMainWindow { background: #edf2f8; }"
        "QToolBar { background: #142943; color: white; border: 0; spacing: 6px; padding: 8px; }"
        "QToolBar QToolButton { color: white; padding: 7px 10px; border-radius: 6px; }"
        "QToolBar QToolButton:hover { background: #2c4563; }"
        "QLineEdit { background: #ffffff; color: #1c2b3e; border: 1px solid #cbd5e1; border-radius: 6px; padding: 7px; min-width: 190px; }"
        "QFrame#inspector { background: #f8fafc; border-left: 1px solid #d7e0ea; }"
        "QLabel#muted { color: #63758b; }"
        "QStatusBar { background: #f8fafc; color: #52657b; }"
    ));

    auto *toolbar = addToolBar(QStringLiteral("Reader"));
    toolbar->setMovable(false);

    auto *openAction = toolbar->addAction(
        style()->standardIcon(QStyle::SP_DialogOpenButton), QStringLiteral("Open PDF"));
    openAction->setShortcut(QKeySequence::Open);
    connect(openAction, &QAction::triggered, this, &MainWindow::openDocument);

    toolbar->addSeparator();
    previousAction_ = toolbar->addAction(QStringLiteral("Previous"));
    previousAction_->setShortcut(QKeySequence(Qt::Key_Left));
    connect(previousAction_, &QAction::triggered, this, &MainWindow::previousPage);

    nextAction_ = toolbar->addAction(QStringLiteral("Next"));
    nextAction_->setShortcut(QKeySequence(Qt::Key_Right));
    connect(nextAction_, &QAction::triggered, this, &MainWindow::nextPage);

    toolbar->addSeparator();
    zoomOutAction_ = toolbar->addAction(QStringLiteral("−"));
    zoomOutAction_->setToolTip(QStringLiteral("Zoom out"));
    connect(zoomOutAction_, &QAction::triggered, this, &MainWindow::zoomOut);

    zoomInAction_ = toolbar->addAction(QStringLiteral("+"));
    zoomInAction_->setToolTip(QStringLiteral("Zoom in"));
    connect(zoomInAction_, &QAction::triggered, this, &MainWindow::zoomIn);

    fitWidthAction_ = toolbar->addAction(QStringLiteral("Fit Width"));
    connect(fitWidthAction_, &QAction::triggered, this, &MainWindow::fitWidth);

    fitPageAction_ = toolbar->addAction(QStringLiteral("Fit Page"));
    connect(fitPageAction_, &QAction::triggered, this, &MainWindow::fitPage);

    toolbar->addSeparator();
    searchEdit_ = new QLineEdit(this);
    searchEdit_->setPlaceholderText(QStringLiteral("Search in document…"));
    searchEdit_->setClearButtonEnabled(true);
    toolbar->addWidget(searchEdit_);
    connect(searchEdit_, &QLineEdit::returnPressed, this, &MainWindow::findText);

    auto *splitter = new QSplitter(Qt::Horizontal, this);
    splitter->setChildrenCollapsible(false);

    scrollArea_ = new QScrollArea(splitter);
    scrollArea_->setObjectName(QStringLiteral("pdfScrollArea"));
    scrollArea_->setWidgetResizable(false);
    scrollArea_->setAlignment(Qt::AlignHCenter | Qt::AlignTop);
    scrollArea_->setFrameShape(QFrame::NoFrame);
    scrollArea_->setBackgroundRole(QPalette::AlternateBase);

    pageCanvas_ = new QLabel(scrollArea_);
    pageCanvas_->setAlignment(Qt::AlignCenter);
    pageCanvas_->setMinimumSize(1, 1);
    pageCanvas_->setStyleSheet(QStringLiteral("background: white;"));
    scrollArea_->setWidget(pageCanvas_);
    splitter->addWidget(scrollArea_);

    auto *inspector = new QFrame(splitter);
    inspector->setObjectName(QStringLiteral("inspector"));
    inspector->setMinimumWidth(230);
    inspector->setMaximumWidth(340);
    auto *inspectorLayout = new QVBoxLayout(inspector);
    inspectorLayout->setContentsMargins(18, 18, 18, 18);
    inspectorLayout->setSpacing(12);

    auto *inspectorHeading = new QLabel(QStringLiteral("DOCUMENT INSPECTOR"), inspector);
    inspectorHeading->setObjectName(QStringLiteral("muted"));
    inspectorHeading->setStyleSheet(QStringLiteral("font-size: 10pt; font-weight: 700;"));
    inspectorLayout->addWidget(inspectorHeading);

    documentInfo_ = new QLabel(QStringLiteral("No document open"), inspector);
    documentInfo_->setWordWrap(true);
    documentInfo_->setTextInteractionFlags(Qt::TextSelectableByMouse);
    inspectorLayout->addWidget(documentInfo_);
    inspectorLayout->addStretch(1);

    auto *engineLabel = new QLabel(QStringLiteral("Native engine: MuPDF C API"), inspector);
    engineLabel->setObjectName(QStringLiteral("muted"));
    engineLabel->setWordWrap(true);
    inspectorLayout->addWidget(engineLabel);
    auto *cacheLabel = new QLabel(QStringLiteral("Render cache: Rust"), inspector);
    cacheLabel->setObjectName(QStringLiteral("muted"));
    inspectorLayout->addWidget(cacheLabel);
    splitter->addWidget(inspector);
    splitter->setStretchFactor(0, 1);
    splitter->setSizes({1100, 280});

    setCentralWidget(splitter);
    pageStatus_ = new QLabel(QStringLiteral("No document open"), this);
    statusBar()->addPermanentWidget(pageStatus_);
    statusBar()->showMessage(QStringLiteral("Ready — native preview"));

}

void MainWindow::openDocument()
{
    const QString selectedPath = QFileDialog::getOpenFileName(
        this,
        QStringLiteral("Open PDF"),
        QString(),
        QStringLiteral("PDF documents (*.pdf);;All files (*)")
    );
    if (!selectedPath.isEmpty())
        openDocumentPath(selectedPath);
}

bool MainWindow::openDocumentPath(const QString &selectedPath)
{
    MupdfDocument candidate;
    QString error;
    if (!candidate.open(selectedPath, QString(), &error) &&
        error.contains(QStringLiteral("password"), Qt::CaseInsensitive)) {
        bool accepted = false;
        const QString password = QInputDialog::getText(
            this,
            QStringLiteral("Protected PDF"),
            QStringLiteral("Enter the document password:"),
            QLineEdit::Password,
            QString(),
            &accepted
        );
        if (!accepted)
            return false;
        if (!candidate.open(selectedPath, password, &error)) {
            QMessageBox::warning(this, QStringLiteral("Could not open PDF"), error);
            return false;
        }
    } else if (!candidate.isOpen()) {
        QMessageBox::warning(this, QStringLiteral("Could not open PDF"), error);
        return false;
    }

    document_ = std::move(candidate);
    currentPage_ = 0;
    zoom_ = 1.0;
    fitWidthMode_ = false;
    fitPageMode_ = false;
    renderCache_.clear();
    renderCurrentPage();
    updateDocumentState();
    statusBar()->showMessage(QStringLiteral("Opened %1").arg(QFileInfo(document_.path()).fileName()), 4000);
    return true;
}

void MainWindow::previousPage()
{
    if (!document_.isOpen() || currentPage_ <= 0)
        return;
    --currentPage_;
    renderCurrentPage();
    updateDocumentState();
}

void MainWindow::nextPage()
{
    if (!document_.isOpen() || currentPage_ + 1 >= document_.pageCount())
        return;
    ++currentPage_;
    renderCurrentPage();
    updateDocumentState();
}

void MainWindow::zoomIn()
{
    if (!document_.isOpen())
        return;
    fitWidthMode_ = false;
    fitPageMode_ = false;
    zoom_ = std::min<qreal>(zoom_ * 1.15, 8.0);
    renderCurrentPage();
    updateDocumentState();
}

void MainWindow::zoomOut()
{
    if (!document_.isOpen())
        return;
    fitWidthMode_ = false;
    fitPageMode_ = false;
    zoom_ = std::max<qreal>(zoom_ / 1.15, 0.1);
    renderCurrentPage();
    updateDocumentState();
}

void MainWindow::fitWidth()
{
    if (!document_.isOpen())
        return;
    QString error;
    const QSizeF points = document_.pageSize(currentPage_, &error);
    if (points.isEmpty()) {
        QMessageBox::warning(this, QStringLiteral("Could not size page"), error);
        return;
    }
    const int availableWidth = std::max(120, scrollArea_->viewport()->width() - 40);
    zoom_ = std::clamp<qreal>(availableWidth / points.width(), 0.1, 8.0);
    fitWidthMode_ = true;
    fitPageMode_ = false;
    renderCurrentPage();
    updateDocumentState();
}

void MainWindow::fitPage()
{
    if (!document_.isOpen())
        return;
    QString error;
    const QSizeF points = document_.pageSize(currentPage_, &error);
    if (points.isEmpty()) {
        QMessageBox::warning(this, QStringLiteral("Could not size page"), error);
        return;
    }
    const QSize viewport = scrollArea_->viewport()->size() - QSize(40, 40);
    const qreal widthScale = std::max(1, viewport.width()) / points.width();
    const qreal heightScale = std::max(1, viewport.height()) / points.height();
    zoom_ = std::clamp<qreal>(std::min(widthScale, heightScale), 0.1, 8.0);
    fitWidthMode_ = false;
    fitPageMode_ = true;
    renderCurrentPage();
    updateDocumentState();
}

QByteArray MainWindow::cacheKey() const
{
    return QStringLiteral("%1|page=%2|zoom=%3")
        .arg(document_.path())
        .arg(currentPage_)
        .arg(qRound(zoom_ * 1000.0))
        .toUtf8();
}

QImage MainWindow::decodeCachedImage(const QByteArray &payload) const
{
    if (payload.isEmpty())
        return {};

    QByteArray buffer = payload;
    QBuffer input(&buffer);
    if (!input.open(QIODevice::ReadOnly))
        return {};
    QDataStream stream(&input);
    quint32 width = 0;
    quint32 height = 0;
    quint32 stride = 0;
    stream >> width >> height >> stride;

    const qint64 offset = input.pos();
    const quint64 byteCount = static_cast<quint64>(stride) * height;
    if (stream.status() != QDataStream::Ok || width == 0 || height == 0 ||
        stride < width * 3u || width > 12000 || height > 12000 ||
        static_cast<quint64>(width) * height > 16000000u ||
        byteCount > 48u * 1024u * 1024u ||
        offset < 0 || offset + static_cast<qint64>(byteCount) > buffer.size()) {
        return {};
    }

    const auto *pixels = reinterpret_cast<const uchar *>(buffer.constData() + offset);
    return QImage(pixels, static_cast<int>(width), static_cast<int>(height),
        static_cast<int>(stride), QImage::Format_RGB888).copy();
}

QByteArray MainWindow::encodeImage(const QImage &image) const
{
    if (image.isNull() || image.format() != QImage::Format_RGB888)
        return {};
    QByteArray payload;
    QDataStream stream(&payload, QIODevice::WriteOnly);
    stream << static_cast<quint32>(image.width())
           << static_cast<quint32>(image.height())
           << static_cast<quint32>(image.bytesPerLine());
    if (stream.status() != QDataStream::Ok)
        return {};
    payload.append(reinterpret_cast<const char *>(image.constBits()),
        static_cast<qsizetype>(image.sizeInBytes()));
    return payload;
}

void MainWindow::renderCurrentPage()
{
    if (!document_.isOpen())
        return;

    QImage image = decodeCachedImage(renderCache_.get(cacheKey()));
    if (image.isNull()) {
        QString error;
        image = document_.renderPage(currentPage_, zoom_, &error);
        if (image.isNull()) {
            QMessageBox::warning(this, QStringLiteral("Could not render page"), error);
            return;
        }
        renderCache_.put(cacheKey(), encodeImage(image));
    }

    pageCanvas_->setPixmap(QPixmap::fromImage(image));
    pageCanvas_->resize(image.size());
    scrollArea_->horizontalScrollBar()->setValue(0);
    updateDocumentState();
}

void MainWindow::updateDocumentState()
{
    const bool open = document_.isOpen();
    const int pages = document_.pageCount();
    previousAction_->setEnabled(open && currentPage_ > 0);
    nextAction_->setEnabled(open && currentPage_ + 1 < pages);
    zoomOutAction_->setEnabled(open);
    zoomInAction_->setEnabled(open);
    fitWidthAction_->setEnabled(open);
    fitPageAction_->setEnabled(open);

    if (!open) {
        pageCanvas_->clear();
        documentInfo_->setText(QStringLiteral("No document open"));
        pageStatus_->setText(QStringLiteral("No document open"));
        return;
    }

    QString sizeError;
    const QSizeF points = document_.pageSize(currentPage_, &sizeError);
    documentInfo_->setText(QStringLiteral(
        "<b>%1</b><br><br>Pages: %2<br>Current page: %3 / %2<br>"
        "Page size: %4 × %5 pt<br>Zoom: %6%<br><br>"
        "<span style='color:#64748b'>Read-only native preview</span>")
        .arg(QFileInfo(document_.path()).fileName().toHtmlEscaped())
        .arg(pages)
        .arg(currentPage_ + 1)
        .arg(qRound(points.width()))
        .arg(qRound(points.height()))
        .arg(qRound(zoom_ * 100.0)));
    pageStatus_->setText(QStringLiteral("Page %1 / %2  ·  %3%")
        .arg(currentPage_ + 1).arg(pages).arg(qRound(zoom_ * 100.0)));
}

void MainWindow::findText()
{
    if (!document_.isOpen() || searchEdit_->text().trimmed().isEmpty())
        return;

    const QString query = searchEdit_->text().trimmed();
    const int pageCount = document_.pageCount();
    for (int offset = 0; offset < pageCount; ++offset) {
        const int candidatePage = (currentPage_ + offset) % pageCount;
        QString error;
        const int hits = document_.searchPage(candidatePage, query, &error);
        if (hits < 0) {
            QMessageBox::warning(this, QStringLiteral("Search failed"), error);
            return;
        }
        if (hits > 0) {
            currentPage_ = candidatePage;
            renderCurrentPage();
            updateDocumentState();
            statusBar()->showMessage(
                QStringLiteral("Found %1 match(es) on page %2").arg(hits).arg(candidatePage + 1),
                5000
            );
            return;
        }
    }
    QMessageBox::information(this, QStringLiteral("Search"), QStringLiteral("No matches found."));
}

void MainWindow::resizeEvent(QResizeEvent *event)
{
    QMainWindow::resizeEvent(event);
    if (!document_.isOpen())
        return;
    if (fitWidthMode_)
        fitWidth();
    else if (fitPageMode_)
        fitPage();
}

} // namespace parin
