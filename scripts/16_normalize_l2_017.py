#!/usr/bin/env python3
"""OWNER_DECISION_L2_017 — deterministic central post-processing of the haiku candidates (03_lus_ar/l2_017_cand_raw.csv).
Never invents content. Each fix is a closed mechanical rule; anything unresolved is FLAGGED (flags column), not guessed.
 F1 AL_STRIPPED       leading definite article removed (ال + sukun/sun-letter shadda); skipped for فعل/حرف/مبني/تركيب and roots starting with ل
 F2 ROOT_NORMALIZED   marks/spaces removed; K map أإآؤئء→ء ، ى→ي ; initial ا → ء
    ROOT_ALIF         medial/final ا left in root (weak radical unknown) — flag only
    ROOT_LEN          root length not 3 or 4 (non-empty) — flag only
    ROOT_MISSING      root empty where pos needs one — flag only
 F3 WAZN_NOT_IN_INV   wazn not in the ratified inventory (noun_inventory_v3 / verb awzan ∪ L2_015) → moved to wazn_note
    WAZN_MISSING      empty wazn where pos needs one
    WAZN_LEMMA_MISMATCH  consonant skeleton of wazn∘root ≠ lemma skeleton (strong roots only) — flag only
 F4 POS_NOT_CLOSED    pos_ar outside pos_ar_closed.txt — flag only
    MUBALAGHA_NOT_FAAAL / MARRA_NOT_FALA — flag only
 F5 UNVOCALIZED       lemma has no harakat — flag only
 F6 LU_KEY merge      rows with the same (lemma_ar,pos_ar,frame_id) merged; en_lu_ids joined
Output: 03_lus_ar/l2_017_cand_norm.csv (lus_ar columns + flags), 03_lus_ar/l2_017_nae.csv, report on stdout."""
import csv, hashlib, os, pathlib, re, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import wazn_rules as W
ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "03_lus_ar/l2_017_cand_raw.csv"
RAW_SHA = "4f566faef91ca2fea544ba5d0e26297be8e8b3347400f0ef54fd43c3f07484c1"
if hashlib.sha256(RAW.read_bytes()).hexdigest() != RAW_SHA: print("STOP raw sha"); sys.exit(2)
SIB = os.environ.get("AWZAN_SIB", "/Users/husseinhiyassat/hokom-local-validation/taaqol-executor-wt/data/awzan-sibawayh-308.csv")
VERBS = os.environ.get("AWZAN_VERBS", "/Users/husseinhiyassat/arabic-net/Arabic-Mother-language-wazn-net/data/awzaan_af3aal_all.csv")
for p, h in ((SIB, "a1c1f7f94378eb6e4ad5a994ee180c38c2f5da5058fc9ac1a670f25a3555b1a0"), (VERBS, "ba0aee787f997d20900f2c3bd790ce5d658e138b2464cd6476e9dd4408594e9b")):
    if hashlib.sha256(open(p, "rb").read()).hexdigest() != h: print("STOP sha", p); sys.exit(2)
OWN = ROOT / "03_lus_ar/wazn_owner_l2_015.csv"
VA = {r["wazn"].strip() for r in csv.DictReader(open(VERBS, encoding="utf-8-sig"))}
inv = W.noun_inventory_v3({r["pattern_vocalized"].strip() for r in csv.DictReader(open(SIB, encoding="utf-8-sig")) if r["status"] == "EXISTS"}, VA, OWN)
_, OV = W.owner_lines(OWN)
VK = {W.key(v): v for v in VA | OV}
POS = [l.strip() for l in open(ROOT / "03_lus_ar/pos_ar_closed.txt", encoding="utf-8") if l.strip()]
NO_ROOT = {"تركيب", "حرف", "مبني"}
HARAKAT = "ًٌٍَُِّْ"
SUN = set("تثدذرزسشصضطظلن")
KMAP = str.maketrans("أإآؤئءى", "ءءءءءءي")
def bare(s): return "".join(c for c in s if c not in HARAKAT and c != "ـ")
def strip_al(lemma, pos, root):
    if pos in NO_ROOT | {"فعل"} or not lemma.startswith("ال") or bare(root).startswith("ل"): return lemma, False
    m = re.match(r"^ا[َ]?لْ?([^" + HARAKAT + r"])([" + HARAKAT + r"]*)(.*)$", lemma)
    if not m: return lemma, False
    c, marks, rest = m.groups()
    strong = [x for k, x in enumerate(norm_root(root)) if x not in "ءويا" and (k == 0 or x != norm_root(root)[k-1])]
    sk = bare(c + rest).translate(KMAP); i = 0
    for x in strong:                                    # all strong radicals must survive in order after removing ال
        j = sk.find(x, i)
        if j < 0: return lemma, False
        i = j + 1
    if c in SUN: marks = marks.replace("ّ", "")          # assimilation shadda belongs to the article
    return c + marks + rest, True
def norm_root(r):
    s = re.sub(r"[\s\-_.,،]", "", bare(r)).translate(KMAP)
    if s.startswith("ا"): s = "ء" + s[1:]
    return s
def skel(s): return bare(s).translate(KMAP).replace("ا", "").replace("ة", "").replace("و", "").replace("ي", "")
def instantiate(wazn, root):
    rl = list(root)
    if len(rl) == 3: m = {"ف": rl[0], "ع": rl[1], "ل": rl[2]}; s = bare(wazn); out = []
    else: return None
    seen_l = 0
    for c in s:
        out.append(m.get(c, c))
    return "".join(out)
rows = list(csv.DictReader(open(RAW, encoding="utf-8")))
st = collections.Counter(); fl = collections.Counter()
merged = collections.OrderedDict(); nae = []
for r in rows:
    if r["status_en"] != "MAPPED":
        nae.append(r); st["status_" + r["status_en"]] += 1; continue
    flags = []
    lemma, pos, root, wazn = r["lemma_ar"].strip(), r["pos_ar"].strip(), r["root"].strip(), r["wazn"].strip()
    lemma2, did = strip_al(lemma, pos, root)
    if did: flags.append("AL_STRIPPED"); lemma = lemma2
    elif lemma.startswith("ال") and pos not in NO_ROOT | {"فعل"} and not bare(root).startswith("ل"): flags.append("AL_UNRESOLVED")
    r2 = norm_root(root)
    if r2 != root: flags.append("ROOT_NORMALIZED")
    root = r2
    if pos not in NO_ROOT:
        if not root: flags.append("ROOT_MISSING")
        else:
            if "ا" in root[1:]: flags.append("ROOT_ALIF")
            if len(root) not in (3, 4): flags.append("ROOT_LEN")
    else:
        if root or wazn: flags.append("ROOT_WAZN_CLEARED_NO_ROOT_POS"); root = ""; wazn = ""
    wazn_note = ""
    if pos not in NO_ROOT:
        if not wazn: flags.append("WAZN_MISSING")
        else:
            k = W.key(wazn)
            if pos == "فعل":
                if k in VK: wazn = VK[k]
                else: flags.append("WAZN_NOT_IN_INV"); wazn_note, wazn = wazn, ""
            else:
                if k in inv: wazn = inv[k][0]
                else: flags.append("WAZN_NOT_IN_INV"); wazn_note, wazn = wazn, ""
        w_any = wazn or wazn_note
        if w_any and root and len(root) == 3 and not set(root) & set("ءويا"):
            inst = instantiate(re.sub(r"\s*\([^)]*\)", "", w_any), root)
            if inst is not None and skel(inst) != skel(lemma): flags.append("WAZN_LEMMA_MISMATCH")
    if pos not in POS: flags.append("POS_NOT_CLOSED")
    if pos == "صيغة مبالغة" and W.key(wazn or wazn_note) not in {W.key(x) for x in W.MUBALAGHA_WAZN}: flags.append("MUBALAGHA_NOT_FAAAL")
    if pos == "اسم مرة" and W.key(wazn or wazn_note) not in {W.key(x) for x in W.MARRA_WAZN}: flags.append("MARRA_NOT_FALA")
    if not any(c in HARAKAT for c in lemma): flags.append("UNVOCALIZED")
    for f in flags: fl[f] += 1
    K = (lemma, pos, r["frame_id"].strip())
    if K in merged:
        m = merged[K]; m["en_lu_ids"].append(r["en_lu_id"]); m["flags"] |= set(flags); st["merged_same_LU_KEY"] += 1
    else:
        merged[K] = dict(lemma_ar=lemma, pos_ar=pos, frame_id=K[2], en_lu_ids=[r["en_lu_id"]], definition_ar=r["definition_ar"].strip(),
                         root=root, wazn=wazn, wazn_note=wazn_note, flags=set(flags), note=("L2_017 haiku b" + r["src_batch"] + (" | " + r["note"].strip() if r["note"].strip() else "")))
cur = [r["ar_lu_id"] for r in csv.DictReader(open(ROOT / "03_lus_ar/lus_ar.csv", encoding="utf-8-sig"))]
n0 = max(int(x[2:]) for x in cur)
COLS = ["ar_lu_id","lemma_ar","pos_ar","frame_id","en_lu_ids","definition_ar","root","wazn","evidence_primary","evidence_frame_level","metaphor_flag","owner_choice","status","wazn_note","note","flags"]
out = ROOT / "03_lus_ar/l2_017_cand_norm.csv"
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(COLS)
    for i, m in enumerate(merged.values(), 1):
        w.writerow([f"AR{n0+i:05d}", m["lemma_ar"], m["pos_ar"], m["frame_id"], ";".join(m["en_lu_ids"]), m["definition_ar"], m["root"], m["wazn"],
                    "", "", "", "", "CANDIDATE", m["wazn_note"], m["note"], ";".join(sorted(m["flags"]))])
with open(ROOT / "03_lus_ar/l2_017_nae.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["en_lu_id", "frame_id", "status_en", "note"])
    for r in nae: w.writerow([r["en_lu_id"], r["frame_id"], r["status_en"], r["note"]])
print(f"raw_rows = {len(rows)}\nmapped_rows = {len(rows)-len(nae)}\nnae_rows = {len(nae)}\nar_lus_after_merge = {len(merged)}\nfirst_id = AR{n0+1:05d}\nlast_id = AR{n0+len(merged):05d}")
print(f"rows_with_no_flag = {sum(1 for m in merged.values() if not m['flags'])}")
for k, v in sorted(st.items()): print(f"{k} = {v}")
for k, v in sorted(fl.items()): print(f"flag_{k} = {v}")
print("pos_counts:", dict(collections.Counter(m["pos_ar"] for m in merged.values()).most_common()))
print("sha256 l2_017_cand_norm.csv =", hashlib.sha256(out.read_bytes()).hexdigest())
