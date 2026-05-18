# VAULT-9 Webapp — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the hackathon from a download-based experience to a fully in-browser webapp where stages 3–6 each have an interactive tool (terminal emulator, canvas inspector, SQL editor, Python terminal) powered by embedded data rather than downloadable files.

**Architecture:** All stage data (log file, PNG, SQLite DB, Python script) is embedded inside the AES-GCM encrypted stage payloads. When a stage is unlocked, the decrypted payload contains both the problem HTML and `toolType`/`toolData` fields. A dispatcher renders the appropriate in-browser widget. No backend; still a single static HTML file. configure.py embeds the file data at build time.

**Tech Stack:** xterm.js 5.3 (terminal UI, CDN), sql.js 1.11 (SQLite WASM, CDN), Pyodide 0.26 (Python WASM, CDN — lazy-loaded only when Stage 6 unlocks), vanilla JS, no build step.

---

## File Structure

```
hackathon.html    ← modified: CDN tags, CSS for tools, tool renderers, async renderNextStage
configure.py      ← modified: embed vault_logs.txt / mittens_cam.png / vault_records.db /
                              final_lock.py in stage payloads under toolType + toolData
```

No new files. All tool logic lives inline in `hackathon.html`.

---

## Task 1: configure.py — embed file data in stage payloads

**Files:**
- Modify: `configure.py`

Each of stages 3–6 gets two new payload fields: `toolType` (string) and `toolData` (dict with file content).

- [ ] **Step 1: Add base64 import and file-reading helpers to configure.py**

Open `configure.py`. After the existing imports block (the line `from cryptography.hazmat.primitives.ciphers.aead import AESGCM`), add:

```python
import base64

def read_b64(rel: str) -> str:
    return base64.b64encode((ROOT / rel).read_bytes()).decode()

def read_text(rel: str) -> str:
    return (ROOT / rel).read_text()
```

- [ ] **Step 2: Add toolType/toolData to the four stage payloads**

Find the four payload dicts in configure.py and add the tool fields as shown.

**s3_payload** — find the existing dict and extend it:
```python
s3_payload = {
    "title": "Stage 3 — The Server Room",
    "problem": s3_html,
    "answerHashes": [hash_answer(a) for a in s3_answers],
    "labels": ["Number of CRITICAL events", "Session number", "Last vault locked"],
    "toolType": "terminal",
    "toolData": {"logContent": read_text("stages/stage3/vault_logs.txt")},
}
```

**s4_payload**:
```python
s4_payload = {
    "title": "Stage 4 — The Surveillance Room",
    "problem": s4_html,
    "answerHashes": [hash_answer(a) for a in s4_answers],
    "labels": ["Override code 1", "Override code 2", "Override code 3"],
    "toolType": "canvas",
    "toolData": {"imageBase64": read_b64("stages/stage4/mittens_cam.png")},
}
```

**s5_payload**:
```python
s5_payload = {
    "title": "Stage 5 — The Records Room",
    "problem": s5_html,
    "answerHashes": [hash_answer(a) for a in s5_answers],
    "labels": ["V006 emergency code", "Sum of reversed transactions", "Mittens vault code"],
    "toolType": "sql",
    "toolData": {"dbBase64": read_b64("stages/stage5/vault_records.db")},
}
```

**s6_payload**:
```python
s6_payload = {
    "title": "Stage 6 — The Vault",
    "problem": s6_html,
    "answerHashes": [hash_answer(a) for a in s6_answers],
    "labels": ["Final code 1", "Final code 2", "Final code 3"],
    "toolType": "python",
    "toolData": {"script": read_text("stages/stage6/final_lock.py")},
}
```

- [ ] **Step 3: Run configure.py and verify blob sizes grew**

```bash
cd /home/samp/projects/AI/hackathon
python3 configure.py
```

Then check blob sizes in hackathon.html — stage 3's blob should now be much larger (the log file is ~500KB of text):

```bash
python3 -c "
import re, json
html = open('hackathon.html').read()
for n in range(2, 7):
    m = re.search(rf\"^\s+{n}: '(.*?)'\", html, re.MULTILINE)
    if m:
        print(f'Stage {n} blob length: {len(m.group(1))} chars')
"
```

Expected: Stage 3 blob should be 600,000+ chars. Stages 4–5 several thousand chars each.

- [ ] **Step 4: Verify stage 3 blob decrypts with correct toolType**

```python
import hashlib, json, base64, re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

html = open('hackathon.html').read()
m = re.search(r"^\s+3: '(.*?)'", html, re.MULTILINE)
blob = json.loads(m.group(1))
iv = base64.b64decode(blob['iv'])
ct = base64.b64decode(blob['ct'])

# Derive key from stage 2 answers (29703, 48, 8133)
answers = ['29703', '48', '8133']
combined = 'hackathon:stage2:' + '|'.join(a.strip().lower() for a in answers)
key = hashlib.sha256(combined.encode()).digest()

plain = AESGCM(key).decrypt(iv, ct, None)
payload = json.loads(plain)
print('toolType:', payload.get('toolType'))
print('logContent lines:', payload['toolData']['logContent'].count('\n'))
```

Expected:
```
toolType: terminal
logContent lines: 11726
```

- [ ] **Step 5: Commit**

```bash
git add configure.py hackathon.html
git commit -m "feat: embed stage file data in encrypted payloads (toolType + toolData)"
```

---

## Task 2: hackathon.html — CDN scripts, CSS, async renderNextStage

**Files:**
- Modify: `hackathon.html`

- [ ] **Step 1: Add CDN script and style tags to `<head>`**

In `hackathon.html`, find the closing `</style>` tag and add immediately after it (before `</head>`):

```html
    <!-- xterm.js — terminal emulator for Stage 3 -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.min.css">
    <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.min.js"></script>
    <!-- sql.js — SQLite in WebAssembly for Stage 5 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.11.0/sql-wasm.min.js"></script>
    <!-- Pyodide — Python in WebAssembly for Stage 6 (loaded lazily) -->
    <script src="https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js" defer></script>
```

- [ ] **Step 2: Add tool widget CSS**

In `hackathon.html`, inside `<style>`, append these rules before the closing `</style>` tag:

```css
        /* ── Tool widgets ── */
        .tool-container {
            width: 100%;
            max-width: 760px;
            margin-bottom: 1rem;
        }

        /* Terminal (Stage 3) */
        .terminal-outer {
            background: #0d1117;
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }
        .terminal-titlebar {
            background: var(--surface2);
            padding: 0.5rem 1rem;
            font-size: 0.78rem;
            color: var(--muted);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .terminal-dot { width: 10px; height: 10px; border-radius: 50%; }
        .terminal-body { padding: 0.5rem; }
        .xterm { padding: 4px; }

        /* Canvas inspector (Stage 4) */
        .canvas-outer {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem 2rem;
        }
        .canvas-outer h3 { font-size: 0.85rem; color: var(--muted); margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.06em; }
        .canvas-img-wrap { margin-bottom: 1rem; }
        .canvas-img-wrap canvas { border: 1px solid var(--border); border-radius: 6px; max-width: 100%; }
        .canvas-controls { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
        .canvas-controls label { font-size: 0.85rem; color: var(--muted); }
        .canvas-controls input[type="number"] {
            width: 80px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 0.4rem 0.6rem;
            color: var(--text);
            font-family: monospace;
        }
        .canvas-output {
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            font-size: 0.9rem;
            color: var(--accent-light);
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 0.6rem 0.9rem;
            min-height: 2rem;
        }

        /* SQL editor (Stage 5) */
        .sql-outer {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem 2rem;
        }
        .sql-outer h3 { font-size: 0.85rem; color: var(--muted); margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.06em; }
        .sql-status { font-size: 0.82rem; color: var(--muted); margin-bottom: 0.75rem; }
        .sql-input {
            width: 100%;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.6rem 0.9rem;
            color: var(--text);
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            font-size: 0.9rem;
            resize: vertical;
            outline: none;
            margin-bottom: 0.75rem;
        }
        .sql-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(124,58,237,0.2); }
        .sql-results { margin-top: 0.75rem; overflow-x: auto; }
        .sql-table { border-collapse: collapse; font-size: 0.85rem; font-family: monospace; width: 100%; }
        .sql-table th { background: var(--surface2); color: var(--accent-light); padding: 0.4rem 0.75rem; text-align: left; border: 1px solid var(--border); }
        .sql-table td { padding: 0.35rem 0.75rem; border: 1px solid var(--border); color: var(--text); }
        .sql-table tr:nth-child(even) td { background: var(--surface2); }
        .sql-error { color: var(--error); font-size: 0.85rem; font-family: monospace; }
        .sql-ok { color: var(--success); font-size: 0.85rem; }

        /* Python editor (Stage 6) */
        .python-outer {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }
        .python-titlebar {
            background: var(--surface2);
            padding: 0.5rem 1rem;
            font-size: 0.82rem;
            color: var(--muted);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .python-code {
            width: 100%;
            background: var(--bg);
            border: none;
            border-bottom: 1px solid var(--border);
            padding: 1rem;
            color: #e6edf3;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            font-size: 0.85rem;
            resize: vertical;
            outline: none;
            min-height: 280px;
        }
        .python-run-row {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            background: var(--surface2);
            flex-wrap: wrap;
        }
        .python-run-row label { font-size: 0.82rem; color: var(--muted); white-space: nowrap; }
        .python-passphrase {
            flex: 1;
            min-width: 200px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 0.45rem 0.75rem;
            color: var(--text);
            font-family: monospace;
            font-size: 0.9rem;
            outline: none;
        }
        .python-passphrase:focus { border-color: var(--accent); }
        .python-status { font-size: 0.8rem; color: var(--muted); padding: 0.4rem 1rem; background: var(--surface); border-bottom: 1px solid var(--border); }
        .python-output {
            background: #0d1117;
            color: #a3e635;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            font-size: 0.85rem;
            padding: 1rem;
            margin: 0;
            min-height: 60px;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .load-py-btn {
            background: var(--border);
            color: var(--text);
            border: none;
            border-radius: 6px;
            padding: 0.35rem 0.85rem;
            font-size: 0.8rem;
            cursor: pointer;
        }
        .load-py-btn:hover { background: #444c56; }
        .load-py-btn:disabled { opacity: 0.5; cursor: not-allowed; }
```

- [ ] **Step 3: Make `renderNextStage` async and add tool container slot**

In `hackathon.html`, find the function:

```javascript
    function renderNextStage(stageNum, payload) {
        const wrapper = document.createElement('div');
        wrapper.className = 'stage-wrapper';
        wrapper.id = `stage-${stageNum}`;
        wrapper.innerHTML = `
            <div class="stage-divider"></div>
            <div class="card">
                <div class="card-title">${esc(payload.title)}</div>
                <div class="problem">${payload.problem}</div>
            </div>
            <div id="answer-section-${stageNum}"></div>
        `;
        document.getElementById('stages-container').appendChild(wrapper);

        renderAnswerForm(stageNum);

        // Two rAF ticks so the element is in the DOM before the transition fires
        requestAnimationFrame(() => requestAnimationFrame(() => {
            wrapper.classList.add('visible');
            wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }));

        updateProgress(stageNum);
        document.getElementById('stage-indicator').textContent = `Stage ${stageNum} of ${TOTAL_STAGES}`;

        setTimeout(() => document.getElementById(`s${stageNum}a1`)?.focus(), 600);
    }
```

Replace with:

```javascript
    function renderNextStage(stageNum, payload) {
        const wrapper = document.createElement('div');
        wrapper.className = 'stage-wrapper';
        wrapper.id = `stage-${stageNum}`;
        wrapper.innerHTML = `
            <div class="stage-divider"></div>
            <div class="card">
                <div class="card-title">${esc(payload.title)}</div>
                <div class="problem">${payload.problem}</div>
            </div>
            ${payload.toolType ? `<div id="tool-${stageNum}" class="tool-container"></div>` : ''}
            <div id="answer-section-${stageNum}"></div>
        `;
        document.getElementById('stages-container').appendChild(wrapper);

        renderAnswerForm(stageNum);

        if (payload.toolType) {
            initStageTool(stageNum, payload);  // fire-and-forget: tools init async in bg
        }

        requestAnimationFrame(() => requestAnimationFrame(() => {
            wrapper.classList.add('visible');
            wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }));

        updateProgress(stageNum);
        document.getElementById('stage-indicator').textContent = `Stage ${stageNum} of ${TOTAL_STAGES}`;

        setTimeout(() => document.getElementById(`s${stageNum}a1`)?.focus(), 600);
    }

    function initStageTool(stageNum, payload) {
        const container = document.getElementById(`tool-${stageNum}`);
        if (!container) return;
        switch (payload.toolType) {
            case 'terminal': initTerminalTool(stageNum, container, payload.toolData); break;
            case 'canvas':   initCanvasTool(stageNum, container, payload.toolData);   break;
            case 'sql':      initSQLTool(stageNum, container, payload.toolData);      break;
            case 'python':   initPythonTool(stageNum, container, payload.toolData);   break;
        }
    }
```

- [ ] **Step 4: Commit**

```bash
cd /home/samp/projects/AI/hackathon
git add hackathon.html
git commit -m "feat: add CDN deps, tool widget CSS, async renderNextStage with tool dispatch"
```

---

## Task 3: Stage 3 — terminal emulator (bash subset + xterm.js)

**Files:**
- Modify: `hackathon.html` (add `initTerminalTool` + bash helpers)

- [ ] **Step 1: Add the terminal tool renderer and bash engine**

In `hackathon.html`, inside the `<script>` block, add the following after the `initStageTool` function:

```javascript
    // ====================================================================
    //  STAGE 3 — TERMINAL EMULATOR
    // ====================================================================

    function initTerminalTool(stageNum, container, toolData) {
        const logContent = toolData.logContent;
        const vaultFS    = { 'vault_logs.txt': logContent };

        container.innerHTML = `
            <div class="terminal-outer">
                <div class="terminal-titlebar">
                    <span class="terminal-dot" style="background:#ef4444"></span>
                    <span class="terminal-dot" style="background:#f59e0b"></span>
                    <span class="terminal-dot" style="background:#10b981"></span>
                    <span style="margin-left:0.5rem">VAULT-9 Security Terminal &nbsp;·&nbsp; vault_logs.txt loaded</span>
                </div>
                <div class="terminal-body" id="xterm-${stageNum}"></div>
            </div>`;

        const term = new Terminal({
            theme: { background: '#0d1117', foreground: '#e6edf3', cursor: '#7c3aed',
                     selectionBackground: 'rgba(124,58,237,0.3)' },
            fontFamily: "'Cascadia Code','Fira Code',monospace",
            fontSize: 13,
            rows: 22,
            convertEol: true,
            cursorBlink: true,
        });
        const fitAddon = new FitAddon.FitAddon();
        term.loadAddon(fitAddon);
        term.open(document.getElementById(`xterm-${stageNum}`));
        fitAddon.fit();

        term.writeln('\x1b[32mVAULT-9 Security Terminal v2.1\x1b[0m');
        term.writeln('\x1b[90mFile system: vault_logs.txt  |  Commands: grep  wc  cut  awk  tail  head  sort  uniq\x1b[0m');
        term.write('\n\x1b[35m$\x1b[0m ');

        let line = '';
        term.onKey(({ key, domEvent }) => {
            const k = domEvent.key;
            if (k === 'Enter') {
                term.write('\r\n');
                if (line.trim()) {
                    const out = bashRun(line.trim(), vaultFS);
                    if (out) term.write(out.replace(/\n/g, '\r\n') + '\r\n');
                }
                line = '';
                term.write('\x1b[35m$\x1b[0m ');
            } else if (k === 'Backspace') {
                if (line.length) { line = line.slice(0, -1); term.write('\b \b'); }
            } else if (key.length === 1 && !domEvent.ctrlKey && !domEvent.altKey) {
                line += key;
                term.write(key);
            }
        });
    }

    // ── Bash engine ───────────────────────────────────────────────────────

    function bashRun(cmdLine, fs) {
        try {
            const pipes = bashSplitPipes(cmdLine);
            let data = null;
            for (const cmd of pipes) {
                data = bashExec(cmd.trim(), data, fs);
            }
            return data ?? '';
        } catch (e) {
            return '\x1b[31m' + e.message + '\x1b[0m';
        }
    }

    function bashSplitPipes(cmdLine) {
        const cmds = []; let cur = ''; let q1 = false, q2 = false;
        for (const ch of cmdLine) {
            if (ch === "'" && !q2) { q1 = !q1; cur += ch; continue; }
            if (ch === '"' && !q1) { q2 = !q2; cur += ch; continue; }
            if (ch === '|' && !q1 && !q2) { cmds.push(cur.trim()); cur = ''; continue; }
            cur += ch;
        }
        if (cur.trim()) cmds.push(cur.trim());
        return cmds;
    }

    function bashTokens(s) {
        const toks = []; let cur = ''; let q1 = false, q2 = false;
        for (const ch of s) {
            if (ch === "'" && !q2) { q1 = !q1; continue; }
            if (ch === '"' && !q1) { q2 = !q2; continue; }
            if (ch === ' ' && !q1 && !q2) { if (cur) { toks.push(cur); cur = ''; } continue; }
            cur += ch;
        }
        if (cur) toks.push(cur);
        return toks;
    }

    function bashLines(text) {
        return text ? text.split('\n').filter(l => l !== '') : [];
    }

    function bashExec(cmd, stdin, fs) {
        const toks = bashTokens(cmd);
        if (!toks.length) return stdin;
        const name = toks[0];

        // resolve file arg (last non-flag token if it doesn't start with -)
        function getFileContent(args) {
            const fname = args.find(a => !a.startsWith('-'));
            if (fname) {
                if (!fs[fname]) throw new Error(`${fname}: No such file or directory`);
                return fs[fname];
            }
            return stdin ?? '';
        }

        const args = toks.slice(1);

        switch (name) {
            case 'grep': {
                let countMode = false, onlyMode = false, remaining = [...args];
                while (remaining[0]?.startsWith('-')) {
                    const f = remaining.shift();
                    if (f.includes('c')) countMode = true;
                    if (f.includes('o')) onlyMode = true;
                }
                const pattern = remaining.shift() ?? '';
                const fname   = remaining[0];
                const source  = fname ? (fs[fname] ?? (() => { throw new Error(`${fname}: No such file`); })()) : (stdin ?? '');
                const re      = new RegExp(pattern);
                const lines   = bashLines(source);
                if (countMode) return String(lines.filter(l => re.test(l)).length);
                if (onlyMode) {
                    const matches = [];
                    for (const l of lines) {
                        const m = l.match(new RegExp(pattern, 'g'));
                        if (m) matches.push(...m);
                    }
                    return matches.join('\n');
                }
                return lines.filter(l => re.test(l)).join('\n');
            }
            case 'wc': {
                const hasL = args.includes('-l');
                const src  = getFileContent(args.filter(a => !a.startsWith('-')));
                if (hasL || !args.length) return String(bashLines(src).length);
                return String(src.split('\n').length);
            }
            case 'cut': {
                let delim = '\t', field = 1;
                for (let i = 0; i < args.length; i++) {
                    if (args[i] === '-d' && args[i+1]) { delim = args[++i]; continue; }
                    if (args[i].startsWith('-d'))       { delim = args[i].slice(2); continue; }
                    if (args[i] === '-f' && args[i+1]) { field = parseInt(args[++i]); continue; }
                    if (args[i].startsWith('-f'))       { field = parseInt(args[i].slice(2)); continue; }
                }
                const src = stdin ?? '';
                return bashLines(src).map(l => (l.split(delim)[field - 1]) ?? '').join('\n');
            }
            case 'awk': {
                // Support: awk '{print $N}' and awk -F'X' '{print $N}'
                let fs_delim = /\s+/;
                let prog = '';
                for (let i = 0; i < args.length; i++) {
                    if (args[i] === '-F' && args[i+1]) { fs_delim = new RegExp(args[++i].replace(/[.*+?^${}()|[\]\\]/g, '\\$&')); continue; }
                    if (args[i].startsWith('-F'))       { fs_delim = new RegExp(args[i].slice(2).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')); continue; }
                    prog = args[i];
                }
                const m = prog.match(/\{.*?print\s+\$(\d+)/);
                if (!m) throw new Error(`awk: unsupported program: ${prog}`);
                const col = parseInt(m[1]);
                const src = stdin ?? '';
                return bashLines(src).map(l => (l.split(fs_delim)[col - 1]) ?? '').join('\n');
            }
            case 'head': {
                const nIdx = args.indexOf('-n');
                const n    = nIdx >= 0 ? parseInt(args[nIdx + 1]) : parseInt(args.find(a => a.startsWith('-'))?.slice(1) ?? '10');
                const src  = getFileContent(args.filter(a => !a.startsWith('-') && !/^\d+$/.test(a)));
                return bashLines(src).slice(0, isNaN(n) ? 10 : n).join('\n');
            }
            case 'tail': {
                const nIdx = args.indexOf('-n');
                const n    = nIdx >= 0 ? parseInt(args[nIdx + 1]) : parseInt(args.find(a => a.startsWith('-'))?.slice(1) ?? '10');
                const src  = getFileContent(args.filter(a => !a.startsWith('-') && !/^\d+$/.test(a)));
                const ls   = bashLines(src);
                return ls.slice(-(isNaN(n) ? 10 : n)).join('\n');
            }
            case 'sort': {
                const reverse  = args.includes('-r') || args.includes('-rn') || args.includes('-nr');
                const numeric  = args.includes('-n') || args.includes('-rn') || args.includes('-nr');
                const src = getFileContent(args.filter(a => !a.startsWith('-')));
                const ls  = bashLines(src);
                ls.sort((a, b) => numeric ? (parseFloat(a) - parseFloat(b)) : a.localeCompare(b));
                if (reverse) ls.reverse();
                return ls.join('\n');
            }
            case 'uniq': {
                const count = args.includes('-c');
                const src   = stdin ?? '';
                const ls    = bashLines(src);
                const out   = [];
                let prev = null, cnt = 0;
                for (const l of ls) {
                    if (l === prev) { cnt++; }
                    else { if (prev !== null) out.push(count ? `${String(cnt).padStart(4)} ${prev}` : prev); prev = l; cnt = 1; }
                }
                if (prev !== null) out.push(count ? `${String(cnt).padStart(4)} ${prev}` : prev);
                return out.join('\n');
            }
            case 'cat': {
                return getFileContent(args);
            }
            case 'ls': {
                return Object.keys(fs).join('\n');
            }
            default:
                throw new Error(`command not found: ${name}`);
        }
    }
```

- [ ] **Step 2: Update Stage 3 problem.html to remove download/bash hints and add terminal instruction**

Replace `stages/stage3/problem.html` with:

```html
<p>
    VAULT-9 logs every event. Mittens' intrusion is buried in thousands of lines of system
    logs. The terminal below has <code>vault_logs.txt</code> pre-loaded.
</p>
<p>Use the terminal to answer the three questions:</p>
<ol>
    <li>
        How many <code>CRITICAL</code> log lines contain <code>FELINE_INPUT</code>?<br>
        <small>Try: <code>grep -c "FELINE_INPUT" vault_logs.txt</code></small>
    </li>
    <li>
        What is the <strong>numeric part</strong> of the session ID in the lockdown event?<br>
        <small>e.g. if the log shows <code>session=SID-1234</code>, the answer is <code>1234</code></small>
    </li>
    <li>
        Which vault was locked <strong>last</strong>? (e.g. <code>V001</code>)
    </li>
</ol>
<div class="hint-box">
    Supported commands: <code>grep</code> <code>grep -c</code> <code>grep -o</code>
    <code>wc -l</code> <code>cut</code> <code>awk</code> <code>tail</code> <code>head</code>
    <code>sort</code> <code>uniq</code> — and pipes with <code>|</code>
</div>
```

- [ ] **Step 3: Re-run configure.py to update stage 3 blob with new problem HTML**

```bash
cd /home/samp/projects/AI/hackathon
python3 configure.py
```

- [ ] **Step 4: Smoke-test the bash engine**

Open a browser console on any page and paste this to test the engine in isolation (after hackathon.html is loaded):

```javascript
// Quick sanity tests (paste in browser console after opening hackathon.html)
// These won't work until the page is open but can verify logic manually:

const testFS = { 'vault_logs.txt': ['[CRITICAL] trigger=FELINE_INPUT session=SID-7429 vault_id=V001',
'[CRITICAL] trigger=FELINE_INPUT session=SID-7429 vault_id=V002',
'[INFO] heartbeat ok',
'[CRITICAL] LOCKDOWN INITIATED trigger=FELINE_INPUT vault_id=V004'].join('\n') };

console.assert(bashRun('grep -c "FELINE_INPUT" vault_logs.txt', testFS) === '3', 'grep -c failed');
console.assert(bashRun('grep "FELINE_INPUT" vault_logs.txt | grep -o "SID-[0-9]*" | head -1 | cut -d- -f2', testFS) === '7429', 'pipe chain failed');
console.assert(bashRun('grep "LOCKDOWN INITIATED" vault_logs.txt | tail -1 | grep -o "vault_id=[A-Z0-9]*" | cut -d= -f2', testFS) === 'V004', 'last vault failed');
console.log('All bash tests passed');
```

Run the assertions. Expected: `All bash tests passed` (no assertion errors).

- [ ] **Step 5: Commit**

```bash
git add hackathon.html stages/stage3/problem.html
git commit -m "feat: stage 3 terminal emulator with bash subset (grep/cut/awk/tail/head/sort/uniq)"
```

---

## Task 4: Stage 4 — canvas pixel inspector

**Files:**
- Modify: `hackathon.html` (add `initCanvasTool`)
- Modify: `stages/stage4/problem.html`

- [ ] **Step 1: Add `initCanvasTool` to hackathon.html**

In the `<script>` block, after the bash engine section, add:

```javascript
    // ====================================================================
    //  STAGE 4 — CANVAS PIXEL INSPECTOR
    // ====================================================================

    function initCanvasTool(stageNum, container, toolData) {
        container.innerHTML = `
            <div class="canvas-outer">
                <h3>Surveillance image inspector</h3>
                <div class="canvas-img-wrap">
                    <canvas id="cam-canvas-${stageNum}"></canvas>
                </div>
                <div class="canvas-controls">
                    <label>STEP (every Nth pixel):</label>
                    <input type="number" id="cam-step-${stageNum}" value="1" min="1" max="100">
                    <button class="submit-btn" onclick="runExtraction(${stageNum})">Extract hidden data</button>
                </div>
                <div class="canvas-output" id="cam-output-${stageNum}">Output will appear here after extraction.</div>
            </div>`;

        const img = new Image();
        img.onload = () => {
            const canvas = document.getElementById(`cam-canvas-${stageNum}`);
            canvas.width  = img.width;
            canvas.height = img.height;
            canvas.getContext('2d').drawImage(img, 0, 0);
        };
        img.src = 'data:image/png;base64,' + toolData.imageBase64;

        window[`camImg_${stageNum}`] = img;
    }

    function runExtraction(stageNum) {
        const canvas  = document.getElementById(`cam-canvas-${stageNum}`);
        const output  = document.getElementById(`cam-output-${stageNum}`);
        const step    = parseInt(document.getElementById(`cam-step-${stageNum}`).value) || 1;
        const ctx     = canvas.getContext('2d');
        const { width, height } = canvas;
        const imgData = ctx.getImageData(0, 0, width, height).data;  // RGBA flat array
        const total   = width * height;

        // Collect LSBs of R channel at every STEP-th pixel
        const bits = [];
        for (let i = 0; i < total; i += step) {
            bits.push(imgData[i * 4] & 1);  // R channel of pixel i
        }

        // Decode bits → string (8 bits per char, MSB first, null-terminated)
        const chars = [];
        for (let i = 0; i + 7 < bits.length; i += 8) {
            let byte = 0;
            for (let b = 0; b < 8; b++) byte = (byte << 1) | bits[i + b];
            if (byte === 0) break;
            if (byte < 32 || byte > 126) { chars.push('?'); continue; }
            chars.push(String.fromCharCode(byte));
        }

        const hidden = chars.join('');
        if (!hidden) {
            output.textContent = 'No readable data found. Check STEP value.';
            return;
        }

        const codes = hidden.split(',');
        let html = `<strong>Hidden data:</strong> ${esc(hidden)}<br><br>`;
        codes.forEach((c, i) => {
            html += `Override code ${i + 1}: <strong>${esc(c.trim())}</strong><br>`;
        });
        output.innerHTML = html;
    }
```

- [ ] **Step 2: Update Stage 4 problem.html**

Replace `stages/stage4/problem.html` with:

```html
<p>
    The security camera caught Mittens in the act. The paranoid lead engineer always
    embedded backup override codes into surveillance images. His recovered notes say:
</p>
<blockquote style="border-left:3px solid var(--accent);padding:0.5rem 1rem;margin:1rem 0;color:#cdd9e5;font-style:italic;">
    "Override codes hidden in R channel, every 1st pixel (i.e. every pixel),
    starting at pixel 0. LSB steganography. Standard."
</blockquote>
<p>
    The camera image is loaded in the inspector below.
    Set <code>STEP</code> to match the engineer's notes and click <strong>Extract hidden data</strong>.
</p>
<div class="hint-box">
    The three answers are the three comma-separated integers shown in the extraction output.
</div>
```

- [ ] **Step 3: Re-run configure.py**

```bash
cd /home/samp/projects/AI/hackathon
python3 configure.py
```

- [ ] **Step 4: Commit**

```bash
git add hackathon.html stages/stage4/problem.html
git commit -m "feat: stage 4 canvas pixel inspector for LSB steganography"
```

---

## Task 5: Stage 5 — in-browser SQL editor (sql.js)

**Files:**
- Modify: `hackathon.html` (add `initSQLTool`, `runSQL`)
- Modify: `stages/stage5/problem.html`

- [ ] **Step 1: Add sql.js state and `initSQLTool` to hackathon.html**

In the `<script>` block, after the canvas section, add:

```javascript
    // ====================================================================
    //  STAGE 5 — SQL EDITOR (sql.js)
    // ====================================================================

    let _sqlJs = null;  // cached initSqlJs promise

    async function initSQLTool(stageNum, container, toolData) {
        container.innerHTML = `
            <div class="sql-outer">
                <h3>vault_records.db &nbsp;·&nbsp; SQL editor</h3>
                <div class="sql-status" id="sql-status-${stageNum}">Loading SQLite engine…</div>
                <textarea class="sql-input" id="sql-input-${stageNum}" rows="5"
                          placeholder="SELECT * FROM vaults LIMIT 5;" spellcheck="false"></textarea>
                <button class="submit-btn" id="sql-run-${stageNum}"
                        onclick="runSQL(${stageNum})" disabled>Run Query</button>
                <div class="sql-results" id="sql-results-${stageNum}"></div>
            </div>`;

        try {
            if (!_sqlJs) _sqlJs = initSqlJs({
                locateFile: f => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.11.0/${f}`
            });
            const SQL = await _sqlJs;
            const bytes = Uint8Array.from(atob(toolData.dbBase64), c => c.charCodeAt(0));
            const db    = new SQL.Database(bytes);
            window[`sqlDb_${stageNum}`] = db;
            document.getElementById(`sql-status-${stageNum}`).textContent =
                'SQLite ready — database: vault_records.db  |  tables: vaults, transactions, access_log';
            document.getElementById(`sql-run-${stageNum}`).disabled = false;
        } catch (e) {
            document.getElementById(`sql-status-${stageNum}`).textContent =
                `Failed to load SQLite: ${e.message}`;
        }
    }

    function runSQL(stageNum) {
        const db      = window[`sqlDb_${stageNum}`];
        const query   = document.getElementById(`sql-input-${stageNum}`).value.trim();
        const results = document.getElementById(`sql-results-${stageNum}`);
        if (!db || !query) return;

        try {
            const rows = db.exec(query);
            if (!rows.length) {
                results.innerHTML = '<span class="sql-ok">Query OK — no rows returned.</span>';
                return;
            }
            const { columns, values } = rows[0];
            let html = '<table class="sql-table"><thead><tr>';
            columns.forEach(c => { html += `<th>${esc(c)}</th>`; });
            html += '</tr></thead><tbody>';
            values.forEach(row => {
                html += '<tr>';
                row.forEach(v => { html += `<td>${esc(String(v ?? 'NULL'))}</td>`; });
                html += '</tr>';
            });
            html += '</tbody></table>';
            results.innerHTML = html;
        } catch (e) {
            results.innerHTML = `<span class="sql-error">Error: ${esc(e.message)}</span>`;
        }
    }
```

Also add Enter-key shortcut for the SQL editor — add to the existing `document.addEventListener('keydown', ...)` handler, or add a new one at the bottom of the script:

```javascript
    document.addEventListener('keydown', e => {
        if (e.key === 'Enter' && e.ctrlKey && document.activeElement?.classList.contains('sql-input')) {
            const id = document.activeElement.id;   // "sql-input-N"
            const n  = parseInt(id.split('-').pop());
            runSQL(n);
        }
    });
```

- [ ] **Step 2: Update Stage 5 problem.html**

Replace `stages/stage5/problem.html` with:

```html
<p>
    The vault management database holds the master override codes.
    Mittens walked on the delete key — several records are now marked deleted.
    But SQLite doesn't truly forget.
</p>
<p>
    The SQL editor below is connected to <code>vault_records.db</code>.
    Tables: <code>vaults</code>, <code>transactions</code>, <code>access_log</code>.
    Use <kbd>Ctrl+Enter</kbd> or the Run button to execute a query.
</p>
<ol>
    <li>
        What is the <code>emergency_code</code> of vault <code>V006</code>
        (which has a non-NULL <code>deleted_at</code>)?
    </li>
    <li>
        What is the total <code>amount</code> of all transactions
        where <code>status = 'REVERSED'</code>? (integer, no decimals)
    </li>
    <li>
        There is an entry in <code>access_log</code> where <code>username = 'MITTENS'</code>.
        Join it to the <code>vaults</code> table and find that vault's <code>emergency_code</code>.
    </li>
</ol>
<div class="hint-box">
    Tip: run <code>SELECT name FROM sqlite_master WHERE type='table';</code> to list tables,
    or <code>PRAGMA table_info(vaults);</code> to see columns.
</div>
```

- [ ] **Step 3: Re-run configure.py**

```bash
cd /home/samp/projects/AI/hackathon
python3 configure.py
```

- [ ] **Step 4: Commit**

```bash
git add hackathon.html stages/stage5/problem.html
git commit -m "feat: stage 5 in-browser SQL editor via sql.js"
```

---

## Task 6: Stage 6 — Python terminal (Pyodide)

**Files:**
- Modify: `hackathon.html` (add `initPythonTool`, `loadPyodideEnv`, `runPython`)
- Modify: `stages/stage6/problem.html`

- [ ] **Step 1: Add Pyodide state and tool renderer to hackathon.html**

In the `<script>` block, after the SQL section, add:

```javascript
    // ====================================================================
    //  STAGE 6 — PYTHON TERMINAL (Pyodide)
    // ====================================================================

    let _pyodide = null;  // cached Pyodide instance

    function initPythonTool(stageNum, container, toolData) {
        const script = toolData.script;
        container.innerHTML = `
            <div class="python-outer">
                <div class="python-titlebar">
                    <span>final_lock.py — edit below, then run with your passphrase</span>
                    <button class="load-py-btn" id="load-py-${stageNum}"
                            onclick="loadPyodideEnv(${stageNum})">Load Python (5–10s)</button>
                </div>
                <textarea class="python-code" id="py-code-${stageNum}"
                          spellcheck="false">${esc(script)}</textarea>
                <div class="python-run-row">
                    <label>Passphrase:</label>
                    <input type="text" class="python-passphrase" id="py-pass-${stageNum}"
                           placeholder='e.g. Mittens Fluffington III'
                           autocomplete="off" spellcheck="false">
                    <button class="submit-btn" id="py-run-${stageNum}"
                            onclick="runPython(${stageNum})" disabled>Run</button>
                </div>
                <div class="python-status" id="py-status-${stageNum}">
                    Click <strong>Load Python</strong> to start the Python environment (~5–10s).
                </div>
                <pre class="python-output" id="py-out-${stageNum}"></pre>
            </div>`;
    }

    async function loadPyodideEnv(stageNum) {
        const btn    = document.getElementById(`load-py-${stageNum}`);
        const status = document.getElementById(`py-status-${stageNum}`);
        btn.disabled = true;
        btn.textContent = 'Loading…';
        status.textContent = 'Loading Python environment (5–10 seconds the first time)…';
        try {
            if (!_pyodide) _pyodide = loadPyodide();
            await _pyodide;
            document.getElementById(`py-run-${stageNum}`).disabled = false;
            status.textContent = 'Python ready. Fix any bugs in the script, enter the passphrase, and click Run.';
            btn.textContent = 'Python loaded ✓';
        } catch (e) {
            status.textContent = `Failed to load Python: ${e.message}`;
            btn.disabled = false;
            btn.textContent = 'Retry';
        }
    }

    async function runPython(stageNum) {
        const py     = await _pyodide;
        const code   = document.getElementById(`py-code-${stageNum}`).value;
        const pass   = document.getElementById(`py-pass-${stageNum}`).value;
        const status = document.getElementById(`py-status-${stageNum}`);
        const out    = document.getElementById(`py-out-${stageNum}`);

        status.textContent = 'Running…';
        out.textContent = '';

        let stdout = '';
        py.setStdout({ batched: s => { stdout += s + '\n'; } });
        py.setStderr({ batched: s => { stdout += s + '\n'; } });

        // Inject sys.argv so the script receives the passphrase as a single argument
        const patched = `import sys\nsys.argv = ['final_lock.py', ${JSON.stringify(pass)}]\n` + code;

        try {
            await py.runPythonAsync(patched);
            out.textContent = stdout.trim() || '(no output)';
            status.textContent = 'Done.';
        } catch (e) {
            out.textContent = e.message;
            status.textContent = 'Script raised an error — check the output above.';
        }
    }
```

- [ ] **Step 2: Update Stage 6 problem.html**

Replace `stages/stage6/problem.html` with:

```html
<p>
    Almost there. The final vault is controlled by an override module the Head of Security
    obfuscated <em>"for safety"</em> — and then promptly forgot the passphrase to.
</p>
<p>
    The script is loaded in the editor below. Two things stand between you and the codes:
</p>
<ol>
    <li>There is <strong>one bug</strong> preventing the script from running. Find and fix it in the editor.</li>
    <li>
        Find the passphrase. The Head of Security's note in the comments says:<br>
        <em>"the passphrase is the cat's full name, as registered with the vet."</em>
    </li>
</ol>
<p>Once fixed, click <strong>Load Python</strong>, enter the passphrase, and click <strong>Run</strong>.</p>
<div class="hint-box">
    The cat's full registered name has appeared somewhere in this hackathon.
    The three answers are the codes printed when the script runs successfully.
</div>
```

- [ ] **Step 3: Re-run configure.py**

```bash
cd /home/samp/projects/AI/hackathon
python3 configure.py
```

- [ ] **Step 4: Commit**

```bash
git add hackathon.html stages/stage6/problem.html
git commit -m "feat: stage 6 in-browser Python terminal via Pyodide"
```

---

## Task 7: End-to-end verification

**Files:** none modified — verification only.

- [ ] **Step 1: Verify all stage blobs have toolType field**

```bash
cd /home/samp/projects/AI/hackathon
python3 - << 'EOF'
import hashlib, json, base64, re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

html = open('hackathon.html').read()

stage_answers = {
    1: ['9068', '5884', '2700'],
    2: ['29703', '48', '8133'],
    3: ['6', '7429', 'v004'],
    4: ['4821', '8803', '5142'],
    5: ['3847', '47750', '9163'],
}
expected_tools = {2: None, 3: 'terminal', 4: 'canvas', 5: 'sql', 6: 'python'}

for n in range(2, 7):
    m = re.search(rf"^\s+{n}: '(.*?)'", html, re.MULTILINE)
    blob = json.loads(m.group(1))
    iv = base64.b64decode(blob['iv'])
    ct = base64.b64decode(blob['ct'])
    prev = stage_answers[n - 1]
    combined = f'hackathon:stage{n-1}:' + '|'.join(a.strip().lower() for a in prev)
    key = hashlib.sha256(combined.encode()).digest()
    payload = json.loads(AESGCM(key).decrypt(iv, ct, None))
    tool = payload.get('toolType')
    data_keys = list(payload.get('toolData', {}).keys()) if 'toolData' in payload else []
    print(f'Stage {n}: toolType={tool!r}  toolData keys={data_keys}  title={payload["title"]!r}')
    assert tool == expected_tools[n], f'Stage {n}: expected toolType {expected_tools[n]!r}, got {tool!r}'

print('\nAll assertions passed.')
EOF
```

Expected:
```
Stage 2: toolType=None  toolData keys=[]  title='Stage 2 — The Keycard Room'
Stage 3: toolType='terminal'  toolData keys=['logContent']  title='Stage 3 — The Server Room'
Stage 4: toolType='canvas'  toolData keys=['imageBase64']  title='Stage 4 — The Surveillance Room'
Stage 5: toolType='sql'  toolData keys=['dbBase64']  title='Stage 5 — The Records Room'
Stage 6: toolType='python'  toolData keys=['script']  title='Stage 6 — The Vault'

All assertions passed.
```

- [ ] **Step 2: Verify vault9-files.zip is no longer needed (optional: remove or leave as-is)**

The webapp embeds all data — the zip is no longer necessary for participants. It can stay as an organiser backup but shouldn't be distributed.

Update README.md to reflect the change:

Find and replace the Session 2 distribution section in `README.md`:

Old:
```markdown
### Session 2 (stages 3–6)

1. Distribute `vault9-files.zip` to each team at the start of the session (USB stick, shared drive, or download link).
2. Teams unzip it — they'll need the files for stages 3–6.
3. Stage 4 requires Pillow: `pip install Pillow`
```

New:
```markdown
### Session 2 (stages 3–6)

No files to distribute. All stage data is embedded in the webapp. Teams just continue on the same `hackathon.html` they opened in session 1.

> **Note:** `vault9-files.zip` still exists as an organiser backup but participants do not need it.
```

- [ ] **Step 3: Final commit**

```bash
cd /home/samp/projects/AI/hackathon
git add README.md
git commit -m "chore: verified webapp end-to-end, update README for no-distribution flow"
```

---

## Self-Review

**Spec coverage:**
- [x] Stage 3: xterm.js terminal with bash subset — Task 3
- [x] Stage 4: Canvas pixel inspector, STEP input, extraction in JS — Task 4
- [x] Stage 5: sql.js SQL editor with results table — Task 5
- [x] Stage 6: Pyodide Python terminal, editable code, passphrase input — Task 6
- [x] File data embedded in encrypted payloads — Task 1 (configure.py)
- [x] No backend required, single static file — all CDN, no build step
- [x] configure.py updated — Task 1
- [x] Stages 1–2 unchanged — they have no toolType, initStageTool is a no-op

**Placeholder scan:** No TBDs or incomplete steps found.

**Type consistency:**
- `initStageTool(stageNum, payload)` — called in `renderNextStage`, dispatches to per-tool init functions
- `initTerminalTool(stageNum, container, toolData)` / `initCanvasTool` / `initSQLTool` / `initPythonTool` — all receive same signature
- `runExtraction(stageNum)` / `runSQL(stageNum)` / `runPython(stageNum)` / `loadPyodideEnv(stageNum)` — all global, invoked from onclick attributes
- `window[`sqlDb_${stageNum}`]` — consistent between initSQLTool and runSQL
- `_pyodide` (Promise) / `await _pyodide` (resolved Pyodide instance) — consistent across loadPyodideEnv and runPython
- `bashRun(cmdLine, fs)` called in terminal onKey handler — consistent with definition
