#!/usr/bin/env python3
"""Freeze Layer 2 (Arabic LUs, 50 pilot frames) into release/layer2_v1/. Blocks unless checker gives rejected=0 and every
included LU is APPROVED with owner_choice. EVIDENCE_GAP LUs are excluded (OWNER_DELEGATION_L2_001 / D2) and only counted.
Writes MANIFEST.json (sha256 per file) and README.md. Read-only on sources; never touches release/layer1_v1."""
import csv, hashlib, json, os, pathlib, shutil, subprocess, sys, datetime, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "layer2_v1"
REL = ROOT / "release" / TAG
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if REL.exists() and any(REL.iterdir()): sys.exit(f"FREEZE BLOCKED: {REL} exists (immutable; use a new tag)")
out = subprocess.run([sys.executable, str(ROOT / "scripts/06_check_lus.py")], capture_output=True, text=True).stdout
kv = dict(l.split(" = ", 1) for l in out.splitlines() if " = " in l and not l.startswith("sha256"))
if kv.get("rejected") != "0": sys.exit("FREEZE BLOCKED: checker rejected=" + str(kv.get("rejected")))
L1 = ROOT / "release/layer1_v1/MANIFEST.json"
if sha(L1) != "817e5143e6ebb9ae6e57bb222ef890b55d032196b5f2cf8928556574fa9d7f2e": sys.exit("FREEZE BLOCKED: layer1 manifest changed")
ar = list(csv.DictReader(open(ROOT / "03_lus_ar/lus_ar.csv", encoding="utf-8-sig"))); cols = list(ar[0])
app = [r for r in ar if r["status"] == "APPROVED"]; gap = [r for r in ar if r["status"] == "EVIDENCE_GAP"]
if any(not r["owner_choice"] for r in app): sys.exit("FREEZE BLOCKED: APPROVED without owner_choice")
if len(app) + len(gap) != len(ar): sys.exit("FREEZE BLOCKED: unexpected status")
REL.mkdir(parents=True)
with open(REL / "lus_ar.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(app)
approved_en = {e for r in app for e in r["en_lu_ids"].split(";") if e}
gap_en = {e for r in gap for e in r["en_lu_ids"].split(";") if e}
en = list(csv.DictReader(open(ROOT / "03_lus_ar/lus_en_status.csv", encoding="utf-8-sig"))); enst = collections.Counter()
with open(REL / "lus_en_status.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["en_lu_id", "status"])
    for r in en:
        s = r["status"]
        if s == "MAPPED": s = "MAPPED" if r["en_lu_id"] in approved_en else ("EVIDENCE_GAP_ONLY" if r["en_lu_id"] in gap_en else "MAPPED?")
        enst[s] += 1; w.writerow([r["en_lu_id"], s])
if enst.get("MAPPED?"): sys.exit("FREEZE BLOCKED: inconsistent en status")
sys.path.insert(0, str(ROOT / "scripts")); import wazn_rules as W
SIB = os.environ["AWZAN_SIB"]; VB = os.environ["AWZAN_VERBS"]
inv = W.noun_inventory_v3({r["pattern_vocalized"].strip() for r in csv.DictReader(open(SIB, encoding="utf-8-sig")) if r["status"] == "EXISTS"},
                          {r["wazn"].strip() for r in csv.DictReader(open(VB, encoding="utf-8-sig"))}, ROOT / "03_lus_ar/wazn_owner_l2_015.csv")
with open(REL / "wazn_nouns_inventory.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["key", "wazn", "provenance"])
    for k, (l, p) in sorted(inv.items(), key=lambda x: (x[1][1].split(" ")[0], x[0])): w.writerow([k, l, p])
for src in ("03_lus_ar/pos_ar_closed.txt", "03_lus_ar/pos_glossary.tsv", "03_lus_ar/wazn_owner_l2_015.csv", "03_lus_ar/root_alert_waived.txt",
            "03_lus_ar/v21_roots_index.csv", "01_glossary/APPROVAL_LOG.txt", "scripts/06_check_lus.py", "scripts/wazn_rules.py"):
    shutil.copy(ROOT / src, REL / pathlib.Path(src).name)
files = sorted(p.name for p in REL.iterdir())
pos = collections.Counter(r["pos_ar"] for r in app); frames = len({r["frame_id"] for r in app})
man = {"tag": TAG, "frozen_at": datetime.datetime.now().isoformat(timespec="seconds"), "layer1_manifest": sha(L1), "license_verified": (ROOT / "00_source/LICENSE.txt").exists(),
       "counts": {"ar_lus_approved": len(app), "ar_lus_evidence_gap_excluded": len(gap), "frames": frames, "en_lus_in_scope": len(en), **{"en_" + k: v for k, v in enst.items()},
                  "with_wazn": sum(bool(r["wazn"]) for r in app), "with_evidence_primary": sum(bool(r["evidence_primary"]) for r in app), "noun_wazn_inventory": len(inv)},
       "pos_ar_distribution": dict(pos), "checker": {k: kv[k] for k in kv if k.startswith(("rejected", "OWNER_ALERT"))},
       "files": {f: sha(REL / f) for f in files},
       "upstream_fingerprints": {"03_lus_ar/lus_ar.csv": sha(ROOT / "03_lus_ar/lus_ar.csv"), "03_lus_ar/lus_en_status.csv": sha(ROOT / "03_lus_ar/lus_en_status.csv"),
                                 "03_lus_ar/lus_template.csv": sha(ROOT / "03_lus_ar/lus_template.csv"), "roots-4662-meaning.csv": sha(os.environ["R2_ROOTS"]), "awzan-sibawayh-308.csv": sha(SIB), "awzaan_af3aal_all.csv": sha(VB)}}
(REL / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
(REL / "README.md").write_text(f"""# Arabic FrameNet — Layer 2 release `{TAG}`

RULE_OWNER = DR_HUSSEIN. Frozen {man['frozen_at']}. Builds on layer1_v1 (MANIFEST sha {sha(L1)[:12]}); keys are FrameNet 1.7 frame_id / lu_id.

## What this is
Arabic lexical units for the **50 pilot frames**: {len(app)} APPROVED Arabic LUs (key = lemma_ar, pos_ar, frame_id), linked many-to-many to the
{len(en)} English LUs of those frames ({enst['MAPPED']} MAPPED, {enst.get('NO_ARABIC_EQUIVALENT',0)} NO_ARABIC_EQUIVALENT, {enst.get('EVIDENCE_GAP_ONLY',0)} EVIDENCE_GAP_ONLY).
Each LU carries root, wazn (from the ratified inventory: Sibawayh EXISTS + L2_005 feminine + L2_006 verb derivatives + L2_007 nisba + L2_015 owner patterns),
pos_ar from a closed list of 16, an independent Arabic definition, and evidence pointers (roots-4662 / v21: المحكم، مقاييس، الأساس).

## What this is NOT
- Not all of FrameNet: 1171 other frames have no Arabic LUs yet (no expansion before this gate).
- {len(gap)} LUs whose root is a «مكمِّل» root in roots-4662 are EXCLUDED (D2 → EVIDENCE_GAP); listed only in the working file.
- No annotated sentences or valence patterns. Not a source of rulings (frame ≠ ruling).
- Evidence columns are pointers, not quoted text; COD definitions were not translated.

## Files
{' · '.join(files)} · MANIFEST.json
Read by fingerprint; immutable — corrections produce a new tag.

## Status
license_verified = {man['license_verified']} — DO NOT REDISTRIBUTE until 00_source/LICENSE.txt is added (G0.1).
""", encoding="utf-8")
print(f"FROZEN {TAG}: approved={len(app)} gap_excluded={len(gap)} frames={frames} en={dict(enst)} files={len(files)+2}")
print("sha256 MANIFEST.json =", sha(REL / "MANIFEST.json"))
