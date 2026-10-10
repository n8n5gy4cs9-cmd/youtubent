# Tasks (keep updated — `[x]` done, `[ ]` todo). Mirror in PRD.json.

## Phase 0 — Planning
- [x] T00 PRD.md, PRD.json, task.md written

## Phase 1 — Core (no Qt)
- [x] T01 Project scaffold, requirements.txt, .gitignore
- [x] T02 models.py + time format/parse + project save/load
- [x] T03 urls.py (video id parsing)
- [x] T04 points.py (even / random generation)
- [x] T05 downloader.py (yt-dlp info + download)
- [x] T06 frames.py (ffmpeg frame grab)
- [x] T07 storyboard.py (grid compose, captions, timestamps, PNG/JPG/PDF)
- [x] T08 captions.py + settings.py

## Phase 2 — Sprites
- [x] T09 tools/make_sprites.py generates all icons, app icon, spinner, illustrations

## Phase 3 — UI
- [x] T10 theme.py (dark QSS + icon loader)
- [x] T11 workers.py
- [x] T12 preview.py
- [x] T13 timeline.py (draggable markers)
- [x] T14 gallery.py (reorder/remove/include)
- [x] T15 side_panels.py (Point + Export panels)
- [x] T16 main_window.py wiring, shortcuts, status bar, project open/save, autosave
- [x] T17 app.py entry + `python -m youtubent`

## Phase 4 — Ship
- [x] T18 pytest tests (core + offscreen UI smoke)
- [x] T19 guide.html
- [x] T20 PyInstaller spec + build_mac.sh
- [x] T21 README, final PRD.json/task.md sync
