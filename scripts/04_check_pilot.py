#!/usr/bin/env python3
"""Offline checker for agent-written translations (no API). Enforces glossary lock and reports measured stats.
Usage: python3 scripts/04_check_pilot.py
Reads:  00_source/frames.jsonl, 00_source/fes.jsonl, 01_glossary/fe_glossary.tsv, 02_frames_ar/pilot_frames.txt,
        02_frames_ar/pilot_frames_ar.jsonl, 02_frames_ar/pilot_fes_ar.jsonl
Writes: 02_frames_ar/pilot_rejected.jsonl (rewritten each run), prints key=value report.
"""
import csv, json, re, pathlib, hashlib, collections
import os
FRAMES_FILE = os.environ.get("FRAMES_FILE", "02_frames_ar/pilot_frames.txt")
OUT_PREFIX  = os.environ.get("OUT_PREFIX", "pilot")   # pilot | full
ROOT = pathlib.Path(__file__).resolve().parents[1]
INTENDED_SHARED = {'المدى الزمني','الحد 1','الحد 2','المشارك 1','المشارك 2','مصدر الحرارة أو البرودة','المسافر'}
gl = list(csv.DictReader(open(ROOT/"01_glossary/fe_glossary.tsv", encoding="utf-8"), delimiter="\t"))
bad = [r["fe_name"] for r in gl if r["status"]!="APPROVED" or not r["owner_choice"].strip()]
shared = {k for k,v in collections.Counter(r["owner_choice"].strip() for r in gl).items() if v>1} - INTENDED_SHARED
G = {r["fe_name"]: r["owner_choice"].strip() for r in gl}
print(f"FRAMES_FILE = {FRAMES_FILE}  OUT_PREFIX = {OUT_PREFIX}")
print(f"GATE_1 = {'CLOSED' if not bad and not shared else 'FAILED'} not_approved={len(bad)} unintended_shared={len(shared)}")

ids = {int(x) for x in open(ROOT/FRAMES_FILE).read().split()}
frames = {json.loads(l)["frame_id"]: json.loads(l) for l in open(ROOT/"00_source/frames.jsonl", encoding="utf-8")}
fes = {json.loads(l)["fe_id"]: json.loads(l) for l in open(ROOT/"00_source/fes.jsonl", encoding="utf-8")}
exp_fr = {i for i in ids}; exp_fe = {k for k,v in fes.items() if v["frame_id"] in ids and v["definition_en"].strip()}
source_empty = sum(1 for v in fes.values() if v["frame_id"] in ids and not v["definition_en"].strip())

def load(p):
    p = ROOT/"02_frames_ar"/p
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []
def terms_in(text): return [n for n in G if re.search(r"(?<![A-Za-z_])"+re.escape(n)+r"(?![A-Za-z_])", text)]
LATIN = re.compile(r"[A-Za-z]{3,}")

st = collections.Counter(); rej = []
def check(kind, rec, src):
    ar = (rec.get("definition_ar") or "").strip(); en = src["definition_en"]
    problems = []
    scope = set(frames[src["frame_id"]]["fe_names"])
    viol = [n for n in terms_in(en) if n in scope and G[n] not in ar]
    if viol: problems.append(("glossary_violation", viol))
    if not ar or len(ar) < 0.2*len(en): problems.append(("empty_or_short", len(ar)))
    # Quoted English examples are allowed ONLY inside parentheses or quotes; strip them before the latin check.
    ar_stripped = re.sub(r"\([^()]*\)|\"[^\"]*\"|'[^']*'|«[^»]*»|“[^”]*”", " ", ar)
    leak = [w for w in LATIN.findall(ar_stripped) if w not in frames_names]
    if leak: problems.append(("latin_leak", leak[:5]))
    if problems:
        st["rejected"] += 1
        for k,_ in problems: st[k] += 1
        rej.append({**rec, "problems": problems})
    else: st[kind+"_ok"] += 1

frames_names = {f["name"] for f in frames.values()} | {w for f in frames.values() for w in f["name"].split("_")}
seen_fr, seen_fe = set(), set()
for r in load(f"{OUT_PREFIX}_frames_ar.jsonl"):
    if r["frame_id"] in exp_fr and r["frame_id"] not in seen_fr:
        seen_fr.add(r["frame_id"]); check("frame", r, frames[r["frame_id"]])
    else: st["extra_or_dup_frame"] += 1
for r in load(f"{OUT_PREFIX}_fes_ar.jsonl"):
    if r["fe_id"] in exp_fe and r["fe_id"] not in seen_fe:
        seen_fe.add(r["fe_id"]); check("fe", r, fes[r["fe_id"]])
    else: st["extra_or_dup_fe"] += 1
with open(ROOT/f"02_frames_ar/{OUT_PREFIX}_rejected.jsonl","w",encoding="utf-8") as w:
    for r in rej: w.write(json.dumps(r, ensure_ascii=False)+"\n")

print(f"frames_in = {len(exp_fr)}\nframes_done = {len(seen_fr)}\nframes_ok = {st['frame_ok']}\nframes_missing = {len(exp_fr-seen_fr)}")
print(f"source_empty = {source_empty}")
print(f"fes_in = {len(exp_fe)}\nfes_done = {len(seen_fe)}\nfes_ok = {st['fe_ok']}\nfes_missing = {len(exp_fe-seen_fe)}")
print(f"rejected = {st['rejected']}  glossary_violation={st['glossary_violation']} empty_or_short={st['empty_or_short']} latin_leak={st['latin_leak']}")
print(f"extra_or_dup = {st['extra_or_dup_frame']+st['extra_or_dup_fe']}")
# a frame is "to do" if its frame record OR any of its non-empty FEs is missing (partial frames get revisited)
fe_frames_missing = {fes[k]["frame_id"] for k in (exp_fe-seen_fe)}
todo = sorted((exp_fr-seen_fr) | fe_frames_missing)
print(f"frames_incomplete = {len(fe_frames_missing & seen_fr)}")
print(f"next_frames_missing = {todo[:10]}")
for p in (f"{OUT_PREFIX}_frames_ar.jsonl",f"{OUT_PREFIX}_fes_ar.jsonl",f"{OUT_PREFIX}_rejected.jsonl"):
    q = ROOT/"02_frames_ar"/p
    print(f"sha256 {p} = {hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else 'NOT_CREATED'}")
