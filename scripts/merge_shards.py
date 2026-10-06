#!/usr/bin/env python3
"""Merge full_<x>_*.jsonl and names_map_<x>.tsv into full_*.jsonl / names_map.tsv. Refuses on any conflict.
Run only when all shard drivers have stopped. Prints measured counts; never deletes shard files.
"""
import json, csv, pathlib, hashlib, collections, glob
ROOT = pathlib.Path(__file__).resolve().parents[1]
def rows(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
def key(r): return ("f", r["frame_id"]) if "fe_id" not in r else ("e", r["fe_id"])
main_f = rows(ROOT/"02_frames_ar/full_frames_ar.jsonl"); main_e = rows(ROOT/"02_frames_ar/full_fes_ar.jsonl")
have = {key(r) for r in main_f} | {key(r) for r in main_e}
add_f, add_e, dup = [], [], 0
for p in sorted(glob.glob(str(ROOT/"02_frames_ar/full_[a-z]_frames_ar.jsonl"))): 
    for r in rows(p):
        if key(r) in have: dup += 1
        else: have.add(key(r)); add_f.append(r)
for p in sorted(glob.glob(str(ROOT/"02_frames_ar/full_[a-z]_fes_ar.jsonl"))):
    for r in rows(p):
        if key(r) in have: dup += 1
        else: have.add(key(r)); add_e.append(r)
# names: conflict = same en with different ar across files
names = {}
conf = []
for p in [ROOT/"01_glossary/names_map.tsv"] + sorted(ROOT.glob("01_glossary/names_map_[a-z].tsv")):
    for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
        en, ar = r[list(r)[0]].strip(), r[list(r)[1]].strip()
        if not en: continue
        if en in names and names[en] != ar: conf.append((en, names[en], ar, p.name))
        names.setdefault(en, ar)
print(f"frames_to_add={len(add_f)} fes_to_add={len(add_e)} duplicates_skipped={dup} name_conflicts={len(conf)}")
for c in conf: print("  CONFLICT", c)
if conf: raise SystemExit("REFUSED: resolve name conflicts (owner decision) then rerun")
with open(ROOT/"02_frames_ar/full_frames_ar.jsonl","a",encoding="utf-8") as w:
    for r in add_f: w.write(json.dumps(r, ensure_ascii=False)+"\n")
with open(ROOT/"02_frames_ar/full_fes_ar.jsonl","a",encoding="utf-8") as w:
    for r in add_e: w.write(json.dumps(r, ensure_ascii=False)+"\n")
with open(ROOT/"01_glossary/names_map.tsv","w",encoding="utf-8") as w:
    w.write("en\tar\n"); [w.write(f"{k}\t{v}\n") for k,v in names.items()]
for p in ("02_frames_ar/full_frames_ar.jsonl","02_frames_ar/full_fes_ar.jsonl","01_glossary/names_map.tsv"):
    print(p, "sha256=", hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
print("MERGED — now run: FRAMES_FILE=02_frames_ar/all_frames.txt OUT_PREFIX=full python3 scripts/04_check_pilot.py")
