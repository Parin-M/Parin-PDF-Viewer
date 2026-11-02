#include "ui/main_window.h"

#include <QApplication>
#include <QCoreApplication>
#include <QFileInfo>
#include <QUrl>

int main(int argc, char *argv[])
{
    QApplication application(argc, argv);
    QCoreApplication::setApplicationName(QStringLiteral("Parin"));
    QCoreApplication::setApplicationVersion(QStringLiteral(PARIN_APP_VERSION));
    QCoreApplication::setOrganizationName(QStringLiteral("Parin"));

    parin::MainWindow window;
    window.show();

    const QStringList arguments = QCoreApplication::arguments();
    for (qsizetype index = 1; index < arguments.size(); ++index) {
        const QString argument = arguments.at(index);
        const QUrl url(argument);
        QString localPath;
        if (url.isLocalFile()) {
            localPath = url.toLocalFile();
        } else if (url.scheme().isEmpty()) {
            localPath = QFileInfo(argument).absoluteFilePath();
        }
        if (!localPath.isEmpty() && QFileInfo::exists(localPath)) {
            window.openDocumentPath(localPath);
            break;
        }
    }

    return application.exec();
}
