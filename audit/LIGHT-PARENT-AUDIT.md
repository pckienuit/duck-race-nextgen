# Parent audit: light mascot release

## Scope and actual execution
Parent reran the delivered code in real isolated headless Chromium, reviewed source, and added failure-first probes rather than accepting child summaries.

Final execution:
- python audit/test_light.py: 41/41 passed.
- python audit/test_light_independent.py: 34/34 passed.
- python audit/test_light_parent.py: 7/7 passed after reproducing seven failures before fixes.
- Inline script syntax checked with node --check; git diff --check clean.
- Local server responds HTTP 200 at http://127.0.0.1:8788/index.html.

## Additional defects found and fixed by parent
1. Default simRandom still called Math.random, shared with FX/audio despite injected-seed test passing. Default now draws from crypto.getRandomValues; test injection retained.
2. Cosmetic initial wobble consumed simulation random draws. It now uses FX RNG.
3. Shared renderer existed but results had no duck avatars. Added row and winner Canvas avatars using actual participant skin/accessory.
4. ResizeObserver could unset sidebar inert while result dialog remained open. Sidebar synchronization now prioritizes modal state and collapsed desktop sidebar.
5. Epsilon tie comparison plus timestamp clamping could reverse near-simultaneous actual crossings and conceal the error. Strict finishTime sort now preserves timestamps; randomized per-run tie order used only for exact equal times. No certification of statistical fairness implied.
6. Minimum lane spacing 36px was less than mascot plus name-tag extent. Increased to 64px with vertical scrolling.
7. Reduced motion did not disable cosmetic bob/spin. It now suppresses those transforms while preserving race progression.

Also corrected a weakened viewport assertion in test_light.py which accidentally allowed right <= innerHeight. It now checks innerWidth only and passes.

## Delivered
- index.html: standalone light interface, original rounded Canvas duck mascots, full classification with avatars, scrollable lanes, desktop/mobile controls.
- design/character-sheet.html and design/mockup.html: design references, not canonical production render source.
- Existing source preserved in audit/backups/pre-light-20260926-222604.zip.

## Boundaries of verification
- Tests cover real pointer and keyboard interactions, controlled simulation probes, unmodified RAF races, 2..100 participants, XSS, duplicates, results scrolling, five viewport sizes and sampled functional text contrast.
- This is not a complete WCAG certification. Earlier child claim of 100% contrast compliance is too broad; tests sample elements.
- Parent used DOM geometry and source inspection, not independent pixel-based aesthetic inspection. Child-provided screenshots predate parent fixes.
- Firefox/WebKit, physical phones, 200% zoom and full performance profiling were not verified in this parent audit.
- Engine remains variable-step. No claim of FPS-independent results or exact wall-clock deadline; background throttling and slow-motion affect viewing time.
- No cross-refresh results history added. Config persistence retained.

This report supersedes absolute claims in LIGHT-IMPLEMENTATION.md about complete compliance, initial default RNG isolation, 36px lane adequacy, and timestamp clamping safety.
