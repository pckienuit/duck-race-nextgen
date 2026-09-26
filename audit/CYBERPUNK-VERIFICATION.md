# Cyberpunk + complete race classification

## Delivered
- Self-contained index.html: dark circuit Canvas, cyan/magenta HUD, acid-yellow CTA, angular console, neon duck visors.
- Race completes only after every participant crosses. Full result table uses recorded rank, participant ID, name, interpolated simulation finish time and gap to first place.
- Closing/Escape preserves results, Xếp hạng reopens them. Reset, roster edits and new race clear current results. Results are session-only, not persisted across reload.
- Results dialog is outside the stage, with inert background, focus loop and restoration, scrollable table and responsive action buttons.
- Active/paused races guard presets and input rebuilds; duplicate-name elimination uses the winning ID.

## Executed verification
`python audit/test_cyberpunk.py`: 38/38 assertions passed on real headless Chromium.
- All participants classified exactly once for 2, 8, 32 and 100 participant rosters.
- Ordered finite times and contiguous ranks; top-three finish does not truncate race.
- Result modal and last row reachable at 320x568, 390x844, 768x1024, 1440x900 and 844x390.
- Mobile start/pause/resume/reset, close/reopen, pending-result cancellation, duplicate names, literal HTML names and real RAF race.
- No uncaught JavaScript exceptions.
- Extracted inline JS passed `node --check`; `git diff --check` passed.
- Standalone vanilla HTML/JS has no TypeScript or Bun test configuration; assertions run through Python/CDP instead.

Evidence: cyberpunk-evidence.json. Theme source draft: cyberpunk-theme.css; integrated adjustments in index.html are authoritative.

## Limits
No claim of cross-browser or physical-device verification, WCAG certification, provable random fairness or FPS independence. Existing variable-step simulation remains. Large rosters have complete results, but lane labels can crowd during the live race. Duration is a simulation target, not an exact wall-clock deadline. This verification supersedes older blanket claims that all prior audit findings were resolved.
