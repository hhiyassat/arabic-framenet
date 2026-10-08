#!/usr/bin/env python3
"""Arabic FrameNet — deterministic lookup API (no AI / no LLM at runtime).

Reads ONLY the frozen, licensed releases (verified by sha256 before serving):
  release/layer1_v3  (frames, frame elements, relations — Arabic)
  release/layer2_v3  (7533 APPROVED Arabic lexical units, 980 frames)
  03_lus_ar/lus_template.csv  (FrameNet 1.7 English LU list, for English equivalents)

Run:   python3 api/afn_api.py                 # serves http://127.0.0.1:8765
       python3 api/afn_api.py --cli "غضب التاجر ولبس قميصه"   # one-shot JSON to stdout
Endpoints:
  POST /analyze      body {"text": "...", "mode": "exact"|"affix"}   (mode default "exact")
  GET  /analyze?text=...&mode=...
  GET  /frame/<frame_id>
  GET  /lu?lemma=<arabic>          (diacritics-insensitive)
  GET  /health
  GET  /            (built-in test page: form + rendered result + full JSON)

Matching (every hit reports how it matched; nothing is guessed silently):
  exact : token == lemma after removing tashkeel/tatweel and unifying أإآٱ→ا ، ى→ي ، ة→ه   (ORTHOGRAPHIC_NORMALIZATION)
  affix : additionally strips one common prefix (و ف ب ل ك ال …) and/or one suffix (ه ها هم ت ات ون …)  → match.method="AFFIX_STRIP"
  Both rules are NOT owner-ratified (status DEFER); they are reported in every response under "rules".
Not available (no data in the releases): assignment of frame elements to sentence spans (semantic role labelling),
valence patterns, annotated sentences, frames outside the 50 covered ones.
"""
import csv, hashlib, json, pathlib, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = pathlib.Path(__file__).resolve().parents[1]
REL = ROOT / "release"
PIN = {"layer1_v3": "84c69ebbd0c125c2792d97b1f7b941c162d2dd6dd3dce433a72bdcd53c589cc1",
       "layer2_v3": "2246dc4c11c481157726a015954f9e65c4e4d3ea0f583955a246d5caccbd90f7"}
TEMPLATE_SHA = {"5616d5fadcd89b4f2e46f24a17f20e6499915782ec9a0e6bb2ae047c4020e980",   # full FrameNet LU list (local)
                "75a240ae7dfc420c5c55c0ec238d146f4c27b7d4a6c6fa837b9c92602def1db9"}   # public copy: COD-sourced English definitions blanked
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def verify():
    for tag, h in PIN.items():
        d = REL / tag
        if sha(d / "MANIFEST.json") != h: sys.exit(f"STOP: {tag}/MANIFEST.json changed")
        m = json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))
        bad = [f for f, fh in m["files"].items() if sha(d / f) != fh]
        if bad or m.get("license_verified") is not True: sys.exit(f"STOP: {tag} {bad or 'license'}")
    if sha(ROOT / "03_lus_ar/lus_template.csv") not in TEMPLATE_SHA: sys.exit("STOP: lus_template.csv changed")

# ---------- load ----------
verify()
jl = lambda p: [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
FRAMES = {f["frame_id"]: f for f in jl(REL / "layer1_v3/frames_ar.jsonl")}
FES = {}
for e in jl(REL / "layer1_v3/frame_elements_ar.jsonl"): FES.setdefault(e["frame_id"], []).append(e)
RELS = {}
for r in jl(REL / "layer1_v3/frame_relations.jsonl"):
    RELS.setdefault(r["super_frame_id"], []).append(("sub", r))
    RELS.setdefault(r["sub_frame_id"], []).append(("super", r))
LUS = list(csv.DictReader(open(REL / "layer2_v3/lus_ar.csv", encoding="utf-8")))
EN = {r["lu_id"]: r for r in csv.DictReader(open(ROOT / "03_lus_ar/lus_template.csv", encoding="utf-8-sig"))}
ENST = {r["en_lu_id"]: r["status"] for r in csv.DictReader(open(REL / "layer2_v3/lus_en_status.csv", encoding="utf-8"))}
COVERED = {int(r["frame_id"]) for r in LUS}

DIAC = re.compile("[ً-ٰٟـ]")
def norm(s): return DIAC.sub("", s).translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}))
SINGLE, MULTI = {}, []
for i, lu in enumerate(LUS):
    t = norm(lu["lemma_ar"]).split()
    if len(t) > 1: MULTI.append((t, i))
    elif t: SINGLE.setdefault(t[0], []).append(i)
MULTI.sort(key=lambda x: -len(x[0]))
PREF = ["وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك", "س"]
SUF = ["هما", "كما", "تما", "تان", "تين", "ون", "ين", "ان", "ات", "ها", "هم", "هن", "كم", "نا", "وا", "تم", "ني", "ه", "ت", "ي", "ك", "ا"]
RULES = {"ORTHOGRAPHIC_NORMALIZATION": {"status": "DEFER (not owner-ratified)", "def": "remove tashkeel/tatweel; أإآٱ→ا ، ى→ي ، ة→ه"},
         "AFFIX_STRIP": {"status": "DEFER (not owner-ratified)", "def": "mode=affix only: strip one prefix " + "/".join(PREF) + " and/or one suffix " + "/".join(SUF) + "; stem ≥3 letters; may restore final ي/ه; حرف LUs excluded"}}

# ---------- views ----------
def lu_view(i):
    r = LUS[i]
    en = [{"lu_id": e, "lemma": EN[e]["lemma"], "pos": EN[e]["pos"], "status": ENST.get(e)} for e in r["en_lu_ids"].split(";") if e in EN]
    return {"ar_lu_id": r["ar_lu_id"], "lemma_ar": r["lemma_ar"], "pos_ar": r["pos_ar"], "frame_id": int(r["frame_id"]),
            "frame": FRAMES[int(r["frame_id"])]["name"], "frame_ar": FRAMES[int(r["frame_id"])]["name_ar"],
            "root": r["root"] or None, "wazn": r["wazn"] or None, "wazn_note": r["wazn_note"] or None,
            "definition_ar": r["definition_ar"], "en_lus": en,
            "evidence": {"primary": r["evidence_primary"] or None, "frame_level": r["evidence_frame_level"] or None, "metaphor": r["metaphor_flag"] or None},
            "status": r["status"]}

def frame_view(fid, full=True):
    f = FRAMES.get(fid)
    if not f: return None
    fes = sorted(FES.get(fid, []), key=lambda e: (e["core_type"] != "Core", e["fe_id"]))
    rels = [{"type": r["type"], "type_ar": r["type_ar"], "direction": d,
             "frame_id": r["super_frame_id"] if d == "super" else r["sub_frame_id"],
             "frame": r["super"] if d == "super" else r["sub"], "frame_ar": r["super_ar"] if d == "super" else r["sub_ar"]}
            for d, r in RELS.get(fid, [])]
    out = {"frame_id": fid, "name": f["name"], "name_ar": f["name_ar"], "coverage": "COVERED" if fid in COVERED else "NOT_COVERED",
           "definition_ar": f["definition_ar"],
           "frame_elements": [{"fe_id": e["fe_id"], "name": e["name"], "name_ar": e["name_ar"], "core_type": e["core_type"],
                               "sem_type": e.get("sem_type"), **({"definition_ar": e["definition_ar"]} if full else {})} for e in fes],
           "relations": rels,
           "lexical_units_ar": [{"ar_lu_id": r["ar_lu_id"], "lemma_ar": r["lemma_ar"], "pos_ar": r["pos_ar"]} for r in LUS if int(r["frame_id"]) == fid]}
    if full: out["definition_en"] = f["definition_en"]
    return out

def lookup(tok, mode):
    n = norm(tok)
    if n in SINGLE: return SINGLE[n], {"method": "EXACT_NORMALIZED", "stripped": None, "lemma_key": n}
    if mode != "affix": return None, None
    for p in [""] + [p for p in PREF if n.startswith(p) and len(n) - len(p) >= 2]:
        a = n[len(p):]
        cands = [(a, "")] + [(a[:-len(s)], s) for s in SUF if a.endswith(s) and len(a) - len(s) >= 2]
        for st, s in cands:
            if st == n or len(st) < 3: continue
            for c in (st, st + "ي", st + "ه"):
                ids = [i for i in SINGLE.get(c, []) if LUS[i]["pos_ar"] != "حرف"]
                if ids: return ids, {"method": "AFFIX_STRIP", "stripped": {"prefix": p or None, "suffix": s or None}, "lemma_key": c}
    return None, None

def analyze(text, mode="exact"):
    toks = [{"i": k, "surface": m.group(), "start": m.start(), "end": m.end(), "norm": norm(m.group())}
            for k, m in enumerate(re.finditer(r"[؀-ۿݐ-ݿ]+", text))]
    hits = [None] * len(toks)
    for k in range(len(toks)):
        for t, i in MULTI:
            L = len(t)
            if k + L <= len(toks) and all(toks[k + j]["norm"] == t[j] for j in range(L)) and not any(hits[k:k + L]):
                for j in range(L): hits[k + j] = ([i], {"method": "EXACT_NORMALIZED_MULTIWORD", "stripped": None, "lemma_key": " ".join(t)}, (k, L))
    for k, tk in enumerate(toks):
        if hits[k] is None:
            ids, how = lookup(tk["surface"], mode)
            if ids: hits[k] = (ids, how, (k, 1))
    targets, seen, fids = [], set(), []
    for k, h in enumerate(hits):
        if not h or h[2][0] in seen: continue
        seen.add(h[2][0]); s, L = h[2]
        lus = [lu_view(i) for i in h[0]]
        for lu in lus:
            if lu["frame_id"] not in fids: fids.append(lu["frame_id"])
        targets.append({"token_span": [s, s + L - 1], "surface": " ".join(t["surface"] for t in toks[s:s + L]),
                        "char_span": [toks[s]["start"], toks[s + L - 1]["end"]], "match": h[1],
                        "ambiguous_frames": len({lu["frame_id"] for lu in lus}) > 1, "lexical_units": lus})
    return {"input": text, "mode": mode, "engine": "deterministic lookup — no AI at runtime",
            "release": {"layer1_v3": PIN["layer1_v3"], "layer2_v3": PIN["layer2_v3"]}, "rules": RULES,
            "tokens": [{k: v for k, v in t.items()} for t in toks],
            "targets": targets,
            "frames": {str(f): frame_view(f) for f in fids},
            "uncovered_tokens": [t["surface"] for k, t in enumerate(toks) if hits[k] is None],
            "stats": {"tokens": len(toks), "targets": len(targets), "frames": len(fids),
                      "affix_matches": sum(1 for t in targets if t["match"]["method"] == "AFFIX_STRIP")},
            "not_available": ["frame-element (semantic role) assignment to sentence spans — no Arabic valence/annotation layer",
                              "inflection analysis beyond affix stripping (present tense, broken plurals) — no morphological analyzer",
                              f"frames outside the {len(COVERED)} covered frames (of {len(FRAMES)})",
                              "EVIDENCE_GAP lexical units (excluded from layer2_v3 by D2)"]}


INDEX_HTML = """<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arabic FrameNet API</title><style>
:root{--bg:#f2f4f3;--card:#fff;--ink:#1c2622;--mut:#5b6862;--rule:#d7ddda;--acc:#0d6b5f;--tgt:#b5651d;--tsoft:#f6e6d6;--asoft:#d9ece8}
@media (prefers-color-scheme:dark){:root{--bg:#121816;--card:#1a2220;--ink:#e4ebe8;--mut:#9aa8a2;--rule:#2c3733;--acc:#4fbfae;--tgt:#e3a15c;--tsoft:#3a2a19;--asoft:#1d3632}}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.7 "Noto Naskh Arabic","Geeza Pro",Tahoma,serif}
.w{max-width:900px;margin:auto;padding:24px 16px;display:grid;gap:16px}h1{margin:0;font-size:28px}
.box,.c{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:14px}
textarea{width:100%;min-height:70px;font:inherit;font-size:20px;background:transparent;color:var(--ink);border:0;outline:0;box-sizing:border-box}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-size:14px}
button{font:inherit;font-size:15px;background:var(--acc);color:var(--card);border:0;border-radius:999px;padding:6px 18px;cursor:pointer}
.s{font-size:26px;line-height:2.2}.h{background:var(--tsoft);color:var(--tgt);border-bottom:2px solid var(--tgt);font-weight:700}.h.a{border-bottom-style:dashed}
.m{color:var(--mut);font-size:14px}.fe{display:inline-block;font-size:13px;border:1px solid var(--rule);border-radius:6px;padding:0 8px;margin:2px}.fe.k{background:var(--asoft);border-color:transparent}
h3{margin:.4em 0 .2em}pre{direction:ltr;text-align:left;overflow:auto;font-size:12px;max-height:420px;background:var(--bg);padding:10px;border-radius:8px}
</style></head><body><div class="w"><h1>Arabic FrameNet API</h1>
<div class="m">بحث محدّد بلا ذكاء اصطناعي، من release/layer1_v3 و layer2_v3. نقاط الـ API: POST /analyze · GET /analyze?text= · GET /frame/&lt;id&gt; · GET /lu?lemma= · GET /health</div>
<form class="box" id="f"><textarea id="t">غضب التاجر من جاره، ثم لبس قميصه ومشى إلى السوق.</textarea>
<div class="row"><button>حلّل</button><label><input type="radio" name="m" value="exact" checked> مطابقة تامة</label><label><input type="radio" name="m" value="affix"> مع تجريد اللواصق (غير معتمد)</label></div></form>
<div id="o"></div></div><script>
const e=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
async function go(ev){ev&&ev.preventDefault();const text=document.getElementById("t").value,mode=document.querySelector("input[name=m]:checked").value;
const d=await (await fetch("/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text,mode})})).json();
const hit={};d.targets.forEach(t=>{for(let k=t.token_span[0];k<=t.token_span[1];k++)hit[k]=t.match.method});
let s="";let last=0;d.tokens.forEach(k=>{s+=e(text.slice(last,k.start));s+=hit[k.i]?`<span class="h${hit[k.i]=="AFFIX_STRIP"?" a":""}">${e(k.surface)}</span>`:e(k.surface);last=k.end});s+=e(text.slice(last));
let h=`<div class="c"><div class="s">${s}</div><div class="m">كلمات ${d.stats.tokens} · هدف ${d.stats.targets} · أطر ${d.stats.frames} · تجريد ${d.stats.affix_matches} · غير مغطّاة: ${e(d.uncovered_tokens.join("، "))}</div></div>`;
d.targets.forEach(t=>{h+=`<div class="c"><h3>${e(t.surface)} — <span class="m">${e(t.match.method)}${t.match.stripped?" ("+e(JSON.stringify(t.match.stripped))+")":""}</span></h3>`;
t.lexical_units.forEach(l=>{const F=d.frames[l.frame_id];h+=`<div><b>${e(l.lemma_ar)}</b> <span class="m">${e(l.pos_ar)} · جذر ${e(l.root||"—")} · وزن ${e(l.wazn||l.wazn_note||"—")} · ${e(l.en_lus.map(x=>x.lemma+"."+x.pos).join(", "))}</span><br>${e(l.definition_ar)}<br>
<b>${e(F.name_ar)}</b> <span class="m">${e(F.name)}</span><div class="m">${e(F.definition_ar)}</div>
${F.frame_elements.map(x=>`<span class="fe${x.core_type=="Core"?" k":""}" title="${e(x.name+": "+x.definition_ar)}">${e(x.name_ar)}</span>`).join("")}
<div class="m">علاقات: ${F.relations.map(r=>e(r.type_ar+" "+(r.direction=="super"?"← ":"→ ")+r.frame_ar)).join(" · ")||"—"}</div></div>`});h+="</div>"});
h+=`<details class="c"><summary>JSON الكامل</summary><pre>${e(JSON.stringify(d,null,1))}</pre></details>`;document.getElementById("o").innerHTML=h}
document.getElementById("f").addEventListener("submit",go);go();
</script></body></html>"""

# ---------- http ----------
class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False, indent=1).encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS"); self.send_header("Access-Control-Allow-Headers", "Content-Type"); self.end_headers()
    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path in ("/", "/index.html"):
            body = INDEX_HTML.encode("utf-8"); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if u.path == "/health": return self._send(200, {"ok": True, "frames": len(FRAMES), "covered_frames": len(COVERED), "lexical_units_ar": len(LUS)})
        if u.path == "/analyze": return self._send(200, analyze(q.get("text", ""), q.get("mode", "exact")))
        if u.path.startswith("/frame/"):
            try: fv = frame_view(int(u.path.split("/")[2]))
            except ValueError: fv = None
            return self._send(200 if fv else 404, fv or {"error": "frame_id not found"})
        if u.path == "/lu":
            n = norm(q.get("lemma", "")); ids = [i for i, r in enumerate(LUS) if norm(r["lemma_ar"]) == n]
            return self._send(200, {"lemma": q.get("lemma"), "lexical_units": [lu_view(i) for i in ids]})
        self._send(404, {"error": "unknown endpoint", "endpoints": ["POST /analyze", "GET /analyze?text=", "GET /frame/<id>", "GET /lu?lemma=", "GET /health"]})
    def do_POST(self):
        if urlparse(self.path).path != "/analyze": return self._send(404, {"error": "use POST /analyze"})
        try: body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except json.JSONDecodeError: return self._send(400, {"error": "body must be JSON: {\"text\": \"...\"}"})
        self._send(200, analyze(body.get("text", ""), body.get("mode", "exact")))
    def log_message(self, *a): pass

if __name__ == "__main__":
    if "--cli" in sys.argv:
        i = sys.argv.index("--cli"); mode = "affix" if "--affix" in sys.argv else "exact"
        print(json.dumps(analyze(sys.argv[i + 1], mode), ensure_ascii=False, indent=1)); sys.exit(0)
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
    print(f"Arabic FrameNet API on http://127.0.0.1:{port}  (verified layer1_v3 + layer2_v3)")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
