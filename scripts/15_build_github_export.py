#!/usr/bin/env python3
"""OWNER_DECISION_PUB_001 — build github_export/ : a cleaned public copy of the project (the working project is not changed).
Excluded: logs/, output/, __pycache__/, dotfiles, *.xlsx, release/*_v1, release/layer1_v2 (third-party column), empty/stray folders.
Transformed: 01_glossary/fe_glossary.tsv without `mac_dict_candidate`; 03_lus_ar/lus_template.csv with COD-sourced English
definitions blanked (definition_source kept). Prints a manifest of every exported file with sha256."""
import csv, hashlib, io, pathlib, shutil, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]; OUT = ROOT / "github_export"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if OUT.exists() and any(p.name != ".git" for p in OUT.iterdir()): sys.exit("STOP: github_export/ not empty")
COPY = ["00_source/frames.jsonl", "00_source/fes.jsonl", "00_source/relations.jsonl", "00_source/LICENSE.txt",
        "01_glossary/APPROVAL_LOG.txt", "01_glossary/frame_names.tsv", "01_glossary/grammar_glossary.tsv", "01_glossary/relation_types.tsv",
        "01_glossary/names_map.tsv", "01_glossary/names_map_a.tsv", "01_glossary/names_map_b.tsv", "01_glossary/names_map_c.tsv",
        "03_lus_ar/lus_ar.csv", "03_lus_ar/lus_en_status.csv", "03_lus_ar/lus_rejected.csv", "03_lus_ar/pos_ar_closed.txt", "03_lus_ar/pos_glossary.tsv",
        "03_lus_ar/root_alert_waived.txt", "03_lus_ar/v21_roots_index.csv", "03_lus_ar/wazn_nouns_inventory.csv", "03_lus_ar/wazn_owner_l2_015.csv",
        "03_lus_ar/l2_017_cand_raw.csv", "03_lus_ar/l2_017_cand_norm.csv", "03_lus_ar/l2_017_cand_norm2.csv", "03_lus_ar/l2_017_nae.csv", "03_lus_ar/l2_017_deferred.csv", "03_lus_ar/l2_027_redraft.csv",
        "api/afn_api.py", "HANDOFF_ARABIC_FRAMENET_USE.md", "frame_relations_ar.csv", "AGENT_PROMPT_v2.md", "CONTINUE_005.md", "CONTINUE_006.md"]
COPY += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "02_frames_ar").iterdir()) if p.is_file() and not p.name.startswith(".")]
COPY += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "scripts").iterdir()) if p.is_file() and p.suffix in (".py", ".sh")]
for tag in ("layer1_v3", "layer2_v4"):   # layer2_v4 supersedes layer2_v3 (L2_020..L2_028)
    COPY += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "release" / tag).iterdir()) if p.is_file()]
OUT.mkdir(exist_ok=True)
for rel in COPY:
    d = OUT / rel; d.parent.mkdir(parents=True, exist_ok=True); shutil.copy(ROOT / rel, d)
shutil.copy(ROOT / "README.md", (OUT / "docs").mkdir(exist_ok=True) or OUT / "docs/PROJECT_PLAN.md")
# transformed files
lines = (ROOT / "01_glossary/fe_glossary.tsv").read_text(encoding="utf-8").split("\n"); i = lines[0].split("\t").index("mac_dict_candidate")
(OUT / "01_glossary/fe_glossary.tsv").write_text("\n".join("\t".join(c[:i] + c[i + 1:]) if l else l for l in lines for c in [l.split("\t")]), encoding="utf-8")
rows = list(csv.DictReader(open(ROOT / "03_lus_ar/lus_template.csv", encoding="utf-8-sig"))); cols = list(rows[0]); blank = 0
for r in rows:
    if r["definition_source"] == "COD": r["definition_en"] = ""; blank += 1
buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(rows)
(OUT / "03_lus_ar/lus_template.csv").write_text(buf.getvalue(), encoding="utf-8")
tpl = sha(OUT / "03_lus_ar/lus_template.csv")
for api in (OUT / "api/afn_api.py", ROOT / "api/afn_api.py"):
    s = api.read_text(encoding="utf-8"); api.write_text(s.replace("__PUBLIC_TEMPLATE_SHA__", tpl), encoding="utf-8")
assert "mac_dict_candidate" not in (OUT / "01_glossary/fe_glossary.tsv").read_text(encoding="utf-8").split("\n")[0]
files = sorted(p for p in OUT.rglob("*") if p.is_file() and ".git" not in p.parts)
print(f"exported_files = {len(files)}  bytes = {sum(p.stat().st_size for p in files)}  cod_blanked = {blank}  public_template_sha256 = {tpl}")
with open(OUT / "EXPORT_MANIFEST.tsv", "w", encoding="utf-8") as f:
    f.write("path\tsha256\n"); [f.write(f"{p.relative_to(OUT)}\t{sha(p)}\n") for p in files]
