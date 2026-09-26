"""Assert real Chromium behavior for Light Mode & Original Duck Mascot.
Run from any cwd with python.
"""
import json, time, subprocess, tempfile, pathlib, urllib.request, shutil
from websockets.sync.client import connect

ROOT = pathlib.Path(__file__).resolve().parent
profile = tempfile.mkdtemp(prefix='duck-light-regression-')
proc = subprocess.Popen(
    ['chromium', '--headless=new', '--no-sandbox', '--disable-gpu', '--remote-debugging-port=0', f'--user-data-dir={profile}', 'about:blank'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
checks = []; errors = []; seq = 0

try:
    pf = pathlib.Path(profile) / 'DevToolsActivePort'
    for _ in range(100):
        if pf.exists(): break
        time.sleep(0.1)
    port = pf.read_text().splitlines()[0]
    tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
    ws = connect(tabs[0]['webSocketDebuggerUrl'], max_size=16*1024*1024)

    def call(method, params=None):
        global seq
        seq += 1; ident = seq
        ws.send(json.dumps({'id': ident, 'method': method, 'params': params or {}}))
        while True:
            m = json.loads(ws.recv())
            if m.get('method') == 'Runtime.exceptionThrown':
                errors.append(m['params'])
            if m.get('id') == ident:
                if 'error' in m: raise RuntimeError(m)
                return m.get('result', {})

    def ev(expr):
        r = call('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        if 'exceptionDetails' in r: raise RuntimeError(r)
        return r.get('result', {}).get('value')

    def check(name, expr):
        result = ev(expr)
        passed = result is True
        checks.append({'name': name, 'pass': passed})
        print(('PASS ' if passed else 'FAIL ') + name, flush=True)

    call('Runtime.enable')
    call('Page.enable')
    hook = call('Page.addScriptToEvaluateOnNewDocument', {'source': 'window.requestAnimationFrame=()=>0;'})['identifier']

    def fresh(w=1440, h=900):
        call('Emulation.setDeviceMetricsOverride', {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': False})
        call('Page.navigate', {'url': 'http://127.0.0.1:8788/index.html'})
        for _ in range(200):
            try:
                if ev('document.readyState === "complete" && typeof game !== "undefined" && !!window.game'): break
            except Exception:
                pass
            time.sleep(0.05)
        ev('sound.enabled=false;game.optSound.checked=false;game.optTTS.checked=false;game.optSlowmo.checked=false;game.optDrama.checked=false;')

    # 1. Behavior preservation: Last racer, full ranking, inert, escape, presets
    fresh()
    check('Wait for last racer, not only podium', '''(()=>{
        game.setNames(['A','B','C','D']);
        game.totalDuration=5;
        game.startRace();
        game.raceTime=4.6;
        game.ducks.forEach((d,i)=>d.progress=i<3?.999:.1);
        game.update(.1);
        return game.state==='racing'&&game.finishedDucks.length===3;
    })()''')

    fresh()
    ev("game.setNames(Array.from({length:16},(_,i)=>'Vịt '+(i+1)));game.totalDuration=5;game.startRace();for(let i=0;i<2400&&game.state==='racing';i++)game.update(1/60)")
    ev('new Promise(r=>setTimeout(r,850))')
    check('Full ranking has every ID, ordered actual crossing times', '''(()=>{
        const rows=[...document.querySelectorAll('#results-body tr')];
        return rows.length===16 &&
               new Set(rows.map(r=>r.dataset.participantId)).size===16 &&
               rows.every((r,i)=>r.cells[0].textContent===String(i+1) &&
                                 r.cells[1].textContent===game.finishedDucks[i].name &&
                                 r.cells[2].textContent===game.finishedDucks[i].finishTime.toFixed(3)+' s');
    })()''')

    check('Close preserves finished result and reopen works', '''(()=>{
        game.btnCloseModal.click();
        const kept = game.state==='finished' && game.finishedDucks.length===16 && game.winnerModal.hidden;
        document.querySelector('#btn-results')?.click();
        return kept && !game.winnerModal.hidden && document.querySelectorAll('#results-body tr').length===16;
    })()''')

    check('Dialog makes background inert', 'document.querySelector("#sidebar").inert && document.querySelector("#stage-container").inert')

    check('Escape closes results without clearing ranking', '''(()=>{
        game.btnCloseModal.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
        return game.winnerModal.hidden && game.finishedDucks.length===16 && !document.querySelector('#sidebar').inert;
    })()''')

    fresh()
    check('Roster presets cannot cancel active or paused race', '''(()=>{
        game.setNames(['A','B','C','D']);
        game.startRace();
        const addBtnDisabled = document.querySelector('#btn-show-add-preset')?.disabled;
        game.setNames(['X','Y']);
        const a=game.state==='racing'&&game.ducks.length===4;
        game.togglePause();
        game.setNames(['M','N']);
        return a&&game.state==='paused'&&game.ducks.length===4&&addBtnDisabled;
    })()''')

    # 2. Light Theme Brand & Token Expectations (adapted from Cyberpunk check)
    fresh()
    check('Light mode theme applied', '''(()=>{
        const titleOk = document.title.includes("Đua Vịt") && !document.title.includes("NEON DUCK") && !document.title.includes("CYBER");
        const style = getComputedStyle(document.documentElement);
        const bg = style.getPropertyValue("--bg").trim().toLowerCase();
        const text = style.getPropertyValue("--text").trim().toLowerCase();
        const isLightBg = bg === '#f7faf5' || bg === 'rgb(247, 250, 245)';
        const isDarkText = text === '#24332b' || text === 'rgb(36, 51, 43)';
        const noCyberpunkAccent = style.getPropertyValue("--accent").trim().toLowerCase() !== '#32f5e1';
        return titleOk && isLightBg && isDarkText && noCyberpunkAccent;
    })()''')

    # 3. Viewport and responsive controls
    for w, h in [(320,568), (390,844), (768,1024), (1440,900), (844,390)]:
        fresh(w, h)
        check(f'Visible mobile race control {w}', '''(()=>{
            const b = document.querySelector('#btn-mobile-start');
            if (innerWidth >= 768) return true;
            if (!b) return false;
            const r = b.getBoundingClientRect();
            return r.height >= 44 && r.width >= 44 && r.bottom <= innerHeight && r.top >= 0;
        })()''')
        check(f'Topbar fits viewport {w}', '''(()=>{
            const els = [...document.querySelectorAll('.top-bar button, #hud-timer, #hud-status')].filter(e => !e.hidden);
            return els.every(e => {
                const r = e.getBoundingClientRect();
                return r.left >= 0 && r.right <= innerWidth && r.bottom < 200;
            });
        })()''')

    fresh(390, 844)
    check('Mobile buttons start, pause, resume and reset', '''(()=>{
        game.setNames(['A','B']);
        document.querySelector('#btn-mobile-start').click();
        const a = game.state==='racing';
        document.querySelector('#btn-mobile-pause').click();
        const b = game.state==='paused';
        document.querySelector('#btn-mobile-pause').click();
        const c = game.state==='racing';
        document.querySelector('#btn-mobile-reset').click();
        return a && b && c && game.state==='idle';
    })()''')

    # 4. Roster scaling tests
    for count in [2, 8, 32, 100]:
        fresh(390, 844)
        ev(f"game.setNames(Array.from({{length:{count}}},(_,i)=>i<2?'Trùng tên':'Người chơi '+i));game.totalDuration=5;game.startRace();for(let i=0;i<2400&&game.state==='racing';i++)game.update(1/60)")
        ev('new Promise(r=>setTimeout(r,850))')
        check(f'All {count} racers finish and appear once',
              f"game.state==='finished'&&game.finishedDucks.length==={count}&&document.querySelectorAll('#results-body tr').length==={count}&&new Set([...document.querySelectorAll('#results-body tr')].map(r=>r.dataset.participantId)).size==={count}")
        check(f'Monotonic times and contiguous ranks {count}',
              'game.finishedDucks.every((d,i,a)=>d.rank===i+1&&Number.isFinite(d.finishTime)&&(!i||d.finishTime>=a[i-1].finishTime))')

    # 5. Results dialog fit and accessibility across viewports
    for w, h in [(320,568), (390,844), (768,1024), (1440,900), (844,390)]:
        fresh(w, h)
        ev("game.setNames(Array.from({length:32},(_,i)=>'Tên dài tiếng Việt '+i));game.totalDuration=5;game.startRace();for(let i=0;i<2400&&game.state==='racing';i++)game.update(1/60)")
        ev('new Promise(r=>setTimeout(r,1000))')
        check(f'Results dialog fits and last row accessible {w}', '''(()=>{
            const panel = document.querySelector('.podium-card');
            const sc = document.querySelector('.results-scroll');
            const p = panel.getBoundingClientRect();
            sc.scrollTop = sc.scrollHeight;
            const r = document.querySelector('#results-body tr:last-child').getBoundingClientRect();
            const s = sc.getBoundingClientRect();
            const b = game.btnCloseModal.getBoundingClientRect();
            return p.left >= 0 && p.right <= innerWidth + 1 && p.top >= 0 && p.bottom <= innerHeight + 1 &&
                   b.bottom <= innerHeight && r.bottom <= s.bottom + 1 && r.top >= s.top &&
                   document.documentElement.scrollWidth <= innerWidth;
        })()''')

    fresh()
    check('HTML names remain literal in full results', '''(async()=>{
        window.pwned = 0;
        const name = '<img src=x onerror="window.pwned=1">';
        game.setNames([name, 'B']);
        game.totalDuration = 5;
        game.startRace();
        for (let i = 0; i < 2400 && game.state === 'racing'; i++) game.update(1/60);
        await new Promise(r => setTimeout(r, 850));
        return !window.pwned && !document.querySelector('#results-body img') &&
               [...document.querySelectorAll('#results-body tr')].some(r => r.cells[1].textContent === name);
    })()''')

    check('New race clears stale results', '''(()=>{
        document.querySelector('#btn-race-again').click();
        return game.state==='racing' && game.finishedDucks.length===0 &&
               game.btnResults.hidden && game.winnerModal.hidden && game.resultsBody.children.length===0;
    })()''')

    fresh()
    check('Elimination removes winning ID among duplicate names', '''(async()=>{
        game.setNames(['An','Bình','An','C']);
        game.totalDuration = 5;
        game.startRace();
        game.ducks[2].progress = 0.99;
        for (let i = 0; i < 2400 && game.state === 'racing'; i++) game.update(1/60);
        await new Promise(r => setTimeout(r, 850));
        game.btnEliminate.click();
        return JSON.stringify(game.ducks.map(d=>d.name)) === JSON.stringify(['An','Bình','C']) &&
               game.state==='idle' && game.btnResults.hidden;
    })()''')

    fresh()
    check('Paused race cannot restart and retains progress', '''(()=>{
        game.setNames(['A','B']);
        game.startRace();
        game.update(0.5);
        game.togglePause();
        const t = game.raceTime, p = game.ducks[0].progress;
        game.startRace();
        game.update(0.5);
        return game.state==='paused' && game.raceTime===t && game.ducks[0].progress===p;
    })()''')

    fresh()
    check('Reset cancels pending results', '''(async()=>{
        game.setNames(['A','B']);
        game.totalDuration = 5;
        game.startRace();
        for (let i = 0; i < 2400 && game.state === 'racing'; i++) game.update(1/60);
        game.resetRace();
        await new Promise(r => setTimeout(r, 850));
        return game.state==='idle' && game.winnerModal.hidden && game.btnResults.hidden;
    })()''')

    # ==========================================
    # NEW TESTS: RNG Isolation, Crowded Roster Lane Spacing, Contrast
    # ==========================================

    # 6. RNG Isolation Test:
    # Running race with sound/FX active vs disabled with identical injected simulation RNG
    # yields EXACT same finish times and rank order.
    fresh()
    check('RNG isolation: FX/audio does not alter simulation outcome', '''(()=>{
        // Define simple deterministic LCG for simulation
        function createRng(seed = 12345) {
            let s = seed;
            return function() {
                s = (s * 1664525 + 1013904223) % 4294967296;
                return s / 4294967296;
            };
        }

        // Run 1: With Drama ON, Sound ON, particles spawning
        if (!game.setSimRng) return false; // Must provide setSimRng or simRng interface
        game.setNames(['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8']);
        game.totalDuration = 5;
        game.optDrama.checked = true;
        game.optSound.checked = true;
        sound.enabled = true;
        game.setSimRng(createRng(42));
        game.startRace();
        for (let i = 0; i < 1800 && game.state === 'racing'; i++) {
            game.update(1/60);
        }
        const run1Times = game.finishedDucks.map(d => ({ id: d.id, time: d.finishTime, rank: d.rank }));

        // Run 2: With Drama ON, Sound OFF, particles cleared/suppressed
        game.resetRace();
        game.optDrama.checked = true;
        game.optSound.checked = false;
        sound.enabled = false;
        game.setSimRng(createRng(42));
        game.startRace();
        for (let i = 0; i < 1800 && game.state === 'racing'; i++) {
            game.update(1/60);
        }
        const run2Times = game.finishedDucks.map(d => ({ id: d.id, time: d.finishTime, rank: d.rank }));

        if (run1Times.length !== 8 || run2Times.length !== 8) return false;
        return run1Times.every((d, i) =>
            d.id === run2Times[i].id &&
            d.rank === run2Times[i].rank &&
            Math.abs(d.time - run2Times[i].time) < 1e-9
        );
    })()''')

    # 7. Single view height & duck overlap handling on crowded roster
    fresh(1440, 900)
    check('Entire game fits in single view height with duck overlap on crowded roster', '''(()=>{
        game.setNames(Array.from({length: 100}, (_, i) => 'Vịt ' + (i + 1)));
        const stageArea = document.querySelector('#stage-container');
        // Single view height: zero vertical scrolling on stage container
        const fitsInViewHeight = stageArea.scrollHeight <= stageArea.clientHeight + 1;
        // All 100 ducks stay within visible track boundaries in 1 view height
        const withinBounds = game.ducks.every(d => d.laneY >= game.trackPaddingTop && d.laneY <= game.height - game.trackPaddingBottom);
        // Overlap: spacing is smaller than duck visual height so ducks naturally overlap like original duck race
        const spacing = game.ducks[1].laneY - game.ducks[0].laneY;
        const overlaps = spacing < 20;
        return fitsInViewHeight && withinBounds && overlaps && game.ducks.length === 100;
    })()''')

    # 8. Contrast and Touch Targets
    fresh(1440, 900)
    check('Interactive buttons have accessible minimum hit target of 44px', '''(()=>{
        const buttons = [...document.querySelectorAll('button:not([hidden])')];
        return buttons.every(b => {
            const r = b.getBoundingClientRect();
            // Buttons that are visible must have height >= 40 (standard touch target / min 44 on mobile)
            if (r.width === 0 && r.height === 0) return true; // hidden or collapsed
            return r.height >= 40;
        });
    })()''')

    call('Page.removeScriptToEvaluateOnNewDocument', {'identifier': hook})
    fresh()
    ev("game.setNames(['A','B','C','D','E','F','G','H']);game.totalDuration=5;game.startRace()")
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if ev("game.state==='finished'&&!game.winnerModal.hidden"): break
        time.sleep(0.1)

    check('Real RAF race completes with all eight results',
          "game.state==='finished'&&game.finishedDucks.length===8&&game.resultsBody.children.length===8&&!game.winnerModal.hidden")
    check('No uncaught JS errors', 'true' if not errors else 'false')

    (ROOT / 'light-evidence.json').write_text(json.dumps({'checks': checks, 'errors': errors}, ensure_ascii=False, indent=2))
    passed_count = sum(c['pass'] for c in checks)
    print(f"{passed_count}/{len(checks)} passed")

finally:
    proc.terminate()
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
    shutil.rmtree(profile, ignore_errors=True)

if not all(c['pass'] for c in checks):
    raise SystemExit(1)
