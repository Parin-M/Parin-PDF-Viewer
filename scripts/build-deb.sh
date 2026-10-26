#!/bin/bash
set -euo pipefail
VERSION="9.1.0"

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
python -m pip install "maturin>=1.7,<2.0"
maturin develop --release --manifest-path rust-core/Cargo.toml

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
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Parin
Depends: libc6, libstdc++6, libgcc-s1, libgl1, libegl1, libpulse0, libxkbcommon0, libxkbcommon-x11-0, libxcb-cursor0, libxcb-icccm4, libxcb-keysyms1, libxcb-shape0, libxcb-xinerama0, libxcb-randr0, libxcb-render-util0, libxcb-xfixes0, libxcb-xkb1, libdbus-1-3, libfontconfig1, libx11-xcb1
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

dpkg-deb --build package "dist-deb/parin-pdf_${VERSION}_amd64.deb"

echo
echo "SUCCESS:"
echo "  $ROOT/dist-deb/parin-pdf_${VERSION}_amd64.deb"
