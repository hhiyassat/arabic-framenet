# Arabic FrameNet — Layer 1 release `layer1_v3`

RULE_OWNER = DR_HUSSEIN. Frozen 2026-09-15T07:11:20. Keys are FrameNet 1.7 numeric IDs (frame_id / fe_id); Arabic names are labels, not keys.

## What this is
Arabic translations of FrameNet 1.7 **frame definitions (1221) and frame-element definitions (11416)**, with approved Arabic terms for
1285 frame-element names, 17 grammatical-function terms, 1221 frame names, and 10 frame-relation types; relations (2070) carried by ID.

## What this is NOT
- No Arabic lexical units: no link from any Arabic word to any frame exists in this release. Arabic LU = 0.
- No Arabic annotated sentences or valence patterns.
- Not a source of rulings: frames describe event types, never their legal/juristic status (see HANDOFF).

## Files
frames_ar.jsonl · frame_elements_ar.jsonl · frame_relations.jsonl · fe_glossary.tsv · grammar_glossary.tsv · frame_names.tsv · relation_types.tsv · names_map.tsv · APPROVAL_LOG.txt · MANIFEST.json
Consumers must read by fingerprint (MANIFEST.json) and treat the release as immutable; corrections produce a new tag.

## Status
license_verified = True — FrameNet 1.7 data used under CC BY 3.0 Unported (see LICENSE.txt). Attribution required:
cite FrameNet (http://framenet.icsi.berkeley.edu) and Fillmore & Baker (2010). COD-sourced English definitions are not covered and not included.
Derived from `layer1_v1` (MANIFEST 817e5143e6eb) with LICENSE.txt added; all other files byte-identical.

layer1_v3: identical to layer1_v2 except fe_glossary.tsv without the third-party column `mac_dict_candidate`.
