#!/usr/bin/env python3
"""Owner instruction 2026-10-05 (L2_010): for LUs whose root is NOT in roots-4662, take evidence pointers from v21
(03_lus_ar/v21_roots_index.csv, sha pinned). Same column roles as 07. Pointer form: v21:<root>:<column>. Status unchanged
(D2 applies only to roots-4662 group مكمِّل). Rows whose root is in neither source are counted."""
import csv, hashlib, os, pathlib, re, sys, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]
IDX = ROOT / "03_lus_ar/v21_roots_index.csv"
if hashlib.sha256(IDX.read_bytes()).hexdigest() != "6b8beda92318b93eaa160e2e152228cd7cb15f4c858c78cb9f2421bf494dd174": print("STOP index sha"); sys.exit(2)
R2 = os.environ.get("R2_ROOTS", "/Users/husseinhiyassat/hokom-local-validation/taaqol-executor-wt/data/roots-4662-meaning.csv")
K = lambda s: re.sub(r"[أإآؤئء]", "ء", re.sub(r"[\s\-‌‍ـ]", "", s or "")).replace("ى", "ي").replace("ک", "ك")   # ک→ك L2_020
r2 = {K(r["الجذر"]) for r in csv.DictReader(open(R2, encoding="utf-8-sig"))}
v21 = {r["key"]: r for r in csv.DictReader(open(IDX, encoding="utf-8-sig"))}
p = ROOT / "03_lus_ar/lus_ar.csv"; rows = list(csv.DictReader(open(p, encoding="utf-8-sig"))); cols = list(rows[0])
st = collections.Counter(); miss = collections.Counter()
for r in rows:
    k = K(r["root"])
    if not k or k in r2: continue
    v = v21.get(k)
    if not v: st["root_in_neither"] += 1; miss[r["root"]] += 1; continue
    ptr = lambda c: f"v21:{v['root']}:{c}" if v.get(c) else ""
    r["evidence_primary"] = ptr("المحكم — المعاني")
    r["evidence_frame_level"] = ptr("مقاييس — المحور") or ptr("مقاييس — النص")
    r["metaphor_flag"] = ptr("الأساس — المجاز")
    st["root_in_v21"] += 1; st["v21_primary_filled" if r["evidence_primary"] else "v21_primary_empty"] += 1
with open(p, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
for k in sorted(st): print(f"{k} = {st[k]}")
print("root_in_neither_list =", " ".join(f"{k}×{v}" if v > 1 else k for k, v in sorted(miss.items())))
print("sha256 03_lus_ar/lus_ar.csv =", hashlib.sha256(p.read_bytes()).hexdigest())
