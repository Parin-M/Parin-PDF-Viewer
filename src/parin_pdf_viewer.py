#!/usr/bin/env python3
import sys
import re
import pymupdf as fitz  # PyMuPDF (modern API; avoids deprecated fitz import)
from PySide6.QtCore import Qt, QUrl, QPointF, QTimer, QSettings, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QLineEdit, QScrollArea, 
    QInputDialog, QMessageBox, QMenu, QColorDialog, QSpinBox, QDialog, QCheckBox,
    QComboBox, QSlider, QTabWidget, QFormLayout, QGroupBox, QDialogButtonBox,
    QRadioButton, QButtonGroup, QListWidget, QStackedWidget, QFrame, QToolButton, QSizePolicy, QStyle, QGraphicsOpacityEffect
)
from PySide6.QtGui import QImage, QPixmap, QAction, QColor, QPainter, QMouseEvent, QIcon, QFont, QLinearGradient
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

# Text helper must be defined before translation tables are normalized.
EMOJI_RE = re.compile(r'[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF]')
def clean_label(value):
    if not isinstance(value, str):
        return value
    return re.sub(r'\s{2,}', ' ', EMOJI_RE.sub('', value)).strip()

TRANSLATIONS = {
    'fa': {'title': 'پرین | Parin v8.7', 'open': '📂 باز کردن', 'save': '💾 ذخیره', 'pen': '✏️ قلم', 'highlight': '🖍️ هایلایت', 'eraser': '🧹 پاک\u200cکن', 'add_text': '✍️ متن', 'color': '🎨 رنگ', 'theme': '🎨 تم', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ عرض', 'fit_page': '⤢ صفحه', 'prev': 'صفحه قبل ⬅️', 'next': '➡️ صفحه بعد', 'print_opt': '🖨️ چاپ', 'pass_remove': '🔓 حذف رمز', 'pass_add': '🔒 گذاشتن رمز', 'lofi': '🎵 موسیقی آرامش\u200cبخش', 'lang': '🌐 زبان', 'search': 'Search جستجو', 'rotate_left': '↶ چرخش', 'rotate_right': '↷ چرخش', 'fullscreen': '⛶ تمام\u200cصفحه', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'صفحه:', 'of': 'از', 'enter_pass': 'لطفاً رمز عبور فایل را وارد کنید:', 'set_pass': 'رمز عبور جدید برای فایل تعیین کنید:', 'enter_text': 'متن مورد نظر را وارد کنید:', 'find_text': 'عبارت جستجو در PDF:', 'not_found': 'عبارت موردنظر پیدا نشد.', 'saved': 'فایل با موفقیت ذخیره شد.', 'opened': 'File opened.', 'wrong_pass': 'رمز عبور اشتباه است!', 'choose_file': 'Choose file', 'unlock_name': 'ذخیره بدون رمز', 'protected_name': 'ذخیره فایل رمزگذاری\u200cشده', 'unlocked': 'رمز فایل برداشته شد.', 'protected': 'رمز عبور با موفقیت اعمال شد.', 'color_pick': 'انتخاب رنگ', 'music_stop': '⏸️ توقف موسیقی', 'dir': Qt.RightToLeft},
    'en': {'title': 'Parin v8.7', 'open': '📂 Open', 'save': '💾 Save', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Theme', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Fit Width', 'fit_page': '⤢ Fit Page', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Language', 'search': 'Search Search', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Fullscreen', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Page:', 'of': 'of', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'da': {'title': 'Parin v8.7', 'open': '📂 Åbn', 'save': '💾 Gem', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Tema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Tilpas bredde', 'fit_page': '⤢ Tilpas side', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Sprog', 'search': 'Search Søg', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Fuldskærm', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Side:', 'of': 'af', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'de': {'title': 'Parin v8.7', 'open': '📂 Öffnen', 'save': '💾 Speichern', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Thema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Seitenbreite', 'fit_page': '⤢ Seite anpassen', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Sprache', 'search': 'Search Suchen', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Vollbild', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Seite:', 'of': 'von', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'es': {'title': 'Parin v8.7', 'open': '📂 Abrir', 'save': '💾 Guardar', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Tema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Ajustar ancho', 'fit_page': '⤢ Ajustar página', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Idioma', 'search': 'Search Buscar', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Pantalla completa', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Página:', 'of': 'de', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'no': {'title': 'Parin v8.7', 'open': '📂 Åpne', 'save': '💾 Lagre', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Tema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Tilpass bredde', 'fit_page': '⤢ Tilpass side', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Språk', 'search': 'Search Søk', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Fullskjerm', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Side:', 'of': 'av', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'fi': {'title': 'Parin v8.7', 'open': '📂 Avaa', 'save': '💾 Tallenna', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Teema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Sovita leveyteen', 'fit_page': '⤢ Sovita sivulle', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Kieli', 'search': 'Search Hae', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Koko näyttö', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Sivu:', 'of': '/', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'sv': {'title': 'Parin v8.7', 'open': '📂 Öppna', 'save': '💾 Spara', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Tema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Anpassa bredd', 'fit_page': '⤢ Anpassa sida', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Språk', 'search': 'Search Sök', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Helskärm', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Sida:', 'of': 'av', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'fr': {'title': 'Parin v8.7', 'open': '📂 Ouvrir', 'save': '💾 Enregistrer', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Thème', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Ajuster largeur', 'fit_page': '⤢ Ajuster page', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Langue', 'search': 'Search Rechercher', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Plein écran', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Page :', 'of': 'sur', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'el': {'title': 'Parin v8.7', 'open': '📂 Άνοιγμα', 'save': '💾 Αποθήκευση', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Θέμα', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Προσαρμογή πλάτους', 'fit_page': '⤢ Προσαρμογή σελίδας', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Γλώσσα', 'search': 'Search Αναζήτηση', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Πλήρης οθόνη', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Σελίδα:', 'of': 'από', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'ar': {'title': 'Parin v8.7', 'open': '📂 فتح', 'save': '💾 حفظ', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 السمة', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ ملاءمة العرض', 'fit_page': '⤢ ملاءمة الصفحة', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 اللغة', 'search': 'Search بحث', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ ملء الشاشة', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'صفحة:', 'of': 'من', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.RightToLeft},
}

# Final UI text normalization: feature labels use icons, not emoji.
for _lang, _items in TRANSLATIONS.items():
    for _key, _value in list(_items.items()):
        if isinstance(_value, str): _items[_key] = clean_label(_value)

LOFI_STREAM_URL = "https://stream.zeno.fm/f3wvbbqmdg8uv"

THEME_DEFINITIONS = [
    ('Arctic Glass', 'Arctic', '#3A8DFF', '#EAF4FF', '#F8FBFF'),
    ('Ocean Mist', 'Ocean', '#1597D4', '#E9F8FF', '#F7FCFF'),
    ('Lavender Bloom', 'Lavender', '#8066D8', '#F2EDFF', '#FBF9FF'),
    ('Sakura', 'Sakura', '#E86A9A', '#FFF0F6', '#FFF9FC'),
    ('Peach', 'Peach', '#E77B5D', '#FFF1EA', '#FFFAF7'),
    ('Mint', 'Mint', '#29A889', '#E8FBF4', '#F8FFFC'),
    ('Forest', 'Forest', '#3E9360', '#EAF7EE', '#FAFFFB'),
    ('Lemon', 'Lemon', '#D6A900', '#FFF8D9', '#FFFEF6'),
    ('Coral', 'Coral', '#E56757', '#FFF0ED', '#FFF9F7'),
    ('Orchid', 'Orchid', '#9A5BC7', '#F6ECFF', '#FCF9FF'),
    ('Sky', 'Sky', '#4C9FEA', '#EAF5FF', '#F9FCFF'),
    ('Ice', 'Ice', '#4FAEC1', '#EAFBFF', '#F9FEFF'),
    ('Rose', 'Rose', '#D95D82', '#FFEAF1', '#FFF9FB'),
    ('Sage', 'Sage', '#769B73', '#F0F6ED', '#FCFFFA'),
    ('Berry', 'Berry', '#665CC8', '#F0EEFF', '#FBFAFF'),
    ('Mocha', 'Mocha', '#9A6A52', '#F8EFE9', '#FFFCFA'),
    ('Tropical', 'Tropical', '#159E83', '#E7FBF5', '#F9FFFD'),
    ('Azure', 'Azure', '#356FD8', '#EAF1FF', '#F9FBFF'),
    ('Plum', 'Plum', '#784C9D', '#F2EBF8', '#FCFAFF'),
    ('Tulip', 'Tulip', '#C85C8E', '#FFF0F6', '#FFFAFD'),
]

def _build_light_theme(accent, soft, surface):
    return f'''QMainWindow,QWidget{{background:{surface};color:#1B1B1F;}}
QScrollArea{{background:transparent;border:none;}}
QLabel{{color:#1B1B1F;}}
QPushButton{{background:rgba(255,255,255,.82);color:#25252A;border:1px solid #D8D8DE;border-radius:14px;padding:9px 14px;font-weight:700;}}
QPushButton:hover{{background:{soft};border-color:{accent};}}
QPushButton:pressed,QPushButton:checked{{background:{soft};border:2px solid {accent};color:#1A1A1F;}}
QSpinBox,QLineEdit,QComboBox{{background:#FFFFFF;color:#1B1B1F;border:1px solid #CFCFD6;border-radius:12px;padding:8px 10px;selection-background-color:{accent};selection-color:white;}}
QLineEdit:focus,QComboBox:focus,QSpinBox:focus{{border:2px solid {accent};}}
QMenu{{background:#FFFFFF;color:#1B1B1F;border:1px solid #D5D5DC;border-radius:14px;padding:6px;}}
QMenu::item{{padding:9px 16px;border-radius:9px;}}
QMenu::item:selected{{background:{soft};color:#17171B;}}
QCheckBox{{color:#25252A;spacing:9px;padding:7px;}}
QCheckBox::indicator{{width:20px;height:20px;border-radius:10px;border:2px solid #8A8A93;background:#FFFFFF;}}
QCheckBox::indicator:checked{{background:{accent};border-color:{accent};}}
QGroupBox{{border:1px solid #DADAE0;border-radius:16px;margin-top:14px;padding-top:12px;background:rgba(255,255,255,.65);}}
QGroupBox::title{{subcontrol-origin:margin;left:14px;padding:0 6px;color:#4B4B54;font-weight:800;}}
QSlider::groove:horizontal{{height:6px;background:#DFDFE5;border-radius:3px;}}
QSlider::handle:horizontal{{width:20px;height:20px;margin:-7px 0;border-radius:10px;background:{accent};border:3px solid white;}}
QScrollBar:vertical{{width:10px;background:transparent;margin:4px;}}
QScrollBar::handle:vertical{{background:#C8C8D0;border-radius:5px;min-height:30px;}}'''

COLOR_THEMES = {name: _build_light_theme(accent, soft, surface) for name, _, accent, soft, surface in THEME_DEFINITIONS}
THEME_ACCENTS = {name: tuple(int(accent[i:i+2],16) for i in (1,3,5)) for name,_,accent,_,_ in THEME_DEFINITIONS}


ICON_GLYPHS={'Open':'▱','Save':'↓','Print':'▤','Pen':'✎','Highlight':'✦','Eraser':'⌫','Text':'T','Color':'●','Fit':'□','Prev':'‹','Next':'›','Rotate':'⟳','Fullscreen':'⛶','Lo-Fi':'♫','Settings':'⚙','Language':'文','More':'⋯'}
def make_action_icon(symbol,size=20,accent=(80,180,255)):
    pm=QPixmap(size,size); pm.fill(Qt.transparent); painter=QPainter(pm); painter.setRenderHint(QPainter.Antialiasing)
    grad=QLinearGradient(0,0,size,size); grad.setColorAt(0,QColor(*accent)); grad.setColorAt(1,QColor(142,76,255)); painter.setBrush(grad); painter.setPen(Qt.NoPen); painter.drawEllipse(1,1,size-2,size-2)
    painter.setPen(QColor(255,255,255,235)); painter.setFont(QFont('DejaVu Sans',max(8,int(size*.52)),QFont.Bold)); painter.drawText(pm.rect(),Qt.AlignCenter,symbol); painter.end(); return QIcon(pm)


class PDFPageLabel(QLabel):
    def __init__(self, viewer_instance):
        super().__init__()
        self.viewer = viewer_instance
        self.setAlignment(Qt.AlignCenter)
        self.current_stroke = []
        self.setMouseTracking(True)

    def mousePressEvent(self, event: QMouseEvent):
        if not self.viewer.doc or not self.viewer.active_tool or event.button() != Qt.LeftButton: 
            return
        
        pdf_pt = self.viewer.get_pdf_coords(event.position())
        page = self.viewer.doc.load_page(self.viewer.current_page)

        if self.viewer.active_tool in ['pen', 'highlight']:
            self.current_stroke = [(pdf_pt.x, pdf_pt.y)]
            self.viewer.is_drawing = True

        elif self.viewer.active_tool == 'eraser':
            self.viewer.erase_at_point(page, pdf_pt)

        elif self.viewer.active_tool == 'text':
            t = TRANSLATIONS[self.viewer.current_lang]
            text, ok = QInputDialog.getText(self, t["add_text"], t["enter_text"])
            if ok and text:
                r, g, b = self.viewer.selected_color.redF(), self.viewer.selected_color.greenF(), self.viewer.selected_color.blueF()
                annot = page.add_freetext_annot(fitz.Rect(pdf_pt.x, pdf_pt.y, pdf_pt.x + 200, pdf_pt.y + 30), text, fontsize=12, text_color=(r, g, b))
                annot.update()
                self.viewer.render_page()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.viewer.doc or not self.viewer.active_tool: 
            return
        
        pdf_pt = self.viewer.get_pdf_coords(event.position())
        page = self.viewer.doc.load_page(self.viewer.current_page)

        if self.viewer.active_tool in ['pen', 'highlight'] and self.viewer.is_drawing:
            self.current_stroke.append((pdf_pt.x, pdf_pt.y))

        elif self.viewer.active_tool == 'eraser' and (event.buttons() & Qt.LeftButton):
            self.viewer.erase_at_point(page, pdf_pt)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.viewer.is_drawing and len(self.current_stroke) > 1 and self.viewer.doc:
            page = self.viewer.doc.load_page(self.viewer.current_page)
            r, g, b = self.viewer.selected_color.redF(), self.viewer.selected_color.greenF(), self.viewer.selected_color.blueF()

            annot = page.add_ink_annot([self.current_stroke])
            annot.set_colors(stroke=(r, g, b))
            
            if self.viewer.active_tool == 'pen':
                annot.set_border(width=2)
            elif self.viewer.active_tool == 'highlight':
                annot.set_border(width=14)
                annot.set_opacity(0.35)

            annot.update()
            self.viewer.render_page()

        self.viewer.is_drawing = False
        self.current_stroke = []


def make_app_icon(size=64):
    """Create a crisp, vector-like Parin icon without external image dependencies."""
    from PySide6.QtGui import QImage, QPainter, QBrush, QPen
    from PySide6.QtCore import QRectF
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img); p.setRenderHint(QPainter.Antialiasing)
    # layered rounded tiles
    p.setBrush(QColor("#6D4AFF")); p.setPen(Qt.NoPen); p.drawRoundedRect(QRectF(6, 8, size-12, size-12), 15, 15)
    p.setBrush(QColor("#21C7FF")); p.drawRoundedRect(QRectF(11, 3, size-28, size-30), 11, 11)
    p.setBrush(QColor("#9B5CFF")); p.drawRoundedRect(QRectF(16, 14, size-24, size-19), 13, 13)
    # stylized P
    p.setPen(QPen(Qt.white, max(3, size//10), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawLine(size*.34, size*.72, size*.34, size*.30)
    p.drawArc(QRectF(size*.34, size*.27, size*.38, size*.27), 90*16, -180*16)
    p.drawLine(size*.35, size*.54, size*.60, size*.54)
    p.end()
    return QIcon(QPixmap.fromImage(img))


def card_frame(title, subtitle=""):
    frame = QFrame()
    frame.setObjectName("settingsCard")
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    frame.setMinimumHeight(92)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(10)
    h = QLabel(str(title))
    h.setObjectName("settingsCardTitle")
    h.setTextFormat(Qt.PlainText)
    h.setStyleSheet("color:#172233; background:transparent;")
    h.setVisible(True)
    h.setMinimumHeight(30)
    h.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    lay.addWidget(h)
    if subtitle:
        sub = QLabel(str(subtitle))
        sub.setObjectName("settingsCardSubtitle")
        sub.setTextFormat(Qt.PlainText)
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#69778A; background:transparent;")
        sub.setVisible(True)
        sub.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        lay.addWidget(sub)
    return frame, lay

SETTINGS_I18N = {
'en': {'title':'Parin — Advanced Settings','subtitle':'Customize appearance, reading, performance, audio and accessibility','overview':'✨ Overview','appearance':'🎨 Appearance & Themes','eye':'👁️ Eye Comfort','document':'📄 Reading & PDF','performance':'⚡ Performance','audio':'🎵 Audio & Lo-Fi','shortcuts':'⌨️ Shortcuts','reset':'↺ Reset','cancel':'Cancel','apply':'Apply','ok':'OK','theme':'Color theme','theme_sub':'20 bright themes — Parin does not use dark mode','aero':'Aero glass interface','large':'Larger toolbar controls','toolbar':'Show icon + full label','compact':'Compact toolbar','animations':'Smooth UI animations','blue':'Blue-light filter','blue_strength':'Filter strength','night':'Warm reading mode','reduce':'Reduce motion','contrast':'Visual contrast','remember':'Remember last file and page','restore':'Restore previous zoom and view','single':'Single-page reading mode','confirm':'Confirm before closing with unsaved changes','status':'Show status bar','center':'Smart page centering','shadow':'Soft PDF page shadow','fit':'Default view','rotation':'Initial rotation','zoom':'Zoom step','autofit':'Auto-fit on resize','scroll':'Smooth scrolling','gap':'Extra page spacing','cache':'Cache rendered pages','preload':'Preload nearby pages','gpu':'GPU-friendly UI optimization','memory':'Low-memory mode','audio_enabled':'Enable music controls','autoplay':'Autoplay Lo-Fi','volume':'Volume','shortcuts_desc':'Keyboard shortcuts','accent':'Accent color','quality':'Visual quality'},
'fa': {'title':'پرین — تنظیمات پیشرفته','subtitle':'شخصی‌سازی ظاهر، مطالعه، عملکرد، صدا و دسترسی‌پذیری','overview':'✨ نمای کلی','appearance':'🎨 ظاهر و تم‌ها','eye':'👁️ راحتی چشم','document':'📄 مطالعه و PDF','performance':'⚡ عملکرد','audio':'🎵 صدا و Lo-Fi','shortcuts':'⌨️ میانبرها','reset':'↺ بازنشانی','cancel':'لغو','apply':'اعمال','ok':'تأیید','theme':'تم رنگی','theme_sub':'۲۰ تم روشن — پرین از حالت تاریک استفاده نمی‌کند','aero':'رابط شیشه‌ای Aero','large':'کنترل‌های بزرگ‌تر نوار ابزار','toolbar':'نمایش آیکون + عنوان کامل','compact':'نوار ابزار فشرده','animations':'انیمیشن‌های نرم رابط','blue':'فیلتر نور آبی','blue_strength':'شدت فیلتر','night':'حالت مطالعه گرم','reduce':'کاهش حرکت','contrast':'کنتراست دیداری','remember':'آخرین فایل و صفحه به خاطر سپرده شود','restore':'زوم و نمای قبلی بازیابی شود','single':'حالت مطالعه تک‌صفحه‌ای','confirm':'هنگام خروج با تغییرات ذخیره‌نشده تأیید شود','status':'نمایش نوار وضعیت','center':'مرکزچین هوشمند صفحه','shadow':'سایه نرم صفحه PDF','fit':'نمای پیش‌فرض','rotation':'چرخش اولیه','zoom':'گام زوم','autofit':'فیت خودکار هنگام تغییر اندازه','scroll':'اسکرول نرم','gap':'فاصله بیشتر بین صفحات','cache':'کش صفحات رندرشده','preload':'پیش‌بارگذاری صفحات نزدیک','gpu':'بهینه‌سازی رابط برای GPU','memory':'حالت کم‌مصرف','audio_enabled':'کنترل موسیقی فعال باشد','autoplay':'پخش خودکار Lo-Fi','volume':'بلندی صدا','shortcuts_desc':'میانبرهای صفحه‌کلید','accent':'رنگ تأکیدی','quality':'کیفیت ظاهری'}
}


_SETTINGS_LOCALIZED={
'fa':{'live':'پیش‌نمایش زنده','general':'عمومی','workspace':'محیط کار','theme_studio':'استودیو تم','eye_card':'راحتی چشم','reading_card':'مطالعه','performance_card':'عملکرد','audio_card':'صدا','shortcuts_card':'میانبرهای صفحه‌کلید','language':'زبان رابط','theme_preview':'Material You روشن • پیش‌نمایش زنده','large_files':'PDFهای بزرگ صفحه‌به‌صفحه رندر می‌شوند و کل فایل وارد RAM نمی‌شود.'},
'da':{'live':'● Live forhåndsvisning','language':'Sprog','theme_preview':'Material You lys • Live forhåndsvisning','large_files':'Store PDF-filer gengives side for side og indlæses ikke helt i RAM.'},
'de':{'live':'● Live-Vorschau','language':'Sprache','theme_preview':'Material You Hell • Live-Vorschau','large_files':'Große PDFs werden seitenweise gerendert und nicht vollständig in den RAM geladen.'},
'es':{'live':'● Vista previa en vivo','language':'Idioma','theme_preview':'Material You claro • Vista previa en vivo','large_files':'Los PDF grandes se renderizan por página y no se cargan completos en RAM.'},
'no':{'live':'● Direkte forhåndsvisning','language':'Språk','theme_preview':'Material You lys • Direkte forhåndsvisning','large_files':'Store PDF-filer gjengis side for side og lastes ikke helt inn i RAM.'},
'fi':{'live':'● Live-esikatselu','language':'Kieli','theme_preview':'Material You vaalea • Live-esikatselu','large_files':'Suuret PDF:t renderöidään sivu kerrallaan eikä koko tiedostoa ladata RAM-muistiin.'},
'sv':{'live':'● Förhandsvisning live','language':'Språk','theme_preview':'Material You ljust • Live-förhandsvisning','large_files':'Stora PDF-filer renderas sida för sida och laddas inte helt till RAM.'},
'fr':{'live':'● Aperçu en direct','language':'Langue','theme_preview':'Material You clair • Aperçu en direct','large_files':'Les gros PDF sont rendus page par page et ne sont pas chargés entièrement en RAM.'},
'el':{'live':'● Ζωντανή προεπισκόπηση','language':'Γλώσσα','theme_preview':'Material You φωτεινό • Ζωντανή προεπισκόπηση','large_files':'Τα μεγάλα PDF αποδίδονται ανά σελίδα και δεν φορτώνονται ολόκληρα στη RAM.'},
'ar':{'live':'● معاينة مباشرة','language':'اللغة','theme_preview':'Material You فاتح • معاينة مباشرة','large_files':'يتم عرض ملفات PDF الكبيرة صفحةً بصفحة ولا يتم تحميل الملف كاملًا إلى RAM.'}}

SETTINGS_SECTION_LOCALES = {
 'da':('Parin — Indstillinger','Oversigt','Udseende og temaer','Øjenkomfort','Læsning og PDF','Ydeevne','Lyd og Lo-Fi','Genveje'),
 'de':('Parin — Einstellungen','Übersicht','Darstellung und Designs','Augenkomfort','Lesen und PDF','Leistung','Audio und Lo-Fi','Tastenkürzel'),
 'es':('Parin — Ajustes','Resumen','Apariencia y temas','Comodidad visual','Lectura y PDF','Rendimiento','Audio y Lo-Fi','Atajos'),
 'no':('Parin — Innstillinger','Oversikt','Utseende og temaer','Øyekomfort','Lesing og PDF','Ytelse','Lyd og Lo-Fi','Snarveier'),
 'fi':('Parin — Asetukset','Yleiskatsaus','Ulkoasu ja teemat','Silmämukavuus','Lukeminen ja PDF','Suorituskyky','Ääni ja Lo-Fi','Pikanäppäimet'),
 'sv':('Parin — Inställningar','Översikt','Utseende och teman','Ögonkomfort','Läsning och PDF','Prestanda','Ljud och Lo-Fi','Genvägar'),
 'fr':('Parin — Paramètres','Vue d’ensemble','Apparence et thèmes','Confort visuel','Lecture et PDF','Performances','Audio et Lo-Fi','Raccourcis'),
 'el':('Parin — Ρυθμίσεις','Επισκόπηση','Εμφάνιση και θέματα','Άνεση ματιών','Ανάγνωση και PDF','Απόδοση','Ήχος και Lo-Fi','Συντομεύσεις'),
 'ar':('Parin — الإعدادات','نظرة عامة','المظهر والسمات','راحة العين','القراءة وPDF','الأداء','الصوت وLo-Fi','الاختصارات'),
}
for _code, _vals in SETTINGS_SECTION_LOCALES.items():
    _d = SETTINGS_I18N.setdefault(_code, dict(SETTINGS_I18N['en']))
    _d.update({'title':_vals[0],'overview':_vals[1],'appearance':_vals[2],'eye':_vals[3],'document':_vals[4],'performance':_vals[5],'audio':_vals[6],'shortcuts':_vals[7]})

for _l,_v in _SETTINGS_LOCALIZED.items():
    SETTINGS_I18N.setdefault(_l,dict(SETTINGS_I18N['en'])); SETTINGS_I18N[_l].update(_v)

# Settings labels are plain text; icons are supplied by the UI where needed.
for _code, _items in SETTINGS_I18N.items():
    for _key, _value in list(_items.items()):
        if isinstance(_value, str):
            _items[_key] = clean_label(_value)

def soft_tone(hex_color):
    h=hex_color.lstrip('#'); r,g,b=[int(h[i:i+2],16) for i in (0,2,4)]
    return '#%02X%02X%02X'%((r+255*3)//4,(g+255*3)//4,(b+255*3)//4)

class SettingsDialog(QDialog):
    settings_changed=Signal(dict)
    def __init__(self,viewer):
        super().__init__(viewer); self.viewer=viewer; self.settings=viewer.app_settings.copy(); self.lang=viewer.current_lang if viewer.current_lang in SETTINGS_I18N else 'en'; self.setMinimumSize(980,680); self.resize(1120,780); self.setModal(True); self._build_ui(); self._retranslate(); self._fade_in()
    def _build_ui(self):
        root=QVBoxLayout(self); root.setContentsMargins(18,18,18,18); root.setSpacing(14)
        header=QFrame(); header.setObjectName('settingsHeader'); hl=QHBoxLayout(header); hl.setContentsMargins(20,16,20,16); ic=QLabel(); ic.setPixmap(make_app_icon(58).pixmap(58,58)); hl.addWidget(ic); tb=QVBoxLayout(); self.title=QLabel(); self.title.setObjectName('settingsTitle'); self.subtitle=QLabel(); self.subtitle.setObjectName('settingsSubtitle'); self.subtitle.setWordWrap(True); tb.addWidget(self.title); tb.addWidget(self.subtitle); hl.addLayout(tb,1); self.live_chip=QLabel(); self.live_chip.setObjectName('settingsChip'); hl.addWidget(self.live_chip); root.addWidget(header)
        body=QHBoxLayout(); body.setSpacing(14); self.nav=QListWidget(); self.nav.setObjectName('settingsNav'); self.nav.setFixedWidth(255); body.addWidget(self.nav); self.stack=QStackedWidget(); body.addWidget(self.stack,1); root.addLayout(body,1)
        self.card_titles=[]; self._build_overview(); self._build_appearance(); self._build_eye(); self._build_document(); self._build_performance(); self._build_audio(); self._build_shortcuts(); self.nav.currentRowChanged.connect(self._switch_page)
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
        f,fl=card_frame(title,sub); lay.addWidget(f); self.card_titles.append(f.findChild(QLabel,'settingsCardTitle')); return fl
    def _check(self,lay,text,key,default=True):
        c=QCheckBox(text); c.setChecked(bool(self.settings.get(key,default))); lay.addWidget(c); return c
    def _build_overview(self):
        w,l=self._page(); f=self._card(l,'General'); self.language_label=QLabel(); f.addWidget(self.language_label); self.remember_last=self._check(f,'','remember_last'); self.restore_zoom=self._check(f,'','restore_zoom'); self.single_page=self._check(f,'','single_page'); self.confirm_close=self._check(f,'','confirm_close'); f=self._card(l,'Workspace'); self.status=self._check(f,'','status_bar'); self.center_page=self._check(f,'','center_page'); self.page_shadow=self._check(f,'','page_shadow'); l.addStretch(); self.stack.addWidget(w)
    def _build_appearance(self):
        w,l=self._page(); f=self._card(l,'Theme Studio','Bright Material You themes and interface controls.'); self.theme_label=QLabel(); f.addWidget(self.theme_label); self.theme=QComboBox(); self.theme.addItems(list(COLOR_THEMES)); self.theme.setCurrentText(self.settings.get('theme','Arctic Glass')); f.addWidget(self.theme); self.theme_preview=QLabel(); self.theme_preview.setMinimumHeight(54); self.theme_preview.setAlignment(Qt.AlignCenter); f.addWidget(self.theme_preview); self.accent_label=QLabel(); f.addWidget(self.accent_label); self.accent=QComboBox(); self.accent.addItems(['Theme default','Azure','Violet','Turquoise','Rose','Emerald']); self.accent.setCurrentText(self.settings.get('accent','Theme default')); f.addWidget(self.accent); self.aero=self._check(f,'','aero_enabled'); self.large=self._check(f,'','large_toolbar'); self.show_icons=self._check(f,'','show_toolbar_text'); self.compact=self._check(f,'','compact_toolbar',False); self.animations=self._check(f,'','animations'); self.theme.currentTextChanged.connect(self._preview_style); l.addStretch(); self.stack.addWidget(w)
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
    def _retranslate(self):
        self.t=SETTINGS_I18N.get(self.lang,SETTINGS_I18N['en']); self.title.setText(self.t['title']); self.subtitle.setText(self.t['subtitle']); self.live_chip.setText(self.t.get('live','● Live preview')); self.nav.clear(); self.nav.addItems([self.t['overview'],self.t['appearance'],self.t['eye'],self.t['document'],self.t['performance'],self.t['audio'],self.t['shortcuts']]);
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
        _ct=_cards.get(self.lang,_cards['en'])
        for _lab,_txt in zip(self.card_titles,_ct):
            if _lab is not None: _lab.setText(_txt); _lab.setVisible(True)
        self.language_label.setText(self.t.get('language','Interface language')); self._set_texts(); self.reset_btn.setText(self.t['reset']); self.buttons.button(QDialogButtonBox.Cancel).setText(self.t['cancel']); self.buttons.button(QDialogButtonBox.Apply).setText(self.t['apply']); self.buttons.button(QDialogButtonBox.Ok).setText(self.t['ok']); codes=['en','fa','da','de','es','no','fi','sv','fr','el','ar']; self.lang_combo.blockSignals(True); self.lang_combo.setCurrentIndex(codes.index(self.lang)); self.lang_combo.blockSignals(False); self.nav.setCurrentRow(min(self.nav.currentRow(),6)); self._apply_dialog_style()
    def _set_texts(self):
        t=self.t; self.remember_last.setText(t['remember']); self.restore_zoom.setText(t['restore']); self.single_page.setText(t.get('single','Single-page reading mode')); self.confirm_close.setText(t['confirm']); self.status.setText(t['status']); self.center_page.setText(t['center']); self.page_shadow.setText(t['shadow']); self.theme_label.setText(t['theme']); self.accent_label.setText(t['accent']); self.aero.setText(t['aero']); self.large.setText(t['large']); self.show_icons.setText(t['toolbar']); self.compact.setText(t['compact']); self.animations.setText(t['animations']); self.theme_preview.setText(t.get('theme_preview','Material You Light • Live preview')); self.blue.setText(t['blue']); self.blue_label_title.setText(t['blue_strength']); self.warm.setText(t['night']); self.reduce_motion.setText(t['reduce']); self.contrast_label_title.setText(t['contrast']); self.fit.setItemText(0,t.get('fit_width','Fit Width')); self.fit.setItemText(1,t.get('fit_page','Fit Page')); self.fit.setItemText(2,t.get('fit_100','100%')); self.auto_fit.setText(t['autofit']); self.smooth_scroll.setText(t['scroll']); self.page_gap.setText(t['gap']); self.cache_pages.setText(t['cache']); self.smooth_render.setText(t.get('quality_render','High-quality rendering')); self.preload.setText(t['preload']); self.gpu.setText(t['gpu']); self.low_memory.setText(t['memory']); self.large_files.setText(t.get('large_files','Large PDF mode: pages are rendered on demand; the whole document is never loaded into RAM.')); self.audio_enabled.setText(t['audio_enabled']); self.autoplay.setText(t['autoplay']); self.volume_title.setText(t['volume']); self.shortcut_text.setText(t['shortcuts_desc']+'\n\nCtrl+O  '+t.get('open','Open')+'\nCtrl+S  '+t.get('save','Save')+'\nCtrl+F  '+t.get('search','Search')+'\nCtrl+0  '+t.get('reset_zoom','Reset zoom')+'\nF11  '+t.get('fullscreen','Fullscreen'))
    def _language_from_settings(self,index):
        codes=['en','fa','da','de','es','no','fi','sv','fr','el','ar']; code=codes[index]
        if code!=self.lang: self.lang=code; self.viewer.apply_language(code); self._retranslate()
    def _preview_style(self):
        self.settings['theme']=self.theme.currentText(); self._apply_dialog_style(); self.theme_preview.setText(f"{self.theme.currentText()}  •  Material You Light  •  {self.t.get('live','Live preview')}")
    def _apply_dialog_style(self):
        accent=THEME_ACCENTS.get(self.settings.get('theme','Arctic Glass'),(58,141,255)); ah='#%02X%02X%02X'%accent
        self.setStyleSheet(COLOR_THEMES.get(self.settings.get('theme','Arctic Glass'),COLOR_THEMES['Arctic Glass'])+f'''
QDialog{{background:#F7F7FA;color:#172233;}}
QFrame#settingsHeader{{background:#FFFFFF;border:1px solid #DFE3EA;border-radius:24px;}}
QLabel#settingsTitle{{font-size:24px;font-weight:900;color:#172233;}}
QLabel#settingsSubtitle{{font-size:13px;color:#667386;}}
QLabel#settingsChip{{background:{soft_tone(ah)};color:{ah};border-radius:14px;padding:8px 12px;font-weight:800;}}
QListWidget#settingsNav{{background:#FFFFFF;border:1px solid #DFE3EA;border-radius:20px;padding:8px;outline:0;}}
QListWidget#settingsNav::item{{padding:14px 12px;border-radius:13px;margin:3px;color:#263241;font-weight:700;}}
QListWidget#settingsNav::item:selected{{background:{ah};color:#FFFFFF;}}
QStackedWidget{{background:transparent;border:none;}}
QWidget#settingsPage{{background:transparent;}}
QScrollArea#settingsPageScroll{{background:transparent;border:none;}}
QWidget#settingsPageContent{{background:transparent;}}
QFrame#settingsCard{{background:#FFFFFF;border:1px solid #DDE2EA;border-radius:20px;min-height:92px;padding:0;}}
QLabel#settingsCardTitle{{font-size:18px;font-weight:900;color:#172233;background:transparent;padding:0;min-height:30px;}}
QLabel#settingsCardSubtitle{{font-size:12px;color:#69778A;background:transparent;min-height:20px;}}
QScrollArea#settingsPageScroll > QWidget > QWidget{{background:transparent;}}
QLabel{{color:#172233;}}
QCheckBox{{font-size:13px;color:#253246;background:transparent;}}
QComboBox,QLineEdit,QSpinBox{{font-size:13px;min-height:40px;}}
QFormLayout QLabel{{color:#253246;}}
''')
    def _fade_in(self):
        self.effect=QGraphicsOpacityEffect(self); self.setGraphicsEffect(self.effect); self.anim=QPropertyAnimation(self.effect,b'opacity',self); self.anim.setDuration(240); self.anim.setStartValue(0.0); self.anim.setEndValue(1.0); self.anim.setEasingCurve(QEasingCurve.OutCubic); self.anim.start()
    def _switch_page(self,index):
        self.stack.setCurrentIndex(index)
        if self.settings.get('animations',True) and not self.settings.get('reduce_motion',False):
            w=self.stack.currentWidget(); eff=QGraphicsOpacityEffect(w); w.setGraphicsEffect(eff); a=QPropertyAnimation(eff,b'opacity',w); a.setDuration(180); a.setStartValue(.35); a.setEndValue(1.0); a.setEasingCurve(QEasingCurve.OutCubic); w._page_anim=a; a.start()
    def collect(self):
        return {'remember_last':self.remember_last.isChecked(),'restore_zoom':self.restore_zoom.isChecked(),'single_page':self.single_page.isChecked(),'confirm_close':self.confirm_close.isChecked(),'cache_pages':self.cache_pages.isChecked(),'smooth_render':self.smooth_render.isChecked(),'theme':self.theme.currentText(),'accent':self.accent.currentText(),'aero_enabled':self.aero.isChecked(),'compact_toolbar':self.compact.isChecked(),'status_bar':self.status.isChecked(),'page_shadow':self.page_shadow.isChecked(),'fit_mode':self.fit.currentText(),'zoom_step':self.zoom_step.value(),'rotation':self.rotation.currentText(),'auto_fit':self.auto_fit.isChecked(),'center_page':self.center_page.isChecked(),'audio_enabled':self.audio_enabled.isChecked(),'autoplay':self.autoplay.isChecked(),'volume':self.volume.value(),'large_toolbar':self.large.isChecked(),'show_toolbar_text':self.show_icons.isChecked(),'preload_pages':self.preload.isChecked(),'blue_filter':self.blue.isChecked(),'blue_filter_strength':self.blue_strength.value(),'night_reading':self.warm.isChecked(),'reduce_motion':self.reduce_motion.isChecked(),'ui_contrast':self.contrast.value(),'smooth_scroll':self.smooth_scroll.isChecked(),'page_gap':self.page_gap.isChecked(),'gpu_acceleration':self.gpu.isChecked(),'low_memory':self.low_memory.isChecked(),'animations':self.animations.isChecked(),'appearance_mode':'light'}
    def reset_defaults(self):
        d={'remember_last':True,'restore_zoom':True,'confirm_close':True,'cache_pages':False,'smooth_render':True,'theme':'Arctic Glass','accent':'Theme default','aero_enabled':True,'compact_toolbar':False,'status_bar':True,'page_shadow':True,'fit_mode':'Fit Width','zoom_step':25,'rotation':'0°','auto_fit':True,'center_page':True,'audio_enabled':True,'autoplay':False,'volume':50,'large_toolbar':True,'show_toolbar_text':True,'preload_pages':False,'blue_filter':False,'blue_filter_strength':35,'night_reading':False,'reduce_motion':False,'ui_contrast':100,'smooth_scroll':True,'page_gap':True,'gpu_acceleration':True,'low_memory':True,'animations':True,'appearance_mode':'light'}; self.settings.update(d); self.theme.setCurrentText(d['theme']); self.accent.setCurrentText(d['accent']); self.blue.setChecked(False); self.blue_strength.setValue(35); self.warm.setChecked(False); self.contrast.setValue(100); self.aero.setChecked(True); self.animations.setChecked(True); self.reduce_motion.setChecked(False); self.smooth_scroll.setChecked(True); self.page_gap.setChecked(True); self.gpu.setChecked(True); self.low_memory.setChecked(True); self._preview_style()
    def apply_changes(self):
        self.settings.update(self.collect()); self.viewer.app_settings.update(self.settings); self.viewer.apply_app_settings(); self.settings_changed.emit(self.settings)
    def accept(self): self.apply_changes(); super().accept()

class ParinPDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.doc = None
        self.file_path = ""
        self.current_lang = "en"
        self.current_page = 0
        self.zoom_factor = 1.0
        self.fit_mode = 'width'
        self.active_tool = None
        self.rotation = 0
        self.render_pending = False
        self._last_viewport_size = None
        self.is_drawing = False
        self.large_file_mode = False

        self.settings_store = QSettings('Parin', 'ParinPDFViewer')
        self.app_settings = {
            'remember_last': self.settings_store.value('remember_last', True, type=bool),
            'restore_zoom': self.settings_store.value('restore_zoom', True, type=bool),
            'single_page': self.settings_store.value('single_page', True, type=bool),
            'confirm_close': self.settings_store.value('confirm_close', True, type=bool),
            'cache_pages': self.settings_store.value('cache_pages', True, type=bool),
            'smooth_render': self.settings_store.value('smooth_render', True, type=bool),
            'theme': self.settings_store.value('theme', 'Arctic Glass'),
            'compact_toolbar': self.settings_store.value('compact_toolbar', False, type=bool),
            'status_bar': self.settings_store.value('status_bar', True, type=bool),
            'page_shadow': self.settings_store.value('page_shadow', True, type=bool),
            'fit_mode': self.settings_store.value('fit_mode', 'Fit Width'),
            'zoom_step': self.settings_store.value('zoom_step', 25, type=int),
            'rotation': self.settings_store.value('rotation', '0°'),
            'auto_fit': self.settings_store.value('auto_fit', True, type=bool),
            'center_page': self.settings_store.value('center_page', True, type=bool),
            'audio_enabled': self.settings_store.value('audio_enabled', True, type=bool),
            'autoplay': self.settings_store.value('autoplay', False, type=bool),
            'volume': self.settings_store.value('volume', 50, type=int),
            'large_toolbar': self.settings_store.value('large_toolbar', True, type=bool),
            'show_toolbar_text': self.settings_store.value('show_toolbar_text', True, type=bool),
            'preload_pages': self.settings_store.value('preload_pages', True, type=bool),
            'appearance_mode': 'light',
            'accent': self.settings_store.value('accent', 'آبی نئون'),
            'aero_enabled': self.settings_store.value('aero_enabled', True, type=bool),
            'blue_filter': self.settings_store.value('blue_filter', False, type=bool),
            'blue_filter_strength': self.settings_store.value('blue_filter_strength', 35, type=int),
            'night_reading': self.settings_store.value('night_reading', False, type=bool),
            'reduce_motion': self.settings_store.value('reduce_motion', False, type=bool),
            'ui_contrast': self.settings_store.value('ui_contrast', 100, type=int),
            'smooth_scroll': self.settings_store.value('smooth_scroll', True, type=bool),
            'page_gap': self.settings_store.value('page_gap', True, type=bool),
            'gpu_acceleration': self.settings_store.value('gpu_acceleration', True, type=bool),
            'low_memory': self.settings_store.value('low_memory', False, type=bool),
            'animations': self.settings_store.value('animations', True, type=bool)
        }

        legacy_theme = clean_label(str(self.app_settings.get('theme','Arctic Glass')))
        self.app_settings['theme'] = legacy_theme if legacy_theme in COLOR_THEMES else 'Arctic Glass'

        self.selected_color = QColor(103, 80, 164)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        # Load the audio stream lazily only when the user presses Lo-Fi.
        # This prevents FFmpeg/media errors during application startup.
        self.audio_output.setVolume(0.5)
        self.player.errorOccurred.connect(self._audio_error)
        self.is_lofi_playing = False

        self.setMinimumSize(1150, 750)
        self.init_ui()
        self.apply_language(self.current_lang)
        self.apply_app_settings()
        self._install_shortcuts()

    def _install_shortcuts(self):
        for text,key,slot in [
            ("Open","Ctrl+O",self.open_file),("Save","Ctrl+S",self.save_file),
            ("Search","Ctrl+F",self.search_pdf),("Zoom in","Ctrl++",self.zoom_in),
            ("Zoom out","Ctrl+-",self.zoom_out),("Fit width","Ctrl+W",self.fit_width),
            ("Fit page","Ctrl+Shift+W",self.fit_page),("Fullscreen","F11",self.toggle_fullscreen),
            ("Previous","Left",self.prev_page),("Next","Right",self.next_page),
            ("Reset zoom","Ctrl+0",self.reset_zoom)]:
            QAction(text,self,shortcut=key,triggered=slot)

    def open_settings(self):
        dlg=SettingsDialog(self)
        dlg.exec()

    def _style_for_theme(self):
        theme=self.app_settings.get('theme','Arctic Glass')
        return COLOR_THEMES.get(theme, COLOR_THEMES['Arctic Glass'])
    def apply_app_settings(self):
        self.settings_store.setValue('settings',str(self.app_settings))
        for k,v in self.app_settings.items(): self.settings_store.setValue(k,v)
        base=self._style_for_theme(); accent=THEME_ACCENTS.get(self.app_settings.get('theme','Arctic Glass'),(58,141,255)); ah='#%02X%02X%02X'%accent
        common=f'''QWidget#app_header{{background:rgba(255,255,255,.90);border-bottom:1px solid #E1E1E6;}}
QLabel#brand_title{{font-size:21px;font-weight:900;color:#1B1B1F;}}
QLabel#brand_subtitle{{font-size:11px;color:#66666F;}}
QFrame#tool_area{{background:rgba(246,249,253,.98);border-bottom:1px solid #DDE5EF;}}
QFrame#tool_group{{background:rgba(255,255,255,.96);border:1px solid #D7E0EB;border-radius:18px;}}
QLabel#group_label{{font-size:9px;font-weight:900;color:#707079;padding:0 5px;}}
QLineEdit#quick_search,QLineEdit{{min-height:38px;}}
QStatusBar{{background:rgba(255,255,255,.94);color:#62626B;border-top:1px solid #E1E1E6;}}
QPushButton:hover{{border-color:{ah};}}
QPushButton:checked{{background:{soft_tone(ah)};border:2px solid {ah};}}
'''
        self.setStyleSheet(base+common)
        self.statusBar().setVisible(bool(self.app_settings.get('status_bar',True)))
        self.audio_output.setVolume(max(0,min(100,int(self.app_settings.get('volume',50))))/100)
        compact=bool(self.app_settings.get('compact_toolbar',False)); large=bool(self.app_settings.get('large_toolbar',True))
        names=['btn_open','btn_save','btn_print_opt','btn_pen','btn_highlight','btn_eraser','btn_add_text','btn_color','btn_fit_width','btn_fit_page','btn_reset_zoom','btn_prev','btn_next','btn_rotate_left','btn_rotate_right','btn_fullscreen','btn_lofi','btn_more','btn_settings','btn_lang']
        for b in [getattr(self,n,None) for n in names]:
            if b:
                b.setMinimumHeight(32 if compact else (44 if large else 38)); b.setIconSize(QSize(24,24))
                current=clean_label(b.text()); glyph='•'
                for key,val in ICON_GLYPHS.items():
                    if current.lower().startswith(key.lower()): glyph=val; break
                b.setIcon(make_action_icon(glyph,24,accent)); b.setIconSize(QSize(24,24))
        self._update_blue_filter()
        if self.doc:
            fit=self.app_settings.get('fit_mode','Fit Width')
            if fit=='Fit Width': self.fit_width()
            elif fit=='Fit Page': self.fit_page()

    def init_ui(self):
        central_widget=QWidget(self); self.setCentralWidget(central_widget)
        self.main_layout=QVBoxLayout(central_widget); self.main_layout.setContentsMargins(0,0,0,0); self.main_layout.setSpacing(0)

        # Header / brand row
        self.header=QFrame(); self.header.setObjectName("app_header"); hl=QHBoxLayout(self.header); hl.setContentsMargins(16,10,16,8); hl.setSpacing(10)
        self.app_icon=QLabel(); self.app_icon.setPixmap(make_app_icon(46).pixmap(46,46)); hl.addWidget(self.app_icon)
        brand=QVBoxLayout(); self.brand_title=QLabel("Parin"); self.brand_title.setObjectName("brand_title"); self.brand_subtitle=QLabel("Fast • Focused • PDF workspace"); self.brand_subtitle.setObjectName("brand_subtitle"); brand.addWidget(self.brand_title); brand.addWidget(self.brand_subtitle); hl.addLayout(brand)
        hl.addStretch()
        self.quick_search=QLineEdit(); self.quick_search.setPlaceholderText("Search inside PDF…"); self.quick_search.setClearButtonEnabled(True); self.quick_search.setMinimumWidth(280); self.quick_search.returnPressed.connect(self.search_from_bar); hl.addWidget(self.quick_search)
        self.btn_settings=self.create_btn("Settings", self.open_settings, icon_key="Settings"); hl.addWidget(self.btn_settings)
        self.btn_lang=self.create_btn("Language", None, icon_key="Language"); hl.addWidget(self.btn_lang)
        lang_menu = QMenu(self)
        language_names = {
            "fa":"🇮🇷 فارسی", "en":"🇬🇧 English", "da":"🇩🇰 Dansk",
            "de":"🇩🇪 Deutsch", "es":"🇪🇸 Español", "no":"🇳🇴 Norsk",
            "fi":"🇫🇮 Suomi", "sv":"🇸🇪 Svenska", "fr":"🇫🇷 Français",
            "el":"🇬🇷 Ελληνικά", "ar":"🇸🇦 العربية"
        }
        for lang_code, lang_name in language_names.items():
            action = QAction(lang_name, self)
            action.triggered.connect(lambda checked=False, c=lang_code: self.apply_language(c))
            lang_menu.addAction(action)
        self.btn_lang.setMenu(lang_menu)
        self.main_layout.addWidget(self.header)

        # Responsive, readable toolbar with clear groups
        self.tool_area=QFrame(); self.tool_area.setObjectName("tool_area"); tl=QVBoxLayout(self.tool_area); tl.setContentsMargins(8,6,8,6); tl.setSpacing(5)
        row1=QHBoxLayout(); row1.setSpacing(5); row2=QHBoxLayout(); row2.setSpacing(5); self.group_labels={}
        def add_group(row,title,buttons):
            box=QFrame(); box.setObjectName("tool_group"); gl=QHBoxLayout(box); gl.setContentsMargins(5,4,5,4); gl.setSpacing(4)
            lab=QLabel(title); lab.setObjectName("group_label"); gl.addWidget(lab); self.group_labels[title]=lab
            for b in buttons: gl.addWidget(b)
            row.addWidget(box)
        self.btn_open=self.create_btn("Open PDF",self.open_file,icon_key="Open"); self.btn_save=self.create_btn("Save PDF",self.save_file,icon_key="Save"); self.btn_print_opt=self.create_btn("Print",self.print_document,icon_key="Print")
        self.btn_pen=self.create_btn("Pen",lambda:self.toggle_tool('pen'),True,"Pen"); self.btn_highlight=self.create_btn("Highlight",lambda:self.toggle_tool('highlight'),True,"Highlight"); self.btn_eraser=self.create_btn("Eraser",lambda:self.toggle_tool('eraser'),True,"Eraser"); self.btn_add_text=self.create_btn("Text",lambda:self.toggle_tool('text'),True,"Text"); self.btn_color=self.create_btn("Color",self.choose_color,icon_key="Color"); self.update_color_btn_style()
        self.btn_zoom_out=self.create_btn("−",self.zoom_out); self.btn_zoom_in=self.create_btn("+",self.zoom_in); self.btn_fit_width=self.create_btn("Fit Width",self.fit_width,icon_key="Fit"); self.btn_fit_page=self.create_btn("Fit Page",self.fit_page,icon_key="Fit"); self.btn_reset_zoom=self.create_btn("100%",self.reset_zoom)
        self.btn_prev=self.create_btn("Prev",self.prev_page,icon_key="Prev"); self.btn_next=self.create_btn("Next",self.next_page,icon_key="Next"); self.lbl_page=QLabel("Page:"); self.spin_page=QSpinBox(); self.spin_page.setMinimum(1); self.spin_page.setFixedWidth(82); self.spin_page.valueChanged.connect(self.go_to_page)
        self.btn_rotate_left=self.create_btn("Rotate",lambda:self.rotate(-90),icon_key="Rotate"); self.btn_rotate_right=self.create_btn("Rotate",lambda:self.rotate(90),icon_key="Rotate"); self.btn_fullscreen=self.create_btn("Fullscreen",self.toggle_fullscreen,icon_key="Fullscreen")
        self.btn_lofi=self.create_btn("Lo-Fi",self.toggle_lofi,icon_key="Lo-Fi")
        add_group(row1,"FILE",[self.btn_open,self.btn_save,self.btn_print_opt])
        add_group(row1,"ANNOTATE",[self.btn_pen,self.btn_highlight,self.btn_eraser,self.btn_add_text,self.btn_color])
        row1.addStretch(); tl.addLayout(row1)
        add_group(row2,"VIEW",[self.btn_zoom_out,self.btn_zoom_in,self.btn_fit_width,self.btn_fit_page,self.btn_reset_zoom])
        add_group(row2,"PAGE",[self.btn_prev,self.lbl_page,self.spin_page,self.btn_next])
        add_group(row2,"TOOLS",[self.btn_rotate_left,self.btn_rotate_right,self.btn_fullscreen,self.btn_lofi])
        self.btn_more=self.create_btn("More",None,icon_key="More"); more=QMenu(self)
        self.more_actions=[]
        for text,slot,ikey in [("Search PDF",self.search_pdf,"Search"),("Remove Password",self.remove_password,"Remove"),("Set Password",self.add_password,"Set"),("Settings",self.open_settings,"Settings")]:
            a=QAction(text,self); a.setIcon(make_action_icon(ICON_GLYPHS.get(ikey,"•"),22,THEME_ACCENTS.get(self.app_settings.get("theme","Arctic Glass"),(58,141,255)))); a.triggered.connect(slot); more.addAction(a); self.more_actions.append(a)
        self.btn_more.setMenu(more); row2.addWidget(self.btn_more); row2.addStretch(); tl.addLayout(row2)
        self.main_layout.addWidget(self.tool_area)

        self.scroll_area=QScrollArea(self); self.scroll_area.setWidgetResizable(True); self.scroll_area.setAlignment(Qt.AlignCenter); self.page_label=PDFPageLabel(self); self.scroll_area.setWidget(self.page_label); self.main_layout.addWidget(self.scroll_area,1); self.blue_overlay=QFrame(self.scroll_area.viewport()); self.blue_overlay.setAttribute(Qt.WA_TransparentForMouseEvents,True); self.blue_overlay.setGeometry(self.scroll_area.viewport().rect()); self.blue_overlay.hide(); self.blue_overlay.raise_()
        self.statusBar().showMessage("Ready • Open a PDF to begin")
        self.setWindowIcon(make_app_icon(64))

    def search_from_bar(self):
        if self.quick_search.text().strip(): self._search_query(self.quick_search.text().strip())

    def create_btn(self,text,slot,checkable=False,icon_key=None):
        btn=QPushButton(clean_label(text),self)
        btn.setCursor(Qt.PointingHandCursor); btn.setCheckable(checkable); btn.setMinimumWidth(82)
        glyph=ICON_GLYPHS.get(icon_key or clean_label(text).split(' ')[0],'•')
        accent=THEME_ACCENTS.get(self.app_settings.get('theme','Arctic Glass'),(58,141,255))
        btn.setIcon(make_action_icon(glyph,24,accent)); btn.setIconSize(QSize(24,24))
        if slot: btn.clicked.connect(slot)
        return btn
    def _update_blue_filter(self):
        if not hasattr(self,'blue_overlay'): return
        strength=max(0,min(100,int(self.app_settings.get('blue_filter_strength',35)))); enabled=bool(self.app_settings.get('blue_filter',False)); alpha=int(20+strength*1.5); self.blue_overlay.setStyleSheet(f'background:rgba(255,166,66,{alpha});border:none;'); self.blue_overlay.setVisible(enabled and strength>0); self.blue_overlay.raise_()

    def toggle_tool(self, tool_name):
        if self.active_tool == tool_name:
            self.active_tool = None
        else:
            self.active_tool = tool_name
        
        self.btn_pen.setChecked(self.active_tool == 'pen')
        self.btn_highlight.setChecked(self.active_tool == 'highlight')
        self.btn_eraser.setChecked(self.active_tool == 'eraser')
        self.btn_add_text.setChecked(self.active_tool == 'text')

    def choose_color(self):
        color = QColorDialog.getColor(self.selected_color, self, "انتخاب رنگ")
        if color.isValid():
            self.selected_color = color
            self.update_color_btn_style()

    def update_color_btn_style(self):
        hex_color = self.selected_color.name()
        text_color = "#FFFFFF" if self.selected_color.lightness() < 128 else "#000000"
        self.btn_color.setStyleSheet(f"background-color: {hex_color}; color: {text_color}; border-radius: 8px;")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "انتخاب فایل", "", "سندها (*.pdf)")
        if file_path:
            try:
                if self.doc: 
                    self.doc.close()
                
                import os
                file_size=os.path.getsize(file_path)
                self.large_file_mode = file_size >= 1024**3
                doc = fitz.open(file_path)
                if self.large_file_mode:
                    self.app_settings['low_memory']=True
                    self.app_settings['cache_pages']=False
                    self.app_settings['preload_pages']=False
                t = TRANSLATIONS[self.current_lang]

                if doc.is_encrypted:
                    pwd, ok = QInputDialog.getText(self, "رمز عبور", t["enter_pass"], QLineEdit.Password)
                    if ok and pwd:
                        if not doc.authenticate(pwd):
                            QMessageBox.critical(self, "خطا", "رمز عبور اشتباه است!")
                            return
                    else: 
                        return

                self.doc = doc
                self.file_path = file_path
                self.current_page = 0
                self.zoom_factor = 1.0
                self.rotation = {'0°':0,'90°':90,'180°':180,'270°':270}.get(self.app_settings.get('rotation','0°'),0)
                self.fit_mode = {'Fit Width':'width','Fit Page':'page','100%':None}.get(self.app_settings.get('fit_mode','Fit Width'),'width')
                
                self.spin_page.blockSignals(True)
                self.spin_page.setMaximum(self.doc.page_count)
                self.spin_page.setValue(1)
                self.spin_page.blockSignals(False)
                
                self.fit_width()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در باز کردن فایل: {str(e)}")

    def _effective_page_size(self, page):
        return (page.rect.height, page.rect.width) if self.rotation % 180 else (page.rect.width, page.rect.height)

    def render_page(self):
        if not self.doc or not (0 <= self.current_page < self.doc.page_count):
            return
        page=self.doc.load_page(self.current_page)
        self.zoom_factor=max(0.1,min(self.zoom_factor,8.0))
        mat=fitz.Matrix(self.zoom_factor,self.zoom_factor).prerotate(self.rotation)
        pix=page.get_pixmap(matrix=mat,alpha=False)
        img=QImage(pix.samples,pix.width,pix.height,pix.stride,QImage.Format_RGB888).copy()
        self.page_label.setPixmap(QPixmap.fromImage(img))
        self.page_label.adjustSize()
        self._update_page_indicator()

    def get_pdf_coords(self,pos: QPointF):
        pix=self.page_label.pixmap()
        if not pix or pix.isNull():
            return fitz.Point(pos.x(),pos.y())
        x=float(max(0,min(pos.x(),pix.width()-1)))/self.zoom_factor
        y=float(max(0,min(pos.y(),pix.height()-1)))/self.zoom_factor
        r=self.doc.load_page(self.current_page).rect
        if self.rotation==90: return fitz.Point(y,r.height-x)
        if self.rotation==180: return fitz.Point(r.width-x,r.height-y)
        if self.rotation==270: return fitz.Point(r.width-y,x)
        return fitz.Point(x,y)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'blue_overlay'): self.blue_overlay.setGeometry(self.scroll_area.viewport().rect())
        if not self.doc or not self.app_settings.get('auto_fit', True) or self.fit_mode not in ('width','page'): return
        s=self.scroll_area.viewport().size()
        key=(s.width(),s.height())
        if key==self._last_viewport_size: return
        self._last_viewport_size=key
        QTimer.singleShot(0,self._apply_fit)

    def _available_viewport(self):
        s=self.scroll_area.viewport().size()
        return max(40,s.width()-24),max(40,s.height()-24)

    def _apply_fit(self):
        if not self.doc: return
        if self.fit_mode=='width': self._set_fit_width()
        elif self.fit_mode=='page': self._set_fit_page()

    def _set_fit_width(self):
        page=self.doc.load_page(self.current_page)
        w,_=self._effective_page_size(page)
        aw,_=self._available_viewport()
        if w>0: self.zoom_factor=max(0.1,min(aw/w,8.0))
        self.render_page()

    def _set_fit_page(self):
        page=self.doc.load_page(self.current_page)
        w,h=self._effective_page_size(page)
        aw,ah=self._available_viewport()
        if w>0 and h>0:
            self.zoom_factor=max(0.1,min(aw/w,ah/h,8.0))
        self.render_page()

    def fit_width(self):
        if self.doc:
            self.fit_mode='width'
            self._set_fit_width()

    def fit_page(self):
        if self.doc:
            self.fit_mode='page'
            self._set_fit_page()

    def reset_zoom(self):
        if self.doc:
            self.fit_mode=None
            self.zoom_factor=1.0
            self.render_page()

    def rotate(self,degrees):
        if not self.doc: return
        self.rotation=(self.rotation+degrees)%360
        self._apply_fit() if self.fit_mode in ('width','page') else self.render_page()

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def search_pdf(self):
        if not self.doc: return
        t=TRANSLATIONS[self.current_lang]; text,ok=QInputDialog.getText(self,t['search'],t['find_text'])
        if ok and text.strip(): self._search_query(text.strip())

    def _search_query(self,q):
        if not self.doc: return
        n=self.doc.page_count
        if n <= 0: return
        order=list(range((self.current_page+1)%n,n))+list(range(0,(self.current_page+1)%n))
        for i in order:
            if self.doc.load_page(i).search_for(q):
                self.current_page=i; self.spin_page.blockSignals(True); self.spin_page.setValue(i+1); self.spin_page.blockSignals(False); self._apply_fit() if self.fit_mode in ('width','page') else self.render_page(); self.statusBar().showMessage(f"Found “{q}” on page {i+1}"); return
        QMessageBox.information(self,TRANSLATIONS[self.current_lang]['search'],TRANSLATIONS[self.current_lang]['not_found'])

    def _retranslate_shell(self):
        extra={'en':('Fast • Focused • PDF workspace','FILE','ANNOTATE','VIEW','PAGE','TOOLS','More More','Settings Settings','Ready • Open a PDF to begin','Search Search inside PDF…'),'fa':('سریع • متمرکز • محیط حرفه‌ای PDF','فایل','حاشیه‌نویسی','نمایش','صفحه','ابزارها','More بیشتر','Settings تنظیمات','آماده • یک PDF باز کنید','Search جستجو در PDF…'),'de':('Schnell • Fokus • PDF-Arbeitsbereich','DATEI','ANMERKEN','ANSICHT','SEITE','WERKZEUGE','More Mehr','Settings Einstellungen','Bereit • PDF öffnen','Search Im PDF suchen…'),'es':('Rápido • Enfocado • Espacio PDF','ARCHIVO','ANOTAR','VISTA','PÁGINA','HERRAMIENTAS','More Más','Settings Ajustes','Listo • Abra un PDF','Search Buscar en PDF…'),'fr':('Rapide • Concentré • Espace PDF','FICHIER','ANNOTER','AFFICHAGE','PAGE','OUTILS','More Plus','Settings Paramètres','Prêt • Ouvrez un PDF','Search Rechercher dans le PDF…'),'da':('Hurtig • Fokuseret • PDF-arbejdsområde','FIL','ANNOTERING','VISNING','SIDE','VÆRKTØJER','More Mere','Settings Indstillinger','Klar • Åbn en PDF','Search Søg i PDF…'),'no':('Rask • Fokusert • PDF-område','FIL','MERKNADER','VISNING','SIDE','VERKTØY','More Mer','Settings Innstillinger','Klar • Åpne en PDF','Search Søk i PDF…'),'fi':('Nopea • Keskittynyt • PDF-työtila','TIEDOSTO','MERKINNÄT','NÄKYMÄ','SIVU','TYÖKALUT','More Lisää','Settings Asetukset','Valmis • Avaa PDF','Search Hae PDF:stä…'),'sv':('Snabb • Fokuserad • PDF-arbetsyta','FIL','ANTECKNINGAR','VY','SIDA','VERKTYG','More Mer','Settings Inställningar','Redo • Öppna en PDF','Search Sök i PDF…'),'el':('Γρήγορο • Εστιασμένο • PDF','ΑΡΧΕΙΟ','ΣΧΟΛΙΑΣΜΟΣ','ΠΡΟΒΟΛΗ','ΣΕΛΙΔΑ','ΕΡΓΑΛΕΙΑ','More Περισσότερα','Settings Ρυθμίσεις','Έτοιμο • Ανοίξτε PDF','Search Αναζήτηση στο PDF…'),'ar':('سريع • مركز • مساحة عمل PDF','ملف','تعليقات','عرض','صفحة','أدوات','More المزيد','Settings الإعدادات','جاهز • افتح ملف PDF','Search البحث داخل PDF…')}
        vals=extra.get(self.current_lang,extra['en']); self.brand_subtitle.setText(vals[0]); self.btn_settings.setText(vals[7]); self.btn_more.setText(vals[6]); self.quick_search.setPlaceholderText(vals[9]); self.statusBar().showMessage(vals[8])
        for k,label in zip(['FILE','ANNOTATE','VIEW','PAGE','TOOLS'],vals[1:6]):
            if k in self.group_labels: self.group_labels[k].setText(label)
        more_names=[TRANSLATIONS[self.current_lang]['search']+' PDF',TRANSLATIONS[self.current_lang]['pass_remove'],TRANSLATIONS[self.current_lang]['pass_add'],vals[7]]
        for a,text in zip(getattr(self,'more_actions',[]),more_names): a.setText(text)

    def _update_page_indicator(self):
        if hasattr(self,'lbl_page'):
            t=TRANSLATIONS[self.current_lang]
            self.lbl_page.setText(f"{t['page']} {self.current_page+1} {t['of']} {self.doc.page_count if self.doc else 0}")

    def zoom_in(self):

        self.fit_mode = None
        if self.zoom_factor < 5.0:
            self.zoom_factor += max(0.05, self.app_settings.get('zoom_step',25)/100)
            self.render_page()

    def zoom_out(self):
        self.fit_mode = None
        if self.zoom_factor > 0.3:
            self.zoom_factor -= max(0.05, self.app_settings.get('zoom_step',25)/100)
            self.render_page()

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.spin_page.blockSignals(True)
            self.spin_page.setValue(self.current_page + 1)
            self.spin_page.blockSignals(False)
            self._apply_fit() if self.fit_mode in ('width','page') else self.render_page()

    def next_page(self):
        if self.doc and self.current_page < self.doc.page_count - 1:
            self.current_page += 1
            self.spin_page.blockSignals(True)
            self.spin_page.setValue(self.current_page + 1)
            self.spin_page.blockSignals(False)
            self._apply_fit() if self.fit_mode in ('width','page') else self.render_page()

    def go_to_page(self, val):
        if self.doc and 1 <= val <= self.doc.page_count:
            self.current_page = val - 1
            self._apply_fit() if self.fit_mode in ('width','page') else self.render_page()

    def erase_at_point(self, page, pdf_pt):
        radius = 20 / self.zoom_factor
        erase_rect = fitz.Rect(pdf_pt.x - radius, pdf_pt.y - radius, pdf_pt.x + radius, pdf_pt.y + radius)

        erased = False
        annots_to_delete = []
        for annot in page.annots():
            if annot.rect.intersects(erase_rect):
                annots_to_delete.append(annot)

        for annot in annots_to_delete:
            page.delete_annot(annot)
            erased = True

        if erased:
            self.render_page()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def toggle_lofi(self):
        if self.is_lofi_playing:
            self.player.stop()
            self.is_lofi_playing = False
            self.btn_lofi.setText(TRANSLATIONS[self.current_lang]["lofi"])
            return

        # Set the source on demand so a broken/unavailable stream can never
        # prevent Parin from starting normally.
        self.player.setSource(QUrl(LOFI_STREAM_URL))
        self.player.play()
        self.is_lofi_playing = True
        self.btn_lofi.setText(TRANSLATIONS[self.current_lang]["music_stop"])

    def _audio_error(self, error, error_string):
        if not error_string:
            error_string = "Could not open the audio stream."
        self.is_lofi_playing = False
        if hasattr(self, "btn_lofi"):
            self.btn_lofi.setText(TRANSLATIONS[self.current_lang]["lofi"])
        if hasattr(self, "statusBar"):
            self.statusBar().showMessage(f"Lo-Fi: {error_string}", 5000)

    def print_document(self):
        if not self.doc: return
        printer = QPrinter(QPrinter.HighResolution)
        print_dialog = QPrintDialog(printer, self)
        
        if print_dialog.exec() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            page = self.doc.load_page(self.current_page)
            
            pix = page.get_pixmap(dpi=300)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            
            rect = painter.viewport()
            scaled_img = img.scaled(rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            x = (rect.width() - scaled_img.width()) // 2
            y = (rect.height() - scaled_img.height()) // 2
            
            painter.drawImage(x, y, scaled_img)
            painter.end()

    def save_file(self):
        if not self.doc: return
        save_path, _ = QFileDialog.getSaveFileName(self, "ذخیره فایل", self.file_path, "PDF (*.pdf)")
        if save_path:
            self.doc.save(save_path, garbage=0 if self.large_file_mode else 4, deflate=True)
            QMessageBox.information(self, "موفقیت", "فایل با موفقیت ذخیره شد.")

    def remove_password(self):
        if not self.doc: return
        save_path, _ = QFileDialog.getSaveFileName(self, "ذخیره بدون رمز", "unlocked.pdf", "PDF (*.pdf)")
        if save_path: 
            self.doc.save(save_path, encryption=fitz.PDF_ENCRYPT_NONE, garbage=4, deflate=True)
            QMessageBox.information(self, "موفقیت", "رمز فایل برداشته شد.")

    def add_password(self):
        if not self.doc: return
        t = TRANSLATIONS[self.current_lang]
        pwd, ok = QInputDialog.getText(self, t["pass_add"], t["set_pass"], QLineEdit.Password)
        if ok and pwd:
            save_path, _ = QFileDialog.getSaveFileName(self, "ذخیره فایل رمزگذاری‌شده", "protected.pdf", "PDF (*.pdf)")
            if save_path:
                self.doc.save(save_path, encryption=fitz.PDF_ENCRYPT_AES_128, user_pw=pwd, owner_pw=pwd, garbage=4, deflate=True)
                QMessageBox.information(self, "موفقیت", "رمز عبور با موفقیت اعمال شد.")

    def apply_language(self, code):
        if code not in TRANSLATIONS:
            code = 'en'
        self.current_lang = code
        self.settings_store.setValue('language', code)
        t = TRANSLATIONS[code]
        self.setWindowTitle(t['title'])

        # Only update controls that actually exist in the current v8 toolbar.
        # The previous toolbar had separate Theme/Search/Password buttons;
        # those actions now live in Settings and the More menu.
        button_map = [
            (self.btn_open, 'open'), (self.btn_save, 'save'),
            (self.btn_pen, 'pen'), (self.btn_highlight, 'highlight'),
            (self.btn_eraser, 'eraser'), (self.btn_add_text, 'add_text'),
            (self.btn_color, 'color'), (self.btn_zoom_in, 'zoom_in'),
            (self.btn_zoom_out, 'zoom_out'), (self.btn_fit_width, 'fit_width'),
            (self.btn_fit_page, 'fit_page'), (self.btn_prev, 'prev'),
            (self.btn_next, 'next'), (self.btn_print_opt, 'print_opt'),
            (self.btn_rotate_left, 'rotate_left'),
            (self.btn_rotate_right, 'rotate_right'),
            (self.btn_reset_zoom, 'reset_zoom'),
            (self.btn_fullscreen, 'fullscreen'), (self.btn_lang, 'lang')
        ]
        for btn, key in button_map:
            btn.setText(t[key])

        self.lbl_page.setText(t['page'])
        self.btn_lofi.setText(t['music_stop'] if self.is_lofi_playing else t['lofi'])
        self.quick_search.setPlaceholderText(t['search'] + '…')
        QApplication.setLayoutDirection(t['dir'])
        self._retranslate_shell()
        self._update_page_indicator()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ParinPDFViewer()
    viewer.show()
    if viewer.app_settings.get('animations', True) and not viewer.app_settings.get('reduce_motion', False):
        effect=QGraphicsOpacityEffect(viewer); viewer.setGraphicsEffect(effect); fade=QPropertyAnimation(effect,b'opacity',viewer); fade.setDuration(320); fade.setStartValue(0.0); fade.setEndValue(1.0); fade.setEasingCurve(QEasingCurve.OutCubic); viewer._startup_fade=fade; fade.start()
    sys.exit(app.exec())
