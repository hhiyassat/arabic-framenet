#!/usr/bin/env python3
"""Build examples/index.html — a static, offline demo of the Arabic FrameNet releases (no server, no AI).
Data and match keys are taken from api/afn_api.py itself (same release pins, same norm(), same SINGLE/MULTI index, same
PREF/SUF lists), so the page and the API agree by construction; tests/parity_example_vs_api.py measures that agreement.
Usage: python3 scripts/24_build_example_html.py   (writes examples/index.html and examples/parity_cases.json)"""
import hashlib, json, pathlib, re, runpy, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT / "api/afn_api.py"), run_name="afn_api_lib")      # verifies MANIFEST pins on load
LUS, FRAMES, FES, EN, PIN = API["LUS"], API["FRAMES"], API["FES"], API["EN"], API["PIN"]
SINGLE, MULTI, PREF, SUF, RULES = API["SINGLE"], API["MULTI"], API["PREF"], API["SUF"], API["RULES"]
L2 = [k for k in PIN if k.startswith("layer2")][0]; L1 = [k for k in PIN if k.startswith("layer1")][0]
man = json.loads((ROOT / "release" / L2 / "MANIFEST.json").read_text(encoding="utf-8"))
used = sorted({int(r["frame_id"]) for r in LUS})
lus = [[r["lemma_ar"], r["pos_ar"], int(r["frame_id"]), r["root"], r["wazn"], r["definition_ar"],
        ", ".join(f"{EN[e]['lemma']}.{EN[e]['pos']}" for e in r["en_lu_ids"].split(";") if e in EN), r["ar_lu_id"]] for r in LUS]
frames = {}
for fid in used:
    f = FRAMES[fid]
    fes = sorted(FES.get(fid, []), key=lambda e: (e["core_type"] != "Core", e["fe_id"]))
    frames[fid] = [f["name"], f["name_ar"], f["definition_ar"], [[e["name_ar"], e["name"], 1 if e["core_type"] == "Core" else 0] for e in fes]]
data = {"lus": lus, "frames": frames, "single": SINGLE, "multi": [[t, i] for t, i in MULTI], "pref": PREF, "suf": SUF,
        "meta": {"layer1": [L1, PIN[L1]], "layer2": [L2, PIN[L2]], "counts": man["counts"], "frames_total": len(FRAMES),
                 "pos": man.get("pos_ar_distribution", {}), "rules": RULES}}
SAMPLES = ["غضب التاجر من جاره، ثم لبس قميصه ومشى إلى السوق.",
           "كتب الطالب رسالة طويلة إلى صديقه القديم.",
           "دخل المدمن المستشفى بعد أن فقد السيطرة.",
           "قتل الجندي عدوه بالسيف ثم هرب نحو الشمال.",
           "اشترى الرجل بيتا جديدا وباع سيارته القديمة."]
tpl = (ROOT / "scripts/example_template.html").read_text(encoding="utf-8")
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = tpl.replace("__DATA__", blob).replace("__SAMPLES__", json.dumps(SAMPLES, ensure_ascii=False))
out = ROOT / "examples/index.html"; out.parent.mkdir(exist_ok=True); out.write_text(html, encoding="utf-8")
# parity cases: API output for the samples + every approved-LU definition used as a sentence (measures JS==API)
cases = SAMPLES + [r["definition_ar"] for r in LUS[::7]]
exp = []
for t in cases:
    for mode in ("exact", "affix"):
        a = API["analyze"](t, mode)
        exp.append({"text": t, "mode": mode, "targets": [[x["token_span"][0], x["token_span"][1] - x["token_span"][0] + 1,
                    x["match"]["method"], x["match"]["lemma_key"], [lu["ar_lu_id"] for lu in x["lexical_units"]]] for x in a["targets"]]})
(ROOT / "examples/parity_cases.json").write_text(json.dumps(exp, ensure_ascii=False), encoding="utf-8")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
print(f"lus = {len(lus)}\nframes = {len(frames)}\nsingle_keys = {len(SINGLE)}\nmulti = {len(MULTI)}\nparity_cases = {len(exp)}")
print(f"bytes examples/index.html = {out.stat().st_size}\nsha256 examples/index.html = {sha(out)}")
