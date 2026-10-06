#!/usr/bin/env python3
"""OWNER_DECISION_L2_007 — move LUs to the six new pos_ar values.
Moved only on an explicit signal (closed list, no inference):
  (1) marker in note: POS_DEFER:NISBA|MAKAN|MUBALAGHA|ISM_MASDAR|ALA , OWNER_ALERT:ISM_MARRA
  (2) a note segment (split on | ؛ — ;) that BEGINS with the category name itself
      (اسم منسوب | اسم مكان/اسم المكان | صيغة مبالغة | اسم مصدر/اسم المصدر | اسم آلة/اسم الآلة | اسم مرة/اسم المرة).
      Segments like «صيغته صيغة اسم الآلة» or «(مصدر ميمي/اسم مكان)» do NOT count.
A move that would duplicate an existing (lemma_ar,pos_ar,frame_id) key is not made (counted). Marker text becomes POS_L2_007:X."""
import csv, hashlib, pathlib, re, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]
MARK = {"NISBA": "اسم منسوب", "MAKAN": "اسم مكان", "MUBALAGHA": "صيغة مبالغة", "ISM_MASDAR": "اسم مصدر", "ALA": "اسم آلة", "ISM_MARRA": "اسم مرة"}
NAMES = [("اسم منسوب", "NISBA"), ("اسم المكان", "MAKAN"), ("اسم مكان", "MAKAN"), ("صيغة مبالغة", "MUBALAGHA"), ("صيغة المبالغة", "MUBALAGHA"),
         ("اسم المصدر", "ISM_MASDAR"), ("اسم مصدر", "ISM_MASDAR"), ("اسم الآلة", "ALA"), ("اسم آلة", "ALA"), ("اسم المرة", "ISM_MARRA"), ("اسم مرة", "ISM_MARRA")]
p = ROOT / "03_lus_ar/lus_ar.csv"; rows = list(csv.DictReader(open(p, encoding="utf-8-sig"))); cols = list(rows[0])
keys = collections.Counter((r["lemma_ar"], r["pos_ar"], r["frame_id"]) for r in rows)
st = collections.Counter()
for r in rows:
    m = re.search(r"(?:POS_DEFER|OWNER_ALERT):(NISBA|MAKAN|MUBALAGHA|ISM_MASDAR|ALA|ISM_MARRA)", r["note"])
    cat, how = (m.group(1), "marker") if m else (None, None)
    if not cat:
        for seg in re.split(r"\s*[|؛;—]\s*", r["note"]):
            for n, c in NAMES:
                if seg.strip().startswith(n): cat, how = c, "segment"; break
            if cat: break
    if not cat: continue
    new = MARK[cat]
    if r["pos_ar"] == new: continue
    k = (r["lemma_ar"], new, r["frame_id"])
    if keys[k]: st["blocked_dup_key"] += 1; continue
    keys[(r["lemma_ar"], r["pos_ar"], r["frame_id"])] -= 1; keys[k] += 1
    r["note"] = re.sub(r"(?:POS_DEFER|OWNER_ALERT):" + cat, "POS_L2_007:" + cat, r["note"])
    if how == "segment": r["note"] += f" | POS_L2_007:{cat} (من نص الملاحظة)"
    r["pos_ar"] = new; st[f"moved_{how}_{cat}"] += 1
with open(p, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
for k in sorted(st): print(f"{k} = {st[k]}")
print("sha256 03_lus_ar/lus_ar.csv =", hashlib.sha256(p.read_bytes()).hexdigest())
