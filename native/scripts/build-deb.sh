#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="$(sed -n 's/^    VERSION \\([0-9.]*\\)$/\\1/p' "$ROOT/CMakeLists.txt" | head -n 1)"
if [[ -z "$VERSION" ]]; then echo "Could not read application version." >&2; exit 1; fi
BUILD_DIR="${PARIN_BUILD_DIR:-$ROOT/build/native}"
STAGE="$ROOT/build/deb-root"
ARCH="$(dpkg --print-architecture)"
PACKAGE_DIR="$ROOT/dist-native"
APP_BINARY="$STAGE/opt/parin/bin/parin-native"
LIB_DIR="$STAGE/opt/parin/lib"
PLUGIN_DIR="$LIB_DIR/qt6/plugins"
cmake -S "$ROOT" -B "$BUILD_DIR" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/ -DBUILD_TESTING=ON
cmake --build "$BUILD_DIR" --parallel
ctest --test-dir "$BUILD_DIR" --output-on-failure
rm -rf "$STAGE" "$PACKAGE_DIR"
mkdir -p "$STAGE" "$PACKAGE_DIR"
DESTDIR="$STAGE" cmake --install "$BUILD_DIR"
if [[ ! -x "$APP_BINARY" ]]; then echo "Native executable missing: $APP_BINARY" >&2; exit 1; fi
mkdir -p "$LIB_DIR" "$PLUGIN_DIR"
QT_PLUGIN_SOURCE=""
if command -v qtpaths6 >/dev/null 2>&1; then QT_PLUGIN_SOURCE="$(qtpaths6 --query QT_INSTALL_PLUGINS 2>/dev/null || true)"; elif command -v qtpaths >/dev/null 2>&1; then QT_PLUGIN_SOURCE="$(qtpaths --query QT_INSTALL_PLUGINS 2>/dev/null || true)"; fi
if [[ -z "$QT_PLUGIN_SOURCE" || ! -d "$QT_PLUGIN_SOURCE/platforms" ]]; then echo "Could not locate Qt plugins." >&2; exit 1; fi
PLUGIN_KINDS=(platforms imageformats iconengines platformthemes platforminputcontexts xcbglintegrations wayland-decoration-client wayland-graphics-integration-client wayland-graphics-integration-server wayland-shell-integration tls networkinformation styles generic multimedia)
for kind in "${PLUGIN_KINDS[@]}"; do
 if [[ -d "$QT_PLUGIN_SOURCE/$kind" ]]; then mkdir -p "$PLUGIN_DIR/$kind"; cp -a "$QT_PLUGIN_SOURCE/$kind/." "$PLUGIN_DIR/$kind/"; fi
done
if [[ ! -f "$PLUGIN_DIR/platforms/libqxcb.so" ]]; then echo "Qt xcb platform plugin was not bundled." >&2; exit 1; fi
CORE_ABI_RE='^(linux-vdso\\.so.*|ld-linux[^/]*|ld-[^/]*|libc\\.so\\..*|libm\\.so\\..*|libpthread\\.so\\..*|libdl\\.so\\..*|librt\\.so\\..*|libresolv\\.so\\..*|libutil\\.so\\..*|libnss_[^/]*|libanl\\.so\\..*)$'
declare -a SCAN_QUEUE=("$APP_BINARY")
while IFS= read -r -d '' plugin; do SCAN_QUEUE+=("$plugin"); done < <(find "$PLUGIN_DIR" \\( -type f -o -type l \\) -name '*.so*' -print0)
declare -A SCANNED=()
INDEX=0
while (( INDEX < ${#SCAN_QUEUE[@]} )); do
 ELF_FILE="${SCAN_QUEUE[$INDEX]}"; INDEX=$((INDEX + 1)); [[ -f "$ELF_FILE" ]] || continue
 ELF_REAL="$(readlink -f "$ELF_FILE")"; [[ -n "$ELF_REAL" ]] || continue
 [[ -n "${SCANNED[$ELF_REAL]+x}" ]] && continue; SCANNED["$ELF_REAL"]=1
 while IFS= read -r DEP_PATH; do
  [[ -e "$DEP_PATH" ]] || continue
  DEP_BASE="$(basename "$DEP_PATH")"; [[ "$DEP_BASE" =~ $CORE_ABI_RE ]] && continue
  DEP_REAL="$(readlink -f "$DEP_PATH")"; [[ -f "$DEP_REAL" ]] || continue
  REAL_BASE="$(basename "$DEP_REAL")"
  SONAME="$(readelf -d "$DEP_REAL" 2>/dev/null | sed -n 's/.*(SONAME).*\\[\\(.*\\)\\].*/\\1/p' | head -n 1)"
  [[ -n "$SONAME" ]] || SONAME="$DEP_BASE"; [[ "$SONAME" =~ $CORE_ABI_RE ]] && continue
  if [[ -L "$LIB_DIR/$REAL_BASE" ]]; then rm -f "$LIB_DIR/$REAL_BASE"; fi
  if [[ ! -f "$LIB_DIR/$REAL_BASE" ]]; then cp -L "$DEP_REAL" "$LIB_DIR/$REAL_BASE"; fi
  if [[ "$REAL_BASE" != "$SONAME" ]]; then ln -sfn "$REAL_BASE" "$LIB_DIR/$SONAME"; fi
  SCAN_QUEUE+=("$LIB_DIR/$SONAME")
 done < <(LD_LIBRARY_PATH="$LIB_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" ldd "$ELF_REAL" 2>/dev/null | awk '$2 == "=>" && $3 ~ /^\\// { print $3 } $1 ~ /^\\// { print $1 }')
done
check_runtime() { local output; output="$(LD_LIBRARY_PATH="$LIB_DIR" ldd "$1" 2>&1)" || { echo "$output" >&2; return 1; }; if grep -q 'not found' <<<"$output"; then echo "$output" >&2; return 1; fi; }
check_runtime "$APP_BINARY"
while IFS= read -r -d '' plugin; do check_runtime "$plugin"; done < <(find "$PLUGIN_DIR" \\( -type f -o -type l \\) -name '*.so*' -print0)
mkdir -p "$STAGE/DEBIAN"
DEPENDENCIES="$(cd "$ROOT" && dpkg-shlibdeps -l"$LIB_DIR" -O -e"$APP_BINARY" | sed -n 's/^shlibs:Depends=//p')"
if [[ -z "$DEPENDENCIES" ]]; then echo "Could not determine host runtime dependencies." >&2; exit 1; fi
if grep -Eiq 'libqt6|libgumbo[0-9]*|libmupdf|libmujs|libharfbuzz|libfreetype|libjpeg|libjbig2|libopenjp|liblcms' <<<"$DEPENDENCIES"; then echo "Private runtime dependency leaked: $DEPENDENCIES" >&2; exit 1; fi
cat > "$STAGE/DEBIAN/control" <<EOF
Package: parin-pdf
Version: $VERSION
Section: office
Priority: optional
Architecture: $ARCH
Maintainer: Parin
Depends: $DEPENDENCIES
Description: Parin Persian Grand Edition native PDF workspace
 Persian-inspired native PDF workspace with bundled Qt and PDF engine runtime.
EOF
DEB_PATH="$PACKAGE_DIR/parin-pdf_${VERSION}_${ARCH}.deb"
dpkg-deb --root-owner-group --build "$STAGE" "$DEB_PATH"
dpkg-deb --info "$DEB_PATH"
DEPENDENCY_FIELD="$(dpkg-deb --field "$DEB_PATH" Depends)"
if [[ -z "$DEPENDENCY_FIELD" ]] || grep -Eiq 'libqt6|libgumbo[0-9]*|libmupdf|libmujs|libharfbuzz|libfreetype|libjpeg|libjbig2|libopenjp|liblcms' <<<"$DEPENDENCY_FIELD"; then echo "Unexpected package Depends: $DEPENDENCY_FIELD" >&2; exit 1; fi
echo "Built Parin Persian Grand Edition: $DEB_PATH"
echo "Remaining host ABI dependencies: $DEPENDENCY_FIELD"
