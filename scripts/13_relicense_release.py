#!/usr/bin/env python3
"""G0.1 closed (OWNER_DECISION_G0.1). Produce a new immutable tag = an existing tag's files copied unchanged + 00_source/LICENSE.txt.
Usage: python3 scripts/13_relicense_release.py <from_tag> <to_tag>. Verifies every source file against the source MANIFEST first."""
import hashlib, json, pathlib, shutil, sys, datetime
ROOT = pathlib.Path(__file__).resolve().parents[1]; SRC, DST = (ROOT / "release" / t for t in sys.argv[1:3])
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
LIC = ROOT / "00_source/LICENSE.txt"
if sha(LIC) != "1a17bb4c41476e7c0c3bbb29bf8a73dac0423684aca05908ad6cceb2af17bbd6": sys.exit("BLOCKED: LICENSE sha")
if DST.exists(): sys.exit(f"BLOCKED: {DST} exists")
m = json.loads((SRC / "MANIFEST.json").read_text(encoding="utf-8"))
bad = [f for f, h in m["files"].items() if sha(SRC / f) != h]
if bad: sys.exit(f"BLOCKED: source files changed {bad}")
DST.mkdir(parents=True)
for f in m["files"]: shutil.copy(SRC / f, DST / f)
shutil.copy(LIC, DST / "LICENSE.txt")
m.update(tag=DST.name, frozen_at=datetime.datetime.now().isoformat(timespec="seconds"), license_verified=True,
         derived_from={"tag": SRC.name, "manifest_sha256": sha(SRC / "MANIFEST.json"), "change": "added LICENSE.txt (G0.1 closed by owner); content files unchanged"})
m["files"] = {f: sha(DST / f) for f in sorted(p.name for p in DST.iterdir())}
(DST / "MANIFEST.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
rd = (SRC / "README.md").read_text(encoding="utf-8").replace(f"`{SRC.name}`", f"`{DST.name}`")
i = rd.find("## Status")
rd = rd[:i] + f"""## Status
license_verified = True — FrameNet 1.7 data used under CC BY 3.0 Unported (see LICENSE.txt). Attribution required:
cite FrameNet (http://framenet.icsi.berkeley.edu) and Fillmore & Baker (2010). COD-sourced English definitions are not covered and not included.
Derived from `{SRC.name}` (MANIFEST {sha(SRC / 'MANIFEST.json')[:12]}) with LICENSE.txt added; all other files byte-identical.
"""
(DST / "README.md").write_text(rd, encoding="utf-8")
print(f"{DST.name}: files={len(m['files'])+1} MANIFEST sha256 =", sha(DST / "MANIFEST.json"))
