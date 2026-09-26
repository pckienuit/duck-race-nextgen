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
        for _ in range(100):
            if ev('document.readyState === "complete" && !!window.game'): break
            time.sleep(0.025)
        ev('sound.enabled=false;game.optSound.checked=false;game.optTTS.checked=false;game.optSlowmo.checked=false;game.optDrama.checked=false;')

    fresh()
    check('Default simulation RNG does not call FX Math.random', "(()=>{const old=Math.random;let calls=0;Math.random=()=>{calls++;return .4};game.simRandom();Math.random=old;return calls===0})()")
    check('Cosmetic wobble does not consume simulation RNG', "(()=>{let calls=0;game.setSimRng(()=>{calls++;return .4});game.setNames(['A','B']);return calls===0})()")
    fresh()
    ev("game.setNames(['A','B']);game.totalDuration=5;game.startRace();for(let i=0;i<2400&&game.state==='racing';i++)game.update(1/60)")
    ev('new Promise(r=>setTimeout(r,850))')
    check('Results contain shared mascot avatars', "document.querySelectorAll('#results-body canvas').length===2 && !!document.querySelector('#winner-avatar')")
    check('Resize does not unlock background behind result dialog', "(()=>{game.resize();return game.sidebar.inert&&game.stageContainer.inert})()")
    fresh()
    check('Sub-nanosecond crossings preserve actual order', "(()=>{game.setNames(['A','B']);game.startRace();game.ducks.forEach((d,i)=>{d.update=function(){this.prevProgress=i?.95:.5;this.rawProgress=i?1.05:1.5-1e-9;this.progress=1}});game.update(.1);return game.finishedDucks[0].name==='B'&&game.finishedDucks[0].finishTime<game.finishedDucks[1].finishTime})()")
    fresh()
    check('Single view height and duck overlap on crowded roster', "(()=>{game.setNames(Array.from({length:100},(_,i)=>'Vịt '+i));const s=document.querySelector('#stage-container');return s.scrollHeight<=s.clientHeight+1 && game.ducks[1].laneY-game.ducks[0].laneY<20 && game.ducks.every(d=>d.laneY>=game.trackPaddingTop&&d.laneY<=game.height-game.trackPaddingBottom)})()")
    check('Reduced motion removes cosmetic bob and spin', "(()=>{game.setNames(['A','B']);game.reducedMotion=true;game.startRace();game.update(.1);return game.ducks.every(d=>d.currentY===d.laneY)})()")
    (ROOT/'parent-light-evidence.json').write_text(json.dumps(checks,indent=2))
    print(f"{sum(c['pass'] for c in checks)}/{len(checks)} passed")
finally:
    proc.terminate()
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
    shutil.rmtree(profile, ignore_errors=True)

if not all(c['pass'] for c in checks):
    raise SystemExit(1)
