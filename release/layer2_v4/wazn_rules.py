"""Wazn rules shared by 06_check_lus.py and 08_apply_fem_wazn.py.
OWNER_DECISION_L2_005: feminine wazn = feminizable Sibawayh EXISTS pattern + ة.
Feminizable (closed definition, measured not assumed): singular line ending in tanween-damm ٌ, no '?' (uncertain), not marked (جمع), no '/' alternates, not already ending in ة.
Canonical feminine form: core (annotation in parentheses removed, final ٌ removed) + 'َةٌ'.  e.g. فَعْلٌ → فَعْلَةٌ ; مَفْعَلٌ → مَفْعَلَةٌ"""
import re, unicodedata
MARKS = "ًٌٍَُِّْ"
def canon(s):
    """Order the combining marks on each letter (shadda first) so equal patterns compare equal."""
    out, buf = [], []
    for ch in (s or "").strip():
        if ch in MARKS: buf.append(ch)
        else:
            out += sorted(buf, key=lambda c: (c != "ّ", c)); buf = []; out.append(ch)
    out += sorted(buf, key=lambda c: (c != "ّ", c))
    return "".join(out)
def core(line):
    s = re.sub(r"\s*\([^)]*\)", "", line).strip()
    return re.sub("[ًٌٍُ]+$", "", s)          # drop final tanween / case vowel
def feminizable(line):
    bare = re.sub(r"\s*\([^)]*\)", "", line).strip()      # annotation like (رباعي) does not block feminization
    return (bare.endswith("\u064C") and "?" not in line and "(جمع)" not in line and "/" not in line
            and not core(line).endswith("\u0629"))          # already feminine (…َةٌ) is not feminized again
def derive_fem(noun_lines):
    """returns {canonical feminine wazn: base line}"""
    fem = {}
    for l in sorted(noun_lines):
        if feminizable(l):
            fem.setdefault(canon(core(l) + "َةٌ"), l)
    return fem
def note_key(note):
    """wazn_note like 'فَعْلَة' or 'فَعْلَةٌ' → canonical feminine key (adds ٌ)"""
    s = re.sub(r"\s*\([^)]*\)", "", note or "").strip()
    s = re.sub("[ًٌٍُ]+$", "", s)
    return canon(s + "ٌ") if s.endswith("ة") else None

# ---- OWNER_DECISION_L2_006: regular derivatives of the ratified verb awzan join the noun inventory ----
# Closed list (classical قياس). Key = verb wazn exactly as in awzaan_af3aal_all.csv. Types: فا=اسم فاعل، مف=اسم مفعول، مص=مصدر قياسي.
# Not derived (OWNER_ALERT): فَعَلَ/فَعِلَ/فَعُلَ (مصدر سماعي; فاعل/مفعول already in Sibawayh) and the ـى-final فَعْلَى/تَفَعْلَى/اِفْعَنْلَى (منقوص/مقصور forms).
DERIVED = {
 "فَعْلَلَ":   [("فا","مُفَعْلِلٌ"),("مف","مُفَعْلَلٌ"),("مص","فَعْلَلَةٌ"),("مص","فِعْلَالٌ")],
 "فَوْعَلَ":   [("فا","مُفَوْعِلٌ"),("مف","مُفَوْعَلٌ"),("مص","فَوْعَلَةٌ")],
 "فَعْوَلَ":   [("فا","مُفَعْوِلٌ"),("مف","مُفَعْوَلٌ"),("مص","فَعْوَلَةٌ")],
 "فَيْعَلَ":   [("فا","مُفَيْعِلٌ"),("مف","مُفَيْعَلٌ"),("مص","فَيْعَلَةٌ")],
 "فَعْيَلَ":   [("فا","مُفَعْيِلٌ"),("مف","مُفَعْيَلٌ"),("مص","فَعْيَلَةٌ")],
 "فَعْنَلَ":   [("فا","مُفَعْنِلٌ"),("مف","مُفَعْنَلٌ"),("مص","فَعْنَلَةٌ")],
 "أَفْعَلَ":   [("فا","مُفْعِلٌ"),("مف","مُفْعَلٌ"),("مص","إِفْعَالٌ")],
 "فَاعَلَ":    [("فا","مُفَاعِلٌ"),("مف","مُفَاعَلٌ"),("مص","مُفَاعَلَةٌ"),("مص","فِعَالٌ")],
 "فَعَّلَ":    [("فا","مُفَعِّلٌ"),("مف","مُفَعَّلٌ"),("مص","تَفْعِيلٌ"),("مص","تَفْعِلَةٌ")],
 "اِنْفَعَلَ": [("فا","مُنْفَعِلٌ"),("مف","مُنْفَعَلٌ"),("مص","اِنْفِعَالٌ")],
 "اِفْتَعَلَ": [("فا","مُفْتَعِلٌ"),("مف","مُفْتَعَلٌ"),("مص","اِفْتِعَالٌ")],
 "اِفْعَلَّ":  [("فا","مُفْعَلٌّ"),("مص","اِفْعِلَالٌ")],
 "تَفَعَّلَ":  [("فا","مُتَفَعِّلٌ"),("مف","مُتَفَعَّلٌ"),("مص","تَفَعُّلٌ")],
 "تَفَاعَلَ":  [("فا","مُتَفَاعِلٌ"),("مف","مُتَفَاعَلٌ"),("مص","تَفَاعُلٌ")],
 "اِسْتَفْعَلَ":[("فا","مُسْتَفْعِلٌ"),("مف","مُسْتَفْعَلٌ"),("مص","اِسْتِفْعَالٌ")],
 "اِفْعَوْعَلَ":[("فا","مُفْعَوْعِلٌ"),("مص","اِفْعِيعَالٌ")],
 "اِفْعَالَّ": [("فا","مُفْعَالٌّ"),("مص","اِفْعِيلَالٌ")],
 "اِفْعَوَّلَ":[("فا","مُفْعَوِّلٌ"),("مص","اِفْعِوَّالٌ")],
 "تَفَعْلَلَ": [("فا","مُتَفَعْلِلٌ"),("مف","مُتَفَعْلَلٌ"),("مص","تَفَعْلُلٌ")],
 "اِفْعَنْلَلَ":[("فا","مُفْعَنْلِلٌ"),("مص","اِفْعِنْلَالٌ")],
 "اِفْعَلَلَّ":[("فا","مُفْعَلِلٌّ"),("مص","اِفْعِلَّالٌ")],
 "تَفَعْوَلَ": [("فا","مُتَفَعْوِلٌ"),("مص","تَفَعْوُلٌ")],
 "تَفَيْعَلَ": [("فا","مُتَفَيْعِلٌ"),("مص","تَفَيْعُلٌ")],
 "تَفَوْعَلَ": [("فا","مُتَفَوْعِلٌ"),("مص","تَفَوْعُلٌ")],
 "تَمَفْعَلَ": [("فا","مُتَمَفْعِلٌ"),("مص","تَمَفْعُلٌ")],
}
def key(s):
    """comparison key: annotation removed, final tanween/case-vowel removed, marks ordered"""
    s = re.sub(r"\s*\([^)]*\)", "", s or "").strip()
    s = canon(re.sub("[\u064B\u064C\u064D\u064F]+$", "", s))
    return s.replace("\u064E\u0627", "\u0627")          # orthographic only: fatha before long alif is redundant
def derived_lines(verb_awzan):
    """{line: provenance} for the verb awzan present in the ratified verb file"""
    out = {}
    for v in sorted(verb_awzan):
        for t, l in DERIVED.get(v.strip(), []):
            out.setdefault(l, f"L2_006 {t} من {v.strip()}")
    return out
def noun_inventory(sib_exists, verb_awzan):
    """full noun inventory: {key: (canonical line, provenance)}  = Sibawayh EXISTS ∪ L2_006 derived ∪ L2_005 feminine of both"""
    inv = {}
    for l in sorted(sib_exists): inv.setdefault(key(l), (l, "SIBAWAYH_EXISTS"))
    for l, p in derived_lines(verb_awzan).items(): inv.setdefault(key(l), (l, p))
    base = [v[0] for v in inv.values()]
    for f, b in derive_fem(base).items(): inv.setdefault(key(f), (f, f"L2_005 مؤنث {b}"))
    return inv

# ---- OWNER_DECISION_L2_007: النسبة = إضافة ياء (عنصر→عنصري) ----
def nisba_lines(lines):
    """{nisba line: base}: core of each inventory line (final ـَة dropped) + ـِيٌّ ; feminine + ـِيَّةٌ"""
    out = {}
    for l in sorted(lines):
        if "?" in l or "/" in l or "(جمع)" in l: continue
        c = core(l)
        if c.endswith("ة"): c = re.sub("َ?ة$", "", c)
        if not c or c.endswith(("يّ", "ى", "اء")): continue   # already nisba / ـى / ـاء endings skipped
        out.setdefault(c + "ِيٌّ", l)
        out.setdefault(c + "ِيَّةٌ", l)
    return out
def noun_inventory_v2(sib_exists, verb_awzan):
    inv = noun_inventory(sib_exists, verb_awzan)
    for n, b in nisba_lines([v[0] for v in inv.values()]).items():
        inv.setdefault(key(n), (n, f"L2_007 نسبة {b}"))
    return inv
MUBALAGHA_WAZN = {"فَعَّال", "فَعَّالَة"}   # owner: صيغة المبالغة فَعَّال (feminine by L2_005)
MARRA_WAZN = {"فَعْلَة"}                    # owner: اسم المرة فَعْلَة

# ---- OWNER_DECISION_L2_015: owner-ratified extra patterns (03_lus_ar/wazn_owner_l2_015.csv) ----
def owner_lines(path):
    import csv as _c
    rows = list(_c.DictReader(open(path, encoding="utf-8-sig")))
    return [r["wazn"].strip() + "ٌ" for r in rows if r["class"] == "noun"], {r["wazn"].strip() for r in rows if r["class"] == "verb"}
def noun_inventory_v3(sib_exists, verb_awzan, owner_path):
    inv = noun_inventory_v2(sib_exists, verb_awzan)
    on, _ = owner_lines(owner_path)
    for l in on: inv.setdefault(key(l), (l, "L2_015 المالك"))
    for f, b in derive_fem(on).items(): inv.setdefault(key(f), (f, f"L2_005 مؤنث {b}"))
    for n, b in nisba_lines(on).items(): inv.setdefault(key(n), (n, f"L2_007 نسبة {b}"))
    return inv
