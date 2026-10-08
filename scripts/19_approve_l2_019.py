#!/usr/bin/env python3
"""OWNER_DECISION_L2_019 — apply the owner's approval of l2_017_review.xlsx (owner_choice empty everywhere = approved as displayed).
Run AFTER 18, 07, 11, 08. For rows AR03949+:
  DEFER (moved out of lus_ar.csv into l2_017_deferred.csv, OWNER_ALERT): root written in a non-Arabic script (no ratified rule maps it).
  status CANDIDATE → APPROVED with owner_choice = lemma_ar (as displayed). EVIDENCE_GAP (D2, set by 07) unchanged.
Then English status of the new frames is recomputed from what remains (MAPPED / NO_ARABIC_EQUIVALENT / TODO)."""
import csv, hashlib, pathlib, re, sys, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]; D = ROOT / "03_lus_ar"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if sha(D / "lus_ar.csv") != "826314f0709818f846698235b8b207b49b3e56e37ccc2b612667e53c044ba02b": sys.exit("STOP lus_ar sha")
A = list(csv.DictReader(open(D / "lus_ar.csv", encoding="utf-8-sig"))); cols = list(A[0])
DF = list(csv.DictReader(open(D / "l2_017_deferred.csv", encoding="utf-8"))); dcols = list(DF[0])
st = collections.Counter(); out = []
for r in A:
    if r["ar_lu_id"] < "AR03949": out.append(r); continue
    if r["root"] and re.search(r"[^ء-ي]", r["root"]):
        d = {c: r.get(c, "") for c in dcols}; d["defer_reason"] = "root_not_arabic_script"; d["status"] = "CANDIDATE"; DF.append(d)
        st["defer_root_not_arabic_script"] += 1; continue
    if r["status"] == "CANDIDATE":
        r["status"] = "APPROVED"; r["owner_choice"] = r["lemma_ar"]; st["approved"] += 1
    else: st["kept_" + r["status"]] += 1
    out.append(r)
with open(D / "lus_ar.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
with open(D / "l2_017_deferred.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=dcols); w.writeheader(); w.writerows(DF)
pilot = set(open(ROOT / "02_frames_ar/pilot_frames.txt").read().split())
fr = {r["lu_id"]: r["frame_id"] for r in csv.DictReader(open(D / "lus_template.csv", encoding="utf-8-sig"))}
ref = {e for r in out for e in r["en_lu_ids"].split(";") if e}
nae = {r["en_lu_id"] for r in csv.DictReader(open(D / "l2_017_nae.csv", encoding="utf-8"))}
E = list(csv.DictReader(open(D / "lus_en_status.csv", encoding="utf-8-sig"))); ecols = list(E[0])
for r in E:
    if fr.get(r["en_lu_id"]) in pilot: continue
    i = r["en_lu_id"]; s = "MAPPED" if i in ref else ("NO_ARABIC_EQUIVALENT" if i in nae else "TODO")
    if s != r["status"]: st[f"en_{r['status']}→{s}"] += 1
    r["status"] = s; st["en_new_" + s] += 1
with open(D / "lus_en_status.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=ecols); w.writeheader(); w.writerows(E)
print(f"lus_ar_rows = {len(out)}\ndeferred_total = {len(DF)}")
for k in sorted(st): print(f"{k} = {st[k]}")
for p in ("lus_ar.csv", "lus_en_status.csv", "l2_017_deferred.csv"): print(f"sha256 03_lus_ar/{p} =", sha(D / p))
