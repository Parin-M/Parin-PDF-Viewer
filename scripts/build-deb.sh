#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d ".venv" ]]; then
  echo "ERROR: .venv not found."
  echo "Create it with: python3 -m venv .venv"
  exit 1
fi

source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

rm -rf build dist dist-deb package
mkdir -p dist-deb package/usr/lib/parin-pdf package/usr/bin \
         package/usr/share/applications \
         package/usr/share/icons/hicolor/scalable/apps

pyinstaller --noconfirm --clean packaging/parin_pdf.spec

cp -a dist/Parin/. package/usr/lib/parin-pdf/
install -m 0755 packaging/parin-pdf-launcher package/usr/bin/parin-pdf
install -m 0644 packaging/parin-pdf.desktop package/usr/share/applications/parin-pdf.desktop
install -m 0644 assets/parin-pdf.svg package/usr/share/icons/hicolor/scalable/apps/parin-pdf.svg

# Build with dpkg-deb directly; no fpm required.
mkdir -p package/DEBIAN
cat > package/DEBIAN/control <<EOF
Package: parin-pdf
Version: 8.8.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Parin
Depends: libc6
Description: Parin - Modern PDF workspace
 Modern desktop PDF viewer built with PySide6 and PyMuPDF.
EOF

cat > package/DEBIAN/postinst <<'EOF'
#!/bin/sh
set -e
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -q -f /usr/share/icons/hicolor 2>/dev/null || true
exit 0
EOF
chmod 0755 package/DEBIAN/postinst

dpkg-deb --build package "dist-deb/parin-pdf_8.8.0_amd64.deb"

echo
echo "SUCCESS:"
echo "  $ROOT/dist-deb/parin-pdf_8.8.0_amd64.deb"
