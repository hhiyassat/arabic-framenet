#!/usr/bin/env python3
"""L2-G0 — offline checker for Arabic LUs (Layer 2). No API. Measures; never edits inputs.
Usage:
  python3 scripts/06_check_lus.py              # check 03_lus_ar/lus_ar.csv + lus_en_status.csv
  python3 scripts/06_check_lus.py --selftest   # poison tests on a temp copy; exits 1 on any miss
Env:
  FRAMES_FILE  (default 02_frames_ar/pilot_frames.txt)  — scope: no frame outside it
  R2_ROOTS / AWZAN_VERBS / AWZAN_SIB — paths to frozen external sources (verified by sha256, never copied)
Rules enforced (each traced to an owner decision in 01_glossary/APPROVAL_LOG.txt):
  L2_001 LU_KEY=C (lemma_ar,pos_ar,frame_id) unique · en<->ar many-to-many · Arabic-only LUs allowed
         verbs wazn ∈ awzaan_af3aal_all.csv ; noun/adj wazn ∈ awzan-sibawayh-308.csv
  L2_002 pos_ar ∈ 03_lus_ar/pos_ar_closed.txt (10)
  L2_005 noun wazn may also be a feminine (+ة) of a feminizable inventory pattern (scripts/wazn_rules.py)
  L2_007 pos_ar +6 (اسم منسوب، اسم مكان، صيغة مبالغة، اسم مصدر، اسم آلة، اسم مرة); nisba wazn = pattern + ـِيّ ;
         L2_009 reject صيغة مبالغة ≠ فَعَّال(ة) ; alert when اسم مرة ≠ فَعْلَة
  L2_006 noun inventory also holds the regular derivatives of the ratified verb awzan (wazn_rules.DERIVED)
  L2_022 pos_ar +اسم تفضيل (17) — wazn must be أَفْعَلُ (reject tafdil_not_afal)
  L2_004 root with المجموعة=مكمِّل → status must be EVIDENCE_GAP ; Sibawayh status=EXISTS only
  HANDOFF: owner_choice filled by owner only (CANDIDATE ⇒ empty; APPROVED ⇒ non-empty) · scope = FRAMES_FILE
Reported but NOT enforced (no owner rule yet → OWNER_ALERT): root_not_in_R2, en_lu_frame_mismatch,
  wazn of ظرف/حرف/تركيب/مبني, metaphor_flag values, NUM pos_ar.
"""
import csv, hashlib, json, os, pathlib, re, shutil, sys, tempfile, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import wazn_rules as W

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRAMES_FILE = os.environ.get("FRAMES_FILE", "02_frames_ar/pilot_frames.txt")
SRC = {  # name: (env, default path, sha256)
    "R2_ROOTS":    ("R2_ROOTS",    "/Users/husseinhiyassat/hokom-local-validation/taaqol-executor-wt/data/roots-4662-meaning.csv",
                    "1a711ffe9cc3286d87276b04a836b26756b67f3657f8a0904a0c7b4ac4d020da"),
    "AWZAN_VERBS": ("AWZAN_VERBS", "/Users/husseinhiyassat/arabic-net/Arabic-Mother-language-wazn-net/data/awzaan_af3aal_all.csv",
                    "ba0aee787f997d20900f2c3bd790ce5d658e138b2464cd6476e9dd4408594e9b"),
    "AWZAN_SIB":   ("AWZAN_SIB",   "/Users/husseinhiyassat/hokom-local-validation/taaqol-executor-wt/data/awzan-sibawayh-308.csv",
                    "a1c1f7f94378eb6e4ad5a994ee180c38c2f5da5058fc9ac1a670f25a3555b1a0"),
}
INTERNAL = {
    "release/layer1_v1/MANIFEST.json": "817e5143e6ebb9ae6e57bb222ef890b55d032196b5f2cf8928556574fa9d7f2e",
    "03_lus_ar/lus_template.csv":      "5616d5fadcd89b4f2e46f24a17f20e6499915782ec9a0e6bb2ae047c4020e980",
    "03_lus_ar/v21_roots_index.csv":   "6b8beda92318b93eaa160e2e152228cd7cb15f4c858c78cb9f2421bf494dd174",   # L2_010
    "03_lus_ar/root_alert_waived.txt": "d51dc911a7e574a2801a9082f900267779c98ac1199c8d00b81e2db22ec577d7",   # L2_012
    "03_lus_ar/wazn_owner_l2_015.csv": "cbcfb88029c6588fb7919a0de7472df461e16571d61f84cdd864bf97de89f88a",   # L2_015
    "03_lus_ar/pos_ar_closed.txt":     "c82efc4cd9625799e73406e90ccb54df24d2ff3fee43c657d90e6319a0e9e8b7",   # L2_022 +اسم تفضيل (17)
}
AR_STATUS = {"CANDIDATE", "APPROVED", "EVIDENCE_GAP"}
EN_STATUS = {"TODO", "MAPPED", "NO_ARABIC_EQUIVALENT"}
NOUNLIKE = {"مصدر", "اسم فاعل", "اسم مفعول", "صفة مشبهة", "اسم جامد",
            "اسم منسوب", "اسم مكان", "صيغة مبالغة", "اسم مصدر", "اسم آلة", "اسم مرة", "اسم تفضيل"}   # L2_007 ; L2_022
LATIN = re.compile(r"[A-Za-z]{3,}")
QUOTED = re.compile(r"\([^()]*\)|\"[^\"]*\"|'[^']*'|«[^»]*»|“[^”]*”")
AR_COLS = ["ar_lu_id", "lemma_ar", "pos_ar", "frame_id", "en_lu_ids", "definition_ar", "root", "wazn",
           "evidence_primary", "evidence_frame_level", "metaphor_flag", "owner_choice", "status"]
EN_COLS = ["en_lu_id", "status"]

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def rows(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def norm_root(r):  # join key K (roots project): أإآؤئء→ء ، ى→ي ، ک→ك (L2_020) ; collision-free on roots-4662 (measured 0)
    return re.sub(r"[أإآؤئء]", "ء", re.sub(r"[\s\-‌‍ـ]", "", r or "")).replace("ى", "ي").replace("ک", "ك")

def load_refs(base):
    stop = []
    paths = {}
    for k, (env, default, h) in SRC.items():
        p = os.environ.get(env, default); paths[k] = p
        if not pathlib.Path(p).exists(): stop.append(f"{k}=MISSING")
        elif sha(p) != h: stop.append(f"{k}=SHA_MISMATCH")
    for rel, h in INTERNAL.items():
        q = base / rel
        if not q.exists(): stop.append(f"{rel}=MISSING")
        elif sha(q) != h: stop.append(f"{rel}=SHA_MISMATCH")
    if stop: return None, stop
    R = {}
    R["pos"] = {l.strip() for l in open(base / "03_lus_ar/pos_ar_closed.txt", encoding="utf-8") if l.strip()}
    R["frames"] = {json.loads(l)["frame_id"] for l in open(base / "00_source/frames.jsonl", encoding="utf-8")}
    R["scope"] = {int(x) for x in open(base / FRAMES_FILE).read().split()}
    R["tpl"] = {r["lu_id"]: r for r in rows(base / "03_lus_ar/lus_template.csv")}
    R["r2"] = {norm_root(r["الجذر"]): r["المجموعة"] for r in rows(paths["R2_ROOTS"])}
    R["waived"] = {l.strip() for l in open(base / "03_lus_ar/root_alert_waived.txt", encoding="utf-8") if l.strip()}   # L2_012
    R["ovk"] = {W.key(v) for v in W.owner_lines(base / "03_lus_ar/wazn_owner_l2_015.csv")[1]}   # L2_015 verb patterns
    R["v21"] = {r["key"] for r in rows(base / "03_lus_ar/v21_roots_index.csv")}   # L2_010
    R["vw"] = {r["wazn"].strip() for r in rows(paths["AWZAN_VERBS"]) if r["wazn"].strip()}
    R["nw"] = {r["pattern_vocalized"].strip() for r in rows(paths["AWZAN_SIB"]) if r["status"] == "EXISTS"}
    R["ninv"] = W.noun_inventory_v3(R["nw"], R["vw"], base / "03_lus_ar/wazn_owner_l2_015.csv")   # L2_005 feminine + L2_006 verb derivatives (scripts/wazn_rules.py)
    return R, []

def check(base, R):
    st = collections.Counter(); warn = collections.Counter(); rej = []
    arp, enp = base / "03_lus_ar/lus_ar.csv", base / "03_lus_ar/lus_en_status.csv"
    ar = rows(arp) if arp.exists() else []
    en = rows(enp) if enp.exists() else []
    if ar and set(AR_COLS) - set(ar[0]): st["schema_missing_cols_ar"] = len(set(AR_COLS) - set(ar[0]))
    if en and set(EN_COLS) - set(en[0]): st["schema_missing_cols_en"] = len(set(EN_COLS) - set(en[0]))
    seen = collections.Counter((r.get("lemma_ar","").strip(), r.get("pos_ar","").strip(), r.get("frame_id","").strip()) for r in ar)
    referenced = set()
    for r in ar:
        P = []
        g = lambda k: (r.get(k) or "").strip()
        lemma, pos, fid, s, oc = g("lemma_ar"), g("pos_ar"), g("frame_id"), g("status"), g("owner_choice")
        if not (lemma and pos and fid and s): P.append("missing_required")
        if seen[(lemma, pos, fid)] > 1: P.append("dup_key")
        if pos and pos not in R["pos"]: P.append("pos_not_closed")
        fi = int(fid) if fid.isdigit() else None
        if fi is None or fi not in R["frames"]: P.append("frame_not_in_layer1")
        elif fi not in R["scope"]: P.append("out_of_scope")
        if s and s not in AR_STATUS: P.append("status_not_closed")
        if s == "CANDIDATE" and oc: P.append("owner_choice_by_agent")
        if s == "APPROVED" and not oc: P.append("approved_without_owner")
        for e in [x.strip() for x in g("en_lu_ids").split(";") if x.strip()]:
            referenced.add(e)
            if e not in R["tpl"]: P.append("en_lu_not_in_template")
            elif fi is not None and R["tpl"][e]["frame_id"] != str(fi): warn["en_lu_frame_mismatch"] += 1
        root = norm_root(g("root"))
        if root:
            grp = R["r2"].get(root)
            if grp is None:
                if root in R["v21"]: warn["root_in_v21_only"] += 1
                elif root in R["waived"]: warn["root_alert_waived_L2_012"] += 1
                else: warn["root_not_in_R2_nor_v21"] += 1
            elif grp == "مكمِّل" and s != "EVIDENCE_GAP": P.append("mukammil_not_evidence_gap")
        w = g("wazn")
        if w:
            if pos == "فعل" and w not in R["vw"] and W.key(w) not in R["ovk"]: P.append("wazn_not_in_inventory")
            elif pos in NOUNLIKE and W.key(w) not in R["ninv"]: P.append("wazn_not_in_inventory")
            if pos == "صيغة مبالغة" and W.key(w) not in {W.key(x) for x in W.MUBALAGHA_WAZN}: P.append("mubalagha_not_faaal")   # L2_009
            if pos == "اسم مرة" and W.key(w) not in {W.key(x) for x in W.MARRA_WAZN}: warn["marra_wazn_not_falah"] += 1
            elif pos not in NOUNLIKE | {"فعل"}: warn["wazn_unchecked_pos"] += 1
        if pos == "اسم تفضيل" and W.key(w) != W.key("أَفْعَلُ"): P.append("tafdil_not_afal")   # L2_022: اسم تفضيل وزنه أَفْعَلُ
        d = g("definition_ar")
        if s in ("CANDIDATE", "APPROVED") and not d: P.append("empty_definition")
        if [x for x in LATIN.findall(QUOTED.sub(" ", d))]: P.append("latin_leak")
        if P:
            st["rejected_ar"] += 1
            for p in set(P): st[p] += 1
            rej.append({"file": "lus_ar", "id": g("ar_lu_id") or lemma, "problems": ";".join(sorted(set(P)))})
        else: st["ok_ar"] += 1
        st["status_" + (s or "EMPTY")] += 1
    en_seen = collections.Counter(r.get("en_lu_id", "").strip() for r in en)
    for r in en:
        P = []; i = (r.get("en_lu_id") or "").strip(); s = (r.get("status") or "").strip()
        if i not in R["tpl"]: P.append("en_id_not_in_template")
        elif int(R["tpl"][i]["frame_id"]) not in R["scope"]: P.append("en_out_of_scope")
        if en_seen[i] > 1: P.append("en_dup")
        if s not in EN_STATUS: P.append("en_status_not_closed")
        if s == "MAPPED" and i not in referenced: P.append("mapped_without_ar_lu")
        if s != "MAPPED" and i in referenced: P.append("referenced_not_mapped")
        if P:
            st["rejected_en"] += 1
            for p in set(P): st[p] += 1
            rej.append({"file": "lus_en_status", "id": i, "problems": ";".join(sorted(set(P)))})
        else: st["ok_en"] += 1
        st["en_" + (s or "EMPTY")] += 1
    scope_en = {k for k, v in R["tpl"].items() if int(v["frame_id"]) in R["scope"]}
    st["en_scope_total"] = len(scope_en)
    st["en_scope_uncovered"] = len(scope_en - set(en_seen))
    st["ar_rows"] = len(ar); st["en_rows"] = len(en)
    st["ar_file"] = "PRESENT" if arp.exists() else "NOT_CREATED"
    st["en_file"] = "PRESENT" if enp.exists() else "NOT_CREATED"
    return st, warn, rej

def report(base, st, warn, rej):
    out = base / "03_lus_ar/lus_rejected.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file", "id", "problems"]); w.writeheader(); w.writerows(rej)
    print(f"FRAMES_FILE = {FRAMES_FILE}  scope_frames = {len(load_scope(base))}")
    for k in sorted(st): print(f"{k} = {st[k]}")
    print(f"rejected = {st['rejected_ar'] + st['rejected_en']}")
    for k in sorted(warn): print(f"OWNER_ALERT_{k} = {warn[k]}")
    for p in ("03_lus_ar/lus_ar.csv", "03_lus_ar/lus_en_status.csv", "03_lus_ar/lus_rejected.csv"):
        q = base / p; print(f"sha256 {p} = {sha(q) if q.exists() else 'NOT_CREATED'}")

def load_scope(base): return {int(x) for x in open(base / FRAMES_FILE).read().split()}

def selftest(R):
    """Poison rows: each must trigger exactly its named problem; one clean row must pass."""
    tpl_in = next(k for k, v in R["tpl"].items() if int(v["frame_id"]) in R["scope"])
    fid = R["tpl"][tpl_in]["frame_id"]
    out_fid = str(next(f for f in sorted(R["frames"]) if f not in R["scope"]))
    muk = next(k for k, v in R["r2"].items() if v == "مكمِّل")
    ver = next(k for k, v in R["r2"].items() if v != "مكمِّل")
    vw = sorted(R["vw"])[0]; nw = sorted(R["nw"])[0]
    base_row = dict(ar_lu_id="", lemma_ar="", pos_ar="فعل", frame_id=fid, en_lu_ids=tpl_in, definition_ar="تعريف عربي",
                    root=ver, wazn=vw, evidence_primary="", evidence_frame_level="", metaphor_flag="", owner_choice="", status="CANDIDATE")
    cases = [  # (id, overrides, expected problem or None)
        ("ok",   {}, None),
        ("p1",   {"pos_ar": "اسم"}, "pos_not_closed"),
        ("p2",   {"frame_id": out_fid, "en_lu_ids": ""}, "out_of_scope"),
        ("p3",   {"frame_id": "999999", "en_lu_ids": ""}, "frame_not_in_layer1"),
        ("p4",   {"en_lu_ids": "0"}, "en_lu_not_in_template"),
        ("p5",   {"owner_choice": "x"}, "owner_choice_by_agent"),
        ("p6",   {"status": "APPROVED"}, "approved_without_owner"),
        ("p7",   {"root": muk}, "mukammil_not_evidence_gap"),
        ("p8",   {"wazn": "فَعْلَلَانَ"}, "wazn_not_in_inventory"),
        ("p9",   {"pos_ar": "مصدر", "wazn": vw}, "wazn_not_in_inventory"),
        ("p10",  {"definition_ar": ""}, "empty_definition"),
        ("p11",  {"definition_ar": "يترك leave the car"}, "latin_leak"),
        ("p12",  {"status": "DONE"}, "status_not_closed"),
        ("p13",  {"lemma_ar": ""}, "missing_required"),
        ("ok2",  {"root": muk, "status": "EVIDENCE_GAP"}, None),
        ("ok3",  {"pos_ar": "مصدر", "wazn": nw, "en_lu_ids": ""}, None),
        ("ok4",  {"definition_ar": "يترك (leave)"}, None),
        ("ok5",  {"pos_ar": "مصدر", "wazn": "فَعْلَةٌ", "en_lu_ids": ""}, None),
        ("p14",  {"pos_ar": "مصدر", "wazn": "فَاعُولَاءَةٌ", "en_lu_ids": ""}, "wazn_not_in_inventory"),   # فَعَالَة became valid by L2_015
        ("p15",  {"pos_ar": "مصدر", "wazn": "تَفْعِلَةَةٌ", "en_lu_ids": ""}, "wazn_not_in_inventory"),
        ("ok6",  {"pos_ar": "اسم فاعل", "wazn": "مُفْتَعِل", "en_lu_ids": ""}, None),
        ("ok8",  {"pos_ar": "اسم منسوب", "wazn": "فَعْلِيّ", "en_lu_ids": ""}, None),
        ("p17",  {"pos_ar": "اسم منسوب", "wazn": "فَعْلِيَيّ", "en_lu_ids": ""}, "wazn_not_in_inventory"),
        ("p18",  {"pos_ar": "صيغة مبالغة", "wazn": "فَعُولٌ", "en_lu_ids": ""}, "mubalagha_not_faaal"),
        ("ok9",  {"pos_ar": "صيغة مبالغة", "wazn": "فَعَّالٌ", "en_lu_ids": ""}, None),
        ("ok7",  {"pos_ar": "اسم فاعل", "wazn": "مُتَفَعِّلَةٌ", "en_lu_ids": ""}, None),
        ("p16",  {"pos_ar": "اسم فاعل", "wazn": "مُفَعْلِيلٌ", "en_lu_ids": ""}, "wazn_not_in_inventory"),
        ("p19",  {"pos_ar": "اسم تفضيل", "wazn": "فَعِيلٌ", "en_lu_ids": ""}, "tafdil_not_afal"),   # L2_022
        ("ok10", {"pos_ar": "اسم تفضيل", "wazn": "أَفْعَلُ", "en_lu_ids": ""}, None),
    ]
    tmp = pathlib.Path(tempfile.mkdtemp()); (tmp / "03_lus_ar").mkdir()
    ar = []
    for cid, ov, _ in cases:
        r = dict(base_row); r.update(ov); r["ar_lu_id"] = cid
        if cid != "p13": r["lemma_ar"] = r["lemma_ar"] or f"لفظ_{cid}"
        ar.append(r)
    ar.append(dict(base_row, ar_lu_id="d1", lemma_ar="مكرر")); ar.append(dict(base_row, ar_lu_id="d2", lemma_ar="مكرر"))
    with open(tmp / "03_lus_ar/lus_ar.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=AR_COLS); w.writeheader(); w.writerows(ar)
    en = [{"en_lu_id": tpl_in, "status": "MAPPED"}, {"en_lu_id": tpl_in, "status": "MAPPED"},
          {"en_lu_id": "0", "status": "TODO"}, {"en_lu_id": tpl_in, "status": "BAD"}]
    with open(tmp / "03_lus_ar/lus_en_status.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EN_COLS); w.writeheader(); w.writerows(en)
    st, warn, rej = check(tmp, R)
    got = {x["id"]: set(x["problems"].split(";")) for x in rej if x["file"] == "lus_ar"}
    miss = 0
    for cid, _, exp in cases:
        ok = (cid not in got) if exp is None else (got.get(cid) == {exp})
        print(f"SELFTEST {cid:5s} expect={exp or 'PASS':28s} got={';'.join(sorted(got.get(cid, []))) or 'PASS':40s} {'OK' if ok else 'MISS'}")
        miss += not ok
    dup_ok = got.get("d1") == {"dup_key"} and got.get("d2") == {"dup_key"}
    print(f"SELFTEST dup   expect=dup_key x2  {'OK' if dup_ok else 'MISS'}"); miss += not dup_ok
    en_ok = st["en_dup"] == 3 and st["en_id_not_in_template"] == 1 and st["en_status_not_closed"] == 1 and st["referenced_not_mapped"] == 2
    print(f"SELFTEST en    dup=3 not_in_tpl=1 bad_status=1 ref_not_mapped=2 (BAD row + id 0 referenced by p4)  got={st['en_dup']},{st['en_id_not_in_template']},{st['en_status_not_closed']},{st['referenced_not_mapped']} {'OK' if en_ok else 'MISS'}")
    miss += not en_ok
    shutil.rmtree(tmp)
    poison = len([c for c in cases if c[2]]) + 2 + 4
    print(f"SELFTEST_POISON = {poison}  SELFTEST_MISS = {miss}  SELFTEST = {'PASS' if miss == 0 else 'FAIL'}")
    return miss

if __name__ == "__main__":
    R, stop = load_refs(ROOT)
    if stop:
        print("STOP / OWNER_ALERT / NO_INFERENCE"); [print(f"  {s}") for s in stop]; sys.exit(2)
    if "--selftest" in sys.argv: sys.exit(1 if selftest(R) else 0)
    st, warn, rej = check(ROOT, R); report(ROOT, st, warn, rej)
