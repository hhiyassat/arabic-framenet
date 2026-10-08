#!/usr/bin/env python3
"""OWNER_DECISIONS L2_022..L2_025 — resolve the 106 deferred rows with pos «صفة»/«حال».
Closed sort by wazn (L2_025), أَفْعَلُ by closed id list (L2_022 اسم تفضيل / L2_023 لون-عيب), فَاعِل→اسم فاعل (L2_024).
Rows not covered by a ratified rule stay deferred (reason replaced, OWNER_ALERT). Resolved rows return to lus_ar.csv as CANDIDATE
(L2_019 approval is applied after 07/11 by --approve). LU_KEY collision → en_lu_ids merged into the existing row (L2_001)."""
import csv, hashlib, pathlib, re, sys, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]; D = ROOT / "03_lus_ar"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if "--approve" in sys.argv:
    A = list(csv.DictReader(open(D / "lus_ar.csv", encoding="utf-8-sig"))); cols = list(A[0]); st = collections.Counter()
    for r in A:
        if r["status"] == "CANDIDATE" and "L2_025" in r["note"]: r["status"] = "APPROVED"; r["owner_choice"] = r["lemma_ar"]; st["approved"] += 1
        elif "L2_025" in r["note"]: st["kept_" + r["status"]] += 1
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
if sha(D / "l2_017_deferred.csv") != "1809b384da5c5e6622c261e1ea0bc2e10eb62c8ea928249a2a5075516b939512": sys.exit("STOP deferred sha")
if sha(D / "lus_ar.csv") != "43cec6ebf95db9a74c0d2291891291ed76646c69edc68231180a6bf8c3e32dc3": sys.exit("STOP lus_ar sha")
BYWAZN = {**{w: "صفة مشبهة" for w in ("فَعِيلٌ", "فَعُولٌ", "فَعِلٌ", "فُعْلٌ", "فَعَالٍ", "فِعْلاءٌ")},
          **{w: "اسم فاعل" for w in ("فَاعِلٌ", "مُتَفَعِّلٌ", "مُنْفَعِلٌ", "مُتَفَاعِلٌ", "مُسْتَفْعِلٌ", "مُفْعِلٌ", "مُفَعِّلٌ")},
          **{w: "اسم مفعول" for w in ("مَفْعُولٌ", "مُفَعَّلٌ")}}
AFAL = {"AR04639": "اسم تفضيل", "AR04651": "اسم تفضيل", "AR08301": "اسم تفضيل", "AR05047": "صفة مشبهة"}   # أَسْبَق، أَحْدَث، أَكْثَر ؛ أَشْقَر
DF = list(csv.DictReader(open(D / "l2_017_deferred.csv", encoding="utf-8"))); dcols = list(DF[0])
A = list(csv.DictReader(open(D / "lus_ar.csv", encoding="utf-8-sig"))); cols = list(A[0])
key = {(r["lemma_ar"], r["pos_ar"], r["frame_id"]): r for r in A}
st = collections.Counter(); keep = []
for r in DF:
    if "pos_not_closed" not in r["defer_reason"]: keep.append(r); continue
    w = r["wazn"] or r["wazn_note"]; new = None; rule = ""
    if r["ar_lu_id"] in AFAL: new = AFAL[r["ar_lu_id"]]; rule = "L2_022" if new == "اسم تفضيل" else "L2_023"
    elif w == "أَفْعَلُ": r["defer_reason"] = "afal_wazn_wrong_for_lemma (OWNER_ALERT)"; st["still_deferred_afal_wrong"] += 1; keep.append(r); continue
    elif w in BYWAZN: new = BYWAZN[w]; rule = "L2_024" if w == "فَاعِلٌ" else "L2_025"
    elif re.search(r"(ِيّ|يّ|ي)ٌ?$", r["lemma_ar"]): new = "اسم منسوب"; rule = "L2_025"
    if r["pos_ar"] == "حال" and r["lemma_ar"].endswith(("ًا", "اً")): r["lemma_ar"] = r["lemma_ar"][:-2]; st["hal_lemma_fixed"] += 1
    if new is None: r["defer_reason"] = "no_rule (OWNER_ALERT)"; st["still_deferred_no_rule"] += 1; keep.append(r); continue
    if r["defer_reason"] != "pos_not_closed": r["defer_reason"] = r["defer_reason"].replace("pos_not_closed", "").strip(";"); r["pos_ar"] = new; keep.append(r); st["still_deferred_other_reason"] += 1; continue
    st[f"{r['pos_ar']}→{new}"] += 1; r["pos_ar"] = new
    note = (r["note"] + " | " if r["note"] else "") + f"POS ← {rule} | L2_025"
    k = (r["lemma_ar"], new, r["frame_id"])
    if k in key:
        ex = key[k]; ids = [e for e in ex["en_lu_ids"].split(";") if e]
        ex["en_lu_ids"] = ";".join(ids + [e for e in r["en_lu_ids"].split(";") if e and e not in ids]); st["merged_into_existing_LU_KEY"] += 1; continue
    o = {c: r.get(c, "") for c in cols}; o["status"] = "CANDIDATE"; o["owner_choice"] = ""; o["note"] = note
    A.append(o); key[k] = o; st["returned_to_lus_ar"] += 1
A.sort(key=lambda r: r["ar_lu_id"])
with open(D / "lus_ar.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(A)
with open(D / "l2_017_deferred.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=dcols); w.writeheader(); w.writerows(keep)
for k in sorted(st): print(f"{k} = {st[k]}")
print(f"lus_ar_rows = {len(A)}\ndeferred_rows = {len(keep)}")
for p in ("lus_ar.csv", "l2_017_deferred.csv"): print(f"sha256 03_lus_ar/{p} =", sha(D / p))
