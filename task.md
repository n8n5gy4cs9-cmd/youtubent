# Tasks (keep updated — `[x]` done, `[ ]` todo). Mirror in PRD.json.

## Phase 0 — Planning
- [x] T00 PRD.md, PRD.json, task.md written

## Phase 1 — Core (no Qt)
- [ ] T01 Project scaffold, requirements.txt, .gitignore
- [ ] T02 models.py + time format/parse + project save/load
- [ ] T03 urls.py (video id parsing)
- [ ] T04 points.py (even / random generation)
- [ ] T05 downloader.py (yt-dlp info + download)
- [ ] T06 frames.py (ffmpeg frame grab)
- [ ] T07 storyboard.py (grid compose, captions, timestamps, PNG/JPG/PDF)
- [ ] T08 captions.py + settings.py

## Phase 2 — Sprites
- [ ] T09 tools/make_sprites.py generates all icons, app icon, spinner, illustrations

## Phase 3 — UI
- [ ] T10 theme.py (dark QSS + icon loader)
- [ ] T11 workers.py
- [ ] T12 preview.py
- [ ] T13 timeline.py (draggable markers)
- [ ] T14 gallery.py (reorder/remove/include)
- [ ] T15 side_panels.py (Point + Export panels)
- [ ] T16 main_window.py wiring, shortcuts, status bar, project open/save, autosave
- [ ] T17 app.py entry + `python -m youtubent`

## Phase 4 — Ship
- [ ] T18 pytest tests (core + offscreen UI smoke)
- [ ] T19 guide.html
- [ ] T20 PyInstaller spec + build_mac.sh
- [ ] T21 README, final PRD.json/task.md sync
