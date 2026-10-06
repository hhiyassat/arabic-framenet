#!/usr/bin/env python3
"""OWNER_DECISION_L2_005/006 — fill wazn for LUs whose wazn_note is in the noun inventory (Sibawayh EXISTS ∪ L2_006 verb derivatives ∪ L2_005 feminines).
Moves the pattern from wazn_note to wazn (canonical form, e.g. فَعْلَةٌ) and appends 'WAZN_L2_005 ← <base line>' to note.
Rows whose feminine base is not in the inventory are left unchanged (counted). Never touches owner_choice/status."""
import csv, hashlib, os, pathlib, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import wazn_rules as W
ROOT = pathlib.Path(__file__).resolve().parents[1]
SIB = os.environ.get("AWZAN_SIB", "/Users/husseinhiyassat/hokom-local-validation/taaqol-executor-wt/data/awzan-sibawayh-308.csv")
if hashlib.sha256(open(SIB, "rb").read()).hexdigest() != "a1c1f7f94378eb6e4ad5a994ee180c38c2f5da5058fc9ac1a670f25a3555b1a0": print("STOP sib sha"); sys.exit(2)
VERBS = os.environ.get("AWZAN_VERBS", "/Users/husseinhiyassat/arabic-net/Arabic-Mother-language-wazn-net/data/awzaan_af3aal_all.csv")
if hashlib.sha256(open(VERBS, "rb").read()).hexdigest() != "ba0aee787f997d20900f2c3bd790ce5d658e138b2464cd6476e9dd4408594e9b": print("STOP verbs sha"); sys.exit(2)
inv = W.noun_inventory_v3({r["pattern_vocalized"].strip() for r in csv.DictReader(open(SIB, encoding="utf-8-sig")) if r["status"] == "EXISTS"},
                       {r["wazn"].strip() for r in csv.DictReader(open(VERBS, encoding="utf-8-sig"))}, ROOT / "03_lus_ar/wazn_owner_l2_015.csv")
_, OV = W.owner_lines(ROOT / "03_lus_ar/wazn_owner_l2_015.csv"); OVK = {W.key(v): v for v in OV}
p = ROOT / "03_lus_ar/lus_ar.csv"; rows = list(csv.DictReader(open(p, encoding="utf-8-sig"))); cols = list(rows[0])
st = collections.Counter()
for r in rows:
    if r["wazn"] or not r["wazn_note"]: continue
    k = W.key(r["wazn_note"])
    if r["pos_ar"] == "فعل":
        if k in OVK: r["wazn"] = OVK[k]; r["note"] = (r["note"] + " | " if r["note"] else "") + "WAZN ← L2_015 المالك"; r["wazn_note"] = ""; st["filled_verb_L2_015"] += 1
        else: st["verb_note_not_in_inventory"] += 1
        continue
    if k in inv:
        line, prov = inv[k]
        r["wazn"] = line; r["note"] = (r["note"] + " | " if r["note"] else "") + f"WAZN ← {prov}"; r["wazn_note"] = ""; st["filled_" + prov.split(" ")[0]] += 1
    else: st["not_in_inventory"] += 1
with open(p, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(f"noun_inventory = {len(inv)}"); [print(f"{k} = {v}") for k, v in sorted(st.items())]
print("sha256 03_lus_ar/lus_ar.csv =", hashlib.sha256(p.read_bytes()).hexdigest())
