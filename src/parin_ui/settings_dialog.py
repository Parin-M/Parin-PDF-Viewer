"""Modular settings dialog for Parin PDF Viewer."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True, slots=True)
class SettingsDialogResources:
    """Application-owned resources injected into the settings UI."""

    settings_i18n: Mapping[str, Mapping[str, str]]
    color_themes: Sequence[str]
    theme_accents: Mapping[str, tuple[int, int, int]]
    theme_stylesheet: Callable[[str, str], str]
    app_version: str
    about_attribution: str
    make_app_icon: Callable[[int], Any]
    card_frame: Callable[[str, str], tuple[QFrame, QVBoxLayout]]


class SettingsDialog(QDialog):
    settings_changed=Signal(dict)
    def __init__(
        self,
        viewer,
        resources: SettingsDialogResources | None = None,
    ):
        super().__init__(viewer)
        self.viewer = viewer
        if resources is None:
            resource_factory = getattr(viewer, "_settings_dialog_resources", None)
            if not callable(resource_factory):
                raise TypeError(
                    "SettingsDialog requires resources or a viewer with "
                    "_settings_dialog_resources()."
                )
            resources = resource_factory()
        self.resources = resources
        self.settings = viewer.app_settings.copy()
        self.lang = (
            viewer.current_lang
            if viewer.current_lang in self.resources.settings_i18n
            else "en"
        )
        self.setMinimumSize(920, 640)
        self.resize(1100, 760)
        self.setModal(True)
        self._build_ui()
        self._retranslate()
        self._fade_in()
    def _build_ui(self):
        root=QVBoxLayout(self); root.setContentsMargins(18,18,18,18); root.setSpacing(14)
        header=QFrame(); header.setObjectName('settingsHeader'); hl=QHBoxLayout(header); hl.setContentsMargins(20,16,20,16); ic=QLabel(); ic.setPixmap(self.resources.make_app_icon(58).pixmap(58,58)); hl.addWidget(ic); tb=QVBoxLayout(); self.title=QLabel(); self.title.setObjectName('settingsTitle'); self.subtitle=QLabel(); self.subtitle.setObjectName('settingsSubtitle'); self.subtitle.setWordWrap(True); tb.addWidget(self.title); tb.addWidget(self.subtitle); hl.addLayout(tb,1); self.live_chip=QLabel(); self.live_chip.setObjectName('settingsChip'); hl.addWidget(self.live_chip); root.addWidget(header)
        body=QHBoxLayout(); body.setSpacing(14); self.nav=QListWidget(); self.nav.setObjectName('settingsNav'); self.nav.setFixedWidth(255); body.addWidget(self.nav); self.stack=QStackedWidget(); body.addWidget(self.stack,1); root.addLayout(body,1)
        self.card_titles=[]; self._build_overview(); self._build_appearance(); self._build_eye(); self._build_document(); self._build_performance(); self._build_audio(); self._build_shortcuts(); self._build_about(); self.nav.currentRowChanged.connect(self._switch_page)
        foot=QHBoxLayout(); self.reset_btn=QPushButton(); self.reset_btn.clicked.connect(self.reset_defaults); foot.addWidget(self.reset_btn); foot.addStretch(); self.lang_combo=QComboBox(); self.lang_combo.addItems(['English','فارسی','Dansk','Deutsch','Español','Norsk','Suomi','Svenska','Français','Ελληνικά','العربية']); self.lang_combo.currentIndexChanged.connect(self._language_from_settings); foot.addWidget(self.lang_combo); self.buttons=QDialogButtonBox(QDialogButtonBox.Cancel|QDialogButtonBox.Apply|QDialogButtonBox.Ok); self.buttons.rejected.connect(self.reject); self.buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_changes); self.buttons.accepted.connect(self.accept); foot.addWidget(self.buttons); root.addLayout(foot); self.nav.setCurrentRow(0)
    def _page(self):
        # Each settings page owns a real scroll area with an explicitly sized
        # content widget. This avoids the previous zero-height/transparent
        # content issue that could make the settings center appear blank.
        w = QWidget()
        w.setObjectName("settingsPage")
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("settingsPageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        inner = QWidget()
        inner.setObjectName("settingsPageContent")
        inner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(8, 8, 18, 18)
        lay.setSpacing(14)
        lay.setAlignment(Qt.AlignTop)
        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)
        return w, lay
    def _card(self,lay,title,sub=''):
        f,fl=self.resources.card_frame(title,sub); lay.addWidget(f); self.card_titles.append(f.findChild(QLabel,'settingsCardTitle')); return fl
    def _check(self,lay,text,key,default=True):
        c=QCheckBox(text); c.setChecked(bool(self.settings.get(key,default))); lay.addWidget(c); return c
    def _build_overview(self):
        w,l=self._page(); f=self._card(l,'General'); self.language_label=QLabel(); f.addWidget(self.language_label); self.remember_last=self._check(f,'','remember_last'); self.restore_zoom=self._check(f,'','restore_zoom'); self.single_page=self._check(f,'','single_page'); self.confirm_close=self._check(f,'','confirm_close'); f=self._card(l,'Workspace'); self.status=self._check(f,'','status_bar'); self.center_page=self._check(f,'','center_page'); self.page_shadow=self._check(f,'','page_shadow'); l.addStretch(); self.stack.addWidget(w)
    def _build_appearance(self):
        w,l=self._page()
        f=self._card(l,"Theme Studio","A clean theme with light and dark appearance modes.")
        self.appearance_label=QLabel()
        f.addWidget(self.appearance_label)
        self.appearance_mode=QComboBox()
        self.appearance_mode.addItem("Light","light")
        self.appearance_mode.addItem("Dark","dark")
        self.appearance_mode.setCurrentIndex(1 if str(self.settings.get("appearance_mode","light")).lower()=="dark" else 0)
        f.addWidget(self.appearance_mode)
        self.theme_label=QLabel()
        f.addWidget(self.theme_label)
        self.theme=QComboBox()
        self.theme.addItems(list(self.resources.color_themes))
        self.theme.setCurrentText(self.settings.get("theme","Arctic Glass"))
        f.addWidget(self.theme)
        self.theme_preview=QLabel()
        self.theme_preview.setMinimumHeight(54)
        self.theme_preview.setAlignment(Qt.AlignCenter)
        f.addWidget(self.theme_preview)
        self.accent_label=QLabel()
        f.addWidget(self.accent_label)
        self.accent=QComboBox()
        self.accent.addItems(["Theme default","Azure","Violet","Turquoise","Rose","Emerald"])
        self.accent.setCurrentText(self.settings.get("accent","Theme default"))
        f.addWidget(self.accent)
        self.aero=self._check(f,"","aero_enabled")
        self.large=self._check(f,"","large_toolbar")
        self.show_icons=self._check(f,"","show_toolbar_text")
        self.compact=self._check(f,"","compact_toolbar",False)
        self.animations=self._check(f,"","animations")
        self.theme.currentTextChanged.connect(self._preview_style)
        self.appearance_mode.currentIndexChanged.connect(self._preview_style)
        l.addStretch()
        self.stack.addWidget(w)
    def _build_eye(self):
        w,l=self._page(); f=self._card(l,'Eye Comfort','Optional controls for visual comfort.'); self.blue=self._check(f,'','blue_filter',False); self.blue_label_title=QLabel(); f.addWidget(self.blue_label_title); row=QHBoxLayout(); self.blue_strength=QSlider(Qt.Horizontal); self.blue_strength.setRange(0,100); self.blue_strength.setValue(int(self.settings.get('blue_filter_strength',35))); self.blue_value=QLabel('35%'); row.addWidget(self.blue_strength,1); row.addWidget(self.blue_value); f.addLayout(row); self.warm=self._check(f,'','night_reading',False); self.reduce_motion=self._check(f,'','reduce_motion',False); self.contrast_label_title=QLabel(); f.addWidget(self.contrast_label_title); row=QHBoxLayout(); self.contrast=QSlider(Qt.Horizontal); self.contrast.setRange(80,120); self.contrast.setValue(int(self.settings.get('ui_contrast',100))); self.contrast_value=QLabel('100%'); row.addWidget(self.contrast,1); row.addWidget(self.contrast_value); f.addLayout(row); self.blue_strength.valueChanged.connect(lambda v:self.blue_value.setText(f'{v}%')); self.contrast.valueChanged.connect(lambda v:self.contrast_value.setText(f'{v}%')); l.addStretch(); self.stack.addWidget(w)
    def _build_document(self):
        w,l=self._page(); f=self._card(l,'Reading'); form=QFormLayout(); self.fit=QComboBox(); self.fit.addItems(['Fit Width','Fit Page','100%']); self.fit.setCurrentText(self.settings.get('fit_mode','Fit Width')); form.addRow('',self.fit); self.rotation=QComboBox(); self.rotation.addItems(['0°','90°','180°','270°']); self.rotation.setCurrentText(self.settings.get('rotation','0°')); form.addRow('',self.rotation); row=QHBoxLayout(); self.zoom_step=QSlider(Qt.Horizontal); self.zoom_step.setRange(5,50); self.zoom_step.setValue(int(self.settings.get('zoom_step',25))); self.zoom_value=QLabel('25%'); row.addWidget(self.zoom_step,1); row.addWidget(self.zoom_value); form.addRow('',row); self.zoom_step.valueChanged.connect(lambda v:self.zoom_value.setText(f'{v}%')); f.addLayout(form); self.auto_fit=self._check(f,'','auto_fit'); self.smooth_scroll=self._check(f,'','smooth_scroll'); self.page_gap=self._check(f,'','page_gap'); l.addStretch(); self.stack.addWidget(w)
    def _build_performance(self):
        w,l=self._page(); f=self._card(l,'Performance','Rendering and large-document controls.'); self.cache_pages=self._check(f,'','cache_pages'); self.smooth_render=self._check(f,'','smooth_render'); self.preload=self._check(f,'','preload_pages',False); self.gpu=self._check(f,'','gpu_acceleration'); self.low_memory=self._check(f,'','low_memory',True); self.large_files=QLabel(); self.large_files.setWordWrap(True); f.addWidget(self.large_files); l.addStretch(); self.stack.addWidget(w)
    def _build_audio(self):
        w,l=self._page(); f=self._card(l,'Audio'); self.audio_enabled=self._check(f,'','audio_enabled'); self.autoplay=self._check(f,'','autoplay'); self.volume_title=QLabel(); f.addWidget(self.volume_title); row=QHBoxLayout(); self.volume=QSlider(Qt.Horizontal); self.volume.setRange(0,100); self.volume.setValue(int(self.settings.get('volume',50))); self.volume_value=QLabel('50%'); row.addWidget(self.volume,1); row.addWidget(self.volume_value); f.addLayout(row); self.volume.valueChanged.connect(lambda v:self.volume_value.setText(f'{v}%')); l.addStretch(); self.stack.addWidget(w)
    def _build_shortcuts(self):
        w,l=self._page(); f=self._card(l,'Keyboard shortcuts'); self.shortcut_text=QLabel(); self.shortcut_text.setWordWrap(True); f.addWidget(self.shortcut_text); l.addStretch(); self.stack.addWidget(w)
    def _build_about(self):
        w,l=self._page()
        f=self._card(l,'About','Application information and project credits.')
        self.about_version=QLabel()
        self.about_version.setTextInteractionFlags(Qt.TextSelectableByMouse)
        f.addWidget(self.about_version)
        self.about_credit=QLabel(self.resources.about_attribution)
        self.about_credit.setWordWrap(True)
        self.about_credit.setTextInteractionFlags(Qt.TextSelectableByMouse)
        f.addWidget(self.about_credit)
        self.about_repo=QLabel()
        self.about_repo.setOpenExternalLinks(True)
        f.addWidget(self.about_repo)
        self.about_license=QLabel()
        f.addWidget(self.about_license)
        self.about_copy_version=QPushButton()
        self.about_copy_version.clicked.connect(lambda: QApplication.clipboard().setText(self.resources.app_version))
        f.addWidget(self.about_copy_version)
        l.addStretch()
        self.stack.addWidget(w)
    def _retranslate(self):
        self.t=self.resources.settings_i18n.get(self.lang,self.resources.settings_i18n['en']); self.title.setText(self.t['title']); self.subtitle.setText(self.t['subtitle']); self.live_chip.setText(self.t.get('live','● Live preview')); self.nav.clear(); self.nav.addItems([self.t['overview'],self.t['appearance'],self.t['eye'],self.t['document'],self.t['performance'],self.t['audio'],self.t['shortcuts'],self.t['about']]);
        _cards={
            'en':['General','Workspace','Theme Studio','Eye Comfort','Reading','Performance','Audio','Keyboard shortcuts'],
            'fa':['عمومی','محیط کار','استودیو تم','راحتی چشم','مطالعه','عملکرد','صدا','میانبرهای صفحه‌کلید'],
            'de':['Allgemein','Arbeitsbereich','Theme Studio','Augenkomfort','Lesen','Leistung','Audio','Tastenkürzel'],
            'es':['General','Espacio de trabajo','Estudio de temas','Comodidad visual','Lectura','Rendimiento','Audio','Atajos'],
            'fr':['Général','Espace de travail','Studio des thèmes','Confort visuel','Lecture','Performances','Audio','Raccourcis'],
            'da':['Generelt','Arbejdsområde','Temaer','Øjenkomfort','Læsning','Ydeevne','Lyd','Genveje'],
            'no':['Generelt','Arbeidsområde','Temaer','Øyekomfort','Lesing','Ytelse','Lyd','Snarveier'],
            'fi':['Yleiset','Työtila','Teemat','Silmämukavuus','Lukeminen','Suorituskyky','Ääni','Pikanäppäimet'],
            'sv':['Allmänt','Arbetsyta','Teman','Ögonkomfort','Läsning','Prestanda','Ljud','Genvägar'],
            'el':['Γενικά','Χώρος εργασίας','Θέματα','Άνεση ματιών','Ανάγνωση','Απόδοση','Ήχος','Συντομεύσεις'],
            'ar':['عام','مساحة العمل','استوديو السمات','راحة العين','القراءة','الأداء','الصوت','الاختصارات']}
        _about_titles={'en':'About','fa':'درباره','de':'Über','es':'Acerca de','fr':'À propos','da':'Om','no':'Om','fi':'Tietoja','sv':'Om','el':'Πληροφορίες','ar':'حول'}
        for _code,_label in _about_titles.items():
            if _code in _cards: _cards[_code].append(_label)
        _ct=_cards.get(self.lang,_cards['en'])
        for _lab,_txt in zip(self.card_titles,_ct):
            if _lab is not None: _lab.setText(_txt); _lab.setVisible(True)
        self.language_label.setText(self.t.get('language','Interface language')); self._set_texts();
        _appearance_options={'en':('Light','Dark'),'fa':('روشن','تیره'),'de':('Hell','Dunkel'),'es':('Claro','Oscuro'),'fr':('Clair','Sombre'),'da':('Lys','Mørk'),'no':('Lys','Mørk'),'fi':('Vaalea','Tumma'),'sv':('Ljust','Mörkt'),'el':('Φωτεινό','Σκούρο'),'ar':('فاتح','داكن')}.get(self.lang,('Light','Dark'))
        self.appearance_mode.setItemText(0,_appearance_options[0]); self.appearance_mode.setItemText(1,_appearance_options[1]); self.about_version.setText(f"{self.t.get('version','Version')} {self.resources.app_version}"); self.about_credit.setText(self.resources.about_attribution); self.about_repo.setText(f"<a href='https://github.com/Parin-M/Parin-PDF-Viewer'>{self.t.get('repository','GitHub repository')}</a>"); self.about_license.setText(f"{self.t.get('license','License')}: GPL-3.0"); self.about_copy_version.setText(self.t.get('copy_version','Copy version')); self.reset_btn.setText(self.t['reset']); self.buttons.button(QDialogButtonBox.Cancel).setText(self.t['cancel']); self.buttons.button(QDialogButtonBox.Apply).setText(self.t['apply']); self.buttons.button(QDialogButtonBox.Ok).setText(self.t['ok']); codes=['en','fa','da','de','es','no','fi','sv','fr','el','ar']; self.lang_combo.blockSignals(True); self.lang_combo.setCurrentIndex(codes.index(self.lang)); self.lang_combo.blockSignals(False); self.nav.setCurrentRow(min(self.nav.currentRow(),7)); self._preview_style()
    def _set_texts(self):
        t=self.t; self.remember_last.setText(t['remember']); self.restore_zoom.setText(t['restore']); self.single_page.setText(t.get('single','Single-page reading mode')); self.confirm_close.setText(t['confirm']); self.status.setText(t['status']); self.center_page.setText(t['center']); self.page_shadow.setText(t['shadow']); self.appearance_label.setText(t.get('appearance_mode','Appearance mode')); self.theme_label.setText(t['theme']); self.accent_label.setText(t['accent']); self.aero.setText(t['aero']); self.large.setText(t['large']); self.show_icons.setText(t['toolbar']); self.compact.setText(t['compact']); self.animations.setText(t['animations']); self.theme_preview.setText(t.get('theme_preview','Material You Light • Live preview')); self.blue.setText(t['blue']); self.blue_label_title.setText(t['blue_strength']); self.warm.setText(t['night']); self.reduce_motion.setText(t['reduce']); self.contrast_label_title.setText(t['contrast']); self.fit.setItemText(0,t.get('fit_width','Fit Width')); self.fit.setItemText(1,t.get('fit_page','Fit Page')); self.fit.setItemText(2,t.get('fit_100','100%')); self.auto_fit.setText(t['autofit']); self.smooth_scroll.setText(t['scroll']); self.page_gap.setText(t['gap']); self.cache_pages.setText(t['cache']); self.smooth_render.setText(t.get('quality_render','High-quality rendering')); self.preload.setText(t['preload']); self.gpu.setText(t['gpu']); self.low_memory.setText(t['memory']); self.large_files.setText(t.get('large_files','Large PDF mode: pages are rendered on demand; the whole document is never loaded into RAM.')); self.audio_enabled.setText(t['audio_enabled']); self.autoplay.setText(t['autoplay']); self.volume_title.setText(t['volume']); self.shortcut_text.setText(t['shortcuts_desc']+'\n\nCtrl+O  '+t.get('open','Open')+'\nCtrl+S  '+t.get('save','Save')+'\nCtrl+F  '+t.get('search','Search')+'\nCtrl+0  '+t.get('reset_zoom','Reset zoom')+'\nF11  '+t.get('fullscreen','Fullscreen'))
    def _language_from_settings(self,index):
        codes=['en','fa','da','de','es','no','fi','sv','fr','el','ar']; code=codes[index]
        if code!=self.lang: self.lang=code; self.viewer.apply_language(code); self._retranslate()
    def _preview_style(self,*_args):
        self.settings["theme"] = self.theme.currentText()
        self.settings["appearance_mode"] = self.appearance_mode.currentData() or "light"
        self._apply_dialog_style()
        mode_label = "Dark" if self.settings["appearance_mode"] == "dark" else "Light"
        self.theme_preview.setText(f"{self.theme.currentText()}  •  {mode_label} appearance  •  {self.t.get('live','Live preview')}")

    def _apply_dialog_style(self):
        theme=self.settings.get("theme","Arctic Glass")
        dark=str(self.settings.get("appearance_mode","light")).lower()=="dark"
        accent=self.resources.theme_accents.get(theme,(58,141,255)); ah="#%02X%02X%02X"%accent
        panel="#172235" if dark else "#FFFFFF"
        surface="#111827" if dark else "#F7F9FC"
        text="#E5EDF7" if dark else "#172B49"
        muted="#A8B7CA" if dark else "#66778E"
        border="#30425A" if dark else "#D9E3EF"
        selected="#244361" if dark else ah
        self.setStyleSheet(self.resources.theme_stylesheet(theme,"dark" if dark else "light")+f'''
QDialog{{background:{surface};color:{text};}}
QFrame#settingsHeader{{background:{panel};border:1px solid {border};border-radius:20px;}}
QLabel#settingsTitle{{font-size:24px;font-weight:800;color:{text};}}
QLabel#settingsSubtitle{{font-size:13px;color:{muted};}}
QLabel#settingsChip{{background:{selected};color:#FFFFFF;border-radius:14px;padding:8px 12px;font-weight:700;}}
QListWidget#settingsNav{{background:{panel};border:1px solid {border};border-radius:16px;padding:8px;outline:0;}}
QListWidget#settingsNav::item{{padding:13px 12px;border-radius:10px;margin:3px;color:{text};font-weight:600;}}
QListWidget#settingsNav::item:selected{{background:{selected};color:#FFFFFF;}}
QStackedWidget{{background:transparent;border:none;}}
QWidget#settingsPage{{background:transparent;}}
QScrollArea#settingsPageScroll{{background:transparent;border:none;}}
QWidget#settingsPageContent{{background:transparent;}}
QFrame#settingsCard{{background:{panel};border:1px solid {border};border-radius:16px;min-height:92px;padding:0;}}
QLabel#settingsCardTitle{{font-size:17px;font-weight:800;color:{text};background:transparent;padding:0;min-height:30px;}}
QLabel#settingsCardSubtitle{{font-size:12px;color:{muted};background:transparent;min-height:20px;}}
QScrollArea#settingsPageScroll > QWidget > QWidget{{background:transparent;}}
QLabel{{color:{text};}}
QCheckBox{{font-size:13px;color:{text};background:transparent;}}
QComboBox,QLineEdit,QSpinBox{{font-size:13px;min-height:40px;}}
QFormLayout QLabel{{color:{text};}}
''')

    def _fade_in(self):
        self.effect=QGraphicsOpacityEffect(self); self.setGraphicsEffect(self.effect); self.anim=QPropertyAnimation(self.effect,b'opacity',self); self.anim.setDuration(240); self.anim.setStartValue(0.0); self.anim.setEndValue(1.0); self.anim.setEasingCurve(QEasingCurve.OutCubic); self.anim.start()
    def _switch_page(self,index):
        self.stack.setCurrentIndex(index)
        if self.settings.get('animations',True) and not self.settings.get('reduce_motion',False):
            w=self.stack.currentWidget(); eff=QGraphicsOpacityEffect(w); w.setGraphicsEffect(eff); a=QPropertyAnimation(eff,b'opacity',w); a.setDuration(180); a.setStartValue(.35); a.setEndValue(1.0); a.setEasingCurve(QEasingCurve.OutCubic); w._page_anim=a; a.start()
    def collect(self):
        return {'remember_last':self.remember_last.isChecked(),'restore_zoom':self.restore_zoom.isChecked(),'single_page':self.single_page.isChecked(),'confirm_close':self.confirm_close.isChecked(),'cache_pages':self.cache_pages.isChecked(),'smooth_render':self.smooth_render.isChecked(),'theme':self.theme.currentText(),'accent':self.accent.currentText(),'aero_enabled':self.aero.isChecked(),'compact_toolbar':self.compact.isChecked(),'status_bar':self.status.isChecked(),'page_shadow':self.page_shadow.isChecked(),'fit_mode':self.fit.currentText(),'zoom_step':self.zoom_step.value(),'rotation':self.rotation.currentText(),'auto_fit':self.auto_fit.isChecked(),'center_page':self.center_page.isChecked(),'audio_enabled':self.audio_enabled.isChecked(),'autoplay':self.autoplay.isChecked(),'volume':self.volume.value(),'large_toolbar':self.large.isChecked(),'show_toolbar_text':self.show_icons.isChecked(),'preload_pages':self.preload.isChecked(),'blue_filter':self.blue.isChecked(),'blue_filter_strength':self.blue_strength.value(),'night_reading':self.warm.isChecked(),'reduce_motion':self.reduce_motion.isChecked(),'ui_contrast':self.contrast.value(),'smooth_scroll':self.smooth_scroll.isChecked(),'page_gap':self.page_gap.isChecked(),'gpu_acceleration':self.gpu.isChecked(),'low_memory':self.low_memory.isChecked(),'animations':self.animations.isChecked(),'appearance_mode':self.appearance_mode.currentData() or 'light'}
    def reset_defaults(self):
        defaults = {
            "remember_last": True, "restore_zoom": True, "single_page": True,
            "confirm_close": True, "status_bar": True, "center_page": True,
            "page_shadow": True, "appearance_mode": "light", "theme": "Arctic Glass",
            "accent": "Theme default", "aero_enabled": True, "large_toolbar": True,
            "show_toolbar_text": True, "compact_toolbar": False, "animations": True,
            "blue_filter": False, "blue_filter_strength": 35, "night_reading": False,
            "reduce_motion": False, "ui_contrast": 100, "fit_mode": "Fit Width",
            "rotation": "0°", "zoom_step": 25, "auto_fit": True, "smooth_scroll": True,
            "page_gap": True, "cache_pages": True, "smooth_render": True,
            "preload_pages": True, "gpu_acceleration": True, "low_memory": False,
            "audio_enabled": True, "autoplay": False, "volume": 50, "smart_ink": True,
        }
        self.settings.clear()
        self.settings.update(defaults)

        checkboxes = {
            "remember_last": self.remember_last, "restore_zoom": self.restore_zoom,
            "single_page": self.single_page, "confirm_close": self.confirm_close,
            "status_bar": self.status, "center_page": self.center_page,
            "page_shadow": self.page_shadow, "aero_enabled": self.aero,
            "large_toolbar": self.large, "show_toolbar_text": self.show_icons,
            "compact_toolbar": self.compact, "animations": self.animations,
            "blue_filter": self.blue, "night_reading": self.warm,
            "reduce_motion": self.reduce_motion, "auto_fit": self.auto_fit,
            "smooth_scroll": self.smooth_scroll, "page_gap": self.page_gap,
            "cache_pages": self.cache_pages, "smooth_render": self.smooth_render,
            "preload_pages": self.preload, "gpu_acceleration": self.gpu,
            "low_memory": self.low_memory, "audio_enabled": self.audio_enabled,
            "autoplay": self.autoplay,
        }
        for key, widget in checkboxes.items():
            widget.setChecked(defaults[key])

        self.appearance_mode.setCurrentIndex(0)
        self.theme.setCurrentText(defaults["theme"])
        self.accent.setCurrentText(defaults["accent"])
        self.fit.setCurrentText(defaults["fit_mode"])
        self.rotation.setCurrentText(defaults["rotation"])
        self.zoom_step.setValue(defaults["zoom_step"])
        self.blue_strength.setValue(defaults["blue_filter_strength"])
        self.contrast.setValue(defaults["ui_contrast"])
        self.volume.setValue(defaults["volume"])
        self._preview_style()

    def apply_changes(self):
        self.settings.update(self.collect()); self.viewer.app_settings.update(self.settings); self.viewer.apply_app_settings(); self.settings_changed.emit(self.settings)
    def accept(self): self.apply_changes(); super().accept()
