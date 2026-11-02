#include "ui/main_window.h"

#include <QAction>
#include <QAbstractAnimation>
#include <QCoreApplication>
#include <QIcon>
#include <QUrl>
#include <QApplication>
#include <QAudioOutput>
#include <QBuffer>
#include <QComboBox>
#include <QDataStream>
#include <QDialog>
#include <QDialogButtonBox>
#include <QDockWidget>
#include <QFileDialog>
#include <QFileInfo>
#include <QFormLayout>
#include <QFrame>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QInputDialog>
#include <QKeySequence>
#include <QLabel>
#include <QLineEdit>
#include <QMediaPlayer>
#include <QMenu>
#include <QMessageBox>
#include <QPixmap>
#include <QPushButton>
#include <QResizeEvent>
#include <QScrollArea>
#include <QScrollBar>
#include <QSettings>
#include <QSlider>
#include <QSpinBox>
#include <QStatusBar>
#include <QSplitter>
#include <QStyle>
#include <QTabWidget>
#include <QToolBar>
#include <QVBoxLayout>
#include <QWidget>
#include <QPropertyAnimation>
#include <QGraphicsOpacityEffect>
#include <algorithm>
#include <cmath>

namespace parin {
MainWindow::MainWindow(QWidget *parent) : QMainWindow(parent) {
    QSettings settings(QStringLiteral("Parin"), QStringLiteral("Parin"));
    themeIndex_ = settings.value(QStringLiteral("appearance/themeIndex"), 17).toInt();
    language_ = settings.value(QStringLiteral("general/language"), QStringLiteral("English")).toString();
    buildUi();
    refreshAppearance();
    updateDocumentState();
    resize(1540, 960);
}
void MainWindow::buildUi() {
    setWindowTitle(QStringLiteral("Parin 10.2.01 — Persian Grand Edition"));
    setMinimumSize(1040, 680);
    auto *root = new QWidget(this);
    auto *rootLayout = new QVBoxLayout(root);
    rootLayout->setContentsMargins(0,0,0,0);
    rootLayout->setSpacing(0);

    auto *top = new QFrame(root);
    top->setObjectName(QStringLiteral("topBar"));
    auto *topLayout = new QHBoxLayout(top);
    topLayout->setContentsMargins(18,10,18,10);
    topLayout->setSpacing(14);
    brandMark_ = new QLabel(QStringLiteral("✦  PARIN"), top);
    brandMark_->setObjectName(QStringLiteral("brandMark"));
    brandMark_->setStyleSheet(QStringLiteral("font-size:20px;font-weight:900;letter-spacing:2px;"));
    topLayout->addWidget(brandMark_);
    auto *edition = new QLabel(QStringLiteral("P E R S I A N   G R A N D   E D I T I O N   •   10.2.01"), top);
    edition->setObjectName(QStringLiteral("editionLabel"));
    topLayout->addWidget(edition);
    topLayout->addStretch();
    auto *settingsButton = new QPushButton(QIcon(QCoreApplication::applicationDirPath() + QStringLiteral("/../share/icons/parin/settings.svg")), QStringLiteral("Settings"), top);
    settingsButton->setObjectName(QStringLiteral("accentButton"));
    connect(settingsButton, &QPushButton::clicked, this, &MainWindow::showSettings);
    topLayout->addWidget(settingsButton);
    auto *aboutButton = new QPushButton(QStringLiteral("About"), top);
    connect(aboutButton, &QPushButton::clicked, this, &MainWindow::showAbout);
    topLayout->addWidget(aboutButton);
    rootLayout->addWidget(top);

    auto *toolbar = addToolBar(QStringLiteral("Grand Reader"));
    toolbar->setObjectName(QStringLiteral("mainToolbar"));
    toolbar->setMovable(false);
    toolbar->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    auto *openAction = toolbar->addAction(QIcon(QCoreApplication::applicationDirPath() + QStringLiteral("/../share/icons/parin/open.svg")), QStringLiteral("Open PDF"));
    openAction->setShortcut(QKeySequence::Open);
    connect(openAction, &QAction::triggered, this, &MainWindow::openDocument);
    toolbar->addSeparator();
    previousAction_ = toolbar->addAction(QStringLiteral("◀  Previous"));
    previousAction_->setShortcut(QKeySequence(Qt::Key_Left));
    connect(previousAction_, &QAction::triggered, this, &MainWindow::previousPage);
    nextAction_ = toolbar->addAction(QStringLiteral("Next  ▶"));
    nextAction_->setShortcut(QKeySequence(Qt::Key_Right));
    connect(nextAction_, &QAction::triggered, this, &MainWindow::nextPage);
    toolbar->addSeparator();
    zoomOutAction_ = toolbar->addAction(QStringLiteral("−"));
    connect(zoomOutAction_, &QAction::triggered, this, &MainWindow::zoomOut);
    zoomInAction_ = toolbar->addAction(QStringLiteral("+"));
    connect(zoomInAction_, &QAction::triggered, this, &MainWindow::zoomIn);
    fitWidthAction_ = toolbar->addAction(QStringLiteral("Fit Width"));
    connect(fitWidthAction_, &QAction::triggered, this, &MainWindow::fitWidth);
    fitPageAction_ = toolbar->addAction(QStringLiteral("Fit Page"));
    connect(fitPageAction_, &QAction::triggered, this, &MainWindow::fitPage);
    toolbar->addSeparator();
    searchEdit_ = new QLineEdit(this);
    searchEdit_->setPlaceholderText(QStringLiteral("⌕  Search inside your document…"));
    searchEdit_->setClearButtonEnabled(true);
    searchEdit_->setMinimumWidth(260);
    toolbar->addWidget(searchEdit_);
    connect(searchEdit_, &QLineEdit::returnPressed, this, &MainWindow::findText);
    toolbar->addSeparator();
    musicPanelAction_ = toolbar->addAction(QIcon(QCoreApplication::applicationDirPath() + QStringLiteral("/../share/icons/parin/music.svg")), QStringLiteral("Lo-fi Studio"));
    connect(musicPanelAction_, &QAction::triggered, this, &MainWindow::showMusicPanel);

    auto *splitter = new QSplitter(Qt::Horizontal, root);
    splitter->setChildrenCollapsible(false);
    scrollArea_ = new QScrollArea(splitter);
    scrollArea_->setObjectName(QStringLiteral("pdfScrollArea"));
    scrollArea_->setWidgetResizable(false);
    scrollArea_->setAlignment(Qt::AlignHCenter | Qt::AlignTop);
    scrollArea_->setFrameShape(QFrame::NoFrame);
    scrollArea_->setBackgroundRole(QPalette::Dark);
    pageCanvas_ = new QLabel(scrollArea_);
    pageCanvas_->setAlignment(Qt::AlignCenter);
    pageCanvas_->setMinimumSize(1,1);
    pageCanvas_->setStyleSheet(QStringLiteral("background:white;"));
    scrollArea_->setWidget(pageCanvas_);
    splitter->addWidget(scrollArea_);

    auto *inspector = new QFrame(splitter);
    inspector->setObjectName(QStringLiteral("inspector"));
    inspector->setMinimumWidth(250);
    inspector->setMaximumWidth(380);
    auto *inspectorLayout = new QVBoxLayout(inspector);
    inspectorLayout->setContentsMargins(20,22,20,20);
    inspectorLayout->setSpacing(14);
    auto *eyebrow = new QLabel(QStringLiteral("✧  DOCUMENT ATELIER"), inspector);
    eyebrow->setObjectName(QStringLiteral("eyebrow"));
    inspectorLayout->addWidget(eyebrow);
    auto *inspectorTitle = new QLabel(QStringLiteral("Document Inspector"), inspector);
    inspectorTitle->setObjectName(QStringLiteral("panelTitle"));
    inspectorLayout->addWidget(inspectorTitle);
    documentInfo_ = new QLabel(QStringLiteral("Open a PDF to explore its details."), inspector);
    documentInfo_->setWordWrap(true);
    documentInfo_->setTextInteractionFlags(Qt::TextSelectableByMouse);
    documentInfo_->setObjectName(QStringLiteral("documentInfo"));
    inspectorLayout->addWidget(documentInfo_);
    auto *quickGroup = new QGroupBox(QStringLiteral("QUICK TOOLS"), inspector);
    auto *quickLayout = new QVBoxLayout(quickGroup);
    const QStringList quicks{QStringLiteral("Page navigation"),QStringLiteral("Reading appearance"),QStringLiteral("Lo-fi listening room"),QStringLiteral("Application preferences")};
    for (const auto &label : quicks) {
        const QString iconName = label.contains(QStringLiteral("Lo-fi")) ? QStringLiteral("music.svg") : (label.contains(QStringLiteral("appearance")) ? QStringLiteral("theme.svg") : (label.contains(QStringLiteral("preferences")) ? QStringLiteral("settings.svg") : QStringLiteral("pages.svg")));
        auto *b = new QPushButton(QIcon(QCoreApplication::applicationDirPath() + QStringLiteral("/../share/icons/parin/") + iconName), label, quickGroup);
        b->setObjectName(QStringLiteral("quickButton"));
        quickLayout->addWidget(b);
        if (label.contains(QStringLiteral("Lo-fi"))) connect(b,&QPushButton::clicked,this,&MainWindow::showMusicPanel);
        else if (label.contains(QStringLiteral("preferences"))) connect(b,&QPushButton::clicked,this,&MainWindow::showSettings);
        else if (label.contains(QStringLiteral("appearance"))) connect(b,&QPushButton::clicked,this,&MainWindow::showSettings);
        else connect(b,&QPushButton::clicked,this,[this]{ if(document_.isOpen()) fitPage(); });
    }
    inspectorLayout->addWidget(quickGroup);
    inspectorLayout->addStretch(1);
    auto *engine = new QLabel(QStringLiteral("NATIVE ENGINE  ·  MuPDF C API\nRENDER CACHE  ·  Rust"), inspector);
    engine->setObjectName(QStringLiteral("engineLabel"));
    inspectorLayout->addWidget(engine);
    splitter->addWidget(inspector);
    splitter->setStretchFactor(0,1);
    splitter->setSizes({1180,320});
    rootLayout->addWidget(splitter,1);
    setCentralWidget(root);
    pageStatus_ = new QLabel(QStringLiteral("Welcome to Parin"), this);
    statusBar()->addPermanentWidget(pageStatus_);
    statusBar()->showMessage(QStringLiteral("Persian Grand Edition  ·  Ready"));
    musicPlayer_ = new QMediaPlayer(this);
    audioOutput_ = new QAudioOutput(this);
    musicPlayer_->setAudioOutput(audioOutput_);
    connect(musicPlayer_, &QMediaPlayer::errorOccurred, this, [this](QMediaPlayer::Error,const QString &error){ statusBar()->showMessage(QStringLiteral("Audio: %1").arg(error),6000); });
}
void MainWindow::refreshAppearance() {
    const int hue = (themeIndex_ * 137) % 360;
    const QColor accent = QColor::fromHsv(hue, 155 + ((themeIndex_/360)%2)*35 + (themeIndex_%4)*20, 205);
    const QColor accentDark = accent.darker(145);
    const QString a = accent.name();
    const QString ad = accentDark.name();
    const QString css = QStringLiteral(
      "QMainWindow{background:#0b1220;color:#e9edf5;} QWidget{font-family:'Noto Sans','DejaVu Sans';font-size:10pt;color:#e9edf5;}"
      "QFrame#topBar{background:#101b2d;border-bottom:1px solid #293b50;} QLabel#brandMark{color:%1;} QLabel#editionLabel{color:#8294aa;font-size:9pt;}"
      "QToolBar#mainToolbar{background:#15243a;border:0;border-bottom:1px solid #30445e;padding:9px;spacing:7px;} QToolBar QToolButton{color:#e9edf5;padding:9px 12px;border-radius:8px;font-weight:600;} QToolBar QToolButton:hover{background:#263a55;color:white;}"
      "QLineEdit,QComboBox,QSpinBox{background:#111d30;color:#eef3fa;border:1px solid #344a66;border-radius:8px;padding:9px;selection-background-color:%1;}"
      "QFrame#inspector{background:#101b2d;border-left:1px solid #293b50;} QLabel#eyebrow{color:%1;font-weight:800;letter-spacing:2px;font-size:9pt;} QLabel#panelTitle{font-size:17pt;font-weight:800;color:#f4f0e8;} QLabel#documentInfo{background:#15243a;border:1px solid #2b405c;border-radius:12px;padding:14px;line-height:1.6;} QLabel#engineLabel{color:#8294aa;font-size:9pt;}"
      "QGroupBox{border:1px solid #2c405a;border-radius:10px;margin-top:14px;padding:12px;color:%1;font-weight:800;} QGroupBox::title{subcontrol-origin:margin;left:12px;padding:0 5px;}"
      "QPushButton{background:#1a2b43;color:#eaf0f8;border:1px solid #354b68;border-radius:9px;padding:9px 12px;} QPushButton:hover{background:%2;border-color:%1;} QPushButton#accentButton{background:%1;color:#07111e;font-weight:900;border:0;} QPushButton#quickButton{text-align:left;background:#14243a;border:0;padding:12px;} QPushButton#quickButton:hover{background:%2;}"
      "QScrollArea{background:#202b3a;border:0;} QStatusBar{background:#101b2d;color:#9aabc0;border-top:1px solid #293b50;} QTabWidget::pane{border:1px solid #344a66;border-radius:8px;} QTabBar::tab{background:#15243a;padding:10px 16px;border-radius:6px;margin:3px;} QTabBar::tab:selected{background:%1;color:#07111e;} QSlider::groove:horizontal{height:6px;background:#344a66;border-radius:3px;} QSlider::handle:horizontal{background:%1;width:16px;margin:-5px 0;border-radius:8px;}"
    ).arg(a,ad);
    setStyleSheet(css);
    if (brandMark_) brandMark_->setText(QStringLiteral("✦  PARIN"));
}
void MainWindow::applyTheme(int index) {
    themeIndex_ = std::clamp(index,0,499);
    QSettings().setValue(QStringLiteral("appearance/themeIndex"),themeIndex_);
    refreshAppearance();
}
void MainWindow::showSettings() {
    QDialog dialog(this);
    dialog.setWindowTitle(QStringLiteral("Parin Settings Atelier"));
    dialog.resize(720,560);
    auto *layout = new QVBoxLayout(&dialog);
    auto *tabs = new QTabWidget(&dialog);
    auto *general = new QWidget(tabs); auto *generalForm = new QFormLayout(general);
    auto *language = new QComboBox(general);
    language->addItems({QStringLiteral("فارسی"),QStringLiteral("English"),QStringLiteral("Dansk"),QStringLiteral("Svenska"),QStringLiteral("العربية"),QStringLiteral("Norsk"),QStringLiteral("Deutsch"),QStringLiteral("Ελληνικά"),QStringLiteral("Українська"),QStringLiteral("Türkçe"),QStringLiteral("日本語"),QStringLiteral("Italiano"),QStringLiteral("한국어"),QStringLiteral("Монгол"),QStringLiteral("हिन्दी"),QStringLiteral("اردو")});
    language->setCurrentText(language_==QStringLiteral("English")?QStringLiteral("English"):language_);
    generalForm->addRow(QStringLiteral("Interface language"),language);
    auto *animations = new QComboBox(general); animations->addItems({QStringLiteral("Subtle"),QStringLiteral("Balanced"),QStringLiteral("Expressive"),QStringLiteral("Reduced motion")});
    generalForm->addRow(QStringLiteral("Motion profile"),animations);
    auto *startup = new QComboBox(general); startup->addItems({QStringLiteral("New workspace"),QStringLiteral("Restore last session"),QStringLiteral("Open file dialog")});
    generalForm->addRow(QStringLiteral("Startup behavior"),startup);
    tabs->addTab(general,QStringLiteral("General"));
    auto *appearance = new QWidget(tabs); auto *appearanceForm = new QFormLayout(appearance);
    auto *theme = new QComboBox(appearance);
    for(int i=1;i<=500;++i) theme->addItem(QStringLiteral("Theme %1  ·  %2°").arg(i,3,10,QChar('0')).arg(((i-1)*137)%360),i-1);
    theme->setCurrentIndex(themeIndex_);
    appearanceForm->addRow(QStringLiteral("500-color theme library"),theme);
    auto *density = new QComboBox(appearance); density->addItems({QStringLiteral("Comfortable"),QStringLiteral("Compact"),QStringLiteral("Spacious")});
    appearanceForm->addRow(QStringLiteral("Interface density"),density);
    auto *accentPreview = new QLabel(QStringLiteral("Persian geometry  ·  Turquoise / lapis / saffron / midnight"),appearance);
    appearanceForm->addRow(QStringLiteral("Visual identity"),accentPreview);
    tabs->addTab(appearance,QStringLiteral("Appearance"));
    auto *reader = new QWidget(tabs); auto *readerForm = new QFormLayout(reader);
    auto *defaultZoom = new QComboBox(reader); defaultZoom->addItems({QStringLiteral("Fit page"),QStringLiteral("Fit width"),QStringLiteral("100%"),QStringLiteral("125%"),QStringLiteral("150%")});
    readerForm->addRow(QStringLiteral("Default zoom"),defaultZoom);
    auto *smooth = new QComboBox(reader); smooth->addItems({QStringLiteral("High quality"),QStringLiteral("Balanced"),QStringLiteral("Performance")});
    readerForm->addRow(QStringLiteral("Rendering quality"),smooth);
    auto *remember = new QComboBox(reader); remember->addItems({QStringLiteral("Remember last page"),QStringLiteral("Always start at page 1")});
    readerForm->addRow(QStringLiteral("Reopen behavior"),remember);
    tabs->addTab(reader,QStringLiteral("Reader"));
    auto *audio = new QWidget(tabs); auto *audioForm = new QFormLayout(audio);
    auto *volume = new QSlider(Qt::Horizontal,audio); volume->setRange(0,100); volume->setValue(qRound(audioOutput_->volume()*100));
    audioForm->addRow(QStringLiteral("Lo-fi master volume"),volume);
    auto *audioHint = new QLabel(QStringLiteral("Use your own local audio files. Parin does not bundle copyrighted music."),audio); audioHint->setWordWrap(true);
    audioForm->addRow(QStringLiteral("Library"),audioHint);
    tabs->addTab(audio,QStringLiteral("Audio"));
    auto *advanced = new QWidget(tabs); auto *advancedForm = new QFormLayout(advanced);
    auto *cache = new QComboBox(advanced); cache->addItems({QStringLiteral("128 MB"),QStringLiteral("256 MB"),QStringLiteral("512 MB"),QStringLiteral("1024 MB")});
    advancedForm->addRow(QStringLiteral("Render cache limit"),cache);
    auto *hardware = new QComboBox(advanced); hardware->addItems({QStringLiteral("Automatic"),QStringLiteral("Prefer quality"),QStringLiteral("Prefer performance")});
    advancedForm->addRow(QStringLiteral("Performance profile"),hardware);
    tabs->addTab(advanced,QStringLiteral("Advanced"));
    layout->addWidget(tabs);
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Save|QDialogButtonBox::Cancel,&dialog);
    layout->addWidget(buttons);
    connect(buttons,&QDialogButtonBox::rejected,&dialog,&QDialog::reject);
    connect(buttons,&QDialogButtonBox::accepted,&dialog,&QDialog::accept);
    connect(volume,&QSlider::valueChanged,this,[this](int v){audioOutput_->setVolume(v/100.0);});
    connect(theme,qOverload<int>(&QComboBox::currentIndexChanged),this,&MainWindow::applyTheme);
    if(dialog.exec()==QDialog::Accepted) {
        language_=language->currentText();
        const bool rtl = language_ == QStringLiteral("فارسی") || language_ == QStringLiteral("العربية") || language_ == QStringLiteral("اردو");
        setLayoutDirection(rtl ? Qt::RightToLeft : Qt::LeftToRight);
        QSettings settings(QStringLiteral("Parin"),QStringLiteral("Parin"));
        settings.setValue(QStringLiteral("general/language"),language_);
        settings.setValue(QStringLiteral("appearance/motionProfile"),animations->currentText());
        settings.setValue(QStringLiteral("appearance/density"),density->currentText());
        settings.setValue(QStringLiteral("reader/defaultZoom"),defaultZoom->currentText());
        settings.setValue(QStringLiteral("reader/quality"),smooth->currentText());
        settings.setValue(QStringLiteral("reader/rememberPage"),remember->currentText());
        settings.setValue(QStringLiteral("performance/cacheLimit"),cache->currentText());
        settings.setValue(QStringLiteral("performance/profile"),hardware->currentText());
    }
}
void MainWindow::showMusicPanel() {
    auto *dock = findChild<QDockWidget*>(QStringLiteral("lofiDock"));
    if (!dock) {
        dock = new QDockWidget(QStringLiteral("♫  LO-FI LISTENING ROOM"),this);
        dock->setObjectName(QStringLiteral("lofiDock"));
        dock->setAllowedAreas(Qt::LeftDockWidgetArea|Qt::RightDockWidgetArea|Qt::BottomDockWidgetArea);
        auto *panel = new QWidget(dock); auto *layout = new QVBoxLayout(panel);
        auto *title = new QLabel(QStringLiteral("MIDNIGHT STUDY CLUB"),panel); title->setObjectName(QStringLiteral("panelTitle"));
        auto *sub = new QLabel(QStringLiteral("A quiet corner for deep focus. Play your own ambient and lo-fi tracks."),panel); sub->setWordWrap(true);
        musicTrackLabel_ = new QLabel(QStringLiteral("No track selected"),panel);
        auto *pick = new QPushButton(QStringLiteral("＋  Add local audio"),panel);
        auto *controls = new QHBoxLayout();
        auto *play = new QPushButton(QStringLiteral("▶  Play / Pause"),panel);
        auto *stop = new QPushButton(QStringLiteral("■  Stop"),panel);
        controls->addWidget(play); controls->addWidget(stop);
        auto *vol = new QSlider(Qt::Horizontal,panel); vol->setRange(0,100); vol->setValue(55); audioOutput_->setVolume(0.55);
        layout->addWidget(title); layout->addWidget(sub); layout->addWidget(musicTrackLabel_); layout->addWidget(pick); layout->addLayout(controls);
        layout->addWidget(new QLabel(QStringLiteral("MASTER VOLUME"),panel)); layout->addWidget(vol); layout->addStretch();
        connect(pick,&QPushButton::clicked,this,&MainWindow::chooseMusic);
        connect(play,&QPushButton::clicked,this,&MainWindow::toggleMusic);
        connect(stop,&QPushButton::clicked,musicPlayer_,&QMediaPlayer::stop);
        connect(vol,&QSlider::valueChanged,this,[this](int v){audioOutput_->setVolume(v/100.0);});
        dock->setWidget(panel); addDockWidget(Qt::RightDockWidgetArea,dock);
        auto *effect = new QGraphicsOpacityEffect(dock); dock->setGraphicsEffect(effect);
        auto *animation = new QPropertyAnimation(effect,"opacity",dock); animation->setDuration(260); animation->setStartValue(0.35); animation->setEndValue(1.0); animation->start(QAbstractAnimation::DeleteWhenStopped);
    }
    dock->show(); dock->raise();
}
void MainWindow::chooseMusic() {
    const QString file = QFileDialog::getOpenFileName(this,QStringLiteral("Choose local audio"),QString(),QStringLiteral("Audio files (*.mp3 *.ogg *.wav *.flac *.m4a);;All files (*)"));
    if(file.isEmpty()) return;
    musicPlayer_->setSource(QUrl::fromLocalFile(file));
    musicTrackLabel_->setText(QFileInfo(file).fileName());
    musicPlayer_->play();
}
void MainWindow::toggleMusic() {
    if(musicPlayer_->playbackState()==QMediaPlayer::PlayingState) musicPlayer_->pause();
    else if(!musicPlayer_->source().isEmpty()) musicPlayer_->play();
    else chooseMusic();
}
void MainWindow::showAbout() {
    QMessageBox box(this);
    box.setWindowTitle(QStringLiteral("About Parin"));
    box.setTextFormat(Qt::RichText);
    box.setText(QStringLiteral("<div style='font-size:22px;font-weight:800;color:#27c6b5'>✦ PARIN 10.2.01</div><p><b>Persian Grand Edition</b></p><p>این نرم‌افزار توسط <b>پــَــرین مشعلچیان</b><br/>(Parin Mashalchian) ساخته شده است.</p><p>Native PDF workspace · C++ / Qt · MuPDF · Rust</p><p>Crafted with a Persian design spirit.</p>"));
    box.setInformativeText(QStringLiteral("Version 10.2.01"));
    box.exec();
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
