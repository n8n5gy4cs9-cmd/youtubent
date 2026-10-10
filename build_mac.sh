#!/usr/bin/env bash
# Build dist/Youtubent.app (run on a Mac). Works with or without an activated venv.
set -euo pipefail
cd "$(dirname "$0")"

# Pick Python: activated venv > ./.venv > python3 > python
if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then PY="$VIRTUAL_ENV/bin/python"
elif [ -x .venv/bin/python ]; then PY=.venv/bin/python
elif command -v python3 >/dev/null; then PY=python3
elif command -v python >/dev/null; then PY=python
else echo "No Python found. Install Python 3 (https://www.python.org/downloads/)"; exit 1; fi
echo "Using $PY"

"$PY" -c "import PySide6, PyInstaller, yt_dlp, imageio_ffmpeg, PIL" 2>/dev/null || {
  echo "Missing packages. Run: $PY -m pip install -r requirements.txt"; exit 1; }

"$PY" tools/make_sprites.py
"$PY" -m PyInstaller --noconfirm --windowed --name Youtubent \
  --icon assets/app/icon.icns \
  --add-data "assets:assets" \
  --collect-all yt_dlp --collect-all imageio_ffmpeg \
  youtubent/app.py
echo "Done: dist/Youtubent.app"
