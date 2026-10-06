#!/usr/bin/env python3
"""OWNER_DECISION_PUB_001: new tag release/layer1_v3 = layer1_v2 with the third-party column `mac_dict_candidate`
removed from fe_glossary.tsv. All other files byte-identical. layer1_v2 is not touched (immutable)."""
import csv, hashlib, json, pathlib, shutil, sys, datetime, io
ROOT = pathlib.Path(__file__).resolve().parents[1]; SRC, DST = ROOT / "release/layer1_v2", ROOT / "release/layer1_v3"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if sha(SRC / "MANIFEST.json") != "d7a7b300bef676a6426aa50afdeb930644af1f2c4b23d17e9c3cd41b6b836baa": sys.exit("STOP: layer1_v2 changed")
if DST.exists(): sys.exit("STOP: layer1_v3 exists")
m = json.loads((SRC / "MANIFEST.json").read_text(encoding="utf-8"))
if [f for f, h in m["files"].items() if sha(SRC / f) != h]: sys.exit("STOP: layer1_v2 file changed")
DST.mkdir()
for f in m["files"]:
    if f == "fe_glossary.tsv":
        lines = (SRC / f).read_text(encoding="utf-8").split("\n"); rows = [l.split("\t") for l in lines if l]
        i = rows[0].index("mac_dict_candidate")   # raw split/join: no CSV escaping, every other byte unchanged
        (DST / f).write_text("\n".join("\t".join(c[:i] + c[i + 1:]) if l else l for l in lines for c in [l.split("\t")]), encoding="utf-8")
    else: shutil.copy(SRC / f, DST / f)
n_before = len(rows)
m.update(tag="layer1_v3", frozen_at=datetime.datetime.now().isoformat(timespec="seconds"),
         derived_from={"tag": "layer1_v2", "manifest_sha256": sha(SRC / "MANIFEST.json"), "change": "fe_glossary.tsv: removed third-party column mac_dict_candidate (OWNER_DECISION_PUB_001); all other files byte-identical"})
m["files"] = {f: sha(DST / f) for f in sorted(p.name for p in DST.iterdir())}
(DST / "MANIFEST.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
rd = (SRC / "README.md").read_text(encoding="utf-8").replace("`layer1_v2`", "`layer1_v3`")
rd += "\nlayer1_v3: identical to layer1_v2 except fe_glossary.tsv without the third-party column `mac_dict_candidate`.\n"
(DST / "README.md").write_text(rd, encoding="utf-8")
chk = [l.split("\t") for l in (DST / "fe_glossary.tsv").read_text(encoding="utf-8").split("\n") if l]
print("rows", n_before, len(chk), "cols", len(rows[0]), "->", len(chk[0]), "mac_dict left:", "mac_dict_candidate" in chk[0])
print("layer1_v3 MANIFEST sha256 =", sha(DST / "MANIFEST.json"))
