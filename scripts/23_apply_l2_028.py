#!/usr/bin/env python3
"""OWNER_DECISION_L2_028 — apply the owner-approved sonnet re-draft of the 34 Latin-root LUs (l2_027_redraft.csv).
Step 1 (default): rows leave l2_017_deferred.csv and enter lus_ar.csv as CANDIDATE with the re-drafted lemma/pos/root/wazn/definition.
  root stored with K normalization (أإآؤئء→ء ، ى→ي ، ک→ك) ; wazn not in the ratified inventory → wazn_note (L2_017 F3).
Step 2 (--approve, after 07/11): CANDIDATE rows tagged L2_028 → APPROVED (owner_choice = lemma); EVIDENCE_GAP (D2) kept; en TODO→MAPPED when referenced."""
import csv, hashlib, os, pathlib, re, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import wazn_rules as W
ROOT = pathlib.Path(__file__).resolve().parents[1]; D = ROOT / "03_lus_ar"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
st = collections.Counter()
if "--approve" in sys.argv:
    A = list(csv.DictReader(open(D / "lus_ar.csv", encoding="utf-8-sig"))); cols = list(A[0])
    for r in A:
        if "L2_028" in r["note"]:
            if r["status"] == "CANDIDATE": r["status"] = "APPROVED"; r["owner_choice"] = r["lemma_ar"]; st["approved"] += 1
            else: st["kept_" + r["status"]] += 1
    with open(D / "lus_ar.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(A)
    ref = {e for r in A for e in r["en_lu_ids"].split(";") if e}
    E = list(csv.DictReader(open(D / "lus_en_status.csv", encoding="utf-8-sig"))); ec = list(E[0])
    for r in E:
        if r["status"] == "TODO" and r["en_lu_id"] in ref: r["status"] = "MAPPED"; st["en_TODO→MAPPED"] += 1
    with open(D / "lus_en_status.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ec); w.writeheader(); w.writerows(E)
    for k in sorted(st): print(f"{k} = {st[k]}")
    for p in ("lus_ar.csv", "lus_en_status.csv"): print(f"sha256 03_lus_ar/{p} =", sha(D / p))
    sys.exit(0)
if sha(D / "l2_027_redraft.csv") != "75eb58f58b0929023a30ded03533b128b74ee44227bfa722f4763e16a230ae35": sys.exit("STOP redraft sha")
if sha(D / "l2_017_deferred.csv") != "c5608185d2f375bc25c4be81a07bf954a4eb48a098461809f0a60043ce44880c": sys.exit("STOP deferred sha")
SIB = os.environ["AWZAN_SIB"]; VB = os.environ["AWZAN_VERBS"]
VW = {r["wazn"].strip() for r in csv.DictReader(open(VB, encoding="utf-8-sig"))}
inv = W.noun_inventory_v3({r["pattern_vocalized"].strip() for r in csv.DictReader(open(SIB, encoding="utf-8-sig")) if r["status"] == "EXISTS"}, VW, D / "wazn_owner_l2_015.csv")
_, OV = W.owner_lines(D / "wazn_owner_l2_015.csv"); VK = {W.key(v): v for v in VW | OV}
K = lambda s: re.sub(r"[أإآؤئء]", "ء", s).replace("ى", "ي").replace("ک", "ك")
RD = {r["ar_lu_id"]: r for r in csv.DictReader(open(D / "l2_027_redraft.csv", encoding="utf-8"))}
DF = list(csv.DictReader(open(D / "l2_017_deferred.csv", encoding="utf-8"))); dcols = list(DF[0])
A = list(csv.DictReader(open(D / "lus_ar.csv", encoding="utf-8-sig"))); cols = list(A[0])
keys = {(x["lemma_ar"], x["pos_ar"], x["frame_id"]) for x in A}; keep = []
for r in DF:
    n = RD.get(r["ar_lu_id"])
    if not n: keep.append(r); continue
    o = {c: r.get(c, "") for c in cols}
    o.update(lemma_ar=n["lemma_ar"], pos_ar=n["pos_ar"], root=K(n["root"]), definition_ar=n["definition_ar"], status="CANDIDATE", owner_choice="",
             evidence_primary="", evidence_frame_level="", metaphor_flag="", wazn="", wazn_note="")
    k = W.key(n["wazn"])
    if n["pos_ar"] == "فعل" and k in VK: o["wazn"] = VK[k]
    elif n["pos_ar"] != "فعل" and k in inv: o["wazn"] = inv[k][0]
    else: o["wazn_note"] = n["wazn"]; st["wazn_to_note"] += 1
    o["note"] = re.sub(r" \| FLAGS: [^|]*", "", o["note"]) + f" | REDRAFT sonnet L2_027 ({n['changed']}) | L2_028"
    if (o["lemma_ar"], o["pos_ar"], o["frame_id"]) in keys: sys.exit(f"STOP dup key {r['ar_lu_id']}")
    keys.add((o["lemma_ar"], o["pos_ar"], o["frame_id"])); A.append(o); st["entered_lus_ar"] += 1
if st["entered_lus_ar"] != 34: sys.exit("STOP expected 34")
A.sort(key=lambda r: r["ar_lu_id"])
with open(D / "lus_ar.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(A)
with open(D / "l2_017_deferred.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=dcols); w.writeheader(); w.writerows(keep)
for k in sorted(st): print(f"{k} = {st[k]}")
print(f"lus_ar_rows = {len(A)}\ndeferred_rows = {len(keep)}")
for p in ("lus_ar.csv", "l2_017_deferred.csv"): print(f"sha256 03_lus_ar/{p} =", sha(D / p))
