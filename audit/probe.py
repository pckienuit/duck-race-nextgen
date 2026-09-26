import json, time, subprocess, tempfile, pathlib, urllib.request, shutil
from websockets.sync.client import connect
ROOT=pathlib.Path(__file__).resolve().parent
profile=tempfile.mkdtemp(prefix='duck-audit-',dir='/home/pckien/.hermes/cache/scratch')
proc=subprocess.Popen(['chromium','--headless=new','--no-sandbox','--disable-gpu','--remote-debugging-port=0',f'--user-data-dir={profile}','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
results={}; errors=[]
try:
    portfile=pathlib.Path(profile)/'DevToolsActivePort'
    for _ in range(100):
        if portfile.exists(): break
        time.sleep(.1)
    port=portfile.read_text().splitlines()[0]
    tabs=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
    ws=connect(tabs[0]['webSocketDebuggerUrl'],max_size=16*1024*1024)
    seq=0
    def call(method,params=None):
        global seq
        seq+=1; ident=seq; ws.send(json.dumps({'id':ident,'method':method,'params':params or {}}))
        while True:
            msg=json.loads(ws.recv())
            if msg.get('method')=='Runtime.exceptionThrown': errors.append(msg['params'])
            if msg.get('id')==ident:
                if 'error' in msg: raise RuntimeError(msg)
                return msg.get('result',{})
    def ev(expression):
        r=call('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True})
        if 'exceptionDetails' in r: raise RuntimeError(r)
        return r.get('result',{}).get('value')
    call('Runtime.enable'); call('Page.enable')
    hook=call('Page.addScriptToEvaluateOnNewDocument',{'source':'window.requestAnimationFrame=()=>0;'})['identifier']
    def fresh(w=1440,h=900):
        call('Emulation.setDeviceMetricsOverride',{'width':w,'height':h,'deviceScaleFactor':1,'mobile':False})
        call('Page.navigate',{'url':'http://127.0.0.1:8788/index.html'})
        for _ in range(100):
            if ev('document.readyState==="complete" && !!window.game'): break
            time.sleep(.025)
        ev('game.optSound.checked=false; sound.enabled=false; game.optTTS.checked=false; game.optSlowmo.checked=false;')
    fresh()
    results['initial'] = ev('({title:document.title,ducks:game.ducks.length,state:game.state})')
    results['start_twice']=ev('''(()=>{game.startRace();game.update(1);let before={t:game.raceTime,p:game.ducks[0].progress};document.querySelector('#btn-start').click();return {before,after:{t:game.raceTime,p:game.ducks[0].progress,state:game.state},disabled:game.btnStart.disabled}})()''')
    fresh()
    results['restart_finished']=ev('''(()=>{game.startRace(); game.ducks.forEach(d=>{d.finished=true;d.progress=1;d.finishTime=1});game.finishedDucks=[...game.ducks];game.state='finished';game.startRace();for(let i=0;i<120;i++)game.update(1/60);return {state:game.state,finishedCount:game.finishedDucks.length,allAlreadyFinished:game.ducks.every(d=>d.finished)}})()''')
    fresh()
    results['edit_mid_race']=ev('''(()=>{game.startRace();game.update(1);game.namesInput.value+='\\nNgười mới';game.namesInput.dispatchEvent(new Event('input'));return {state:game.state,time:game.raceTime,count:game.ducks.length}})()''')
    results['duplicate_elimination']=ev('''(()=>{game.setNames(['An','An','Bình']);game.finishedDucks=[game.ducks[0]];game.btnEliminate.click();return {remaining:game.ducks.map(d=>d.name),state:game.state}})()''')
    fresh()
    results['same_frame_order']=ev('''(()=>{game.setNames(['A','B']);game.optDrama.checked=false;Math.random=()=>.48;game.startRace();game.ducks[0].progress=.991;game.ducks[1].progress=.999;game.update(.1);return game.finishedDucks.map(d=>({name:d.name,time:d.finishTime,rank:d.rank}))})()''')
    fresh()
    results['grace_period_top3']=ev('''(()=>{game.setNames(['A','B','C']);game.totalDuration=30;game.optDrama.checked=false;Math.random=()=>.48;game.startRace();game.ducks[0].progress=.999;game.ducks[1].progress=.2;game.ducks[2].progress=.1;for(let i=0;i<120;i++)game.update(1/60);return {state:game.state,finished:game.finishedDucks.map(d=>d.name),progress:game.ducks.map(d=>d.progress)}})()''')
    fresh()
    results['stale_result_timer']=ev('''(async()=>{game.finishedDucks=[game.ducks[0],game.ducks[1],game.ducks[2]];game.onFinish();game.resetRace();await new Promise(r=>setTimeout(r,1000));return {state:game.state,modalActive:game.winnerModal.classList.contains('active'),winner:game.modalWinnerName.innerText}})()''')
    fresh()
    results['name_xss']=ev('''(async()=>{window.auditXSS=0;game.setNames(['<img src="data:image/png,invalid" onerror="window.auditXSS=1">','B']);await new Promise(r=>setTimeout(r,100));return {executed:window.auditXSS,imgInLeaderboard:!!game.hudLeaderList.querySelector('img')}})()''')
    fresh()
    results['hidden_modal_focus']=ev('''(()=>{game.btnEliminate.focus();return {active:document.activeElement.id,modalOpacity:getComputedStyle(game.winnerModal).opacity,role:game.winnerModal.getAttribute('role'),ariaModal:game.winnerModal.getAttribute('aria-modal')}})()''')
    results['empty_start']=ev('''(()=>{game.setNames([]);return {startDisabled:game.btnStart.disabled,emptyText:game.hudLeaderList.innerText,namesLabel:game.namesInput.labels.length,durationLabel:game.durationInput.labels.length}})()''')
    fresh()
    ev("game.setNames(['Tên thử lưu','Tên thứ hai']);game.durationInput.value='25';game.durationInput.dispatchEvent(new Event('input'))")
    fresh()
    results['reload_persistence']=ev('({names:game.ducks.map(d=>d.name),duration:game.totalDuration})')
    for w,h in [(1440,900),(768,1024),(390,844),(320,568)]:
        fresh(w,h)
        results[f'layout_{w}']=ev('''(()=>{const rect=id=>{let r=document.getElementById(id).getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right}};return {viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,sidebar:rect('sidebar'),stage:rect('stage-container'),timer:rect('hud-timer'),fullscreen:rect('btn-streamer-mode'),start:rect('btn-start'),trackWidth:game.width-160}})()''')
    fresh(1440,900)
    ev("document.querySelector('#preset-grand').click()")
    results['large_roster']=ev('''(()=>{const originalSpacing=game.ducks[1].laneY-game.ducks[0].laneY;game.setNames(Array.from({length:100},(_,i)=>'Tên '+i));return {spacing16:originalSpacing,spacing100:game.ducks[1].laneY-game.ducks[0].laneY,nameTagHeight:18,duckBodyHeight:24}})()''')
    fresh()
    results['duration_and_fps']=ev('''(()=>{const outputs=[];for(const fps of [30,60,120]){let seed=123456;Math.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};let samples=[];for(let run=0;run<100;run++){game.setNames(['A','B','C','D','E','F','G','H']);game.totalDuration=10;game.startRace();let first=null;for(let i=0;i<fps*40 && game.state==='racing';i++){game.update(1/fps);if(first===null&&game.finishedDucks.length)first=game.raceTime}samples.push({first,done:game.raceTime,finished:game.finishedDucks.length});game.resetRace()}outputs.push({fps,firstMean:samples.reduce((s,x)=>s+x.first,0)/samples.length,doneMean:samples.reduce((s,x)=>s+x.done,0)/samples.length,minFinished:Math.min(...samples.map(x=>x.finished))})}return outputs})()''')
    fresh()
    results['duration_change_mid_race']=ev('''(()=>{game.startRace();game.durationInput.value='30';game.durationInput.dispatchEvent(new Event('input'));return {state:game.state,effectiveDuration:game.totalDuration,disabled:game.durationInput.disabled}})()''')
    fresh()
    results['keyboard_button_space']=ev('''(()=>{game.btnShuffle.focus();game.btnShuffle.dispatchEvent(new KeyboardEvent('keydown',{code:'Space',bubbles:true,cancelable:true}));return {focused:document.activeElement.id,state:game.state}})()''')
    fresh()
    results['paused_effects']=ev('''(()=>{game.startRace();game.togglePause();let before={water:game.waterOffset,life:game.particles[0].life,time:game.raceTime};game.update(.1);return {before,after:{water:game.waterOffset,life:game.particles[0].life,time:game.raceTime}}})()''')
    fresh()
    results['slowmo_real_vs_simulated']=ev('''(()=>{game.setNames(['A','B','C']);game.optDrama.checked=false;game.optSlowmo.checked=true;Math.random=()=>.48;game.startRace();let frames=0;while(game.state==='racing'&&frames<3000){game.timeScale+=(game.targetTimeScale-game.timeScale)*.1;game.update((1/60)*game.timeScale);frames++}return {configuredSeconds:10,renderedSeconds:frames/60,timerSeconds:game.raceTime,slowmo:game.slowMoTriggered}})()''')
    fresh()
    results['hud_overlap']=ev('''(()=>{game.setNames(['A','B','C','D','E','F','G','H']);let r=document.querySelector('#hud-leaderboard').getBoundingClientRect(),s=game.canvas.getBoundingClientRect();let x=s.x+game.width-game.trackPaddingX;return {finishX:x,hud:{left:r.left,right:r.right,top:r.top,bottom:r.bottom},occludedLanes:game.ducks.filter(d=>x>=r.left&&x<=r.right&&d.laneY>=r.top&&d.laneY<=r.bottom).map(d=>d.name)}})()''')
    # Actual RAF-driven race in a fresh page, no manual stepping.
    call('Page.removeScriptToEvaluateOnNewDocument',{'identifier':hook})
    fresh()
    ev("game.durationInput.value='5';game.durationInput.dispatchEvent(new Event('input'));document.querySelector('#btn-start').click()")
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        if ev("game.state==='finished' && game.winnerModal.classList.contains('active')"): break
        time.sleep(.1)
    results['live_raf_race']=ev('({state:game.state,time:game.raceTime,finished:game.finishedDucks.length,winner:game.modalWinnerName.innerText,rank2:game.modalRank2.innerText,rank3:game.modalRank3.innerText,modal:game.winnerModal.classList.contains("active")})')
    results['console_exceptions']=errors
    (ROOT/'evidence.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    print(json.dumps(results,ensure_ascii=False,indent=2))
finally:
    proc.terminate()
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: proc.kill();proc.wait()
    shutil.rmtree(profile,ignore_errors=True)
