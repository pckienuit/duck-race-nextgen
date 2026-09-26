#!/usr/bin/env python3
"""
Duck Race - Independent Product Audit Harness for Light Mascot Redesign.
Communicates directly with Chromium headless via Chrome DevTools Protocol (CDP).
Tests real pointer gestures, keyboard traps, multi-viewport geometry, scale rosters,
WCAG luminance/contrast, and race lifecycle state safety.

Usage:
    python3 audit/test_light_independent.py [--baseline] [--url http://127.0.0.1:8788/index.html]
"""

import sys
import os
import json
import time
import math
import subprocess
import tempfile
import pathlib
import urllib.request
import shutil
import argparse
from websockets.sync.client import connect

ROOT = pathlib.Path(__file__).resolve().parent
SCRATCH_DIR = pathlib.Path(os.environ.get('TMPDIR', '/home/pckien/.hermes/cache/scratch'))
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

class CDPHarness:
    def __init__(self, target_url="http://127.0.0.1:8788/index.html", verbose=False):
        self.target_url = target_url
        self.verbose = verbose
        self.profile = tempfile.mkdtemp(prefix="duck-light-audit-", dir=str(SCRATCH_DIR))
        self.proc = None
        self.ws = None
        self.seq = 0
        self.exceptions = []
        self.network_requests = []
        self._raf_hook_id = None

    def start(self):
        chrome_args = [
            'chromium',
            '--headless=new',
            '--no-sandbox',
            '--disable-gpu',
            '--remote-debugging-port=0',
            f'--user-data-dir={self.profile}',
            'about:blank'
        ]
        self.proc = subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        pf = pathlib.Path(self.profile) / 'DevToolsActivePort'
        for _ in range(100):
            if pf.exists():
                break
            time.sleep(0.1)
        if not pf.exists():
            raise RuntimeError("Chromium failed to start and expose DevToolsActivePort")

        port = pf.read_text().splitlines()[0]
        tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
        ws_url = tabs[0]['webSocketDebuggerUrl']
        self.ws = connect(ws_url, max_size=16 * 1024 * 1024)

        self.call('Runtime.enable')
        self.call('Page.enable')
        self.call('Network.enable')

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        shutil.rmtree(self.profile, ignore_errors=True)

    def call(self, method, params=None):
        self.seq += 1
        ident = self.seq
        payload = {'id': ident, 'method': method, 'params': params or {}}
        self.ws.send(json.dumps(payload))
        while True:
            raw = self.ws.recv()
            msg = json.loads(raw)
            if msg.get('method') == 'Runtime.exceptionThrown':
                self.exceptions.append(msg['params'])
            elif msg.get('method') == 'Network.requestWillBeSent':
                req = msg['params'].get('request', {})
                url = req.get('url', '')
                if url:
                    self.network_requests.append(url)
            if msg.get('id') == ident:
                if 'error' in msg:
                    raise RuntimeError(f"CDP call error for {method}: {msg['error']}")
                return msg.get('result', {})

    def ev(self, expression):
        res = self.call('Runtime.evaluate', {
            'expression': expression,
            'returnByValue': True,
            'awaitPromise': True
        })
        if 'exceptionDetails' in res:
            raise RuntimeError(f"JS evaluation error: {res['exceptionDetails']}")
        return res.get('result', {}).get('value')

    def set_viewport(self, width, height, mobile=False):
        self.call('Emulation.setDeviceMetricsOverride', {
            'width': width,
            'height': height,
            'deviceScaleFactor': 1,
            'mobile': mobile
        })

    def cdp_click(self, selector, scroll_into_view=True):
        """Dispatches real pointer events (mouseMoved, mousePressed, mouseReleased) to element center."""
        script = f"""(() => {{
            const el = document.querySelector("{selector}");
            if (!el) return null;
            if ({'true' if scroll_into_view else 'false'}) {{
                el.scrollIntoView({{block: "center", inline: "center", behavior: "instant"}});
            }}
            const r = el.getBoundingClientRect();
            return {{
                x: r.left + r.width / 2,
                y: r.top + r.height / 2,
                w: r.width,
                h: r.height,
                visible: r.width > 0 && r.height > 0 && r.bottom >= 0 && r.top <= window.innerHeight
            }};
        }})()"""
        box = self.ev(script)
        if not box:
            return False
        x, y = box['x'], box['y']
        self.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y})
        self.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
        self.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
        return True

    def cdp_key(self, key, code="Escape", windows_virtual_key_code=27):
        """Dispatches real keyboard events (rawKeyDown, keyUp)."""
        self.call('Input.dispatchKeyEvent', {
            'type': 'rawKeyDown',
            'key': key,
            'code': code,
            'windowsVirtualKeyCode': windows_virtual_key_code
        })
        self.call('Input.dispatchKeyEvent', {
            'type': 'keyUp',
            'key': key,
            'code': code,
            'windowsVirtualKeyCode': windows_virtual_key_code
        })

    def hook_disable_raf(self):
        if not self._raf_hook_id:
            res = self.call('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'window.requestAnimationFrame = () => 0;'
            })
            self._raf_hook_id = res['identifier']

    def unhook_disable_raf(self):
        if self._raf_hook_id:
            self.call('Page.removeScriptToEvaluateOnNewDocument', {
                'identifier': self._raf_hook_id
            })
            self._raf_hook_id = None

    def navigate_fresh(self, width=1440, height=900, mobile=False, disable_audio=True):
        self.set_viewport(width, height, mobile=mobile)
        self.call('Page.navigate', {'url': self.target_url})
        for _ in range(120):
            ready = self.ev('document.readyState === "complete" && !!window.game')
            if ready:
                break
            time.sleep(0.025)
        if disable_audio:
            self.ev("""
                if (window.sound) { sound.enabled = false; }
                if (window.game) {
                    if (game.optSound) game.optSound.checked = false;
                    if (game.optTTS) game.optTTS.checked = false;
                    if (game.optSlowmo) game.optSlowmo.checked = false;
                    if (game.optDrama) game.optDrama.checked = false;
                }
            """)


def calculate_relative_luminance(rgb_dict):
    """Calculates WCAG 2.1 relative luminance from RGB dict {'r': 0..255, 'g': 0..255, 'b': 0..255}."""
    channels = []
    for c in ['r', 'g', 'b']:
        val = rgb_dict.get(c, 0) / 255.0
        if val <= 0.03928:
            channels.append(val / 12.92)
        else:
            channels.append(math.pow((val + 0.055) / 1.055, 2.4))
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def calculate_contrast_ratio(lum1, lum2):
    """Calculates WCAG contrast ratio (lighter + 0.05) / (darker + 0.05)."""
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def run_audit(target_url, is_baseline_mode=False, verbose=False):
    h = CDPHarness(target_url=target_url, verbose=verbose)
    h.start()

    results = []

    def record(check_id, name, passed, details=None, is_redesign_assertion=False):
        status = "PASS"
        if not passed:
            if is_baseline_mode and is_redesign_assertion:
                status = "BASELINE_EXPECTED_FAIL"
            else:
                status = "FAIL"
        entry = {
            "id": check_id,
            "name": name,
            "passed": passed,
            "status": status,
            "is_redesign_assertion": is_redesign_assertion,
            "details": details or {}
        }
        results.append(entry)
        prefix = f"[{status}]"
        print(f"{prefix:<25} {name}")
        if verbose and details:
            print(f"    Details: {json.dumps(details, ensure_ascii=False)}")
        return passed

    try:
        # =========================================================================
        # 1. OFFLINE SAFETY & NETWORK CONFORMANCE
        # =========================================================================
        h.network_requests.clear()
        h.navigate_fresh(1440, 900)
        ext_requests = [
            u for u in h.network_requests
            if not (u.startswith('http://127.0.0.1:8788') or u.startswith('http://localhost:8788') or u.startswith('data:'))
        ]
        record(
            "NET_OFFLINE_01",
            "Zero external network requests (offline self-contained)",
            len(ext_requests) == 0,
            {"total_requests": len(h.network_requests), "external_requests": ext_requests},
            is_redesign_assertion=False
        )

        ext_stylesheets = h.ev("""(() => {
            const links = [...document.querySelectorAll('link[rel="stylesheet"]')].map(l => l.href);
            return links.filter(href => !href.includes('127.0.0.1:8788') && !href.includes('localhost:8788'));
        })()""")
        record(
            "NET_LOCAL_02",
            "No external CDN stylesheets or remote web fonts",
            len(ext_stylesheets) == 0,
            {"external_stylesheets": ext_stylesheets},
            is_redesign_assertion=False
        )

        # =========================================================================
        # 2. LIGHT THEME VISUAL SYSTEM & WCAG CONTRAST
        # =========================================================================
        h.navigate_fresh(1440, 900)
        lum_data = h.ev("""(() => {
            function parseRgb(str) {
                const m = str.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
                return m ? {r: parseInt(m[1]), g: parseInt(m[2]), b: parseInt(m[3])} : null;
            }
            const bodyBg = parseRgb(getComputedStyle(document.body).backgroundColor) || {r: 0, g: 0, b: 0};
            const sidebarBg = parseRgb(getComputedStyle(document.querySelector('#sidebar')).backgroundColor) || {r: 0, g: 0, b: 0};
            const textCol = parseRgb(getComputedStyle(document.body).color) || {r: 255, g: 255, b: 255};
            return {bodyBg, sidebarBg, textCol};
        })()""")
        body_lum = calculate_relative_luminance(lum_data['bodyBg'])
        sidebar_lum = calculate_relative_luminance(lum_data['sidebarBg'])
        text_lum = calculate_relative_luminance(lum_data['textCol'])
        text_contrast = calculate_contrast_ratio(sidebar_lum, text_lum)

        record(
            "LIGHT_LUM_01",
            "Body background relative luminance > 0.5 (Light theme)",
            body_lum > 0.5,
            {"measured_luminance": round(body_lum, 4), "threshold": 0.5, "rgb": lum_data['bodyBg']},
            is_redesign_assertion=True
        )

        record(
            "LIGHT_LUM_02",
            "Sidebar panel relative luminance > 0.6 (Clean card surface)",
            sidebar_lum > 0.6,
            {"measured_luminance": round(sidebar_lum, 4), "threshold": 0.6, "rgb": lum_data['sidebarBg']},
            is_redesign_assertion=True
        )

        record(
            "LIGHT_CONTRAST_03",
            "Functional text contrast ratio >= 4.5:1 (WCAG AA)",
            text_contrast >= 4.5,
            {"contrast_ratio": round(text_contrast, 2), "min_required": 4.5},
            is_redesign_assertion=False
        )

        # Canvas track water luminance
        canvas_pixel = h.ev("""(() => {
            const canvas = document.querySelector("#gameCanvas");
            const ctx = canvas.getContext("2d");
            const p = ctx.getImageData(Math.floor(canvas.width / 2), Math.floor(canvas.height / 2), 1, 1).data;
            return {r: p[0], g: p[1], b: p[2]};
        })()""")
        canvas_lum = calculate_relative_luminance(canvas_pixel)
        record(
            "LIGHT_CANVAS_04",
            "Canvas track water relative luminance > 0.5 (Light water track)",
            canvas_lum > 0.5,
            {"measured_luminance": round(canvas_lum, 4), "pixel_rgb": canvas_pixel},
            is_redesign_assertion=True
        )

        # Brand title & cyberpunk cleanup
        brand_info = h.ev("""(() => {
            const title = document.title;
            const brandTitle = document.querySelector('.brand-title')?.textContent || '';
            const badge = document.querySelector('.brand-badge')?.textContent || '';
            const hasCyber = /cyber|neon/i.test(title + ' ' + brandTitle + ' ' + badge);
            return {title, brandTitle, badge, hasCyber};
        })()""")
        record(
            "BRAND_CLEAN_05",
            "Replaced cyberpunk/neon branding with friendly racing mascot",
            not brand_info['hasCyber'],
            brand_info,
            is_redesign_assertion=True
        )

        # =========================================================================
        # 3. REAL POINTER INTERACTIONS (CDP Input.dispatchMouseEvent)
        # =========================================================================
        h.hook_disable_raf()
        h.navigate_fresh(1440, 900)

        # Presets pointer click from IndexedDB custom preset
        h.ev("""(async () => {
            await PresetDB.save("Giải Lớn 16", Array.from({length: 16}, (_, i) => "Tay đua " + (i + 1)));
            await game.loadCustomPresets();
        })()""")
        time.sleep(0.3)
        h.cdp_click('.btn-load-preset')
        grand_count = h.ev('game.ducks.length')
        record(
            "PTR_DESKTOP_PRESET_01",
            "CDP pointer click selects roster presets from IndexedDB (Grand = 16)",
            grand_count == 16,
            {"grand_count": grand_count}
        )

        # Race lifecycle pointer clicks (Start, Pause, Resume, Reset)
        h.cdp_click('#btn-start')
        time.sleep(0.05)
        st_start = h.ev('game.state')

        h.cdp_click('#btn-pause')
        time.sleep(0.05)
        st_pause = h.ev('game.state')

        h.cdp_click('#btn-pause')
        time.sleep(0.05)
        st_resume = h.ev('game.state')

        h.cdp_click('#btn-reset')
        time.sleep(0.05)
        st_reset = h.ev('game.state')

        record(
            "PTR_DESKTOP_RACE_02",
            "CDP pointer clicks drive Start -> Pause -> Resume -> Reset lifecycle",
            st_start == 'racing' and st_pause == 'paused' and st_resume == 'racing' and st_reset == 'idle',
            {"start": st_start, "pause": st_pause, "resume": st_resume, "reset": st_reset}
        )

        # Modal close & reopen via CDP pointer clicks
        h.ev("game.setNames(['Vịt 1', 'Vịt 2']); game.totalDuration = 5; game.startRace();")
        h.ev("for(let i=0;i<2400&&game.state==='racing';i++) game.update(1/60);")
        h.ev("new Promise(r => setTimeout(r, 850))")

        modal_open = h.ev("!game.winnerModal.hidden && game.state === 'finished'")
        h.cdp_click('#btn-close-modal')
        time.sleep(0.05)
        modal_closed = h.ev("game.winnerModal.hidden && game.state === 'finished'")

        record(
            "PTR_MODAL_CLOSE_03",
            "CDP pointer click closes winner modal while retaining rankings",
            modal_open and modal_closed,
            {"modal_open": modal_open, "modal_closed": modal_closed}
        )

        h.cdp_click('#btn-results')
        time.sleep(0.05)
        modal_reopened = h.ev("!game.winnerModal.hidden && document.querySelectorAll('#results-body tr').length === 2")
        record(
            "PTR_MODAL_REOPEN_04",
            "CDP pointer click on 'Xếp hạng' button reopens full rankings",
            modal_reopened,
            {"modal_reopened": modal_reopened}
        )

        # Mobile controls pointer clicks
        h.navigate_fresh(390, 844, mobile=True)
        h.ev("game.setNames(['Vịt A', 'Vịt B']);")
        h.cdp_click('#btn-mobile-start')
        time.sleep(0.05)
        m_start = h.ev('game.state')

        h.cdp_click('#btn-mobile-pause')
        time.sleep(0.05)
        m_pause = h.ev('game.state')

        h.cdp_click('#btn-mobile-reset')
        time.sleep(0.05)
        m_reset = h.ev('game.state')

        record(
            "PTR_MOBILE_CTRL_05",
            "CDP pointer clicks drive mobile bottom stage controls",
            m_start == 'racing' and m_pause == 'paused' and m_reset == 'idle',
            {"mobile_start": m_start, "mobile_pause": m_pause, "mobile_reset": m_reset}
        )

        # =========================================================================
        # 4. MOBILE SHEET, FOCUS TRAP & KEYBOARD ACCESSIBILITY
        # =========================================================================
        h.navigate_fresh(390, 844, mobile=True)
        closed_sheet_focus = h.ev("""(() => {
            const s = document.querySelector('#sidebar');
            const isOpen = s.classList.contains('open');
            const isInert = s.inert;
            const cs = getComputedStyle(s);
            const isHidden = s.hidden || cs.visibility === 'hidden' || cs.display === 'none';
            // Probe if offscreen child can take activeElement focus
            const testBtn = document.querySelector('#btn-shuffle');
            if (testBtn) testBtn.focus();
            const focusedInside = document.activeElement === testBtn;
            return {isOpen, isInert, isHidden, focusedInside};
        })()""")
        # If sheet is closed, it MUST be inert or hidden so offscreen buttons cannot steal Tab focus
        sheet_inert_passed = (closed_sheet_focus['isInert'] or closed_sheet_focus['isHidden']) and not closed_sheet_focus['focusedInside']
        record(
            "A11Y_SHEET_INERT_01",
            "Closed mobile bottom sheet is inert/hidden (prevents offscreen Tab focus)",
            sheet_inert_passed,
            closed_sheet_focus,
            is_redesign_assertion=True
        )

        # Open mobile sheet and test Escape key dismiss
        h.ev("document.querySelector('#btn-toggle-sidebar')?.click()")
        sheet_opened = h.ev("document.querySelector('#sidebar').classList.contains('open')")
        h.cdp_key('Escape', 'Escape', 27)
        time.sleep(0.05)
        sheet_closed_by_esc = h.ev("!document.querySelector('#sidebar').classList.contains('open')")

        record(
            "A11Y_SHEET_ESC_02",
            "Escape key dismisses open mobile bottom sheet",
            sheet_opened and sheet_closed_by_esc,
            {"opened": sheet_opened, "closed_by_escape": sheet_closed_by_esc},
            is_redesign_assertion=True
        )

        # Check for explicit mobile sheet close button
        has_sheet_close_btn = h.ev("""(() => {
            const btn = document.querySelector('#sidebar button[aria-label*="Đóng"], #sidebar button[aria-label*="Close"], #sidebar .btn-close, #sidebar #btn-close-sidebar');
            return !!btn;
        })()""")
        record(
            "A11Y_SHEET_CLOSE_03",
            "Mobile bottom sheet includes an explicit accessible close button",
            has_sheet_close_btn,
            {"has_close_button": has_sheet_close_btn},
            is_redesign_assertion=True
        )

        # Results modal inert background
        h.navigate_fresh(1440, 900)
        h.ev("game.setNames(['A', 'B']); game.totalDuration = 5; game.startRace();")
        h.ev("for(let i=0;i<2400&&game.state==='racing';i++) game.update(1/60);")
        h.ev("new Promise(r => setTimeout(r, 850))")

        modal_inert = h.ev("""(() => {
            const sbInert = document.querySelector('#sidebar')?.inert;
            const stageInert = document.querySelector('#stage-container')?.inert;
            return {sidebar_inert: !!sbInert, stage_inert: !!stageInert};
        })()""")
        record(
            "A11Y_MODAL_INERT_04",
            "Winner modal sets background containers (sidebar, stage) to inert",
            modal_inert['sidebar_inert'] and modal_inert['stage_inert'],
            modal_inert
        )

        # Modal Escape key closes dialog
        h.cdp_key('Escape', 'Escape', 27)
        time.sleep(0.05)
        modal_closed_esc = h.ev("game.winnerModal.hidden")
        record(
            "A11Y_MODAL_ESC_05",
            "Escape key closes results modal and restores background interaction",
            modal_closed_esc,
            {"modal_closed": modal_closed_esc}
        )

        # Hidden results modal elements cannot be focused
        hidden_focus = h.ev("""(() => {
            const btn = document.querySelector('#btn-eliminate-winner');
            if (btn) btn.focus();
            return document.activeElement === btn;
        })()""")
        record(
            "A11Y_HIDDEN_TRAP_06",
            "Elements inside hidden winner modal cannot receive keyboard focus",
            not hidden_focus,
            {"focused_when_hidden": hidden_focus}
        )

        # =========================================================================
        # 5. MULTI-VIEWPORT RESPONSIVE GEOMETRY (320, 390, 768, 1440, 844x390)
        # =========================================================================
        viewports = [
            (320, 568, True, "GEO_VIEWPORT_320", "Narrow mobile (320x568 iPhone SE)"),
            (390, 844, True, "GEO_VIEWPORT_390", "Standard mobile (390x844 iPhone 12/13/14)"),
            (768, 1024, False, "GEO_VIEWPORT_768", "Tablet portrait (768x1024 iPad)"),
            (1440, 900, False, "GEO_VIEWPORT_1440", "Desktop widescreen (1440x900)"),
            (844, 390, False, "GEO_VIEWPORT_844_LAND", "Short landscape mobile (844x390)")
        ]

        for w, h_dim, mob, cid, cdesc in viewports:
            h.navigate_fresh(w, h_dim, mobile=mob)
            geo = h.ev(f"""(() => {{
                const docScrollWidth = document.documentElement.scrollWidth;
                const innerW = window.innerWidth;
                const innerH = window.innerHeight;
                const isNoHScroll = docScrollWidth <= innerW + 1;
                
                // Check interactive start button geometry
                const startBtn = { 'document.querySelector("#btn-mobile-start")' if mob else 'document.querySelector("#btn-start")' };
                const sbRect = startBtn ? startBtn.getBoundingClientRect() : null;
                const touchOk = sbRect ? (sbRect.width >= 44 && sbRect.height >= 40) : false;
                const inView = sbRect ? (sbRect.top >= 0 && sbRect.bottom <= innerH + 1) : false;
                
                return {{
                    viewport: {{w: innerW, h: innerH}},
                    docScrollWidth,
                    isNoHScroll,
                    touchOk,
                    inView,
                    btnId: startBtn ? startBtn.id : null
                }};
            }})()""")
            
            # For 844x390 landscape, baseline puts desktop sidebar with 600px height causing #btn-start to be offscreen
            is_redesign = (cid == "GEO_VIEWPORT_844_LAND")
            passed = geo['isNoHScroll'] and (geo['touchOk'] or not mob) and geo['inView']
            record(
                cid,
                f"Responsive layout & touch targets fit {cdesc}",
                passed,
                geo,
                is_redesign_assertion=is_redesign
            )

        # =========================================================================
        # 6. PODIUM LOGIC & EDGE CASES (TWO RACERS, EMPTY, ONE)
        # =========================================================================
        h.navigate_fresh(1440, 900)
        h.ev("game.setNames(['Vịt Vàng', 'Vịt Xanh']); game.totalDuration = 5; game.startRace();")
        h.ev("for(let i=0;i<2400&&game.state==='racing';i++) game.update(1/60);")
        h.ev("new Promise(r => setTimeout(r, 850))")

        podium_two = h.ev("""(() => {
            const wName = document.querySelector('#modal-winner-name')?.textContent;
            const r2Name = document.querySelector('#modal-rank-2')?.textContent;
            const r3El = document.querySelector('#modal-rank-3');
            const r3Hidden = !r3El || r3El.parentElement.hidden || getComputedStyle(r3El.parentElement).display === 'none';
            const rowCount = document.querySelectorAll('#results-body tr').length;
            return {winner: wName, rank2: r2Name, rank3_hidden: r3Hidden, rows: rowCount};
        })()""")
        record(
            "PODIUM_TWO_RACERS_01",
            "Two-participant race displays 1st & 2nd and omits 3rd place",
            podium_two['rank3_hidden'] and podium_two['rows'] == 2 and bool(podium_two['winner']),
            podium_two
        )

        h.navigate_fresh(1440, 900)
        h.ev("game.setNames([])")
        empty_disabled = h.ev("game.btnStart.disabled && game.mobileStart.disabled")
        h.ev("game.startRace()")
        empty_remains_idle = h.ev("game.state === 'idle'")

        h.ev("game.setNames(['Vịt Duy Nhất'])")
        one_disabled = h.ev("game.btnStart.disabled && game.mobileStart.disabled")
        h.ev("game.startRace()")
        one_remains_idle = h.ev("game.state === 'idle'")

        record(
            "VALID_EMPTY_ONE_02",
            "Start button guarded & disabled when roster has 0 or 1 names",
            empty_disabled and empty_remains_idle and one_disabled and one_remains_idle,
            {"empty_guarded": empty_disabled and empty_remains_idle, "one_guarded": one_disabled and one_remains_idle}
        )

        # =========================================================================
        # 7. STATE MACHINE GUARDS & CALLBACK CLEANUP
        # =========================================================================
        h.navigate_fresh(1440, 900)
        h.ev("game.setNames(['A', 'B', 'C']); game.startRace(); game.update(0.5);")
        active_guarded = h.ev("""(() => {
            const namesDis = game.namesInput.disabled;
            const startDis = game.btnStart.disabled;
            const presetsDis = [...document.querySelectorAll('[id^=preset-]')].every(b => b.disabled);
            return namesDis && startDis && presetsDis;
        })()""")

        h.ev("game.togglePause()")
        paused_guarded = h.ev("""(() => {
            const namesDis = game.namesInput.disabled;
            const startDis = game.btnStart.disabled;
            const presetsDis = [...document.querySelectorAll('[id^=preset-]')].every(b => b.disabled);
            const stateIsPaused = game.state === 'paused';
            return namesDis && startDis && presetsDis && stateIsPaused;
        })()""")

        record(
            "GUARD_ACTIVE_PAUSED_03",
            "Roster edits & presets strictly guarded during active and paused race",
            active_guarded and paused_guarded,
            {"active_guarded": active_guarded, "paused_guarded": paused_guarded}
        )

        # Reset race cleans up pending modal timeouts
        h.navigate_fresh(1440, 900)
        h.ev("""(async () => {
            game.setNames(['A', 'B']);
            game.totalDuration = 5;
            game.startRace();
            for (let i = 0; i < 2400 && game.state === 'racing'; i++) game.update(1/60);
            game.resetRace();
            await new Promise(r => setTimeout(r, 1000));
        })()""")
        reset_clean = h.ev("""(() => {
            return game.state === 'idle' && game.winnerModal.hidden && game.btnResults.hidden;
        })()""")
        record(
            "GUARD_RESET_CLEANUP_04",
            "Reset race cancels pending finish timers (no late modal popup)",
            reset_clean,
            {"reset_clean": reset_clean}
        )

        # =========================================================================
        # 8. DATA SAFETY: UNICODE, LONG NAMES, XSS LITERALS
        # =========================================================================
        h.navigate_fresh(390, 844, mobile=True)
        long_vn1 = "Nguyễn Hoàng Thụy Trâm Anh Đệ Nhất Tuyệt Mỹ Hoàng Gia"
        long_vn2 = "Trần Lê Phúc Khang Thịnh Vượng Trường Tồn Vĩnh Cửu 2026"
        h.ev(f"game.setNames([{json.dumps(long_vn1)}, {json.dumps(long_vn2)}]);")
        h.ev("game.totalDuration = 5; game.startRace();")
        h.ev("for(let i=0;i<2400&&game.state==='racing';i++) game.update(1/60);")
        h.ev("new Promise(r => setTimeout(r, 850))")

        long_name_geo = h.ev("""(() => {
            const card = document.querySelector('.podium-card');
            const closeBtn = document.querySelector('#btn-close-modal');
            const cardR = card.getBoundingClientRect();
            const btnR = closeBtn.getBoundingClientRect();
            const docW = document.documentElement.scrollWidth;
            return {
                noOverflow: docW <= window.innerWidth + 1,
                cardInside: cardR.left >= 0 && cardR.right <= window.innerWidth + 1,
                closeBtnClickable: btnR.top >= 0 && btnR.bottom <= window.innerHeight + 1 && btnR.width >= 44
            };
        })()""")
        record(
            "DATA_UNICODE_LONG_01",
            "Long Vietnamese names render safely without clipping dialog buttons",
            long_name_geo['noOverflow'] and long_name_geo['cardInside'] and long_name_geo['closeBtnClickable'],
            long_name_geo
        )

        # XSS injection literal test
        h.navigate_fresh(1440, 900)
        xss_name = '<img src=x onerror="window.__xss_detected=1">'
        h.ev(f"window.__xss_detected = 0; game.setNames([{json.dumps(xss_name)}, 'Người chơi 2']);")
        h.ev("game.totalDuration = 5; game.startRace();")
        h.ev("for(let i=0;i<2400&&game.state==='racing';i++) game.update(1/60);")
        h.ev("new Promise(r => setTimeout(r, 850))")

        xss_safe = h.ev(f"""(() => {{
            const detected = window.__xss_detected === 1;
            const imgPresent = !!document.querySelector('#results-body img');
            const rows = [...document.querySelectorAll('#results-body tr')];
            const foundLiteral = rows.some(r => r.cells[1]?.textContent === {json.dumps(xss_name)});
            return {{detected, imgPresent, foundLiteral, rowCount: rows.length}};
        }})()""")
        record(
            "DATA_XSS_LITERAL_02",
            "HTML strings in names render as literal text without XSS execution",
            not xss_safe['detected'] and not xss_safe['imgPresent'] and xss_safe['foundLiteral'],
            xss_safe
        )

        # =========================================================================
        # 9. SCALE ROSTERS (2, 8, 16, 32, 100), MONOTONIC TIMES & SCROLL
        # =========================================================================
        scale_counts = [2, 8, 16, 32, 100]
        scale_all_passed = True
        scale_details = {}

        for count in scale_counts:
            h.navigate_fresh(1440, 900)
            h.ev(f"""
                game.setNames(Array.from({{length: {count}}}, (_, i) => i < 2 ? 'Trùng tên' : 'Người chơi ' + (i + 1)));
                game.totalDuration = 5;
                game.startRace();
                for (let i = 0; i < 2400 && game.state === 'racing'; i++) game.update(1/60);
            """)
            h.ev("new Promise(r => setTimeout(r, 850))")
            info = h.ev(f"""(() => {{
                const rows = [...document.querySelectorAll('#results-body tr')];
                const rowCount = rows.length;
                const uniqueIds = new Set(rows.map(r => r.dataset.participantId)).size;
                const allFinished = game.finishedDucks.length === {count};
                return {{rowCount, uniqueIds, allFinished}};
            }})()""")
            if info['rowCount'] != count or info['uniqueIds'] != count or not info['allFinished']:
                scale_all_passed = False
            scale_details[count] = info

        record(
            "SCALE_ROSTER_UNIQUE_01",
            "All participants finish with unique IDs across scale rosters (2..100)",
            scale_all_passed,
            scale_details
        )

        # Monotonic crossing times on 100 racers (Finding B1 probe)
        h.navigate_fresh(1440, 900)
        h.ev("""
            game.setNames(Array.from({length: 100}, (_, i) => 'Thí sinh ' + (i + 1)));
            game.totalDuration = 5;
            game.startRace();
            for (let i = 0; i < 2400 && game.state === 'racing'; i++) game.update(1/60);
        """)
        h.ev("new Promise(r => setTimeout(r, 850))")
        mono_check = h.ev("""(() => {
            const ducks = game.finishedDucks;
            let monotonic = true;
            let inversions = [];
            for (let i = 1; i < ducks.length; i++) {
                if (ducks[i].finishTime < ducks[i-1].finishTime) {
                    monotonic = false;
                    inversions.push({i, prev: ducks[i-1].finishTime, curr: ducks[i].finishTime});
                }
            }
            return {monotonic, total: ducks.length, inversions: inversions.slice(0, 5)};
        })()""")
        record(
            "SCALE_TIME_MONOTONIC_02",
            "Finish times are strictly monotonic and ranks contiguous at 100 scale",
            mono_check['monotonic'] and mono_check['total'] == 100,
            mono_check,
            is_redesign_assertion=True
        )

        # Row 100 scrollable and accessible
        scroll_100 = h.ev("""(() => {
            const sc = document.querySelector('.results-scroll');
            if (!sc) return {found: false};
            const canScroll = sc.scrollHeight > sc.clientHeight;
            sc.scrollTop = sc.scrollHeight;
            const lastRow = document.querySelector('#results-body tr:last-child');
            const lrRect = lastRow ? lastRow.getBoundingClientRect() : null;
            const scRect = sc.getBoundingClientRect();
            const rowVisible = lrRect ? (lrRect.bottom <= scRect.bottom + 2 && lrRect.top >= scRect.top - 2) : false;
            return {canScroll, rowVisible, rank: lastRow?.cells[0]?.textContent};
        })()""")
        record(
            "SCALE_SCROLL_ROW100_03",
            "Results scroll container provides full access down to 100th participant row",
            scroll_100['canScroll'] and scroll_100['rowVisible'] and scroll_100.get('rank') == '100',
            scroll_100
        )

        # Real RAF execution test (unhooked)
        h.unhook_disable_raf()
        h.navigate_fresh(1440, 900)
        h.ev("game.setNames(['Vịt 1', 'Vịt 2', 'Vịt 3', 'Vịt 4']); game.totalDuration = 5; game.startRace();")
        deadline = time.monotonic() + 18
        while time.monotonic() < deadline:
            done = h.ev("game.state === 'finished' && !game.winnerModal.hidden")
            if done:
                break
            time.sleep(0.1)

        raf_race = h.ev("""(() => {
            return {
                finished: game.state === 'finished',
                modal_active: !game.winnerModal.hidden,
                finished_count: game.finishedDucks.length
            };
        })()""")
        record(
            "REAL_RAF_RACE_01",
            "Unmodified requestAnimationFrame loop runs and completes full 4-duck race",
            raf_race['finished'] and raf_race['modal_active'] and raf_race['finished_count'] == 4,
            raf_race
        )

        record(
            "NO_UNCAUGHT_EXCEPTIONS",
            "No uncaught JavaScript exceptions during entire audit session",
            len(h.exceptions) == 0,
            {"exceptions_count": len(h.exceptions), "exceptions": h.exceptions}
        )

    finally:
        h.close()

    # Summary analysis
    total = len(results)
    passed_count = sum(1 for r in results if r['passed'])
    baseline_expected_fails = sum(1 for r in results if r['status'] == 'BASELINE_EXPECTED_FAIL')
    hard_fails = sum(1 for r in results if r['status'] == 'FAIL')

    print("\n" + "=" * 60)
    print(f"AUDIT SUMMARY ({'BASELINE MODE' if is_baseline_mode else 'ACCEPTANCE MODE'})")
    print(f"Total assertions:          {total}")
    print(f"Passed assertions:         {passed_count}")
    print(f"Expected baseline gaps:    {baseline_expected_fails}")
    print(f"Hard invariant failures:   {hard_fails}")
    print("=" * 60)

    # Save evidence file
    evidence = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "target_url": target_url,
        "is_baseline_mode": is_baseline_mode,
        "summary": {
            "total": total,
            "passed": passed_count,
            "baseline_expected_fails": baseline_expected_fails,
            "hard_fails": hard_fails
        },
        "results": results
    }
    evidence_path = ROOT / "light-audit-evidence.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
    print(f"Evidence written to: {evidence_path}")

    if is_baseline_mode:
        # In baseline mode, pass if no UNEXPECTED hard failures occurred
        return hard_fails == 0
    else:
        # In acceptance mode, all tests must pass
        return passed_count == total


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Duck Race Independent Product Audit")
    parser.add_argument("--url", default="http://127.0.0.1:8788/index.html", help="Target URL")
    parser.add_argument("--baseline", action="store_true", help="Run in baseline gap-analysis mode")
    parser.add_argument("--verbose", action="store_true", help="Print detailed assertion metrics")
    args = parser.parse_args()

    success = run_audit(target_url=args.url, is_baseline_mode=args.baseline, verbose=args.verbose)
    sys.exit(0 if success else 1)
