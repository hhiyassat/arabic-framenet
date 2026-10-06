# Arabic FrameNet — Layer 2 release `layer2_v2`

RULE_OWNER = DR_HUSSEIN. Frozen 2026-10-05T20:37:10. Builds on layer1_v1 (MANIFEST sha 817e5143e6eb); keys are FrameNet 1.7 frame_id / lu_id.

## What this is
Arabic lexical units for the **50 pilot frames**: 2641 APPROVED Arabic LUs (key = lemma_ar, pos_ar, frame_id), linked many-to-many to the
4007 English LUs of those frames (3023 MAPPED, 243 NO_ARABIC_EQUIVALENT, 741 EVIDENCE_GAP_ONLY).
Each LU carries root, wazn (from the ratified inventory: Sibawayh EXISTS + L2_005 feminine + L2_006 verb derivatives + L2_007 nisba + L2_015 owner patterns),
pos_ar from a closed list of 16, an independent Arabic definition, and evidence pointers (roots-4662 / v21: المحكم، مقاييس، الأساس).

## What this is NOT
- Not all of FrameNet: 1171 other frames have no Arabic LUs yet (no expansion before this gate).
- 1307 LUs whose root is a «مكمِّل» root in roots-4662 are EXCLUDED (D2 → EVIDENCE_GAP); listed only in the working file.
- No annotated sentences or valence patterns. Not a source of rulings (frame ≠ ruling).
- Evidence columns are pointers, not quoted text; COD definitions were not translated.

## Files
06_check_lus.py · APPROVAL_LOG.txt · lus_ar.csv · lus_en_status.csv · pos_ar_closed.txt · pos_glossary.tsv · root_alert_waived.txt · v21_roots_index.csv · wazn_nouns_inventory.csv · wazn_owner_l2_015.csv · wazn_rules.py · MANIFEST.json
Read by fingerprint; immutable — corrections produce a new tag.

## Status
license_verified = True — FrameNet 1.7 data used under CC BY 3.0 Unported (see LICENSE.txt). Attribution required:
cite FrameNet (http://framenet.icsi.berkeley.edu) and Fillmore & Baker (2010). COD-sourced English definitions are not covered and not included.
Derived from `layer2_v1` (MANIFEST 8af42e5cf2c8) with LICENSE.txt added; all other files byte-identical.
