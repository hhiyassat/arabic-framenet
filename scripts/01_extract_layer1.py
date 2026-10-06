#!/usr/bin/env python3
"""Layer-1 extraction: FrameNet 1.7 → JSONL (frames, FEs, relations). Keys = FN numeric IDs.
Run once:  pip install nltk && python3 -c "import nltk; nltk.download('framenet_v17')"
"""
import json, hashlib, pathlib
from nltk.corpus import framenet as fn
OUT = pathlib.Path(__file__).resolve().parents[1] / "00_source"
OUT.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
with open(OUT/"frames.jsonl","w",encoding="utf-8") as fw, open(OUT/"fes.jsonl","w",encoding="utf-8") as ew:
    nf=ne=0
    for f in fn.frames():
        fw.write(json.dumps({"frame_id":f.ID,"name":f.name,"definition_en":f.definition,
            "fe_names":list(f.FE.keys()),"lu_count":len(f.lexUnit)},ensure_ascii=False)+"\n"); nf+=1
        for n,fe in f.FE.items():
            ew.write(json.dumps({"fe_id":fe.ID,"frame_id":f.ID,"frame":f.name,"name":n,
                "core_type":fe.coreType,"definition_en":fe.definition,
                "sem_type":fe.semType.name if fe.semType else None},ensure_ascii=False)+"\n"); ne+=1
with open(OUT/"relations.jsonl","w",encoding="utf-8") as rw:
    nr=0
    for r in fn.frame_relations():
        rw.write(json.dumps({"rel_id":r.ID,"type":r.type.name,"super_frame_id":r.superFrame.ID,
            "sub_frame_id":r.subFrame.ID,"super":r.superFrame.name,"sub":r.subFrame.name},ensure_ascii=False)+"\n"); nr+=1
print(f"frames={nf} fes={ne} relations={nr}")
for p in sorted(OUT.glob("*.jsonl")): print(f"{p.name} sha256={sha(p)}")
