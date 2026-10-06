#!/usr/bin/env python3
"""Phase 2: glossary-locked translation of frame + FE definitions.
Gates enforced at start: every glossary row APPROVED; no unintended shared Arabic term.
Usage:  ANTHROPIC_API_KEY=... python3 scripts/03_agent_translate_defs.py --frames 02_frames_ar/pilot_frames.txt
Provider: Anthropic Messages API via `pip3 install anthropic`. Swap call_model() for another provider if desired.
"""
import csv, json, sys, pathlib, re, argparse, collections, hashlib, time
ROOT = pathlib.Path(__file__).resolve().parents[1]
INTENDED_SHARED = {'المدى الزمني','الحد 1','الحد 2','المشارك 1','المشارك 2','مصدر الحرارة أو البرودة','المسافر'}

gl = list(csv.DictReader(open(ROOT/"01_glossary/fe_glossary.tsv", encoding="utf-8"), delimiter="\t"))
bad = [r["fe_name"] for r in gl if r["status"] != "APPROVED" or not r["owner_choice"].strip()]
if bad: sys.exit(f"GATE_1 FAILED: {len(bad)} rows not APPROVED (first: {bad[:5]})")
shared = {k for k,v in collections.Counter(r["owner_choice"].strip() for r in gl).items() if v>1} - INTENDED_SHARED
if shared: sys.exit(f"GATE_1 FAILED: unintended shared terms: {sorted(shared)}")
G = {r["fe_name"]: r["owner_choice"].strip() for r in gl}
REL = {r["relation_type"]: (r["owner_choice"] or r["claude_draft"]).strip()
       for r in csv.DictReader(open(ROOT/"01_glossary/relation_types.tsv", encoding="utf-8"), delimiter="\t")}

ap = argparse.ArgumentParser(); ap.add_argument("--frames", required=True); ap.add_argument("--model", default="claude-sonnet-4-6")
a = ap.parse_args(); ids = {int(x) for x in open(a.frames).read().split()}

def call_model(system: str, user: str) -> str:
    import anthropic, os
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if len(key) < 20:
        kf = pathlib.Path.home() / ".anthropic_key"
        key = kf.read_text(encoding="utf-8").strip() if kf.is_file() else ""
    if len(key) < 20 or not key.startswith("sk-ant-"):
        sys.exit("STOP / OWNER_ALERT: لا مفتاح صالح في البيئة ولا في ~/.anthropic_key")
    c = anthropic.Anthropic(api_key=key)
    for attempt in range(4):
        try:
            m = c.messages.create(model=a.model, max_tokens=2000, system=system, messages=[{"role":"user","content":user}])
            return "".join(b.text for b in m.content if b.type=="text").strip()
        except Exception as e:
            if attempt == 3: raise
            time.sleep(2**attempt)

SYS = ("أنت مترجم مصطلحي. ترجم تعريف FrameNet إلى العربية الفصحى بدقة ودون زيادة أو حذف. "
       "أسماء عناصر الإطار (بالإنجليزية بحرف كبير، مثل Agent, Theme) تُترجم حصراً بالمصطلح المقابل في المعجم أدناه، "
       "ولا يجوز إنشاء مصطلح غير موجود فيه. أبقِ أسماء الأطر الإنجليزية كما هي بين قوسين بعد ترجمتها إن ورد اسم إطار. "
       "أخرج الترجمة فقط بلا شرح.\n\nالمعجم:\n" + "\n".join(f"{k} = {v}" for k, v in G.items()))

def used_terms(text): return [n for n in G if re.search(r"(?<![A-Za-z_])"+re.escape(n)+r"(?![A-Za-z_])", text)]

stats = collections.Counter()
out_fr = open(ROOT/"02_frames_ar/pilot_frames_ar.jsonl", "a", encoding="utf-8")
out_fe = open(ROOT/"02_frames_ar/pilot_fes_ar.jsonl", "a", encoding="utf-8")
rej = open(ROOT/"02_frames_ar/pilot_rejected.jsonl", "a", encoding="utf-8")
frames = {json.loads(l)["frame_id"]: json.loads(l) for l in open(ROOT/"00_source/frames.jsonl", encoding="utf-8")}
fes = [json.loads(l) for l in open(ROOT/"00_source/fes.jsonl", encoding="utf-8")]

def translate(kind, rec, text, context):
    ar = call_model(SYS, context + "\n\nالنص:\n" + text)
    viol = [n for n in used_terms(text) if G[n] not in ar]
    rec = {**rec, "definition_ar": ar, "status": "DRAFT", "glossary_violations": viol}
    if viol:
        stats["rejected"] += 1; stats["glossary_violations"] += len(viol); rej.write(json.dumps(rec, ensure_ascii=False)+"\n")
    else:
        stats[kind+"_done"] += 1; (out_fr if kind=="frame" else out_fe).write(json.dumps(rec, ensure_ascii=False)+"\n")

for fid in sorted(ids):
    f = frames[fid]
    translate("frame", f, f["definition_en"], f"الإطار: {f['name']}")
    for fe in (x for x in fes if x["frame_id"]==fid):
        translate("fe", fe, fe["definition_en"], f"الإطار: {fe['frame']}\nالعنصر: {fe['name']} = {G[fe['name']]}\n(ترجم تعريف هذا العنصر)")
    print(fid, f["name"], dict(stats), flush=True)

print("FINAL", dict(stats), "# MEASURED")
for p in ("pilot_frames_ar.jsonl","pilot_fes_ar.jsonl","pilot_rejected.jsonl"):
    q = ROOT/"02_frames_ar"/p
    if q.exists(): print(p, "sha256=", hashlib.sha256(q.read_bytes()).hexdigest())
