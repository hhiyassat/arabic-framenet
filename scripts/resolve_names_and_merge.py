#!/usr/bin/env python3
"""Resolve cross-shard name-spelling conflicts, rewrite affected shard records, then merge into full_*.
Rules: approved names_map.tsv wins; else priority shard a > b > c. NONNAMES are dropped from maps (records untouched).
Dry run by default: prints every decision and the rewrite counts. Add --apply to write.
"""
import json, csv, re, glob, pathlib, hashlib, sys, subprocess, os
ROOT = pathlib.Path(__file__).resolve().parents[1]
APPLY = "--apply" in sys.argv
NONNAMES = {"Sun","Apple","Web","Atlantic","Japanese","French","Thames"}   # context-dependent translations, not proper names
OVERRIDE = {}   # e.g. {"Paul": "بولس"} — owner overrides, applied over everything else

def read_map(p):
    out = {}
    for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
        en, ar = r[list(r)[0]].strip(), r[list(r)[1]].strip()
        if en: out.setdefault(en, ar)
    return out
maps = {"approved": read_map(ROOT/"01_glossary/names_map.tsv")}
for s in "abc":
    p = ROOT/f"01_glossary/names_map_{s}.tsv"
    if p.exists(): maps[s] = read_map(p)

# collect all spellings per name
all_en = set().union(*[set(m) for m in maps.values()])
decisions, drops = {}, []
for en in sorted(all_en):
    forms = {k: m[en] for k, m in maps.items() if en in m}
    if en in NONNAMES: drops.append((en, forms)); continue
    if en in OVERRIDE: win = OVERRIDE[en]; src = "OVERRIDE"
    elif "approved" in forms: win = forms["approved"]; src = "approved"
    else:
        src = next(k for k in "abc" if k in forms); win = forms[src]
    losers = {k: v for k, v in forms.items() if v != win}
    if losers: decisions[en] = (win, src, losers)

print(f"names_total={len(all_en)} conflicts={len(decisions)} nonnames_dropped={len(drops)}")
for en, (win, src, losers) in decisions.items():
    print(f"  {en}: WIN={win} ({src})  losers={losers}")
for en, forms in drops: print(f"  DROP {en}: {forms}")

# rewrite shard records that use a losing spelling (only where the English name appears in definition_en)
rewrites = 0; touched = []
for s in "abc":
    for kind in ("frames", "fes"):
        p = ROOT/f"02_frames_ar/full_{s}_{kind}_ar.jsonl"
        if not p.exists(): continue
        recs = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        changed = False
        for r in recs:
            for en, (win, src, losers) in decisions.items():
                lose = losers.get(s)
                if not lose or not re.search(r"\b"+re.escape(en)+r"\b", r["definition_en"]): continue
                if lose in r["definition_ar"]:
                    r["definition_ar"] = r["definition_ar"].replace(lose, win); rewrites += 1; changed = True
                    touched.append((s, r.get("fe_id", r["frame_id"]), en, lose, win))
        if changed and APPLY:
            open(p, "w", encoding="utf-8").write("".join(json.dumps(r, ensure_ascii=False)+"\n" for r in recs))
print(f"record_rewrites={rewrites}")
for t in touched[:40]: print("  ", t)
if len(touched) > 40: print(f"   … +{len(touched)-40} more")

if not APPLY:
    print("\nDRY RUN — nothing written. Re-run with --apply to write maps, rewrite records, and merge."); sys.exit(0)

# write resolved maps: approved map gets all names with winning spelling; shard maps rewritten without nonnames/losers
final = {}
for en in sorted(all_en):
    if en in NONNAMES: continue
    final[en] = decisions[en][0] if en in decisions else next(m[en] for m in maps.values() if en in m)
with open(ROOT/"01_glossary/names_map.tsv", "w", encoding="utf-8") as w:
    w.write("en\tar\n"); [w.write(f"{k}\t{v}\n") for k, v in final.items()]
for s in "abc":
    p = ROOT/f"01_glossary/names_map_{s}.tsv"
    if p.exists():
        with open(p, "w", encoding="utf-8") as w:
            w.write("en\tar\n"); [w.write(f"{k}\t{final[k]}\n") for k in maps[s] if k in final]
with open(ROOT/"01_glossary/APPROVAL_LOG.txt", "a", encoding="utf-8") as w:
    w.write(f"NAMES_RESOLVE_001: {len(decisions)} conflicts resolved (approved-wins, a>b>c), {len(drops)} non-names dropped, {rewrites} records rewritten; OVERRIDE={OVERRIDE}\n")
# per-shard re-check, then merge
env = dict(os.environ)
for s in "abc":
    env.update(FRAMES_FILE=f"02_frames_ar/shard_{s}.txt", OUT_PREFIX=f"full_{s}")
    out = subprocess.run([sys.executable, "scripts/04_check_pilot.py"], cwd=ROOT, env=env, capture_output=True, text=True).stdout
    rj = [l for l in out.splitlines() if l.startswith("rejected")]; print(f"shard {s} recheck:", rj[0] if rj else out[-200:])
print("--- merge ---")
print(subprocess.run([sys.executable, "scripts/merge_shards.py"], cwd=ROOT, capture_output=True, text=True).stdout)
env.update(FRAMES_FILE="02_frames_ar/all_frames.txt", OUT_PREFIX="full")
print("--- full check ---")
print(subprocess.run([sys.executable, "scripts/04_check_pilot.py"], cwd=ROOT, env=env, capture_output=True, text=True).stdout)
