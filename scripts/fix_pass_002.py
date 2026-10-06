#!/usr/bin/env python3
"""FIX_PASS_002 — textual corrections on the full corpus, then status DRAFT→APPROVED. Dry run unless --apply.
1) Domination (frame 1797): 'العامل السببي الأساسي' → 'المؤثِّر السببي الأساسي'  (factor vs Agent collision)
2) 'متمّم حرف جر' → 'متمّم حرف الجر'  (grammar glossary spelling)
3) Asymmetric_reciprocality/Protagonist_2: drop inserted '، وهو المشارك الرئيس 2' (RULE_FIDELITY)
"""
import json, sys, pathlib, hashlib, re
ROOT = pathlib.Path(__file__).resolve().parents[1]; APPLY = "--apply" in sys.argv
def load(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
PF, PE = ROOT/"02_frames_ar/full_frames_ar.jsonl", ROOT/"02_frames_ar/full_fes_ar.jsonl"
F, E = load(PF), load(PE)
counts = {"factor": 0, "pp_def": 0, "insert": 0}
for r in F:
    if r["frame_id"] == 1797 and "العامل السببي الأساسي" in r["definition_ar"]:
        r["definition_ar"] = r["definition_ar"].replace("العامل السببي الأساسي", "المؤثِّر السببي الأساسي"); counts["factor"] += 1
for r in F + E:
    n = r["definition_ar"].count("متمّم حرف جر")
    if n: r["definition_ar"] = r["definition_ar"].replace("متمّم حرف جر", "متمّم حرف الجر"); counts["pp_def"] += n
for r in E:
    if r.get("name") == "Protagonist_2" and r.get("frame") == "Asymmetric_reciprocality" and "، وهو المشارك الرئيس 2" in r["definition_ar"]:
        r["definition_ar"] = r["definition_ar"].replace("، وهو المشارك الرئيس 2", ""); counts["insert"] += 1
        print("  Protagonist_2 →", r["definition_ar"][:160])
print("changes =", counts, " total_records =", len(F) + len(E))
if not APPLY: print("DRY RUN — nothing written"); sys.exit(0)
for r in F + E: r["status"] = "APPROVED"
open(PF, "w", encoding="utf-8").write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in F))
open(PE, "w", encoding="utf-8").write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in E))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
with open(ROOT/"01_glossary/APPROVAL_LOG.txt", "a", encoding="utf-8") as w:
    w.write(f"FIX_PASS_002 {counts}; GATE_2_FULL CLOSED by DR_HUSSEIN; status DRAFT→APPROVED for {len(F)} frames + {len(E)} FEs; sha frames={sha(PF)[:12]} fes={sha(PE)[:12]}\n")
print("APPLIED. sha256 full_frames_ar.jsonl =", sha(PF)); print("sha256 full_fes_ar.jsonl =", sha(PE))
print("now run: FRAMES_FILE=02_frames_ar/all_frames.txt OUT_PREFIX=full python3 scripts/04_check_pilot.py")
