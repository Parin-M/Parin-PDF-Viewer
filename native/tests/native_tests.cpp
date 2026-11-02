#include "core/render_cache.h"
#include "pdf/mupdf_document.h"

#include <QFile>
#include <QTemporaryDir>
#include <QtTest>

#include <cstdio>
#include <string>
#include <vector>

namespace {

QByteArray makeMinimalPdf()
{
    const std::string pageText = "BT /F1 16 Tf 36 320 Td (Native MuPDF Reader) Tj ET";
    const std::vector<std::string> objects = {
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 400] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n",
        "4 0 obj\n<< /Length " + std::to_string(pageText.size()) + " >>\nstream\n" + pageText + "\nendstream\nendobj\n",
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    };

    std::string pdf = "%PDF-1.4\n";
    std::vector<std::size_t> offsets;
    for (const auto &object : objects) {
        offsets.push_back(pdf.size());
        pdf += object;
    }

    const std::size_t xrefOffset = pdf.size();
    pdf += "xref\n0 6\n0000000000 65535 f \n";
    for (const auto offset : offsets) {
        char line[32] = {};
        std::snprintf(line, sizeof(line), "%010zu 00000 n \n", offset);
        pdf += line;
    }
    pdf += "trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n";
    pdf += std::to_string(xrefOffset);
    pdf += "\n%%EOF\n";
    return QByteArray(pdf.data(), static_cast<qsizetype>(pdf.size()));
}

QString writeMinimalPdf(const QString &directory)
{
    const QString path = directory + QStringLiteral("/native-fixture.pdf");
    QFile file(path);
    if (!file.open(QIODevice::WriteOnly))
        return {};
    const QByteArray contents = makeMinimalPdf();
    if (file.write(contents) != contents.size())
        return {};
    file.close();
    return path;
}

} // namespace

class NativeTests final : public QObject {
    Q_OBJECT

private slots:
    void opensCountsAndRendersPdfPage()
    {
        QTemporaryDir directory;
        QVERIFY(directory.isValid());
        const QString path = writeMinimalPdf(directory.path());
        QVERIFY(!path.isEmpty());

        parin::MupdfDocument document;
        QString error;
        QVERIFY2(document.open(path, QString(), &error), qPrintable(error));
        QVERIFY(document.isOpen());
        QCOMPARE(document.pageCount(), 1);

        const QSizeF pageSize = document.pageSize(0, &error);
        QVERIFY2(!pageSize.isEmpty(), qPrintable(error));
        QCOMPARE(qRound(pageSize.width()), 300);
        QCOMPARE(qRound(pageSize.height()), 400);

        const QImage image = document.renderPage(0, 1.0, &error);
        QVERIFY2(!image.isNull(), qPrintable(error));
        QCOMPARE(image.width(), 300);
        QCOMPARE(image.height(), 400);
        QCOMPARE(image.format(), QImage::Format_RGB888);

        const int hits = document.searchPage(0, QStringLiteral("Native MuPDF"), &error);
        QVERIFY2(hits > 0, qPrintable(error));
    }

    void rejectsMissingDocument()
    {
        parin::MupdfDocument document;
        QString error;
        QVERIFY(!document.open(QStringLiteral("/path/that/does/not/exist.pdf"), QString(), &error));
        QVERIFY(!document.isOpen());
        QVERIFY(!error.isEmpty());
    }

    void rejectsUnsafeRenderScale()
    {
        QTemporaryDir directory;
        QVERIFY(directory.isValid());
        const QString path = writeMinimalPdf(directory.path());
        QVERIFY(!path.isEmpty());

        parin::MupdfDocument document;
        QString error;
        QVERIFY2(document.open(path, QString(), &error), qPrintable(error));
        const QImage image = document.renderPage(0, 100.0, &error);
        QVERIFY(image.isNull());
        QVERIFY(!error.isEmpty());
    }

    void rustRenderCacheStoresAndClearsEntries()
    {
        parin::RenderCache cache(8);
        QVERIFY(cache.put(QByteArrayLiteral("page-a"), QByteArrayLiteral("1234")));
        QCOMPARE(cache.get(QByteArrayLiteral("page-a")), QByteArrayLiteral("1234"));
        QCOMPARE(cache.usedBytes(), std::size_t(4));
        cache.clear();
        QVERIFY(cache.get(QByteArrayLiteral("page-a")).isEmpty());
        QCOMPARE(cache.usedBytes(), std::size_t(0));
    }

    void rustRenderCacheEnforcesItsByteBudget()
    {
        parin::RenderCache cache(4);
        QVERIFY(!cache.put(QByteArrayLiteral("too-large"), QByteArrayLiteral("12345")));
        QCOMPARE(cache.usedBytes(), std::size_t(0));
    }
};

QTEST_MAIN(NativeTests)
#include "native_tests.moc"
