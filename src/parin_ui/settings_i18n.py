"""Translations and localized labels for the Parin settings dialog.

This module contains data only; it intentionally has no Qt dependency.
"""

from __future__ import annotations

import re

_EMOJI_RE = re.compile(r'[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF]')


def _clean_label(value: str) -> str:
    """Remove decorative emoji and normalize whitespace in settings labels."""
    return re.sub(r'\s{2,}', ' ', _EMOJI_RE.sub('', value)).strip()


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
            _items[_key] = _clean_label(_value)


# Appearance mode labels for the existing localized Settings screen.
for _code, _label in {
    "en":"Appearance mode","fa":"حالت ظاهری","de":"Darstellungsmodus",
    "es":"Modo de apariencia","fr":"Mode d’apparence","da":"Udseende",
    "no":"Utseende","fi":"Ulkoasu","sv":"Utseende","el":"Εμφάνιση","ar":"وضع المظهر"
}.items():
    SETTINGS_I18N.get(_code, SETTINGS_I18N["en"])["appearance_mode"] = _label

__all__ = ["SETTINGS_I18N"]
