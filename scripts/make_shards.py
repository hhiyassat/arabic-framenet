#!/usr/bin/env python3
"""Split the frames still missing from the main full_* run into N disjoint shard files.
Usage: python3 scripts/make_shards.py 3   → 02_frames_ar/shard_a.txt, shard_b.txt, shard_c.txt
Run this ONLY while no driver is running (or accept that the main run's next few frames overlap: see README note).
"""
import sys, json, pathlib, os
ROOT = pathlib.Path(__file__).resolve().parents[1]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
ids = [int(x) for x in open(ROOT/"02_frames_ar/all_frames.txt").read().split()]
fes = [json.loads(l) for l in open(ROOT/"00_source/fes.jsonl", encoding="utf-8")]
need = {}
for e in fes:
    if e["definition_en"].strip(): need.setdefault(e["frame_id"], set()).add(e["fe_id"])
have_fr, have_fe = set(), {}
for p in ROOT.glob("02_frames_ar/full*_frames_ar.jsonl"):
    have_fr |= {json.loads(l)["frame_id"] for l in open(p, encoding="utf-8") if l.strip()}
for p in ROOT.glob("02_frames_ar/full*_fes_ar.jsonl"):
    for l in open(p, encoding="utf-8"):
        if l.strip(): e = json.loads(l); have_fe.setdefault(e["frame_id"], set()).add(e["fe_id"])
done = {i for i in have_fr if have_fe.get(i, set()) >= need.get(i, set())}   # complete frames only
missing = [i for i in ids if i not in done]
shards = [missing[k::N] for k in range(N)]
for k, sh in enumerate(shards):
    name = chr(ord('a')+k)
    (ROOT/f"02_frames_ar/shard_{name}.txt").write_text("\n".join(map(str, sh))+"\n")
    print(f"shard_{name}.txt frames={len(sh)}")
print(f"missing_total={len(missing)} done={len(done)}")
