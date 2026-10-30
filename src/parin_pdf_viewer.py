#!/usr/bin/env python3
import sys
import re
import os
import tempfile
from collections import OrderedDict
from pathlib import Path
import pymupdf as fitz  # PyMuPDF (modern API; avoids deprecated fitz import)
from PySide6.QtCore import Qt, QUrl, QPoint, QPointF, QRectF, QTimer, QSettings, Signal, QSize, QPropertyAnimation, QEasingCurve, QEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QLineEdit, QScrollArea, 
    QInputDialog, QMessageBox, QMenu, QColorDialog, QSpinBox, QDialog, QCheckBox,
    QComboBox, QSlider, QTabWidget, QFormLayout, QGroupBox, QDialogButtonBox,
    QRadioButton, QButtonGroup, QAbstractItemView, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QDockWidget, QStackedWidget, QFrame, QToolButton, QSizePolicy, QStyle, QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QGridLayout
)
from PySide6.QtGui import QImage, QPixmap, QAction, QColor, QPainter, QMouseEvent, QIcon, QFont, QLinearGradient, QPen, QPainterPath
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from parin_pdf_helpers import APP_VERSION, add_recent_file, normalize_recent_files, ensure_pdf_extension, same_path, clamp_zoom
from parin_handwriting_assist import SmartInkAssistant

# Text helper must be defined before translation tables are normalized.
EMOJI_RE = re.compile(r'[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF]')
def _is_document_encrypted(document):
    """Detect PDF encryption even after PyMuPDF auto-authenticates an empty password."""
    if document is None or getattr(document, "is_closed", False):
        return False
    try:
        encryption = (document.metadata or {}).get("encryption")
        if encryption and str(encryption).strip().lower() not in ("none", "null"):
            return True
    except Exception:
        pass
    try:
        return bool(document.is_encrypted)
    except Exception:
        return False


def clean_label(value):
    if not isinstance(value, str):
        return value
    return re.sub(r'\s{2,}', ' ', EMOJI_RE.sub('', value)).strip()

TRANSLATIONS = {
    'fa': {'title': 'پرین | Parin v8.9', 'open': '📂 باز کردن', 'save': '💾 ذخیره', 'pen': '✏️ قلم', 'highlight': '🖍️ هایلایت', 'eraser': '🧹 پاک\u200cکن', 'add_text': '✍️ متن', 'color': '🎨 رنگ', 'theme': '🎨 تم', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ عرض', 'fit_page': '⤢ صفحه', 'prev': 'صفحه قبل ⬅️', 'next': '➡️ صفحه بعد', 'print_opt': '🖨️ چاپ', 'pass_remove': '🔓 حذف رمز', 'pass_add': '🔒 گذاشتن رمز', 'lofi': '🎵 موسیقی آرامش\u200cبخش', 'lang': '🌐 زبان', 'search': 'Search جستجو', 'rotate_left': '↶ چرخش', 'rotate_right': '↷ چرخش', 'fullscreen': '⛶ تمام\u200cصفحه', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'صفحه:', 'of': 'از', 'enter_pass': 'لطفاً رمز عبور فایل را وارد کنید:', 'set_pass': 'رمز عبور جدید برای فایل تعیین کنید:', 'enter_text': 'متن مورد نظر را وارد کنید:', 'find_text': 'عبارت جستجو در PDF:', 'not_found': 'عبارت موردنظر پیدا نشد.', 'saved': 'فایل با موفقیت ذخیره شد.', 'opened': 'File opened.', 'wrong_pass': 'رمز عبور اشتباه است!', 'choose_file': 'Choose file', 'unlock_name': 'ذخیره بدون رمز', 'protected_name': 'ذخیره فایل رمزگذاری\u200cشده', 'unlocked': 'رمز فایل برداشته شد.', 'protected': 'رمز عبور با موفقیت اعمال شد.', 'color_pick': 'انتخاب رنگ', 'music_stop': '⏸️ توقف موسیقی', 'dir': Qt.RightToLeft},
    'en': {'title': 'Parin v8.9', 'open': '📂 Open', 'save': '💾 Save', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Theme', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Fit Width', 'fit_page': '⤢ Fit Page', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Language', 'search': 'Search Search', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Fullscreen', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Page:', 'of': 'of', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'da': {'title': 'Parin v8.9', 'open': '📂 Åbn', 'save': '💾 Gem', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Tema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Tilpas bredde', 'fit_page': '⤢ Tilpas side', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Sprog', 'search': 'Search Søg', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Fuldskærm', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Side:', 'of': 'af', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'de': {'title': 'Parin v8.9', 'open': '📂 Öffnen', 'save': '💾 Speichern', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Thema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Seitenbreite', 'fit_page': '⤢ Seite anpassen', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Sprache', 'search': 'Search Suchen', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Vollbild', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Seite:', 'of': 'von', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'es': {'title': 'Parin v8.9', 'open': '📂 Abrir', 'save': '💾 Guardar', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Tema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Ajustar ancho', 'fit_page': '⤢ Ajustar página', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Idioma', 'search': 'Search Buscar', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Pantalla completa', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Página:', 'of': 'de', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'no': {'title': 'Parin v8.9', 'open': '📂 Åpne', 'save': '💾 Lagre', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Tema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Tilpass bredde', 'fit_page': '⤢ Tilpass side', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Språk', 'search': 'Search Søk', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Fullskjerm', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Side:', 'of': 'av', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'fi': {'title': 'Parin v8.9', 'open': '📂 Avaa', 'save': '💾 Tallenna', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Teema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Sovita leveyteen', 'fit_page': '⤢ Sovita sivulle', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Kieli', 'search': 'Search Hae', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Koko näyttö', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Sivu:', 'of': '/', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'sv': {'title': 'Parin v8.9', 'open': '📂 Öppna', 'save': '💾 Spara', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Tema', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Anpassa bredd', 'fit_page': '⤢ Anpassa sida', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Språk', 'search': 'Search Sök', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Helskärm', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Sida:', 'of': 'av', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'fr': {'title': 'Parin v8.9', 'open': '📂 Ouvrir', 'save': '💾 Enregistrer', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Thème', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Ajuster largeur', 'fit_page': '⤢ Ajuster page', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Langue', 'search': 'Search Rechercher', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Plein écran', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Page :', 'of': 'sur', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'el': {'title': 'Parin v8.9', 'open': '📂 Άνοιγμα', 'save': '💾 Αποθήκευση', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 Θέμα', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ Προσαρμογή πλάτους', 'fit_page': '⤢ Προσαρμογή σελίδας', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 Γλώσσα', 'search': 'Search Αναζήτηση', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ Πλήρης οθόνη', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'Σελίδα:', 'of': 'από', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.LeftToRight},
    'ar': {'title': 'Parin v8.9', 'open': '📂 فتح', 'save': '💾 حفظ', 'pen': '✏️ Pen', 'highlight': '🖍️ Highlight', 'eraser': '🧹 Eraser', 'add_text': '✍️ Text', 'color': '🎨 Color', 'theme': '🎨 السمة', 'zoom_in': '🔍+', 'zoom_out': '🔍-', 'fit_width': '↔️ ملاءمة العرض', 'fit_page': '⤢ ملاءمة الصفحة', 'prev': '⬅️ Prev', 'next': 'Next ➡️', 'print_opt': '🖨️ Print', 'pass_remove': '🔓 Remove Password', 'pass_add': '🔒 Set Password', 'lofi': '🎵 Lo-Fi Music', 'lang': '🌐 اللغة', 'search': 'Search بحث', 'rotate_left': '↶ Rotate', 'rotate_right': '↷ Rotate', 'fullscreen': '⛶ ملء الشاشة', 'reset_zoom': '100%', 'fit': '📐 Fit', 'page': 'صفحة:', 'of': 'من', 'enter_pass': 'Enter file password:', 'set_pass': 'Enter new password:', 'enter_text': 'Enter text to add:', 'find_text': 'Search text in PDF:', 'not_found': 'Text not found.', 'saved': 'File saved successfully.', 'opened': 'File opened.', 'wrong_pass': 'Incorrect password!', 'choose_file': 'Choose file', 'unlock_name': 'Save without password', 'protected_name': 'Save encrypted PDF', 'unlocked': 'Password removed.', 'protected': 'Password applied successfully.', 'color_pick': 'Choose color', 'music_stop': '⏸️ Stop music', 'dir': Qt.RightToLeft},
}

# Final UI text normalization: feature labels use icons, not emoji.
for _lang, _items in TRANSLATIONS.items():
    for _key, _value in list(_items.items()):
        if isinstance(_value, str): _items[_key] = clean_label(_value)
    if isinstance(_items.get('title'), str):
        _items['title'] = re.sub(r'v\d+\.\d+(?:\.\d+)?', f"v{'.'.join(APP_VERSION.split('.')[:2])}", _items['title'])

ABOUT_ATTRIBUTION = "This project was created by Parin Mashalchian and ChatGPT also contributed to this project."

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
    # Shared visual system: calm surfaces, clear focus states, and consistent controls.
    return f'''QMainWindow,QWidget{{background:{surface};color:#182338;font-family:"Inter","Noto Sans",sans-serif;font-size:10pt;}}
QMainWindow{{background:{surface};}}
QScrollArea{{background:transparent;border:none;}}
QLabel{{color:#182338;background:transparent;}}
QPushButton{{background:#FFFFFF;color:#23334D;border:1px solid #D8E2EF;border-radius:10px;padding:8px 13px;font-weight:600;}}
QPushButton:hover{{background:{soft};border-color:{accent};}}
QPushButton:pressed{{background:{soft};border:1px solid {accent};padding-top:9px;padding-bottom:7px;}}
QPushButton:checked{{background:{soft};border:2px solid {accent};color:#142B4A;}}
QPushButton:disabled{{background:#F1F4F8;color:#A0AABA;border-color:#E3E8EF;}}
QToolButton{{background:transparent;color:#23334D;border:1px solid transparent;border-radius:9px;padding:7px;}}
QToolButton:hover{{background:{soft};border-color:#D7E5F8;}}
QToolButton:checked{{background:{soft};border:1px solid {accent};}}
QSpinBox,QLineEdit,QComboBox{{background:#FFFFFF;color:#182338;border:1px solid #D5DFEC;border-radius:10px;padding:8px 10px;selection-background-color:{accent};selection-color:white;min-height:20px;}}
QLineEdit:focus,QComboBox:focus,QSpinBox:focus{{border:2px solid {accent};background:#FFFFFF;}}
QComboBox::drop-down{{border:none;width:24px;}}
QMenu{{background:#FFFFFF;color:#182338;border:1px solid #D5DFEC;border-radius:12px;padding:6px;}}
QMenu::item{{padding:9px 16px;border-radius:7px;}}
QMenu::item:selected{{background:{soft};color:#142B4A;}}
QCheckBox{{color:#23334D;spacing:9px;padding:6px;}}
QCheckBox::indicator{{width:17px;height:17px;border-radius:5px;border:1px solid #9BAAC0;background:#FFFFFF;}}
QCheckBox::indicator:checked{{background:{accent};border-color:{accent};}}
QGroupBox{{border:1px solid #DCE5F0;border-radius:13px;margin-top:14px;padding:14px 10px 10px;background:rgba(255,255,255,0.72);font-weight:600;}}
QGroupBox::title{{subcontrol-origin:margin;left:14px;padding:0 6px;color:#50617A;font-weight:700;}}
QTabWidget::pane{{border:1px solid #DCE5F0;border-radius:12px;background:#FFFFFF;top:-1px;}}
QTabBar::tab{{background:#F2F6FB;color:#52627A;border:1px solid #E0E7F0;padding:9px 15px;margin-right:4px;border-top-left-radius:8px;border-top-right-radius:8px;}}
QTabBar::tab:selected{{background:#FFFFFF;color:{accent};border-bottom:2px solid {accent};font-weight:700;}}
QSlider::groove:horizontal{{height:6px;background:#E2E9F2;border-radius:3px;}}
QSlider::handle:horizontal{{width:18px;height:18px;margin:-6px 0;border-radius:9px;background:{accent};border:3px solid white;}}
QScrollBar:vertical{{width:10px;background:transparent;margin:4px;}}
QScrollBar::handle:vertical{{background:#C9D4E2;border-radius:5px;min-height:30px;}}
QScrollBar::handle:vertical:hover{{background:#9EADC2;}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
QToolTip{{background:#172B49;color:#FFFFFF;border:1px solid #334B6D;border-radius:6px;padding:5px 8px;}}'''

COLOR_THEMES = {name: _build_light_theme(accent, soft, surface) for name, _, accent, soft, surface in THEME_DEFINITIONS}
THEME_ACCENTS = {name: tuple(int(accent[i:i+2],16) for i in (1,3,5)) for name,_,accent,_,_ in THEME_DEFINITIONS}


def _build_dark_theme(accent):
    """Dark counterpart to light themes; PDF page pixels remain unchanged."""
    return f'''QMainWindow,QWidget{{background:#111827;color:#E5EDF7;font-family:"Inter","Noto Sans",sans-serif;font-size:10pt;}}
QMainWindow{{background:#101725;}}
QScrollArea{{background:transparent;border:none;}}
QLabel{{color:#E5EDF7;background:transparent;}}
QPushButton{{background:#1A2638;color:#E5EDF7;border:1px solid #30425A;border-radius:10px;padding:8px 13px;font-weight:600;}}
QPushButton:hover{{background:#243851;border-color:{accent};}}
QPushButton:pressed{{background:#20334B;border:1px solid {accent};padding-top:9px;padding-bottom:7px;}}
QPushButton:checked{{background:#203A59;border:2px solid {accent};color:#FFFFFF;}}
QPushButton:disabled{{background:#182131;color:#65758C;border-color:#27364B;}}
QToolButton{{background:transparent;color:#DCE6F3;border:1px solid transparent;border-radius:9px;padding:7px;}}
QToolButton:hover{{background:#243851;border-color:#38506E;}}
QToolButton:checked{{background:#203A59;border:1px solid {accent};}}
QSpinBox,QLineEdit,QComboBox{{background:#111B2A;color:#E5EDF7;border:1px solid #30425A;border-radius:10px;padding:8px 10px;selection-background-color:{accent};selection-color:#FFFFFF;min-height:20px;}}
QLineEdit:focus,QComboBox:focus,QSpinBox:focus{{border:2px solid {accent};background:#141F30;}}
QComboBox::drop-down{{border:none;width:24px;}}
QMenu{{background:#172235;color:#E5EDF7;border:1px solid #30425A;border-radius:12px;padding:6px;}}
QMenu::item{{padding:9px 16px;border-radius:7px;}}
QMenu::item:selected{{background:#253D5B;color:#FFFFFF;}}
QCheckBox{{color:#DCE6F3;spacing:9px;padding:6px;}}
QCheckBox::indicator{{width:17px;height:17px;border-radius:5px;border:1px solid #5A6D86;background:#111B2A;}}
QCheckBox::indicator:checked{{background:{accent};border-color:{accent};}}
QGroupBox{{border:1px solid #30425A;border-radius:13px;margin-top:14px;padding:14px 10px 10px;background:#172235;font-weight:600;}}
QGroupBox::title{{subcontrol-origin:margin;left:14px;padding:0 6px;color:#B2C2D7;font-weight:700;}}
QTabWidget::pane{{border:1px solid #30425A;border-radius:12px;background:#172235;top:-1px;}}
QTabBar::tab{{background:#172235;color:#AABAD0;border:1px solid #30425A;padding:9px 15px;margin-right:4px;border-top-left-radius:8px;border-top-right-radius:8px;}}
QTabBar::tab:selected{{background:#203650;color:#FFFFFF;border-bottom:2px solid {accent};font-weight:700;}}
QSlider::groove:horizontal{{height:6px;background:#2A3A51;border-radius:3px;}}
QSlider::handle:horizontal{{width:18px;height:18px;margin:-6px 0;border-radius:9px;background:{accent};border:3px solid #172235;}}
QScrollBar:vertical{{width:10px;background:transparent;margin:4px;}}
QScrollBar::handle:vertical{{background:#3B4D65;border-radius:5px;min-height:30px;}}
QScrollBar::handle:vertical:hover{{background:#536A86;}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
QToolTip{{background:#243851;color:#FFFFFF;border:1px solid #405976;border-radius:6px;padding:5px 8px;}}'''


def _theme_stylesheet(theme, appearance_mode="light"):
    theme = theme if theme in COLOR_THEMES else "Arctic Glass"
    if str(appearance_mode).lower() == "dark":
        accent = "#%02X%02X%02X" % THEME_ACCENTS.get(theme, (58,141,255))
        return _build_dark_theme(accent)
    return COLOR_THEMES[theme]


ICON_GLYPHS={'Open':'▱','Save':'↓','Print':'▤','Pen':'✎','Highlight':'✦','Eraser':'⌫','Text':'T','Color':'●','Fit':'□','Prev':'‹','Next':'›','Rotate':'⟳','Fullscreen':'⛶','Lo-Fi':'♫','Settings':'⚙','Language':'文','More':'⋯'}
def make_action_icon(symbol,size=20,accent=(53,111,216)):
    """Render compact, consistent accent-coloured glyphs for toolbar actions."""
    pm=QPixmap(size,size); pm.fill(Qt.transparent)
    painter=QPainter(pm); painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor(*accent))
    painter.setFont(QFont("DejaVu Sans",max(10,int(size*.62)),QFont.Medium))
    painter.drawText(pm.rect(),Qt.AlignCenter,symbol)
    painter.end()
    return QIcon(pm)

class PDFScrollArea(QScrollArea):
    """Route wheel events from both the viewport and the page widget consistently."""
    def __init__(self, viewer_instance, parent=None):
        super().__init__(parent)
        self.viewer = viewer_instance

    def wheelEvent(self, event):
        if self.viewer.handle_pdf_wheel(event):
            return
        super().wheelEvent(event)

    def viewportEvent(self, event):
        # QAbstractScrollArea routes viewport input through viewportEvent.
        # Intercepting here prevents the native scrollbar moving without the
        # page-transition logic being notified.
        if event.type() == QEvent.Wheel and self.viewer.handle_pdf_wheel(event):
            return True
        return super().viewportEvent(event)


class PDFPageLabel(QLabel):
    """PDF canvas with low-latency live preview for ink annotations."""
    def __init__(self, viewer_instance):
        super().__init__()
        self.viewer = viewer_instance
        self.setAlignment(Qt.AlignCenter)
        self.current_stroke = []
        self.current_stroke_view = []
        self.setMouseTracking(True)

    def wheelEvent(self, event):
        # Page image and viewport-margin wheel events share one implementation.
        if self.viewer.handle_pdf_wheel(event):
            return
        super().wheelEvent(event)

    def _preview_points(self):
        points = [(point.x(), point.y()) for point in self.current_stroke_view]
        assistant = getattr(self.viewer, "handwriting_assist", None)
        if self.viewer.app_settings.get("smart_ink", True) and assistant is not None:
            return assistant.smooth_points(points)
        return points

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.viewer.doc:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            hit = getattr(self.viewer, "search_highlight", None)
            if hit and hit.get("page") == self.viewer.current_page:
                try:
                    page = self.viewer.doc.load_page(self.viewer.current_page)
                    matrix = fitz.Matrix(self.viewer.zoom_factor, self.viewer.zoom_factor).prerotate(self.viewer.rotation)
                    bounds = page.rect * matrix
                    rect = fitz.Rect(hit["rect"]) * matrix
                    rect = fitz.Rect(rect.x0 - bounds.x0, rect.y0 - bounds.y0,
                                     rect.x1 - bounds.x0, rect.y1 - bounds.y0)
                    painter.setPen(QPen(QColor("#FFB300"), 2))
                    painter.setBrush(QColor(255, 193, 7, 52))
                    painter.drawRoundedRect(QRectF(rect.x0, rect.y0, rect.width, rect.height), 3.0, 3.0)
                except Exception:
                    pass

            if self.viewer.is_drawing and self.current_stroke_view and self.viewer.active_tool in ("pen", "highlight"):
                preview = self._preview_points()
                if preview:
                    r = self.viewer.selected_color.red()
                    g = self.viewer.selected_color.green()
                    b = self.viewer.selected_color.blue()
                    if self.viewer.active_tool == "highlight":
                        color = QColor(r, g, b, 100)
                        width = max(5.0, 14.0 * self.viewer.zoom_factor)
                    else:
                        color = QColor(r, g, b, 255)
                        width = max(1.0, 2.0 * self.viewer.zoom_factor)
                    painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                    if len(preview) == 1:
                        painter.drawPoint(QPointF(*preview[0]))
                    else:
                        path = QPainterPath(QPointF(*preview[0]))
                        for x, y in preview[1:]:
                            path.lineTo(QPointF(x, y))
                        painter.drawPath(path)
        finally:
            painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        if not self.viewer.doc or not self.viewer.active_tool or event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        pdf_pt = self.viewer.get_pdf_coords(event.position())
        page = self.viewer.doc.load_page(self.viewer.current_page)

        if self.viewer.active_tool in ("pen", "highlight"):
            self.current_stroke = [(pdf_pt.x, pdf_pt.y)]
            self.current_stroke_view = [QPointF(event.position())]
            self.viewer.is_drawing = True
            self.update()
            return

        if self.viewer.active_tool == "eraser":
            self.viewer._record_undo()
            self.viewer.erase_at_point(page, pdf_pt)
            self.update()
            return

        if self.viewer.active_tool == "text":
            t = TRANSLATIONS[self.viewer.current_lang]
            text, ok = QInputDialog.getText(self, t["add_text"], t["enter_text"])
            if not ok or not text:
                return
            font_size = int(self.viewer.font_size.value()) if hasattr(self.viewer, "font_size") else 12
            font_name = self.viewer.font_selector.currentData() if hasattr(self.viewer, "font_selector") else "helv"
            font_name = str(font_name or "helv")
            width = min(max(80.0, len(text) * font_size * 0.68), max(40.0, page.rect.width))
            height = min(max(30.0, font_size * 2.6), max(20.0, page.rect.height))
            x_max = max(page.rect.x0, page.rect.x1 - width)
            y_max = max(page.rect.y0, page.rect.y1 - height)
            x = min(max(page.rect.x0, pdf_pt.x), x_max)
            y = min(max(page.rect.y0, pdf_pt.y), y_max)
            rect = fitz.Rect(x, y, x + width, y + height)
            r, g, b = (self.viewer.selected_color.redF(),
                       self.viewer.selected_color.greenF(),
                       self.viewer.selected_color.blueF())
            try:
                self.viewer._record_undo()
                annot = page.add_freetext_annot(
                    rect, text, fontsize=font_size, fontname=font_name,
                    text_color=(r, g, b), fill_color=None, border_width=0,
                )
                annot.update()
                self.viewer.mark_document_modified()
                self.viewer.render_page()
            except Exception as exc:
                QMessageBox.warning(self.viewer, "Text annotation", str(exc))

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.viewer.doc or not self.viewer.active_tool:
            super().mouseMoveEvent(event)
            return
        if self.viewer.active_tool in ("pen", "highlight") and self.viewer.is_drawing:
            pdf_pt = self.viewer.get_pdf_coords(event.position())
            self.current_stroke.append((pdf_pt.x, pdf_pt.y))
            self.current_stroke_view.append(QPointF(event.position()))
            self.update()
        elif self.viewer.active_tool == "eraser" and (event.buttons() & Qt.LeftButton):
            pdf_pt = self.viewer.get_pdf_coords(event.position())
            page = self.viewer.doc.load_page(self.viewer.current_page)
            self.viewer.erase_at_point(page, pdf_pt)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            super().mouseReleaseEvent(event)
            return
        if self.viewer.is_drawing and len(self.current_stroke) > 1 and self.viewer.doc:
            page = self.viewer.doc.load_page(self.viewer.current_page)
            stroke = list(self.current_stroke)
            if self.viewer.app_settings.get("smart_ink", True):
                stroke = self.viewer.handwriting_assist.smooth_points(stroke)
            self.viewer.is_drawing = False
            self.current_stroke = []
            self.current_stroke_view = []
            self.update()
            r, g, b = (self.viewer.selected_color.redF(),
                       self.viewer.selected_color.greenF(),
                       self.viewer.selected_color.blueF())
            try:
                self.viewer._record_undo()
                annot = page.add_ink_annot([stroke])
                annot.set_colors(stroke=(r, g, b))
                if self.viewer.active_tool == "pen":
                    annot.set_border(width=2)
                elif self.viewer.active_tool == "highlight":
                    annot.set_border(width=14)
                    annot.set_opacity(0.35)
                annot.update()
                if self.viewer.app_settings.get("smart_ink", True):
                    profile = self.viewer.handwriting_assist.describe_style(stroke)
                    self.viewer.statusBar().showMessage(f"Smart Ink · {profile} stroke", 1800)
                self.viewer.mark_document_modified()
                self.viewer.render_page()
            except Exception as exc:
                QMessageBox.warning(self.viewer, "Ink annotation", str(exc))
        else:
            self.viewer.is_drawing = False
            self.current_stroke = []
            self.current_stroke_view = []
            self.update()


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


_ABOUT_LOCALIZED = {
 'en': {'about':'About','version':'Version','repository':'GitHub repository','license':'License','copy_version':'Copy version'},
 'fa': {'about':'درباره','version':'نسخه','repository':'مخزن گیت‌هاب','license':'مجوز','copy_version':'کپی نسخه'},
 'da': {'about':'Om','version':'Version','repository':'GitHub-projekt','license':'Licens','copy_version':'Kopiér version'},
 'de': {'about':'Über','version':'Version','repository':'GitHub-Repository','license':'Lizenz','copy_version':'Version kopieren'},
 'es': {'about':'Acerca de','version':'Versión','repository':'Repositorio de GitHub','license':'Licencia','copy_version':'Copiar versión'},
 'no': {'about':'Om','version':'Versjon','repository':'GitHub-repositorium','license':'Lisens','copy_version':'Kopier versjon'},
 'fi': {'about':'Tietoja','version':'Versio','repository':'GitHub-tietovarasto','license':'Lisenssi','copy_version':'Kopioi versio'},
 'sv': {'about':'Om','version':'Version','repository':'GitHub-arkiv','license':'Licens','copy_version':'Kopiera version'},
 'fr': {'about':'À propos','version':'Version','repository':'Dépôt GitHub','license':'Licence','copy_version':'Copier la version'},
 'el': {'about':'Πληροφορίες','version':'Έκδοση','repository':'Αποθετήριο GitHub','license':'Άδεια','copy_version':'Αντιγραφή έκδοσης'},
 'ar': {'about':'حول','version':'الإصدار','repository':'مستودع GitHub','license':'الترخيص','copy_version':'نسخ الإصدار'}
}
for _code, _values in _ABOUT_LOCALIZED.items():
    SETTINGS_I18N.setdefault(_code, dict(SETTINGS_I18N['en'])).update(_values)

# Settings labels are plain text; icons are supplied by the UI where needed.
for _code, _items in SETTINGS_I18N.items():
    for _key, _value in list(_items.items()):
        if isinstance(_value, str):
            _items[_key] = clean_label(_value)

def soft_tone(hex_color):
    h=hex_color.lstrip('#'); r,g,b=[int(h[i:i+2],16) for i in (0,2,4)]
    return '#%02X%02X%02X'%((r+255*3)//4,(g+255*3)//4,(b+255*3)//4)


# Appearance mode labels for the existing localized Settings screen.
for _code, _label in {
    "en":"Appearance mode","fa":"حالت ظاهری","de":"Darstellungsmodus",
    "es":"Modo de apariencia","fr":"Mode d’apparence","da":"Udseende",
    "no":"Utseende","fi":"Ulkoasu","sv":"Utseende","el":"Εμφάνιση","ar":"وضع المظهر"
}.items():
    SETTINGS_I18N.get(_code, SETTINGS_I18N["en"])["appearance_mode"] = _label

class SettingsDialog(QDialog):
    settings_changed=Signal(dict)
    def __init__(self,viewer):
        super().__init__(viewer); self.viewer=viewer; self.settings=viewer.app_settings.copy(); self.lang=viewer.current_lang if viewer.current_lang in SETTINGS_I18N else 'en'; self.setMinimumSize(980,680); self.resize(1120,780); self.setModal(True); self._build_ui(); self._retranslate(); self._fade_in()
    def _build_ui(self):
        root=QVBoxLayout(self); root.setContentsMargins(18,18,18,18); root.setSpacing(14)
        header=QFrame(); header.setObjectName('settingsHeader'); hl=QHBoxLayout(header); hl.setContentsMargins(20,16,20,16); ic=QLabel(); ic.setPixmap(make_app_icon(58).pixmap(58,58)); hl.addWidget(ic); tb=QVBoxLayout(); self.title=QLabel(); self.title.setObjectName('settingsTitle'); self.subtitle=QLabel(); self.subtitle.setObjectName('settingsSubtitle'); self.subtitle.setWordWrap(True); tb.addWidget(self.title); tb.addWidget(self.subtitle); hl.addLayout(tb,1); self.live_chip=QLabel(); self.live_chip.setObjectName('settingsChip'); hl.addWidget(self.live_chip); root.addWidget(header)
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
        f,fl=card_frame(title,sub); lay.addWidget(f); self.card_titles.append(f.findChild(QLabel,'settingsCardTitle')); return fl
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
        self.theme.addItems(list(COLOR_THEMES))
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
        self.about_credit=QLabel(ABOUT_ATTRIBUTION)
        self.about_credit.setWordWrap(True)
        self.about_credit.setTextInteractionFlags(Qt.TextSelectableByMouse)
        f.addWidget(self.about_credit)
        self.about_repo=QLabel()
        self.about_repo.setOpenExternalLinks(True)
        f.addWidget(self.about_repo)
        self.about_license=QLabel()
        f.addWidget(self.about_license)
        self.about_copy_version=QPushButton()
        self.about_copy_version.clicked.connect(lambda: QApplication.clipboard().setText(APP_VERSION))
        f.addWidget(self.about_copy_version)
        l.addStretch()
        self.stack.addWidget(w)
    def _retranslate(self):
        self.t=SETTINGS_I18N.get(self.lang,SETTINGS_I18N['en']); self.title.setText(self.t['title']); self.subtitle.setText(self.t['subtitle']); self.live_chip.setText(self.t.get('live','● Live preview')); self.nav.clear(); self.nav.addItems([self.t['overview'],self.t['appearance'],self.t['eye'],self.t['document'],self.t['performance'],self.t['audio'],self.t['shortcuts'],self.t['about']]);
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
        self.appearance_mode.setItemText(0,_appearance_options[0]); self.appearance_mode.setItemText(1,_appearance_options[1]); self.about_version.setText(f"{self.t.get('version','Version')} {APP_VERSION}"); self.about_credit.setText(ABOUT_ATTRIBUTION); self.about_repo.setText(f"<a href='https://github.com/Parin-M/Parin-PDF-Viewer'>{self.t.get('repository','GitHub repository')}</a>"); self.about_license.setText(f"{self.t.get('license','License')}: GPL-3.0"); self.about_copy_version.setText(self.t.get('copy_version','Copy version')); self.reset_btn.setText(self.t['reset']); self.buttons.button(QDialogButtonBox.Cancel).setText(self.t['cancel']); self.buttons.button(QDialogButtonBox.Apply).setText(self.t['apply']); self.buttons.button(QDialogButtonBox.Ok).setText(self.t['ok']); codes=['en','fa','da','de','es','no','fi','sv','fr','el','ar']; self.lang_combo.blockSignals(True); self.lang_combo.setCurrentIndex(codes.index(self.lang)); self.lang_combo.blockSignals(False); self.nav.setCurrentRow(min(self.nav.currentRow(),7)); self._preview_style()
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
        accent=THEME_ACCENTS.get(theme,(58,141,255)); ah="#%02X%02X%02X"%accent
        panel="#172235" if dark else "#FFFFFF"
        surface="#111827" if dark else "#F7F9FC"
        text="#E5EDF7" if dark else "#172B49"
        muted="#A8B7CA" if dark else "#66778E"
        border="#30425A" if dark else "#D9E3EF"
        selected="#244361" if dark else ah
        self.setStyleSheet(_theme_stylesheet(theme,"dark" if dark else "light")+f'''
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


NAVIGATION_I18N = {
    "en": {"dock":"Navigation","outline":"Outline","pages":"Pages","page":"Page {n}","nav_action":"Navigation Panel","recent":"Open Recent","no_recent":"No recent files","clear_recent":"Clear Recent Files","no_outline":"No outline in this PDF"},
    "fa": {"dock":"ناوبری","outline":"فهرست","pages":"صفحات","page":"صفحهٔ {n}","nav_action":"پنل ناوبری","recent":"فایل‌های اخیر","no_recent":"فایل اخیری وجود ندارد","clear_recent":"پاک‌کردن فهرست فایل‌های اخیر","no_outline":"این PDF فهرست داخلی ندارد"},
    "de": {"dock":"Navigation","outline":"Gliederung","pages":"Seiten","page":"Seite {n}","nav_action":"Navigationsbereich","recent":"Zuletzt geöffnet","no_recent":"Keine zuletzt verwendeten Dateien","clear_recent":"Liste leeren","no_outline":"Keine Gliederung in dieser PDF"},
    "es": {"dock":"Navegación","outline":"Esquema","pages":"Páginas","page":"Página {n}","nav_action":"Panel de navegación","recent":"Archivos recientes","no_recent":"No hay archivos recientes","clear_recent":"Borrar recientes","no_outline":"Este PDF no tiene índice"},
    "fr": {"dock":"Navigation","outline":"Sommaire","pages":"Pages","page":"Page {n}","nav_action":"Panneau de navigation","recent":"Fichiers récents","no_recent":"Aucun fichier récent","clear_recent":"Effacer les récents","no_outline":"Aucun sommaire dans ce PDF"},
    "da": {"dock":"Navigation","outline":"Oversigt","pages":"Sider","page":"Side {n}","nav_action":"Navigationspanel","recent":"Seneste filer","no_recent":"Ingen seneste filer","clear_recent":"Ryd seneste","no_outline":"Ingen oversigt i PDF-filen"},
    "no": {"dock":"Navigasjon","outline":"Disposisjon","pages":"Sider","page":"Side {n}","nav_action":"Navigasjonspanel","recent":"Nylige filer","no_recent":"Ingen nylige filer","clear_recent":"Tøm nylige","no_outline":"Ingen disposisjon i PDF-filen"},
    "fi": {"dock":"Siirtyminen","outline":"Jäsennys","pages":"Sivut","page":"Sivu {n}","nav_action":"Siirtymispaneeli","recent":"Viimeisimmät tiedostot","no_recent":"Ei viimeisimpiä tiedostoja","clear_recent":"Tyhjennä viimeisimmät","no_outline":"PDF ei sisällä jäsennystä"},
    "sv": {"dock":"Navigering","outline":"Disposition","pages":"Sidor","page":"Sida {n}","nav_action":"Navigeringspanel","recent":"Senaste filer","no_recent":"Inga senaste filer","clear_recent":"Rensa senaste","no_outline":"Ingen disposition i PDF-filen"},
    "el": {"dock":"Πλοήγηση","outline":"Διάρθρωση","pages":"Σελίδες","page":"Σελίδα {n}","nav_action":"Πίνακας πλοήγησης","recent":"Πρόσφατα αρχεία","no_recent":"Δεν υπάρχουν πρόσφατα αρχεία","clear_recent":"Εκκαθάριση πρόσφατων","no_outline":"Το PDF δεν έχει διάρθρωση"},
    "ar": {"dock":"التنقل","outline":"المخطط","pages":"الصفحات","page":"الصفحة {n}","nav_action":"لوحة التنقل","recent":"الملفات الأخيرة","no_recent":"لا توجد ملفات حديثة","clear_recent":"مسح الملفات الأخيرة","no_outline":"لا يوجد مخطط في هذا الـ PDF"},
}



class PageOrganizerDialog(QDialog):
    """Transactional page organizer with drag/drop reorder, rotation, removal, and extraction."""
    def __init__(self, viewer):
        super().__init__(viewer)
        self.viewer = viewer
        self.rotations = {}
        self.setWindowTitle("Manage PDF pages")
        self.resize(520, 620)
        self.setModal(True)
        root = QVBoxLayout(self)
        intro = QLabel("Drag pages to reorder them. Rotate, remove, or extract selected pages; changes apply only when you choose Apply.")
        intro.setWordWrap(True)
        root.addWidget(intro)
        self.pages = QListWidget()
        self.pages.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.pages.setDragEnabled(True)
        self.pages.setAcceptDrops(True)
        self.pages.setDropIndicatorShown(True)
        self.pages.setDragDropMode(QAbstractItemView.InternalMove)
        self.pages.setDefaultDropAction(Qt.MoveAction)
        for index in range(viewer.doc.page_count):
            item = QListWidgetItem(f"Page {index + 1}")
            item.setData(Qt.UserRole, index)
            self.pages.addItem(item)
        self.pages.setCurrentRow(viewer.current_page)
        root.addWidget(self.pages, 1)
        controls = QHBoxLayout()
        self.rotate_button = QPushButton("Rotate selected +90°")
        self.remove_button = QPushButton("Remove selected")
        self.extract_button = QPushButton("Extract selected…")
        controls.addWidget(self.rotate_button)
        controls.addWidget(self.remove_button)
        root.addLayout(controls)
        root.addWidget(self.extract_button)
        self.rotate_button.clicked.connect(self.rotate_selected)
        self.remove_button.clicked.connect(self.remove_selected)
        self.extract_button.clicked.connect(self.extract_selected)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        self.buttons.button(QDialogButtonBox.Apply).setText("Apply changes")
        self.buttons.rejected.connect(self.reject)
        self.buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_changes)
        root.addWidget(self.buttons)

    def rotate_selected(self):
        for item in self.pages.selectedItems():
            page_index = item.data(Qt.UserRole)
            self.rotations[page_index] = (self.rotations.get(page_index, 0) + 90) % 360
            delta = self.rotations[page_index]
            item.setText(f"Page {page_index + 1}" + (f" · rotate +{delta}°" if delta else ""))

    def remove_selected(self):
        rows = sorted((self.pages.row(item) for item in self.pages.selectedItems()), reverse=True)
        for row in rows:
            self.pages.takeItem(row)

    def extract_selected(self):
        selected = {item.data(Qt.UserRole) for item in self.pages.selectedItems()}
        ordered = [self.pages.item(row).data(Qt.UserRole) for row in range(self.pages.count())
                   if self.pages.item(row).data(Qt.UserRole) in selected]
        if not ordered:
            QMessageBox.information(self, "Extract pages", "Select at least one page first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Extract pages to PDF", "extracted-pages.pdf", "PDF files (*.pdf)")
        if not path:
            return
        path = ensure_pdf_extension(path)
        if self.viewer.file_path and same_path(path, self.viewer.file_path):
            QMessageBox.warning(self, "Extract pages", "Choose a different file name so the open PDF is not overwritten.")
            return
        output = None
        try:
            output = fitz.open()
            for page_index in ordered:
                output.insert_pdf(self.viewer.doc, from_page=page_index, to_page=page_index)
            output.save(path)
            QMessageBox.information(self, "Extract pages", f"Extracted {len(ordered)} page(s) to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Extract pages failed", str(exc))
        finally:
            if output is not None:
                output.close()

    def apply_changes(self):
        order = [self.pages.item(row).data(Qt.UserRole) for row in range(self.pages.count())]
        if not order:
            QMessageBox.warning(self, "Manage PDF pages", "A PDF must contain at least one page.")
            return
        if len(order) != len(set(order)):
            QMessageBox.warning(self, "Manage PDF pages", "The page list is invalid; no changes were applied.")
            return
        original_order = list(range(self.viewer.doc.page_count))
        included = set(order)
        has_rotation = any(delta and page_index in included for page_index, delta in self.rotations.items())
        if order == original_order and not has_rotation:
            self.accept()
            return
        self.viewer._record_undo()
        old_current = self.viewer.current_page
        try:
            for page_index, delta in self.rotations.items():
                if delta and page_index in included:
                    page = self.viewer.doc.load_page(page_index)
                    page.set_rotation((page.rotation + delta) % 360)
            self.viewer.doc.select(order)
            self.viewer.current_page = order.index(old_current) if old_current in order else min(old_current, len(order) - 1)
            self.viewer._after_document_structure_change()
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Could not update pages", str(exc))
            self.viewer.undo_edit()


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
        self._open_render_generation = 0
        self._wheel_transition_generation = 0
        self.is_drawing = False
        self.large_file_mode = False

        self.settings_store = QSettings('Parin', 'ParinPDFViewer')
        self.recent_files = normalize_recent_files(self.settings_store.value('recent_files', []))
        self._last_session_file = self.settings_store.value('last_file', '', type=str)
        self._last_session_page = self.settings_store.value('last_page', 1, type=int)
        try:
            self._last_session_zoom = float(self.settings_store.value('last_zoom', 1.0))
        except (TypeError, ValueError):
            self._last_session_zoom = 1.0
        self._last_session_fit_mode = self.settings_store.value('last_fit_mode', 'width', type=str)
        self._thumbnail_cache = OrderedDict()
        self._undo_stack = []
        self._redo_stack = []
        self._history_max_bytes = 16 * 1024 * 1024
        self._undo_disabled_for_size = False
        self._last_search_query = ''
        self._last_search_page = -1
        self._last_search_rect_index = -1
        self.search_highlight = None
        self._document_password = ''
        self._document_encrypted = False
        self._document_dirty = False
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
            'appearance_mode': str(self.settings_store.value('appearance_mode', 'light', type=str)).lower(),
            'accent': self.settings_store.value('accent', 'Theme default'),
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
            'animations': self.settings_store.value('animations', True, type=bool),
            'smart_ink': self.settings_store.value('smart_ink', True, type=bool)
        }

        legacy_theme = clean_label(str(self.app_settings.get('theme','Arctic Glass')))
        self.app_settings['theme'] = legacy_theme if legacy_theme in COLOR_THEMES else 'Arctic Glass'
        self.app_settings['appearance_mode'] = 'dark' if str(self.app_settings.get('appearance_mode','light')).lower() == 'dark' else 'light'

        self.handwriting_assist = SmartInkAssistant()
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
        self.setAcceptDrops(True)
        self.init_ui()
        self.apply_language(self.current_lang)
        self.apply_app_settings()
        self._install_shortcuts()
        if self.app_settings.get('remember_last', True) and self._last_session_file and os.path.isfile(self._last_session_file):
            QTimer.singleShot(0, lambda path=self._last_session_file: self.open_file(path, restore_session=True))

    def _install_shortcuts(self):
        for text,key,slot in [
            ("Open","Ctrl+O",self.open_file),("Save","Ctrl+S",self.save_file),
            ("Search","Ctrl+F",self.search_pdf),("Zoom in","Ctrl++",self.zoom_in),
            ("Zoom out","Ctrl+-",self.zoom_out),("Fit width","Ctrl+W",self.fit_width),
            ("Fit page","Ctrl+Shift+W",self.fit_page),("Fullscreen","F11",self.toggle_fullscreen),
            ("Previous","Left",self.prev_page),("Next","Right",self.next_page),
            ("Reset zoom","Ctrl+0",self.reset_zoom)]:
            action=QAction(text,self,shortcut=key,triggered=slot)
            self.addAction(action)

    def open_settings(self):
        dlg=SettingsDialog(self)
        dlg.exec()

    def _style_for_theme(self):
        return _theme_stylesheet(self.app_settings.get('theme','Arctic Glass'), self.app_settings.get('appearance_mode','light'))
    def apply_app_settings(self):
        self.settings_store.setValue('settings',str(self.app_settings))
        for k,v in self.app_settings.items():
            self.settings_store.setValue(k,v)
        dark = str(self.app_settings.get("appearance_mode","light")).lower() == "dark"
        base = self._style_for_theme()
        accent = THEME_ACCENTS.get(self.app_settings.get('theme','Arctic Glass'),(58,141,255))
        ah = '#%02X%02X%02X' % accent
        header_bg = "#0B1423" if dark else "#10243F"
        header_border = "#23354D" if dark else "#1C3B60"
        tool_bg = "#131F30" if dark else "#EEF3F9"
        panel_bg = "#182539" if dark else "#FFFFFF"
        border = "#2C405B" if dark else "#D9E3EF"
        muted = "#A8B7CA" if dark else "#73839A"
        canvas = "#0D1522" if dark else "#EDF2F8"
        search_bg = "#111B2A" if dark else "#F8FAFD"
        status_bg = "#111B2A" if dark else "#FFFFFF"
        dialog_bg = "#101827" if dark else "#F8FAFD"
        title_fg = "#F4F7FC" if dark else "#243650"
        active_fill = "#243D5B" if dark else soft_tone(ah)
        active_text = "#FFFFFF" if dark else "#142B4A"
        common=f'''QWidget#app_header{{background:{header_bg};border-bottom:1px solid {header_border};}}
QLabel#brand_title{{font-size:22px;font-weight:800;color:#FFFFFF;letter-spacing:0.2px;}}
QLabel#brand_subtitle{{font-size:10px;color:#B8C7DA;}}
QFrame#tool_area{{background:{tool_bg};border-bottom:1px solid {border};}}
QFrame#tool_group{{background:{panel_bg};border:1px solid {border};border-radius:13px;}}
QLabel#group_label{{font-size:9px;font-weight:800;color:{muted};padding:0 6px;letter-spacing:0.6px;}}
QLineEdit#quick_search{{min-height:38px;background:{search_bg};color:{'#E5EDF7' if dark else '#172B49'};border:1px solid {border};border-radius:11px;padding:7px 12px;selection-background-color:{ah};selection-color:#FFFFFF;}}
QLineEdit#quick_search:focus{{background:{panel_bg};border:2px solid {ah};}}
QStatusBar{{background:{status_bg};color:{muted};border-top:1px solid {border};}}
QStatusBar::item{{border:none;}}
QLabel#status_page,QLabel#status_zoom,QLabel#status_dirty{{color:{muted};padding:2px 8px;font-size:9pt;}}
QLabel#status_dirty[dirty="true"]{{color:{'#FFB4A9' if dark else '#B5473C'};font-weight:700;}}
QPushButton:hover{{border-color:{ah};}}
QPushButton:checked{{background:{active_fill};border:2px solid {ah};color:{active_text};}}
QFrame#app_header QPushButton{{background:rgba(255,255,255,0.08);color:#F5F8FC;border:1px solid #35506F;border-radius:10px;padding:8px 12px;font-weight:600;}}
QFrame#app_header QPushButton:hover{{background:#23466F;border-color:{ah};}}
QFrame#app_header QPushButton:pressed{{background:#1B395E;border-color:{ah};}}
QFrame#app_header QPushButton:disabled{{background:rgba(255,255,255,0.04);color:#71849D;border-color:#2A405B;}}
QFrame#page_canvas{{background:{canvas};border:1px solid {border};border-radius:16px;}}
QScrollArea#document_scroll{{background:{canvas};border:none;}}
QScrollArea#document_scroll QWidget#qt_scrollarea_viewport{{background:{canvas};border:none;}}
QScrollArea#document_scroll QLabel#pdf_page{{background:transparent;}}
QWidget#welcome_page{{background:{canvas};}}
QFrame#welcome_hero{{background:{panel_bg};border:1px solid {border};border-radius:22px;}}
QLabel#welcome_title{{font-size:27px;font-weight:800;color:{title_fg};}}
QLabel#welcome_subtitle{{font-size:12px;color:{muted};}}
QLabel#welcome_section_title{{font-size:17px;font-weight:800;color:{title_fg};}}
QLabel#welcome_hint{{font-size:10pt;color:{muted};}}
QToolButton#recent_file_card{{background:{panel_bg};color:{'#E5EDF7' if dark else '#23334D'};border:1px solid {border};border-radius:14px;padding:12px;font-weight:600;text-align:center;}}
QToolButton#recent_file_card:hover{{background:{'#203650' if dark else '#F4F8FD'};border:1px solid {ah};}}
QToolButton#recent_file_card:pressed{{background:{'#253D5B' if dark else '#EAF2FC'};}}
QPushButton#welcome_clear_button{{background:transparent;color:{ah};border:1px solid transparent;padding:6px 10px;}}
QPushButton#welcome_clear_button:hover{{background:{tool_bg};border-color:{border};}}
QPushButton#welcome_open_button{{background:{ah};color:#FFFFFF;border:1px solid {ah};border-radius:12px;padding:10px 16px;font-weight:700;}}
QPushButton#welcome_open_button:hover{{background:{ah};border-color:{ah};}}
QLabel#welcome_empty{{color:{muted};padding:20px;border:1px dashed {border};border-radius:12px;}}
QDockWidget{{color:{'#E5EDF7' if dark else '#23334D'};font-weight:700;}}
QDockWidget::title{{background:{tool_bg};padding:9px 12px;border-bottom:1px solid {border};}}
QDialog{{background:{dialog_bg};}}
'''
        self.setStyleSheet(base+common)
        if hasattr(self,'page_label'):
            if self.app_settings.get('page_shadow',True):
                shadow=QGraphicsDropShadowEffect(self.page_label); shadow.setBlurRadius(26); shadow.setOffset(0,4); shadow.setColor(QColor(0,0,0,100 if dark else 52)); self.page_label.setGraphicsEffect(shadow)
            else:
                self.page_label.setGraphicsEffect(None)
        self._refresh_welcome_page()
        self._update_page_indicator()
        self.statusBar().setVisible(bool(self.app_settings.get('status_bar',True)))
        if hasattr(self,'btn_smart_ink'):
            self.btn_smart_ink.blockSignals(True); self.btn_smart_ink.setChecked(bool(self.app_settings.get('smart_ink',True))); self.btn_smart_ink.blockSignals(False)
        self.audio_output.setVolume(max(0,min(100,int(self.app_settings.get('volume',50))))/100)
        compact=bool(self.app_settings.get('compact_toolbar',False)); large=bool(self.app_settings.get('large_toolbar',True))
        names=['btn_open','btn_save','btn_print_opt','btn_pen','btn_highlight','btn_eraser','btn_add_text','btn_color','btn_fit_width','btn_fit_page','btn_reset_zoom','btn_prev','btn_next','btn_rotate_left','btn_rotate_right','btn_fullscreen','btn_lofi','btn_more','btn_navigation','btn_smart_ink','btn_settings','btn_lang']
        for b in [getattr(self,n,None) for n in names]:
            if b:
                b.setMinimumHeight(32 if compact else (44 if large else 38)); b.setIconSize(QSize(24,24))
                current=clean_label(b.text()); glyph='•'
                for key,val in ICON_GLYPHS.items():
                    if current.lower().startswith(key.lower()): glyph=val; break
                b.setIcon(make_action_icon(glyph,24,accent)); b.setIconSize(QSize(24,24))
        self._update_blue_filter()
        if hasattr(self, "scroll_area"):
            alignment = Qt.AlignTop | (Qt.AlignHCenter if self.app_settings.get("center_page", True) else Qt.AlignLeft)
            self.scroll_area.setAlignment(alignment)
        if hasattr(self, "btn_lofi"):
            audio_enabled = bool(self.app_settings.get("audio_enabled", True))
            self.btn_lofi.setEnabled(audio_enabled)
            if not audio_enabled and self.is_lofi_playing:
                self.player.stop()
                self.is_lofi_playing = False
                self.btn_lofi.setText(TRANSLATIONS[self.current_lang]["lofi"])
        if self.doc:
            self.rotation = {"0°": 0, "90°": 90, "180°": 180, "270°": 270}.get(
                self.app_settings.get("rotation", "0°"), 0
            )
            fit = self.app_settings.get("fit_mode", "Fit Width")
            self.fit_mode = {"Fit Width": "width", "Fit Page": "page", "100%": None}.get(fit, "width")
            if self.fit_mode == "width":
                self._set_fit_width()
            elif self.fit_mode == "page":
                self._set_fit_page()
            else:
                self.zoom_factor = 1.0
                self.render_page()

    def init_ui(self):
        central_widget=QWidget(self); self.setCentralWidget(central_widget)
        self.main_layout=QVBoxLayout(central_widget); self.main_layout.setContentsMargins(0,0,0,0); self.main_layout.setSpacing(0)

        # Header / brand row
        self.header=QFrame(); self.header.setObjectName("app_header"); self.header.setMinimumHeight(76); hl=QHBoxLayout(self.header); hl.setContentsMargins(20,12,20,12); hl.setSpacing(12)
        self.app_icon=QLabel(); self.app_icon.setPixmap(make_app_icon(46).pixmap(46,46)); hl.addWidget(self.app_icon)
        brand=QVBoxLayout(); self.brand_title=QLabel("Parin"); self.brand_title.setObjectName("brand_title"); self.brand_subtitle=QLabel("Fast • Focused • PDF workspace"); self.brand_subtitle.setObjectName("brand_subtitle"); brand.addWidget(self.brand_title); brand.addWidget(self.brand_subtitle); hl.addLayout(brand)
        hl.addStretch()
        self.quick_search=QLineEdit(); self.quick_search.setObjectName("quick_search"); self.quick_search.setPlaceholderText("Search inside PDF…"); self.quick_search.setClearButtonEnabled(True); self.quick_search.setMinimumWidth(220); self.quick_search.returnPressed.connect(self.search_from_bar); hl.addWidget(self.quick_search)
        self.btn_navigation=self.create_btn("Pages", self.toggle_navigation_panel, icon_key="More"); self.btn_navigation.setMinimumWidth(72); self.btn_navigation.setToolTip("Toggle the navigation panel"); hl.addWidget(self.btn_navigation)
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
        self.tool_area=QFrame(); self.tool_area.setObjectName("tool_area"); tl=QVBoxLayout(self.tool_area); tl.setContentsMargins(10,7,10,7); tl.setSpacing(7)
        row1=QHBoxLayout(); row1.setSpacing(6); row2=QHBoxLayout(); row2.setSpacing(6); self.group_labels={}
        def add_group(row,title,buttons):
            box=QFrame(); box.setObjectName("tool_group"); gl=QHBoxLayout(box); gl.setContentsMargins(6,5,6,5); gl.setSpacing(5)
            lab=QLabel(title); lab.setObjectName("group_label"); gl.addWidget(lab); self.group_labels[title]=lab
            for b in buttons: gl.addWidget(b)
            row.addWidget(box)
        self.btn_open=self.create_btn("Open PDF",self.open_file,icon_key="Open"); self.btn_save=self.create_btn("Save PDF",self.save_file,icon_key="Save"); self.btn_print_opt=self.create_btn("Print",self.print_document,icon_key="Print")
        self.btn_pen=self.create_btn("Pen",lambda:self.toggle_tool('pen'),True,"Pen"); self.btn_highlight=self.create_btn("Highlight",lambda:self.toggle_tool('highlight'),True,"Highlight"); self.btn_eraser=self.create_btn("Eraser",lambda:self.toggle_tool('eraser'),True,"Eraser"); self.btn_add_text=self.create_btn("Text",lambda:self.toggle_tool('text'),True,"Text")
        self.font_selector=QComboBox(); self.font_selector.addItem("Sans serif","helv"); self.font_selector.addItem("Serif","tiro"); self.font_selector.addItem("Monospace","cour"); self.font_selector.setMinimumWidth(100); self.font_selector.setMaximumWidth(124); self.font_selector.setToolTip("Font used for the next text annotation")
        self.font_size=QSpinBox(); self.font_size.setRange(6,72); self.font_size.setValue(12); self.font_size.setSuffix(" pt"); self.font_size.setFixedWidth(76); self.font_size.setToolTip("Font size used for the next text annotation")
        self.btn_color=self.create_btn("Color",self.choose_color,icon_key="Color"); self.update_color_btn_style()
        self.btn_smart_ink=self.create_btn("Smart Ink",self.toggle_smart_ink,True,"Pen"); self.btn_smart_ink.setChecked(bool(self.app_settings.get("smart_ink",True))); self.btn_smart_ink.setToolTip("Local adaptive ink smoothing; no cloud or model download required.")
        self.btn_zoom_out=self.create_btn("−",self.zoom_out); self.btn_zoom_in=self.create_btn("+",self.zoom_in); self.btn_fit_width=self.create_btn("Fit Width",self.fit_width,icon_key="Fit"); self.btn_fit_page=self.create_btn("Fit Page",self.fit_page,icon_key="Fit"); self.btn_reset_zoom=self.create_btn("100%",self.reset_zoom)
        self.btn_prev=self.create_btn("Prev",self.prev_page,icon_key="Prev"); self.btn_next=self.create_btn("Next",self.next_page,icon_key="Next"); self.lbl_page=QLabel("Page:"); self.spin_page=QSpinBox(); self.spin_page.setMinimum(1); self.spin_page.setFixedWidth(82); self.spin_page.valueChanged.connect(self.go_to_page)
        self.btn_rotate_left=self.create_btn("Rotate",lambda:self.rotate(-90),icon_key="Rotate"); self.btn_rotate_right=self.create_btn("Rotate",lambda:self.rotate(90),icon_key="Rotate"); self.btn_fullscreen=self.create_btn("Fullscreen",self.toggle_fullscreen,icon_key="Fullscreen")
        self.btn_lofi=self.create_btn("Lo-Fi",self.toggle_lofi,icon_key="Lo-Fi")
        add_group(row1,"FILE",[self.btn_open,self.btn_save,self.btn_print_opt])
        add_group(row1,"ANNOTATE",[self.btn_pen,self.btn_highlight,self.btn_eraser,self.btn_add_text,self.font_selector,self.font_size,self.btn_color])
        row1.addStretch(); tl.addLayout(row1)
        add_group(row2,"VIEW",[self.btn_zoom_out,self.btn_zoom_in,self.btn_fit_width,self.btn_fit_page,self.btn_reset_zoom])
        add_group(row2,"PAGE",[self.btn_prev,self.lbl_page,self.spin_page,self.btn_next])
        add_group(row2,"TOOLS",[self.btn_rotate_left,self.btn_rotate_right,self.btn_smart_ink,self.btn_fullscreen,self.btn_lofi])
        self.btn_more=self.create_btn("More",None,icon_key="More"); more=QMenu(self)
        self.more_actions=[]
        for text,slot,ikey in [("Search PDF",self.search_pdf,"Search"),("Remove Password",self.remove_password,"Remove"),("Set Password",self.add_password,"Set"),("Settings",self.open_settings,"Settings")]:
            a=QAction(text,self); a.setIcon(make_action_icon(ICON_GLYPHS.get(ikey,"•"),22,THEME_ACCENTS.get(self.app_settings.get("theme","Arctic Glass"),(58,141,255)))); a.triggered.connect(slot); more.addAction(a); self.more_actions.append(a)
        more.addSeparator()
        self.navigation_action = more.addAction(self._nav_text("nav_action"))
        self.navigation_action.triggered.connect(self.toggle_navigation_panel)
        self.recent_menu = more.addMenu(self._nav_text("recent"))
        self.recent_menu.aboutToShow.connect(self._refresh_recent_menu)
        self.page_management_menu = more.addMenu("Page management")
        self.page_actions = {}
        for key, text, slot in [
            ("organize", "Manage pages…", self.open_page_organizer),
            ("insert", "Insert pages from PDF…", self.insert_pages_from_pdf),
        ]:
            action = QAction(text, self)
            action.triggered.connect(slot)
            self.page_management_menu.addAction(action)
            self.page_actions[key] = action
        more.addSeparator()
        self.undo_action = more.addAction("Undo", self.undo_edit)
        self.undo_action.setShortcut("Ctrl+Z")
        self.addAction(self.undo_action)
        self.redo_action = more.addAction("Redo", self.redo_edit)
        self.redo_action.setShortcut("Ctrl+Y")
        self.addAction(self.redo_action)
        self.btn_more.setMenu(more); row2.addWidget(self.btn_more); row2.addStretch(); tl.addLayout(row2)
        self.main_layout.addWidget(self.tool_area)

        self.workspace_stack=QStackedWidget(self)
        self.welcome_page=QWidget()
        self._build_welcome_page()
        self.scroll_area=PDFScrollArea(self, self)
        self.scroll_area.setObjectName("document_scroll")
        # The PDF canvas must keep its rendered pixel size. With widgetResizable
        # enabled, QScrollArea can resize the QLabel independently of its pixmap;
        # that can clip the page and offsets the live-ink overlay coordinates.
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.page_label=PDFPageLabel(self)
        self.page_label.setObjectName("pdf_page")
        self.page_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.page_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.scroll_area.setWidget(self.page_label)
        self.workspace_stack.addWidget(self.welcome_page)
        self.workspace_stack.addWidget(self.scroll_area)
        self.workspace_stack.setCurrentWidget(self.welcome_page)
        self.main_layout.addWidget(self.workspace_stack,1)
        self.blue_overlay=QFrame(self.scroll_area.viewport())
        self.blue_overlay.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        self.blue_overlay.setGeometry(self.scroll_area.viewport().rect())
        self.blue_overlay.hide()
        self.blue_overlay.raise_()
        self.statusBar().showMessage("Ready • Open a PDF to begin")
        self.status_page=QLabel("No PDF open"); self.status_page.setObjectName("status_page")
        self.status_zoom=QLabel("100%"); self.status_zoom.setObjectName("status_zoom")
        self.status_dirty=QLabel("Ready"); self.status_dirty.setObjectName("status_dirty")
        self.statusBar().addPermanentWidget(self.status_page)
        self.statusBar().addPermanentWidget(self.status_zoom)
        self.statusBar().addPermanentWidget(self.status_dirty)
        self.setWindowIcon(make_app_icon(64))
        self._build_navigation_dock()

    def _build_welcome_page(self):
        page_layout=QVBoxLayout(self.welcome_page)
        page_layout.setContentsMargins(30,26,30,24)
        page_layout.setSpacing(18)
        hero=QFrame(self.welcome_page)
        hero.setObjectName("welcome_hero")
        hero_layout=QHBoxLayout(hero)
        hero_layout.setContentsMargins(24,22,24,22)
        hero_layout.setSpacing(18)
        copy=QVBoxLayout()
        copy.setSpacing(8)
        self.welcome_title=QLabel()
        self.welcome_title.setObjectName("welcome_title")
        self.welcome_subtitle=QLabel()
        self.welcome_subtitle.setObjectName("welcome_subtitle")
        self.welcome_subtitle.setWordWrap(True)
        self.welcome_hint=QLabel()
        self.welcome_hint.setObjectName("welcome_hint")
        copy.addWidget(self.welcome_title)
        copy.addWidget(self.welcome_subtitle)
        copy.addWidget(self.welcome_hint)
        hero_layout.addLayout(copy,1)
        self.welcome_open_button=QPushButton()
        self.welcome_open_button.setObjectName("welcome_open_button")
        self.welcome_open_button.setMinimumSize(158,48)
        self.welcome_open_button.setCursor(Qt.PointingHandCursor)
        self.welcome_open_button.setIcon(make_action_icon("▱",24,THEME_ACCENTS.get(self.app_settings.get("theme","Arctic Glass"),(58,141,255))))
        self.welcome_open_button.setIconSize(QSize(22,22))
        self.welcome_open_button.clicked.connect(self.open_file)
        hero_layout.addWidget(self.welcome_open_button,0,Qt.AlignVCenter)
        page_layout.addWidget(hero)

        recent_header=QHBoxLayout()
        self.welcome_recent_title=QLabel()
        self.welcome_recent_title.setObjectName("welcome_section_title")
        recent_header.addWidget(self.welcome_recent_title)
        recent_header.addStretch()
        self.welcome_clear_button=QPushButton()
        self.welcome_clear_button.setObjectName("welcome_clear_button")
        self.welcome_clear_button.setCursor(Qt.PointingHandCursor)
        self.welcome_clear_button.clicked.connect(self.clear_recent_files)
        recent_header.addWidget(self.welcome_clear_button)
        page_layout.addLayout(recent_header)

        self.recent_grid_host=QWidget(self.welcome_page)
        self.recent_grid=QGridLayout(self.recent_grid_host)
        self.recent_grid.setContentsMargins(0,0,0,0)
        self.recent_grid.setHorizontalSpacing(14)
        self.recent_grid.setVerticalSpacing(14)
        for col in range(4):
            self.recent_grid.setColumnStretch(col,1)
        page_layout.addWidget(self.recent_grid_host)
        self.welcome_empty=QLabel()
        self.welcome_empty.setObjectName("welcome_empty")
        self.welcome_empty.setAlignment(Qt.AlignCenter)
        self.welcome_empty.setMinimumHeight(90)
        page_layout.addWidget(self.welcome_empty)
        page_layout.addStretch(1)
        self._retranslate_welcome()
        self._refresh_welcome_page()

    def _welcome_copy(self):
        values={
            "en":("Your PDF workspace","Open a document to start reading, or continue with a recent file.","Tip: You can drop a PDF onto this window.","Open PDF","Recent documents","Clear recent","Your recent PDFs will appear here."),
            "fa":("فضای کاری PDF شما","برای شروع مطالعه یک سند باز کنید یا یکی از فایل‌های اخیر را ادامه دهید.","نکته: می‌توانید فایل PDF را روی پنجره رها کنید.","باز کردن PDF","اسناد اخیر","پاک‌کردن فهرست","فایل‌های اخیر شما اینجا نمایش داده می‌شوند."),
            "de":("Ihr PDF-Arbeitsbereich","Öffnen Sie ein Dokument oder setzen Sie eine zuletzt verwendete Datei fort.","Tipp: Ziehen Sie eine PDF-Datei auf dieses Fenster.","PDF öffnen","Zuletzt verwendete Dokumente","Verlauf leeren","Zuletzt verwendete PDFs erscheinen hier."),
            "es":("Tu espacio PDF","Abre un documento o continúa con un archivo reciente.","Consejo: puedes soltar un PDF sobre esta ventana.","Abrir PDF","Documentos recientes","Borrar recientes","Tus PDF recientes aparecerán aquí."),
            "fr":("Votre espace PDF","Ouvrez un document ou reprenez un fichier récent.","Astuce : déposez un PDF sur cette fenêtre.","Ouvrir un PDF","Documents récents","Effacer les récents","Vos PDF récents apparaîtront ici."),
            "da":("Dit PDF-arbejdsområde","Åbn et dokument, eller fortsæt med en nylig fil.","Tip: Træk en PDF-fil ind i vinduet.","Åbn PDF","Seneste dokumenter","Ryd seneste","Dine seneste PDF-filer vises her."),
            "no":("Ditt PDF-område","Åpne et dokument eller fortsett med en nylig fil.","Tips: Slipp en PDF-fil på dette vinduet.","Åpne PDF","Nylige dokumenter","Tøm nylige","Nylige PDF-filer vises her."),
            "fi":("PDF-työtilasi","Avaa asiakirja tai jatka viimeksi käytetystä tiedostosta.","Vinkki: Pudota PDF tähän ikkunaan.","Avaa PDF","Viimeisimmät asiakirjat","Tyhjennä viimeisimmät","Viimeisimmät PDF-tiedostot näkyvät tässä."),
            "sv":("Din PDF-arbetsyta","Öppna ett dokument eller fortsätt med en nylig fil.","Tips: Släpp en PDF-fil på det här fönstret.","Öppna PDF","Senaste dokument","Rensa senaste","Dina senaste PDF-filer visas här."),
            "el":("Ο χώρος PDF σας","Ανοίξτε ένα έγγραφο ή συνεχίστε από ένα πρόσφατο αρχείο.","Συμβουλή: σύρετε ένα PDF σε αυτό το παράθυρο.","Άνοιγμα PDF","Πρόσφατα έγγραφα","Εκκαθάριση","Τα πρόσφατα PDF θα εμφανίζονται εδώ."),
            "ar":("مساحة عمل PDF","افتح مستندًا أو تابع من ملف حديث.","تلميح: اسحب ملف PDF إلى هذه النافذة.","فتح PDF","المستندات الأخيرة","مسح الأخيرة","ستظهر ملفات PDF الأخيرة هنا.")
        }
        return values.get(self.current_lang,values["en"])

    def _retranslate_welcome(self):
        if not hasattr(self,"welcome_title"):
            return
        title,subtitle,hint,open_text,recent_text,clear_text,empty_text=self._welcome_copy()
        self.welcome_title.setText(title)
        self.welcome_subtitle.setText(subtitle)
        self.welcome_hint.setText(hint)
        self.welcome_open_button.setText(open_text)
        self.welcome_recent_title.setText(recent_text)
        self.welcome_clear_button.setText(clear_text)
        self.welcome_empty.setText(empty_text)

    def _recent_pdf_icon(self,path):
        dark=str(self.app_settings.get("appearance_mode","light")).lower()=="dark"
        pm=QPixmap(112,132)
        pm.fill(QColor("#172235" if dark else "#F0F4F9"))
        accent=QColor(*THEME_ACCENTS.get(self.app_settings.get("theme","Arctic Glass"),(58,141,255)))
        try:
            document=fitz.open(path)
            try:
                if document.is_encrypted:
                    raise ValueError("Preview unavailable for a password-protected PDF.")
                page=document.load_page(0)
                width=max(1.0,page.rect.width); height=max(1.0,page.rect.height)
                scale=min(100/width,116/height,0.45)
                pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
                image=QImage(pix.samples,pix.width,pix.height,pix.stride,QImage.Format_RGB888).copy()
                document.close()
                return QIcon(QPixmap.fromImage(image))
            finally:
                if not document.is_closed:
                    document.close()
        except Exception:
            painter=QPainter(pm)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QColor("#41546E" if dark else "#D1DCE9"))
            painter.setBrush(QColor("#21324A" if dark else "#FFFFFF"))
            painter.drawRoundedRect(10,5,92,122,7,7)
            painter.setPen(accent)
            painter.setFont(QFont("DejaVu Sans",15,QFont.Bold))
            painter.drawText(pm.rect(),Qt.AlignCenter,"PDF")
            painter.end()
            return QIcon(pm)

    def _refresh_welcome_page(self):
        if not hasattr(self,"recent_grid"):
            return
        while self.recent_grid.count():
            item=self.recent_grid.takeAt(0)
            widget=item.widget()
            if widget is not None:
                widget.deleteLater()
        existing=[path for path in self.recent_files if os.path.isfile(path)][:8]
        self.welcome_empty.setVisible(not existing)
        self.welcome_clear_button.setVisible(bool(existing))
        for index,path in enumerate(existing):
            card=QToolButton(self.recent_grid_host)
            card.setObjectName("recent_file_card")
            card.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            card.setToolTip(path)
            card.setText(Path(path).name)
            card.setIcon(self._recent_pdf_icon(path))
            card.setIconSize(QSize(104,116))
            card.setMinimumSize(180,178)
            card.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
            card.setCursor(Qt.PointingHandCursor)
            card.clicked.connect(lambda checked=False,selected=path:self.open_file(selected))
            self.recent_grid.addWidget(card,index//4,index%4)

    def _build_navigation_dock(self):
        self._navigation_needs_refresh = True
        self.navigation_dock = QDockWidget(self._nav_text("dock"), self)
        self.navigation_dock.setObjectName("navigation_dock")
        self.navigation_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.navigation_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.navigation_dock.setMinimumWidth(230)
        self.navigation_tabs = QTabWidget(self.navigation_dock)
        self.outline_tree = QTreeWidget(self.navigation_tabs)
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.itemActivated.connect(self._navigate_outline_item)
        self.page_list = QListWidget(self.navigation_tabs)
        self.page_list.setIconSize(QSize(76, 100))
        self.page_list.setUniformItemSizes(True)
        self.page_list.setSpacing(6)
        self.page_list.setAlternatingRowColors(True)
        self.page_list.currentRowChanged.connect(self._navigate_page_list)
        self.page_list.verticalScrollBar().valueChanged.connect(self._schedule_thumbnail_refresh)
        self.navigation_tabs.addTab(self.outline_tree, self._nav_text("outline"))
        self.navigation_tabs.addTab(self.page_list, self._nav_text("pages"))
        self.navigation_dock.setWidget(self.navigation_tabs)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.navigation_dock)
        self.navigation_dock.hide()
        self._thumbnail_refresh_timer = QTimer(self)
        self._thumbnail_refresh_timer.setSingleShot(True)
        self._thumbnail_refresh_timer.setInterval(80)
        self._thumbnail_refresh_timer.timeout.connect(self._load_visible_thumbnails)

    def _nav_text(self, key, **kwargs):
        language = NAVIGATION_I18N.get(self.current_lang, NAVIGATION_I18N["en"])
        template = language.get(key, NAVIGATION_I18N["en"].get(key, key))
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template

    def _retranslate_navigation(self):
        if not hasattr(self, "navigation_dock"):
            return
        self.navigation_dock.setWindowTitle(self._nav_text("dock"))
        self.navigation_action.setText(self._nav_text("nav_action"))
        self.recent_menu.setTitle(self._nav_text("recent"))
        self.navigation_tabs.setTabText(0, self._nav_text("outline"))
        self.navigation_tabs.setTabText(1, self._nav_text("pages"))
        if self.navigation_dock.isVisible():
            self._refresh_navigation()

    def toggle_navigation_panel(self):
        self.navigation_dock.setVisible(not self.navigation_dock.isVisible())
        if self.navigation_dock.isVisible():
            self._refresh_navigation()

    def _navigate_outline_item(self, item, column=0):
        page_index = item.data(0, Qt.UserRole)
        if isinstance(page_index, int) and self.doc and 0 <= page_index < self.doc.page_count:
            self.go_to_page(page_index + 1)

    def _navigate_page_list(self, row):
        if self.doc and 0 <= row < self.doc.page_count and row != self.current_page:
            self.go_to_page(row + 1)

    def _refresh_navigation(self):
        if not hasattr(self, "page_list"):
            return
        if hasattr(self, "navigation_dock") and not self.navigation_dock.isVisible():
            self._navigation_needs_refresh = True
            return
        self._navigation_needs_refresh = False
        self._thumbnail_cache.clear()
        self.page_list.blockSignals(True)
        self.page_list.clear()
        if self.doc:
            for index in range(self.doc.page_count):
                item = QListWidgetItem(self._nav_text("page", n=index + 1))
                item.setData(Qt.UserRole, index)
                self.page_list.addItem(item)
            self.page_list.setCurrentRow(self.current_page if self.current_page < self.page_list.count() else 0)
        self.page_list.blockSignals(False)

        self.outline_tree.clear()
        if self.doc:
            try:
                stack = []
                for entry in self.doc.get_toc(simple=True):
                    if len(entry) < 3:
                        continue
                    level, title, page_number = entry[:3]
                    if not isinstance(page_number, int) or page_number < 1:
                        continue
                    item = QTreeWidgetItem([str(title or f"Page {page_number}")])
                    item.setData(0, Qt.UserRole, page_number - 1)
                    while stack and stack[-1][0] >= level:
                        stack.pop()
                    if stack:
                        stack[-1][1].addChild(item)
                    else:
                        self.outline_tree.addTopLevelItem(item)
                    stack.append((level, item))
                if self.outline_tree.topLevelItemCount() == 0:
                    empty = QTreeWidgetItem([self._nav_text("no_outline")])
                    empty.setDisabled(True)
                    self.outline_tree.addTopLevelItem(empty)
                self.outline_tree.expandToDepth(1)
            except Exception as exc:
                self.statusBar().showMessage(f"Could not read PDF outline: {exc}", 5000)
        self._schedule_thumbnail_refresh()

    def _schedule_thumbnail_refresh(self, *_args):
        timer = getattr(self, "_thumbnail_refresh_timer", None)
        if timer is not None:
            timer.start()

    def _load_visible_thumbnails(self):
        if not self.doc or not hasattr(self, "page_list") or self.page_list.count() == 0:
            return
        if hasattr(self, "navigation_dock") and not self.navigation_dock.isVisible():
            return
        first = self.page_list.indexAt(QPoint(5, 5)).row()
        if first < 0:
            first = max(0, self.page_list.currentRow())
        visible_count = max(8, min(16, self.page_list.viewport().height() // 90 + 4))
        for index in range(first, min(self.page_list.count(), first + visible_count)):
            item = self.page_list.item(index)
            if index in self._thumbnail_cache:
                item.setIcon(self._thumbnail_cache[index])
                self._thumbnail_cache.move_to_end(index)
                continue
            try:
                page = self.doc.load_page(index)
                width, height = max(1, page.rect.width), max(1, page.rect.height)
                scale = min(88 / width, 112 / height, 0.28)
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
                icon = QIcon(QPixmap.fromImage(image))
                item.setIcon(icon)
                self._thumbnail_cache[index] = icon
                while len(self._thumbnail_cache) > 40:
                    expired_index, _ = self._thumbnail_cache.popitem(last=False)
                    expired_item = self.page_list.item(expired_index)
                    if expired_item is not None:
                        expired_item.setIcon(QIcon())
            except Exception:
                continue

    def _persist_reading_position(self):
        if not self.app_settings.get('remember_last', True):
            self.settings_store.setValue('last_file', '')
            return
        if not self.doc or not self.file_path:
            return
        self._last_session_file = self.file_path
        self._last_session_page = self.current_page + 1
        self._last_session_zoom = clamp_zoom(self.zoom_factor)
        self._last_session_fit_mode = self.fit_mode if self.fit_mode in ('width', 'page') else 'custom'
        self.settings_store.setValue('last_file', self._last_session_file)
        self.settings_store.setValue('last_page', self._last_session_page)
        self.settings_store.setValue('last_zoom', self._last_session_zoom)
        self.settings_store.setValue('last_fit_mode', self._last_session_fit_mode)

    def _refresh_recent_menu(self):
        if not hasattr(self, "recent_menu"):
            return
        self.recent_menu.clear()
        existing = [path for path in self.recent_files if os.path.isfile(path)]
        if not existing:
            empty = self.recent_menu.addAction(self._nav_text("no_recent"))
            empty.setEnabled(False)
        else:
            for path in existing:
                action = self.recent_menu.addAction(Path(path).name)
                action.setToolTip(path)
                action.triggered.connect(lambda checked=False, selected=path: self.open_file(selected))
        self.recent_menu.addSeparator()
        clear_action = self.recent_menu.addAction(self._nav_text("clear_recent"))
        clear_action.triggered.connect(self.clear_recent_files)

    def _add_recent_file(self, file_path):
        self.recent_files = add_recent_file(self.recent_files, file_path)
        self.settings_store.setValue("recent_files", self.recent_files)
        self._refresh_recent_menu()
        self._refresh_welcome_page()

    def clear_recent_files(self):
        self.recent_files = []
        self.settings_store.setValue("recent_files", [])
        self._refresh_recent_menu()
        self._refresh_welcome_page()

    def mark_document_modified(self):
        self._document_dirty = True
        self._update_page_indicator()
        if hasattr(self, "statusBar"):
            self.statusBar().showMessage("Unsaved PDF changes", 4000)


    def _snapshot_for_history(self):
        if not self.doc or self._undo_disabled_for_size:
            return None
        try:
            if self.file_path and os.path.isfile(self.file_path) and os.path.getsize(self.file_path) > self._history_max_bytes:
                return None
            options = {"garbage": 0, "deflate": True}
            if self._document_encrypted:
                options["encryption"] = fitz.PDF_ENCRYPT_KEEP
            snapshot = self.doc.tobytes(**options)
            return snapshot if len(snapshot) <= self._history_max_bytes else None
        except Exception:
            return None

    def _record_undo(self):
        if not self.doc or self._undo_disabled_for_size:
            return False
        snapshot = self._snapshot_for_history()
        if snapshot is None:
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._undo_disabled_for_size = True
            self.statusBar().showMessage("Undo/redo is disabled for this PDF because its history snapshot exceeds 16 MiB or could not be created.", 7000)
            return False
        self._undo_stack.append(snapshot)
        del self._undo_stack[:-5]
        self._redo_stack.clear()
        return True

    def _restore_history_snapshot(self, snapshot, label):
        replacement = None
        try:
            replacement = fitz.open(stream=snapshot, filetype="pdf")
            replacement_encrypted = _is_document_encrypted(replacement)
            if replacement_encrypted and getattr(replacement, "needs_pass", False) and not replacement.authenticate(self._document_password):
                raise RuntimeError("The history snapshot could not be authenticated.")
            previous = self.doc
            self.doc = replacement
            replacement = None
            self._document_encrypted = replacement_encrypted
            self._last_rendered_page_index = None
            if previous:
                previous.close()
            self.current_page = max(0, min(self.current_page, self.doc.page_count - 1))
            self.spin_page.blockSignals(True)
            self.spin_page.setMaximum(self.doc.page_count)
            self.spin_page.setValue(self.current_page + 1)
            self.spin_page.blockSignals(False)
            self._last_search_query = ""
            self._last_search_page = -1
            self._last_search_rect_index = -1
            self.search_highlight = None
            self._document_dirty = True
            self._thumbnail_cache.clear()
            self._refresh_navigation()
            self._apply_fit() if self.fit_mode in ("width", "page") else self.render_page()
            self.statusBar().showMessage(f"{label} complete · unsaved changes", 5000)
            return True
        except Exception as exc:
            self.statusBar().showMessage(f"{label} failed: {exc}", 7000)
            return False
        finally:
            if replacement is not None:
                replacement.close()

    def undo_edit(self):
        if not self.doc or not self._undo_stack:
            self.statusBar().showMessage("There is no edit to undo.", 3000)
            return
        current = self._snapshot_for_history()
        if current is None:
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._undo_disabled_for_size = True
            self.statusBar().showMessage("Undo/redo history is unavailable for this PDF size.", 6000)
            return
        previous = self._undo_stack[-1]
        if self._restore_history_snapshot(previous, "Undo"):
            self._undo_stack.pop()
            self._redo_stack.append(current)

    def redo_edit(self):
        if not self.doc or not self._redo_stack:
            self.statusBar().showMessage("There is no edit to redo.", 3000)
            return
        current = self._snapshot_for_history()
        if current is None:
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._undo_disabled_for_size = True
            self.statusBar().showMessage("Undo/redo history is unavailable for this PDF size.", 6000)
            return
        next_state = self._redo_stack[-1]
        if self._restore_history_snapshot(next_state, "Redo"):
            self._redo_stack.pop()
            self._undo_stack.append(current)
            del self._undo_stack[:-5]

    def open_page_organizer(self):
        if not self.doc:
            QMessageBox.information(self, "Manage PDF pages", "Open a PDF first.")
            return
        if self.file_path and os.path.isfile(self.file_path) and os.path.getsize(self.file_path) > 256 * 1024 * 1024:
            QMessageBox.information(self, "Manage PDF pages", "The page organizer is disabled for PDFs larger than 256 MiB to avoid large in-memory edit histories.")
            return
        PageOrganizerDialog(self).exec()

    def insert_pages_from_pdf(self):
        if not self.doc:
            QMessageBox.information(self, "Insert pages", "Open a destination PDF first.")
            return
        source_path, _ = QFileDialog.getOpenFileName(self, "Insert pages from PDF", "", "PDF documents (*.pdf)")
        if not source_path:
            return
        source = None
        try:
            source = fitz.open(source_path)
            if _is_document_encrypted(source) and getattr(source, "needs_pass", False) and not source.authenticate(""):
                while True:
                    password, ok = QInputDialog.getText(
                        self, "Unlock source PDF", "Enter the source PDF password:", QLineEdit.Password
                    )
                    if not ok:
                        return
                    if source.authenticate(password):
                        break
                    QMessageBox.critical(self, "Insert pages", "The source PDF password is incorrect.")
            if source.page_count < 1:
                QMessageBox.information(self, "Insert pages", "The selected PDF has no pages to insert.")
                return
            self._record_undo()
            insert_at = self.current_page + 1
            inserted_count = source.page_count
            self.doc.insert_pdf(source, start_at=insert_at)
            self.current_page = insert_at
            self._after_document_structure_change()
            self.statusBar().showMessage(f"Inserted {inserted_count} page(s) from {Path(source_path).name}", 6000)
        except Exception as exc:
            QMessageBox.critical(self, "Insert pages failed", str(exc))
        finally:
            if source is not None:
                source.close()

    def _after_document_structure_change(self):
        if not self.doc or self.doc.page_count < 1:
            return
        self.current_page = max(0, min(self.current_page, self.doc.page_count - 1))
        self.spin_page.blockSignals(True)
        self.spin_page.setMaximum(self.doc.page_count)
        self.spin_page.setValue(self.current_page + 1)
        self.spin_page.blockSignals(False)
        self._last_search_query = ""
        self._last_search_page = -1
        self._last_search_rect_index = -1
        self.search_highlight = None
        self._thumbnail_cache.clear()
        self._refresh_navigation()
        self.mark_document_modified()
        self._apply_fit() if self.fit_mode in ("width", "page") else self.render_page()

    def _retranslate_page_management(self):
        if not hasattr(self, "page_management_menu"):
            return
        labels = {
            "en": ("Page management", "Manage pages…", "Insert pages from PDF…", "Undo", "Redo"),
            "fa": ("مدیریت صفحات", "مدیریت صفحات…", "درج صفحه از PDF…", "واگرد", "ازنو"),
            "de": ("Seitenverwaltung", "Seiten verwalten…", "Seiten aus PDF einfügen…", "Rückgängig", "Wiederholen"),
            "es": ("Administrar páginas", "Administrar páginas…", "Insertar páginas desde PDF…", "Deshacer", "Rehacer"),
            "fr": ("Gestion des pages", "Gérer les pages…", "Insérer des pages depuis un PDF…", "Annuler", "Rétablir"),
            "da": ("Sidehåndtering", "Administrer sider…", "Indsæt sider fra PDF…", "Fortryd", "Gentag"),
            "no": ("Sidebehandling", "Administrer sider…", "Sett inn sider fra PDF…", "Angre", "Gjør om"),
            "fi": ("Sivujen hallinta", "Hallitse sivuja…", "Lisää sivuja PDF-tiedostosta…", "Kumoa", "Tee uudelleen"),
            "sv": ("Sidhantering", "Hantera sidor…", "Infoga sidor från PDF…", "Ångra", "Gör om"),
            "el": ("Διαχείριση σελίδων", "Διαχείριση σελίδων…", "Εισαγωγή σελίδων από PDF…", "Αναίρεση", "Επανάληψη"),
            "ar": ("إدارة الصفحات", "إدارة الصفحات…", "إدراج صفحات من PDF…", "تراجع", "إعادة")
        }
        values = labels.get(self.current_lang, labels["en"])
        self.page_management_menu.setTitle(values[0])
        self.page_actions["organize"].setText(values[1])
        self.page_actions["insert"].setText(values[2])
        self.undo_action.setText(values[3])
        self.redo_action.setText(values[4])

    def _confirm_unsaved_changes(self):
        if not self.doc or not self._document_dirty or not self.app_settings.get("confirm_close", True):
            return True
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Unsaved changes")
        box.setText("This PDF has unsaved changes. Save them before continuing?")
        box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Save)
        answer = box.exec()
        if answer == QMessageBox.Save:
            return bool(self.save_file())
        return answer == QMessageBox.Discard

    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls() and any(url.isLocalFile() and url.toLocalFile().lower().endswith(".pdf") for url in event.mimeData().urls()):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self,event):
        for url in event.mimeData().urls():
            if url.isLocalFile() and url.toLocalFile().lower().endswith(".pdf"):
                event.acceptProposedAction()
                self.open_file(url.toLocalFile())
                return
        event.ignore()

    def closeEvent(self, event):
        if not self._confirm_unsaved_changes():
            event.ignore()
            return
        self._open_render_generation += 1
        self._wheel_transition_generation += 1
        thumbnail_timer = getattr(self, "_thumbnail_refresh_timer", None)
        if thumbnail_timer is not None:
            thumbnail_timer.stop()
        self._persist_reading_position()
        try:
            self.player.stop()
        except Exception:
            pass
        if self.doc:
            try:
                self.doc.close()
            except Exception:
                pass
        event.accept()

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

    def toggle_smart_ink(self, enabled=None):
        if enabled is None:
            enabled = not bool(self.app_settings.get("smart_ink", True))
        self.app_settings["smart_ink"] = bool(enabled)
        self.settings_store.setValue("smart_ink", bool(enabled))
        if hasattr(self, "btn_smart_ink"):
            self.btn_smart_ink.blockSignals(True)
            self.btn_smart_ink.setChecked(bool(enabled))
            self.btn_smart_ink.blockSignals(False)
        if hasattr(self, "statusBar"):
            if self.current_lang == "fa":
                status = "فعال" if enabled else "غیرفعال"
                self.statusBar().showMessage(f"قلم هوشمند {status}", 2400)
            else:
                self.statusBar().showMessage(f"Smart Ink {'on' if enabled else 'off'}", 2400)
        if hasattr(self, "page_label"):
            self.page_label.update()

    def toggle_tool(self, tool_name):
        self.page_label.current_stroke = []
        self.page_label.current_stroke_view = []
        self.is_drawing = False
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

    def open_file(self, selected_path=None, restore_session=False):
        file_path = selected_path
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF documents (*.pdf *.PDF);;All files (*)")
        if not file_path:
            return
        candidate = None
        document_encrypted = False
        try:
            file_path = os.path.abspath(os.path.expanduser(file_path))
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"File does not exist: {file_path}")
            file_size = os.path.getsize(file_path)
            candidate = fitz.open(file_path)
            document_encrypted = _is_document_encrypted(candidate)
            password = ""
            if document_encrypted and getattr(candidate, "needs_pass", False):
                # Some encrypted PDFs intentionally use an empty user password.
                if not candidate.authenticate(""):
                    while True:
                        pwd, ok = QInputDialog.getText(
                            self, "Unlock PDF",
                            TRANSLATIONS[self.current_lang]["enter_pass"],
                            QLineEdit.Password,
                        )
                        if not ok:
                            candidate.close()
                            return
                        if candidate.authenticate(pwd):
                            password = pwd
                            break
                        QMessageBox.warning(
                            self, "Cannot open PDF",
                            TRANSLATIONS[self.current_lang]["wrong_pass"],
                        )
            if candidate.page_count < 1:
                raise ValueError("The PDF contains no readable pages.")
            if not self._confirm_unsaved_changes():
                candidate.close()
                return
            previous_doc = self.doc
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._undo_disabled_for_size = False
            self.doc = candidate
            candidate = None
            if previous_doc:
                try:
                    previous_doc.close()
                except Exception:
                    pass
            self.file_path = file_path
            self._document_password = password
            self._document_encrypted = document_encrypted
            self._document_dirty = False
            self.large_file_mode = file_size >= 1024 ** 3
            if self.large_file_mode:
                self.app_settings["low_memory"] = True
                self.app_settings["cache_pages"] = False
                self.app_settings["preload_pages"] = False
            self.current_page = 0
            self._last_rendered_page_index = None
            self.zoom_factor = 1.0
            self.rotation = {"0°": 0, "90°": 90, "180°": 180, "270°": 270}.get(self.app_settings.get("rotation", "0°"), 0)
            self.fit_mode = {"Fit Width": "width", "Fit Page": "page", "100%": None}.get(self.app_settings.get("fit_mode", "Fit Width"), "width")
            if restore_session and self.app_settings.get("remember_last", True) and same_path(file_path, self._last_session_file):
                self.current_page = max(0, min(self.doc.page_count - 1, self._last_session_page - 1))
                if self.app_settings.get("restore_zoom", True):
                    if self._last_session_fit_mode in ("width", "page"):
                        self.fit_mode = self._last_session_fit_mode
                    else:
                        self.fit_mode = None
                        self.zoom_factor = clamp_zoom(self._last_session_zoom)
            self.spin_page.blockSignals(True)
            self.spin_page.setMaximum(self.doc.page_count)
            self.spin_page.setValue(self.current_page + 1)
            self.spin_page.blockSignals(False)
            self._last_search_query = ""
            self._last_search_page = -1
            self._last_search_rect_index = -1
            self.search_highlight = None
            self._refresh_navigation()
            if hasattr(self,'workspace_stack'):
                self.workspace_stack.setCurrentWidget(self.scroll_area)
            self._apply_fit() if self.fit_mode in ('width', 'page') else self.render_page()
            # Re-render once the stacked page has completed its layout pass.
            # This avoids fitting against a hidden/zero-sized viewport when a
            # document is opened immediately after application startup.
            self._open_render_generation += 1
            render_generation = self._open_render_generation
            QTimer.singleShot(0, lambda generation=render_generation: self._finish_open_render(generation))
            self._add_recent_file(file_path)
            self._persist_reading_position()
            self.statusBar().showMessage(f"Opened {Path(file_path).name} · {self.doc.page_count} pages", 5000)
            if self.app_settings.get("audio_enabled", True) and self.app_settings.get("autoplay", False):
                QTimer.singleShot(0, self.toggle_lofi)
        except Exception as exc:
            if candidate is not None:
                try:
                    candidate.close()
                except Exception:
                    pass
            QMessageBox.critical(self, "Cannot open PDF", f"The file could not be opened.\\n\\n{exc}")

    def _finish_open_render(self, generation):
        if generation != self._open_render_generation or self.doc is None or getattr(self.doc, "is_closed", False):
            return
        if hasattr(self, "workspace_stack"):
            self.workspace_stack.setCurrentWidget(self.scroll_area)
        self.scroll_area.ensurePolished()
        viewport_size = self.scroll_area.viewport().size()
        self._last_viewport_size = (viewport_size.width(), viewport_size.height())
        self._apply_fit() if self.fit_mode in ("width", "page") else self.render_page()

    def _effective_page_size(self, page):
        return (page.rect.height, page.rect.width) if self.rotation % 180 else (page.rect.width, page.rect.height)

    def render_page(self):
        if self.doc is None or getattr(self.doc, "is_closed", False) or not (0 <= self.current_page < self.doc.page_count):
            return
        try:
            page_changed = getattr(self, "_last_rendered_page_index", None) != self.current_page
            page = self.doc.load_page(self.current_page)
            self.zoom_factor = clamp_zoom(self.zoom_factor)
            mat = fitz.Matrix(self.zoom_factor, self.zoom_factor).prerotate(self.rotation)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
            rendered_pixmap = QPixmap.fromImage(img)
            if rendered_pixmap.isNull() or rendered_pixmap.width() < 1 or rendered_pixmap.height() < 1:
                raise RuntimeError("The PDF page renderer returned an empty image.")
            self.page_label.setPixmap(rendered_pixmap)
            # Keep widget geometry in sync with the exact rendered image. The
            # scroll area then scrolls the entire page instead of resizing/clipping
            # the QLabel, and annotation coordinates remain image-relative.
            self.page_label.resize(rendered_pixmap.size())
            self.page_label.updateGeometry()
            if page_changed:
                self._last_rendered_page_index = self.current_page
                # New pages start at the top; normal re-renders preserve scroll.
                self.scroll_area.horizontalScrollBar().setValue(0)
                self.scroll_area.verticalScrollBar().setValue(0)
            if not self._navigation_needs_refresh and hasattr(self, "page_list") and 0 <= self.current_page < self.page_list.count() and self.page_list.currentRow() != self.current_page:
                self.page_list.blockSignals(True)
                self.page_list.setCurrentRow(self.current_page)
                self.page_list.blockSignals(False)
                self._schedule_thumbnail_refresh()
            self._update_page_indicator()
            self.page_label.update()
            self._persist_reading_position()
        except Exception as exc:
            self.statusBar().showMessage(f"Could not render page {self.current_page + 1}: {exc}", 6000)

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

    def _search_query(self, q):
        if not self.doc or not q.strip():
            return
        q = q.strip()
        page_count = self.doc.page_count
        if page_count <= 0:
            return
        same_query = q.casefold() == self._last_search_query.casefold() and self._last_search_page == self.current_page
        start_page = self.current_page
        start_rect = self._last_search_rect_index + 1 if same_query else 0
        for offset in range(page_count):
            page_index = (start_page + offset) % page_count
            try:
                page = self.doc.load_page(page_index)
                matches = page.search_for(q)
            except Exception as exc:
                self.statusBar().showMessage(f"Search failed: {exc}", 5000)
                return
            match_index = start_rect if offset == 0 else 0
            if match_index < len(matches):
                self.current_page = page_index
                self.spin_page.blockSignals(True)
                self.spin_page.setValue(page_index + 1)
                self.spin_page.blockSignals(False)
                self._last_search_query = q
                self._last_search_page = page_index
                self._last_search_rect_index = match_index
                self.search_highlight = {"page": page_index, "rect": matches[match_index]}
                if self.fit_mode in ("width", "page"):
                    self._apply_fit()
                else:
                    self.render_page()
                self.statusBar().showMessage(f"Match {match_index + 1} of {len(matches)} on page {page_index + 1} · Enter to find next", 6000)
                return
        self.search_highlight = None
        self.page_label.update()
        QMessageBox.information(self, TRANSLATIONS[self.current_lang]["search"], TRANSLATIONS[self.current_lang]["not_found"])

    def _retranslate_shell(self):
        extra={'en':('Fast • Focused • PDF workspace','FILE','ANNOTATE','VIEW','PAGE','TOOLS','More More','Settings Settings','Ready • Open a PDF to begin','Search Search inside PDF…'),'fa':('سریع • متمرکز • محیط حرفه‌ای PDF','فایل','حاشیه‌نویسی','نمایش','صفحه','ابزارها','More بیشتر','Settings تنظیمات','آماده • یک PDF باز کنید','Search جستجو در PDF…'),'de':('Schnell • Fokus • PDF-Arbeitsbereich','DATEI','ANMERKEN','ANSICHT','SEITE','WERKZEUGE','More Mehr','Settings Einstellungen','Bereit • PDF öffnen','Search Im PDF suchen…'),'es':('Rápido • Enfocado • Espacio PDF','ARCHIVO','ANOTAR','VISTA','PÁGINA','HERRAMIENTAS','More Más','Settings Ajustes','Listo • Abra un PDF','Search Buscar en PDF…'),'fr':('Rapide • Concentré • Espace PDF','FICHIER','ANNOTER','AFFICHAGE','PAGE','OUTILS','More Plus','Settings Paramètres','Prêt • Ouvrez un PDF','Search Rechercher dans le PDF…'),'da':('Hurtig • Fokuseret • PDF-arbejdsområde','FIL','ANNOTERING','VISNING','SIDE','VÆRKTØJER','More Mere','Settings Indstillinger','Klar • Åbn en PDF','Search Søg i PDF…'),'no':('Rask • Fokusert • PDF-område','FIL','MERKNADER','VISNING','SIDE','VERKTØY','More Mer','Settings Innstillinger','Klar • Åpne en PDF','Search Søk i PDF…'),'fi':('Nopea • Keskittynyt • PDF-työtila','TIEDOSTO','MERKINNÄT','NÄKYMÄ','SIVU','TYÖKALUT','More Lisää','Settings Asetukset','Valmis • Avaa PDF','Search Hae PDF:stä…'),'sv':('Snabb • Fokuserad • PDF-arbetsyta','FIL','ANTECKNINGAR','VY','SIDA','VERKTYG','More Mer','Settings Inställningar','Redo • Öppna en PDF','Search Sök i PDF…'),'el':('Γρήγορο • Εστιασμένο • PDF','ΑΡΧΕΙΟ','ΣΧΟΛΙΑΣΜΟΣ','ΠΡΟΒΟΛΗ','ΣΕΛΙΔΑ','ΕΡΓΑΛΕΙΑ','More Περισσότερα','Settings Ρυθμίσεις','Έτοιμο • Ανοίξτε PDF','Search Αναζήτηση στο PDF…'),'ar':('سريع • مركز • مساحة عمل PDF','ملف','تعليقات','عرض','صفحة','أدوات','More المزيد','Settings الإعدادات','جاهز • افتح ملف PDF','Search البحث داخل PDF…')}
        vals=extra.get(self.current_lang,extra['en']); self.brand_subtitle.setText(vals[0]); self.btn_settings.setText(vals[7]); self.btn_more.setText(vals[6]); self.quick_search.setPlaceholderText(vals[9]); self.btn_navigation.setText(self._nav_text('pages')); self.btn_navigation.setToolTip(self._nav_text('nav_action')); self._retranslate_welcome(); self.statusBar().showMessage(f'Opened {Path(self.file_path).name}' if self.doc and self.file_path else vals[8])
        for k,label in zip(['FILE','ANNOTATE','VIEW','PAGE','TOOLS'],vals[1:6]):
            if k in self.group_labels: self.group_labels[k].setText(label)
        more_names=[TRANSLATIONS[self.current_lang]['search']+' PDF',TRANSLATIONS[self.current_lang]['pass_remove'],TRANSLATIONS[self.current_lang]['pass_add'],vals[7]]
        for a,text in zip(getattr(self,'more_actions',[]),more_names): a.setText(text)
        self._update_page_indicator()

    def move_current_page(self, delta):
        if not self.doc:
            return
        source_index = self.current_page
        target_index = source_index + delta
        if target_index < 0 or target_index >= self.doc.page_count:
            return
        self._record_undo()
        order = list(range(self.doc.page_count))
        order[source_index], order[target_index] = order[target_index], order[source_index]
        self.doc.select(order)
        self.current_page = target_index
        self._after_document_structure_change()

    def _update_page_indicator(self):
        t=TRANSLATIONS.get(self.current_lang,TRANSLATIONS["en"])
        if hasattr(self,'lbl_page'):
            self.lbl_page.setText(f"{t['page']} {self.current_page+1} {t['of']} {self.doc.page_count if self.doc else 0}")
        if hasattr(self,"status_page"):
            status_text = {
                "en":("No PDF open","Ready","Saved","Unsaved changes"),
                "fa":("PDF باز نیست","آماده","ذخیره‌شده","تغییرات ذخیره‌نشده"),
                "de":("Keine PDF geöffnet","Bereit","Gespeichert","Ungespeicherte Änderungen"),
                "es":("No hay PDF abierto","Listo","Guardado","Cambios sin guardar"),
                "fr":("Aucun PDF ouvert","Prêt","Enregistré","Modifications non enregistrées"),
                "da":("Ingen PDF åben","Klar","Gemt","Ikke-gemte ændringer"),
                "no":("Ingen PDF åpen","Klar","Lagret","Ulagrede endringer"),
                "fi":("PDF ei ole auki","Valmis","Tallennettu","Tallentamattomat muutokset"),
                "sv":("Ingen PDF öppen","Redo","Sparad","Osparade ändringar"),
                "el":("Δεν υπάρχει ανοιχτό PDF","Έτοιμο","Αποθηκεύτηκε","Μη αποθηκευμένες αλλαγές"),
                "ar":("لا يوجد PDF مفتوح","جاهز","تم الحفظ","تغييرات غير محفوظة")
            }.get(self.current_lang,("No PDF open","Ready","Saved","Unsaved changes"))
            self.status_page.setText(f"{t['page']} {self.current_page+1} {t['of']} {self.doc.page_count}" if self.doc else status_text[0])
            self.status_zoom.setText(f"{round(self.zoom_factor*100)}%")
            dirty=bool(self._document_dirty)
            self.status_dirty.setText(status_text[3] if dirty else (status_text[2] if self.doc else status_text[1]))
            self.status_dirty.setProperty("dirty","true" if dirty else "false")
            self.status_dirty.style().unpolish(self.status_dirty)
            self.status_dirty.style().polish(self.status_dirty)

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
            if self._last_search_page != self.current_page:
                self.search_highlight = None
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
            self.mark_document_modified()
            self.render_page()

    def handle_pdf_wheel(self, event):
        """Handle wheel movement for labels, viewport margins and the scroll area."""
        if self.doc is None or getattr(self.doc, "is_closed", False) or not hasattr(self, "scroll_area"):
            return False

        pixel_delta = event.pixelDelta().y()
        angle_delta = event.angleDelta().y()
        direction = pixel_delta if pixel_delta else angle_delta
        if event.modifiers() & Qt.ControlModifier:
            if direction > 0:
                self.zoom_in()
            elif direction < 0:
                self.zoom_out()
            event.accept()
            return True

        if not pixel_delta and not angle_delta:
            return False

        bar = self.scroll_area.verticalScrollBar()
        # A negative Qt wheel delta means the user is scrolling down.
        if pixel_delta:
            movement = -pixel_delta
        else:
            movement = -round((angle_delta / 120.0) * max(24, bar.singleStep()) * 3)

        target = bar.value() + movement
        if target < bar.minimum() and self.current_page > 0:
            overflow = bar.minimum() - target
            self._change_page_from_wheel(self.current_page - 1, overflow, "bottom")
        elif target > bar.maximum() and self.current_page < self.doc.page_count - 1:
            overflow = target - bar.maximum()
            self._change_page_from_wheel(self.current_page + 1, overflow, "top")
        else:
            bar.setValue(max(bar.minimum(), min(bar.maximum(), target)))
        event.accept()
        return True

    def _change_page_from_wheel(self, page_index, overflow, edge):
        """Change pages once and restore the scroll offset after Qt updates its range."""
        if self.doc is None or getattr(self.doc, "is_closed", False) or not 0 <= page_index < self.doc.page_count:
            return
        self._wheel_transition_generation += 1
        generation = self._wheel_transition_generation
        self.current_page = page_index
        self.spin_page.blockSignals(True)
        self.spin_page.setValue(page_index + 1)
        self.spin_page.blockSignals(False)
        if self._last_search_page != page_index:
            self.search_highlight = None
        self._apply_fit() if self.fit_mode in ("width", "page") else self.render_page()

        def restore_after_layout():
            if generation != self._wheel_transition_generation or not self.doc:
                return
            self.scroll_area.ensurePolished()
            scroll_bar = self.scroll_area.verticalScrollBar()
            value = scroll_bar.maximum() - overflow if edge == "bottom" else scroll_bar.minimum() + overflow
            scroll_bar.setValue(max(scroll_bar.minimum(), min(scroll_bar.maximum(), value)))
            # Give pending layout/resize events another turn, then clamp to the
            # final scrollbar range to avoid landing in a stale blank region.
            QTimer.singleShot(0, finalize_after_layout)

        def finalize_after_layout():
            if generation != self._wheel_transition_generation or not self.doc:
                return
            scroll_bar = self.scroll_area.verticalScrollBar()
            value = scroll_bar.maximum() - overflow if edge == "bottom" else scroll_bar.minimum() + overflow
            scroll_bar.setValue(max(scroll_bar.minimum(), min(scroll_bar.maximum(), value)))

        QTimer.singleShot(0, restore_after_layout)

    def wheelEvent(self, event):
        if self.handle_pdf_wheel(event):
            return
        super().wheelEvent(event)

    def toggle_lofi(self):
        if not self.app_settings.get("audio_enabled", True):
            self.statusBar().showMessage("Audio playback is disabled in Settings.", 4000)
            return
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
        if not self.doc:
            return
        printer = QPrinter(QPrinter.HighResolution)
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() != QPrintDialog.Accepted:
            return
        painter = QPainter(printer)
        if not painter.isActive():
            QMessageBox.critical(self, "Print failed", "Could not initialize the printer.")
            return
        try:
            for page_index in range(self.doc.page_count):
                if page_index > 0 and not printer.newPage():
                    raise RuntimeError("The printer could not start a new page.")
                page = self.doc.load_page(page_index)
                pix = page.get_pixmap(dpi=180, alpha=False)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
                rect = painter.viewport()
                scaled_img = img.scaled(rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                x = (rect.width() - scaled_img.width()) // 2
                y = (rect.height() - scaled_img.height()) // 2
                painter.drawImage(x, y, scaled_img)
            self.statusBar().showMessage(f"Printed {self.doc.page_count} pages", 5000)
        except Exception as exc:
            QMessageBox.critical(self, "Print failed", str(exc))
        finally:
            painter.end()

    def _save_to_path(self, save_path, save_options=None, password_after=None):
        if not self.doc:
            return False

        save_path = ensure_pdf_extension(os.path.abspath(os.path.expanduser(save_path)))
        output_dir = os.path.dirname(save_path) or os.getcwd()
        source_password = self._document_password
        source_encrypted = bool(self._document_encrypted)
        old_doc = self.doc
        page_to_restore = self.current_page
        temp_path = None
        candidate_doc = None

        try:
            fd, temp_path = tempfile.mkstemp(prefix=".parin-pdf-", suffix=".pdf", dir=output_dir)
            os.close(fd)
            os.unlink(temp_path)

            options = {"garbage": 0 if self.large_file_mode else 4, "deflate": True}
            if save_options:
                options.update(save_options)
            elif source_encrypted:
                # Preserve encryption even when the PDF's user password is empty.
                options["encryption"] = fitz.PDF_ENCRYPT_KEEP

            old_doc.save(temp_path, **options)

            # Validate the output while the original document is still usable.
            candidate_doc = fitz.open(temp_path)
            candidate_encrypted = _is_document_encrypted(candidate_doc)
            candidate_password = source_password if password_after is None else password_after
            if candidate_encrypted and getattr(candidate_doc, "needs_pass", False) and not candidate_doc.authenticate(candidate_password):
                raise RuntimeError("The saved PDF could not be unlocked with the active password.")
            if candidate_doc.page_count < 1:
                raise RuntimeError("The saved PDF contains no readable pages.")
            target_page = min(page_to_restore, candidate_doc.page_count - 1)
            candidate_doc.load_page(target_page)

            # Atomic replacement happens only after the new file is valid.
            os.replace(temp_path, save_path)
            temp_path = None

        except Exception as exc:
            if candidate_doc is not None:
                try:
                    candidate_doc.close()
                except Exception:
                    pass
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            QMessageBox.critical(self, "Save failed", f"Could not save the PDF.\\n\\n{exc}")
            return False

        # Commit the new in-memory document only after the replacement is validated.
        self.doc = candidate_doc
        candidate_doc = None
        try:
            old_doc.close()
        except Exception:
            pass
        self.file_path = save_path
        self._document_password = candidate_password
        self._document_encrypted = candidate_encrypted
        self._document_dirty = False
        self.current_page = target_page
        self._last_rendered_page_index = None
        self._thumbnail_cache.clear()
        self._refresh_navigation()
        self._apply_fit() if self.fit_mode in ("width", "page") else self.render_page()
        self._add_recent_file(save_path)
        self.statusBar().showMessage(f"Saved {Path(save_path).name}", 5000)
        return True

    def save_file(self):
        if not self.doc:
            return False
        save_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", self.file_path, "PDF (*.pdf)")
        if not save_path:
            return False
        return self._save_to_path(save_path)

    def remove_password(self):
        if not self.doc:
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save without password", "unlocked.pdf", "PDF (*.pdf)")
        if save_path:
            self._save_to_path(save_path, {"encryption": fitz.PDF_ENCRYPT_NONE}, password_after="")

    def add_password(self):
        if not self.doc:
            return
        t = TRANSLATIONS[self.current_lang]
        pwd, ok = QInputDialog.getText(self, t["pass_add"], t["set_pass"], QLineEdit.Password)
        if not ok or not pwd:
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save encrypted PDF", "protected.pdf", "PDF (*.pdf)")
        if save_path:
            self._save_to_path(save_path, {"encryption": fitz.PDF_ENCRYPT_AES_256, "user_pw": pwd, "owner_pw": pwd}, password_after=pwd)

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
        smart_labels = {
            "en": ("Smart Ink", "Font for new text annotations", "Font size for new text annotations"),
            "fa": ("قلم هوشمند", "فونت متن جدید", "اندازهٔ فونت متن جدید"),
            "de": ("Intelligente Tinte", "Schrift für neue Textanmerkungen", "Schriftgröße für neue Textanmerkungen"),
            "es": ("Tinta inteligente", "Fuente para texto nuevo", "Tamaño de fuente para texto nuevo"),
            "fr": ("Encre intelligente", "Police du nouveau texte", "Taille de police du nouveau texte"),
            "da": ("Smart blæk", "Skrifttype til ny tekst", "Skriftstørrelse til ny tekst"),
            "no": ("Smart blekk", "Skrift for ny tekst", "Skriftstørrelse for ny tekst"),
            "fi": ("Älykäs muste", "Uuden tekstin fontti", "Uuden tekstin fonttikoko"),
            "sv": ("Smart bläck", "Teckensnitt för ny text", "Teckenstorlek för ny text"),
            "el": ("Έξυπνη μελάνη", "Γραμματοσειρά νέου κειμένου", "Μέγεθος γραμματοσειράς νέου κειμένου"),
            "ar": ("حبر ذكي", "خط النص الجديد", "حجم خط النص الجديد")
        }.get(code, ("Smart Ink", "Font for new text annotations", "Font size for new text annotations"))
        self.btn_smart_ink.setText(smart_labels[0])
        self.btn_smart_ink.setToolTip("هموارسازی تطبیقی و محلی مسیر قلم؛ بدون ارسال داده یا دانلود مدل" if code == "fa" else "Local adaptive ink smoothing; no cloud/model download.")
        self.font_selector.setToolTip(smart_labels[1])
        self.font_size.setToolTip(smart_labels[2])
        self.btn_lofi.setText(t['music_stop'] if self.is_lofi_playing else t['lofi'])
        self.quick_search.setPlaceholderText(t['search'] + '…')
        QApplication.setLayoutDirection(t['dir'])
        self._retranslate_shell()
        self._retranslate_navigation()
        self._retranslate_page_management()
        self._update_page_indicator()


def _startup_pdf_path(argument):
    """Resolve a PDF path passed by the shell or a desktop file URL."""
    if not isinstance(argument, str) or not argument or argument.startswith("-"):
        return None
    url = QUrl(argument)
    if url.isLocalFile():
        path = url.toLocalFile()
    elif "://" in argument:
        # Do not mistake remote URLs or other schemes for local file paths.
        return None
    else:
        path = argument
    path = os.path.abspath(os.path.expanduser(path))
    if Path(path).suffix.lower() != ".pdf" or not os.path.isfile(path):
        return None
    return path


if __name__ == "__main__":
    # Keep document arguments away from Qt's CLI parser. Desktop launchers
    # normally pass local documents as file:// URLs through the %U field.
    startup_pdf = next(
        (path for path in (_startup_pdf_path(arg) for arg in sys.argv[1:]) if path),
        None,
    )
    app = QApplication([sys.argv[0]])
    viewer = ParinPDFViewer()
    viewer.show()
    if viewer.app_settings.get('animations', True) and not viewer.app_settings.get('reduce_motion', False):
        effect=QGraphicsOpacityEffect(viewer); viewer.setGraphicsEffect(effect); fade=QPropertyAnimation(effect,b'opacity',viewer); fade.setDuration(320); fade.setStartValue(0.0); fade.setEndValue(1.0); fade.setEasingCurve(QEasingCurve.OutCubic); fade.start()
        viewer._startup_fade=fade
    if startup_pdf:
        QTimer.singleShot(0, lambda path=startup_pdf: viewer.open_file(path))
    sys.exit(app.exec())
