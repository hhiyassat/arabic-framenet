#!/usr/bin/env python3
"""Freeze layer 1 into release/layer1_v1/: copies approved artifacts, adds Arabic names/relation labels,
writes MANIFEST.json (sha256 per file) and README.md. Verifies counts and statuses before writing. Read-only on sources.
Usage: python3 scripts/05_freeze_release.py [--tag layer1_v1]
"""
import json, csv, hashlib, pathlib, shutil, sys, datetime, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]
TAG = sys.argv[sys.argv.index("--tag")+1] if "--tag" in sys.argv else "layer1_v1"
REL = ROOT/"release"/TAG
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def tsv(p, quote_none=True): return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
def jl(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

# --- verify ---
F = jl(ROOT/"02_frames_ar/full_frames_ar.jsonl"); E = jl(ROOT/"02_frames_ar/full_fes_ar.jsonl")
fn = tsv(ROOT/"01_glossary/frame_names.tsv"); fe = tsv(ROOT/"01_glossary/fe_glossary.tsv", False); gr = tsv(ROOT/"01_glossary/grammar_glossary.tsv", False); rt = tsv(ROOT/"01_glossary/relation_types.tsv", False)
rel = jl(ROOT/"00_source/relations.jsonl")
problems = []
if len(F) != 1221: problems.append(f"frames={len(F)}")
if len(E) != 11416: problems.append(f"fes={len(E)}")
if any(r["status"] != "APPROVED" for r in F+E): problems.append("unapproved records")
if len(fn) != 1221 or any(r["status"] != "APPROVED" or not r["owner_choice"] for r in fn): problems.append("frame_names not fully approved")
if any(r["status"] != "APPROVED" or not r["owner_choice"] for r in fe): problems.append("fe_glossary not fully approved")
if any(r["status"] != "APPROVED" for r in rt): problems.append("relation_types not approved")
if problems: sys.exit("FREEZE BLOCKED: " + "; ".join(problems))
license_ok = (ROOT/"00_source/LICENSE.txt").exists()

# --- build enriched release files ---
REL.mkdir(parents=True, exist_ok=True)
name_ar = {r["frame_name"]: r["owner_choice"] for r in fn}
fe_ar = {r["fe_name"]: r["owner_choice"] for r in fe}
rel_ar = {r["relation_type"]: r["owner_choice"] for r in rt}
with open(REL/"frames_ar.jsonl", "w", encoding="utf-8") as w:
    for f in F:
        w.write(json.dumps({"frame_id": f["frame_id"], "name": f["name"], "name_ar": name_ar[f["name"]], "definition_en": f["definition_en"], "definition_ar": f["definition_ar"], "fe_names": f["fe_names"], "lu_count": f["lu_count"], "status": f["status"]}, ensure_ascii=False)+"\n")
with open(REL/"frame_elements_ar.jsonl", "w", encoding="utf-8") as w:
    for e in E:
        w.write(json.dumps({"fe_id": e["fe_id"], "frame_id": e["frame_id"], "frame": e["frame"], "name": e["name"], "name_ar": fe_ar[e["name"]], "core_type": e["core_type"], "sem_type": e["sem_type"], "definition_en": e["definition_en"], "definition_ar": e["definition_ar"], "status": e["status"]}, ensure_ascii=False)+"\n")
with open(REL/"frame_relations.jsonl", "w", encoding="utf-8") as w:
    for r in rel:
        w.write(json.dumps({**r, "type_ar": rel_ar[r["type"]], "super_ar": name_ar.get(r["super"]), "sub_ar": name_ar.get(r["sub"])}, ensure_ascii=False)+"\n")
for src in ("01_glossary/fe_glossary.tsv", "01_glossary/grammar_glossary.tsv", "01_glossary/frame_names.tsv", "01_glossary/relation_types.tsv", "01_glossary/names_map.tsv", "01_glossary/APPROVAL_LOG.txt"):
    shutil.copy(ROOT/src, REL/pathlib.Path(src).name)
if license_ok: shutil.copy(ROOT/"00_source/LICENSE.txt", REL/"LICENSE.txt")

# --- manifest + readme ---
files = sorted(p.name for p in REL.iterdir() if p.name not in ("MANIFEST.json", "README.md"))
man = {"tag": TAG, "frozen_at": datetime.datetime.now().isoformat(timespec="seconds"), "source": "FrameNet 1.7 (ICSI Berkeley) via nltk framenet_v17",
       "license_verified": license_ok, "counts": {"frames": len(F), "frame_elements": len(E), "fe_source_empty_excluded": 12, "relations": len(rel), "fe_name_terms": len(fe), "grammar_terms": len(gr), "names": len(tsv(ROOT/"01_glossary/names_map.tsv", False))},
       "core_type_distribution": dict(collections.Counter(e["core_type"] for e in E)), "files": {f: sha(REL/f) for f in files},
       "upstream_fingerprints": {"full_frames_ar.jsonl": sha(ROOT/"02_frames_ar/full_frames_ar.jsonl"), "full_fes_ar.jsonl": sha(ROOT/"02_frames_ar/full_fes_ar.jsonl")}}
(REL/"MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
(REL/"README.md").write_text(f"""# Arabic FrameNet — Layer 1 release `{TAG}`

RULE_OWNER = DR_HUSSEIN. Frozen {man['frozen_at']}. Keys are FrameNet 1.7 numeric IDs (frame_id / fe_id); Arabic names are labels, not keys.

## What this is
Arabic translations of FrameNet 1.7 **frame definitions ({len(F)}) and frame-element definitions ({len(E)})**, with approved Arabic terms for
{len(fe)} frame-element names, {len(gr)} grammatical-function terms, {len(fn)} frame names, and 10 frame-relation types; relations ({len(rel)}) carried by ID.

## What this is NOT
- No Arabic lexical units: no link from any Arabic word to any frame exists in this release. Arabic LU = 0.
- No Arabic annotated sentences or valence patterns.
- Not a source of rulings: frames describe event types, never their legal/juristic status (see HANDOFF).

## Files
frames_ar.jsonl · frame_elements_ar.jsonl · frame_relations.jsonl · fe_glossary.tsv · grammar_glossary.tsv · frame_names.tsv · relation_types.tsv · names_map.tsv · APPROVAL_LOG.txt · MANIFEST.json
Consumers must read by fingerprint (MANIFEST.json) and treat the release as immutable; corrections produce a new tag.

## Status
license_verified = {license_ok}  — {'' if license_ok else 'DO NOT REDISTRIBUTE until 00_source/LICENSE.txt is added (G0.1).'}
Provenance: 50-frame pilot reviewed by owner (GATE_2), full corpus checker-clean and independently sampled (GATE_2_FULL), see APPROVAL_LOG.txt.
""", encoding="utf-8")
print(f"FROZEN release/{TAG}: files={len(files)} license_verified={license_ok}")
for f, h in man["files"].items(): print(f"  {h[:12]}  {f}")
print("MANIFEST sha256 =", sha(REL/"MANIFEST.json"))
