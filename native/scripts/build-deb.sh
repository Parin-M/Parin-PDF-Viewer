#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="$(sed -n 's/^    VERSION \([0-9.]*\)$/\1/p' "$ROOT/CMakeLists.txt" | head -n 1)"
if [[ -z "$VERSION" ]]; then
  echo "Could not read the native application version from CMakeLists.txt." >&2
  exit 1
fi

BUILD_DIR="${PARIN_BUILD_DIR:-$ROOT/build/native}"
STAGE="$ROOT/build/deb-root"
ARCH="$(dpkg --print-architecture)"
PACKAGE_DIR="$ROOT/dist-native"

cmake -S "$ROOT" -B "$BUILD_DIR" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DBUILD_TESTING=ON
cmake --build "$BUILD_DIR" --parallel
ctest --test-dir "$BUILD_DIR" --output-on-failure

rm -rf "$STAGE" "$PACKAGE_DIR"
mkdir -p "$STAGE" "$PACKAGE_DIR"
DESTDIR="$STAGE" cmake --install "$BUILD_DIR"

mkdir -p "$STAGE/DEBIAN"
DEPENDENCIES="$(cd "$ROOT" && dpkg-shlibdeps -O -e"$STAGE/usr/bin/parin-native" | sed -n 's/^shlibs:Depends=//p')"
if [[ -z "$DEPENDENCIES" ]]; then
  echo "Could not determine shared-library runtime dependencies." >&2
  exit 1
fi

cat > "$STAGE/DEBIAN/control" <<EOF
Package: parin-pdf
Version: $VERSION
Section: office
Priority: optional
Architecture: $ARCH
Maintainer: Parin
Depends: $DEPENDENCIES
Description: Parin native PDF workspace
 Native C++/Qt PDF reader using the MuPDF C API and a Rust render cache.
EOF

dpkg-deb --root-owner-group --build "$STAGE" "$PACKAGE_DIR/parin-pdf_${VERSION}_${ARCH}.deb"
echo "Built: $PACKAGE_DIR/parin-pdf_${VERSION}_${ARCH}.deb"
