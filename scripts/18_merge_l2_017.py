#!/usr/bin/env python3
"""OWNER_DECISION_L2_019 (owner approved l2_017_review.xlsx as displayed). Merge the L2_017 candidates into 03_lus_ar/lus_ar.csv (status CANDIDATE;
approval is applied by 19 AFTER 07/11 so D2 can mark مكمِّل roots EVIDENCE_GAP) and extend lus_en_status.csv to all 9565 English LUs.
DEFER (not merged, kept in 03_lus_ar/l2_017_deferred.csv with reason): rows that break a ratified rule the approval cannot override —
pos_ar outside the closed list (L2_002/L2_007), صيغة مبالغة ≠ فَعَّال (L2_009), empty lemma/definition, Latin in definition.
English status: MAPPED if referenced by a merged row; NO_ARABIC_EQUIVALENT if the agent said so and no merged row references it; else TODO."""
import csv, hashlib, pathlib, re, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import wazn_rules as W
ROOT = pathlib.Path(__file__).resolve().parents[1]; D = ROOT / "03_lus_ar"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
PIN = {"l2_017_cand_norm2.csv": "70ebb67d7eb627e0ed08819979f11a2f3d4689792349791e22deebf1c6aa5fa5",
       "l2_017_review.xlsx": "03615a2e284742495cb2959e47a906ac727a6e5849a34a622bd6fdae6df0f36f"}
for f, h in PIN.items():
    if sha(D / f) != h: sys.exit(f"STOP sha {f}")
POS = {l.strip() for l in open(D / "pos_ar_closed.txt", encoding="utf-8") if l.strip()}
LATIN = re.compile(r"[A-Za-z]{3,}"); Q = re.compile(r"\([^()]*\)|\"[^\"]*\"|'[^']*'|«[^»]*»|“[^”]*”")
N = list(csv.DictReader(open(D / "l2_017_cand_norm2.csv", encoding="utf-8")))
A = list(csv.DictReader(open(D / "lus_ar.csv", encoding="utf-8-sig"))); cols = list(A[0])
E = list(csv.DictReader(open(D / "lus_en_status.csv", encoding="utf-8-sig"))); ecols = list(E[0])
if any(r["ar_lu_id"] >= "AR03949" for r in A): sys.exit("STOP already merged")
st = collections.Counter(); keep, defer = [], []
for r in N:
    why = []
    if r["pos_ar"] not in POS: why.append("pos_not_closed")
    if r["pos_ar"] == "صيغة مبالغة" and W.key(r["wazn"]) not in {W.key(x) for x in W.MUBALAGHA_WAZN}: why.append("mubalagha_not_faaal")
    if not r["lemma_ar"].strip(): why.append("empty_lemma")
    if not r["definition_ar"].strip(): why.append("empty_definition")
    if LATIN.findall(Q.sub(" ", r["definition_ar"])): why.append("latin_leak")
    if why: r["defer_reason"] = ";".join(why); defer.append(r); [st.__setitem__("defer_" + w, st["defer_" + w] + 1) for w in why]
    else: keep.append(r)
for r in keep:
    o = {c: "" for c in cols}
    for c in cols:
        if c in r: o[c] = r[c]
    o["status"] = "CANDIDATE"; o["owner_choice"] = ""
    if r["flags"]: o["note"] = (o["note"] + " | " if o["note"] else "") + "FLAGS: " + r["flags"]
    A.append(o)
with open(D / "lus_ar.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(A)
with open(D / "l2_017_deferred.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(N[0]) + ["defer_reason"]); w.writeheader(); w.writerows(defer)
# English status for the 1023 new frames
pilot = set(open(ROOT / "02_frames_ar/pilot_frames.txt").read().split())
tpl = [r for r in csv.DictReader(open(D / "lus_template.csv", encoding="utf-8-sig"))]
have = {r["en_lu_id"] for r in E}
ref = {e for r in keep for e in r["en_lu_ids"].split(";") if e}
nae = {r["en_lu_id"] for r in csv.DictReader(open(D / "l2_017_nae.csv", encoding="utf-8"))}
allf = set(open(ROOT / "02_frames_ar/l2_all_frames.txt").read().split())
for t in tpl:
    i = t["lu_id"]
    if t["frame_id"] in pilot or t["frame_id"] not in allf or i in have: continue
    s = "MAPPED" if i in ref else ("NO_ARABIC_EQUIVALENT" if i in nae else "TODO")
    if i in ref and i in nae: st["en_nae_but_mapped→MAPPED"] += 1
    st["en_new_" + s] += 1; o = {c: "" for c in ecols}; o["en_lu_id"] = i; o["status"] = s; E.append(o)
with open(D / "lus_en_status.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=ecols); w.writeheader(); w.writerows(E)
print(f"merged = {len(keep)}\ndeferred = {len(defer)}\nlus_ar_rows = {len(A)}\nlus_en_rows = {len(E)}")
for k in sorted(st): print(f"{k} = {st[k]}")
for p in ("lus_ar.csv", "lus_en_status.csv", "l2_017_deferred.csv"): print(f"sha256 03_lus_ar/{p} =", sha(D / p))
