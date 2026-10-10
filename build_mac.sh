#!/usr/bin/env bash
# Build dist/Youtubent.app (run on a Mac, inside the venv).
set -euo pipefail
cd "$(dirname "$0")"
python tools/make_sprites.py
pyinstaller --noconfirm --windowed --name Youtubent \
  --icon assets/app/icon.icns \
  --add-data "assets:assets" \
  --collect-all yt_dlp --collect-all imageio_ffmpeg \
  youtubent/app.py
echo "Done: dist/Youtubent.app"
