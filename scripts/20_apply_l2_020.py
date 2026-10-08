#!/usr/bin/env python3
"""OWNER_DECISION_L2_020 (ک→ك). Rewrites ک→ك in the root column of l2_017_deferred.csv; rows whose ONLY defer reason was
root_not_arabic_script and whose root is now Arabic return to lus_ar.csv as CANDIDATE (L2_019 approval is applied by 21 after 07/11).
Lemma and wazn are NOT changed (owner did not rule on them)."""
import csv, hashlib, pathlib, re, sys, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]; D = ROOT / "03_lus_ar"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if sha(D / "l2_017_deferred.csv") != "deebeca6970abba2b1d3d354786926dbd7b8c0b292c33a4a1dd6fc2c2d871f08": sys.exit("STOP deferred sha")
DF = list(csv.DictReader(open(D / "l2_017_deferred.csv", encoding="utf-8"))); dcols = list(DF[0])
A = list(csv.DictReader(open(D / "lus_ar.csv", encoding="utf-8-sig"))); cols = list(A[0])
st = collections.Counter(); keep = []
for r in DF:
    if "ک" in r["root"]:
        r["root"] = r["root"].replace("ک", "ك"); st["root_kaf_fixed"] += 1
        if r["defer_reason"] == "root_not_arabic_script" and not re.search(r"[^ء-ي]", r["root"]):
            o = {c: r.get(c, "") for c in cols}; o["status"] = "CANDIDATE"; o["owner_choice"] = ""
            o["note"] = (o["note"] + " | " if o["note"] else "") + "ROOT ک→ك L2_020"
            A.append(o); st["returned_to_lus_ar"] += 1; continue
    keep.append(r)
A.sort(key=lambda r: r["ar_lu_id"])
with open(D / "lus_ar.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(A)
with open(D / "l2_017_deferred.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=dcols); w.writeheader(); w.writerows(keep)
for k in sorted(st): print(f"{k} = {st[k]}")
print(f"lus_ar_rows = {len(A)}\ndeferred_rows = {len(keep)}")
for p in ("lus_ar.csv", "l2_017_deferred.csv"): print(f"sha256 03_lus_ar/{p} =", sha(D / p))
