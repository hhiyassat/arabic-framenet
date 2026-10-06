#!/usr/bin/env python3
"""Owner instruction 2026-10-05: roots absent from roots-4662 are looked up in v21-معاني-حسب-الحرف (28 xlsx, 7337 roots).
Reads the frozen folder (each xlsx verified against its README.json sha256; README itself pinned) and writes
03_lus_ar/v21_roots_index.csv: root, key(K), file, and which evidence columns are non-empty. No text is copied."""
import csv, hashlib, json, os, pathlib, re, sys
import openpyxl
ROOT = pathlib.Path(__file__).resolve().parents[1]
V21 = pathlib.Path(os.environ.get("V21_DIR", "/Users/husseinhiyassat/hokom-local-validation/taaqol-executor-wt/data/v21-معاني-حسب-الحرف"))
README_SHA = os.environ.get("V21_README_SHA", "ab0d42b4b205ee460bc3c4331e3c4fffe032c19c56d7a8a8f593cd5ca97e735d")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
rd = V21 / "README.json"
if README_SHA and sha(rd) != README_SHA: print("STOP README sha mismatch"); sys.exit(2)
meta = json.load(open(rd, encoding="utf-8"))["files"]
K = lambda s: re.sub(r"[أإآؤئء]", "ء", re.sub(r"[\s\-‌‍ـ]", "", s or "")).replace("ى", "ي")
COLS = ["المحكم — المعاني", "مقاييس — المحور", "مقاييس — النص", "الأساس — المجاز"]
out, bad = [], []
for rel, m in sorted(meta.items()):
    p = V21 / pathlib.Path(rel).name
    if sha(p) != m["sha256"]: bad.append(p.name); continue
    ws = openpyxl.load_workbook(p, read_only=True).worksheets[0]
    it = ws.iter_rows(values_only=True); hdr = list(next(it)); idx = {c: hdr.index(c) for c in COLS if c in hdr}
    for row in it:
        if not row or not row[0]: continue
        out.append([row[0], K(str(row[0])), p.name] + [("1" if c in idx and row[idx[c]] not in (None, "") else "") for c in COLS])
if bad: print("STOP sha mismatch:", bad); sys.exit(2)
dst = ROOT / "03_lus_ar/v21_roots_index.csv"
with open(dst, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["root", "key", "file"] + COLS); w.writerows(out)
print(f"v21_roots = {len(out)}  unique_keys = {len({r[1] for r in out})}")
print("sha256 03_lus_ar/v21_roots_index.csv =", sha(dst))
