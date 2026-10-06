#!/usr/bin/env python3
"""L2 — fill evidence pointers and D2 status in 03_lus_ar/lus_ar.csv from frozen R2 (roots-4662-meaning.csv).
Pointers only (no text copied): roots-4662:<root>:<column>. Roles (HANDOFF): evidence_primary=المحكم — المعاني ;
evidence_frame_level=مقاييس — المحور else مقاييس — النص ; metaphor_flag=الأساس — المجاز (pointer = source has a مجاز entry for the root; NOT a per-LU judgement).
D2 (OWNER_DECISION_L2_004): root in group مكمِّل → status EVIDENCE_GAP. Root not in R2 → left CANDIDATE, evidence empty, counted.
Never touches owner_choice. Usage: R2_ROOTS=... python3 scripts/07_fill_evidence.py"""
import csv, hashlib, os, pathlib, re, collections, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
R2 = os.environ.get("R2_ROOTS", "/Users/husseinhiyassat/hokom-local-validation/taaqol-executor-wt/data/roots-4662-meaning.csv")
H = "1a711ffe9cc3286d87276b04a836b26756b67f3657f8a0904a0c7b4ac4d020da"
if hashlib.sha256(open(R2, "rb").read()).hexdigest() != H: print("STOP R2 sha mismatch"); sys.exit(2)
K = lambda s: re.sub(r"[أإآؤئء]", "ء", re.sub(r"[\s\-‌‍ـ]", "", s or "")).replace("ى", "ي")
src = {K(r["الجذر"]): r for r in csv.DictReader(open(R2, encoding="utf-8-sig"))}
p = ROOT / "03_lus_ar/lus_ar.csv"
rows = list(csv.DictReader(open(p, encoding="utf-8-sig"))); cols = list(rows[0].keys())
st = collections.Counter()
for r in rows:
    k = K(r["root"])
    if not k: st["no_root"] += 1; continue
    s = src.get(k)
    if s is None: st["root_not_in_R2"] += 1; continue
    ptr = lambda c: f"roots-4662:{s['الجذر']}:{c}" if (s.get(c) or "").strip() else ""
    r["evidence_primary"] = ptr("المحكم — المعاني")
    r["evidence_frame_level"] = ptr("مقاييس — المحور") or ptr("مقاييس — النص")
    r["metaphor_flag"] = ptr("الأساس — المجاز")
    st["evidence_primary_filled" if r["evidence_primary"] else "evidence_primary_empty"] += 1
    if s["المجموعة"] == "مكمِّل":
        if r["status"] != "APPROVED": r["status"] = "EVIDENCE_GAP"; st["set_EVIDENCE_GAP"] += 1
    else: st["root_verified"] += 1
with open(p, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
for k in sorted(st): print(f"{k} = {st[k]}")
print("sha256 03_lus_ar/lus_ar.csv =", hashlib.sha256(p.read_bytes()).hexdigest())
