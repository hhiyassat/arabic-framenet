# Arabic FrameNet · الإطارات الدلالية العربية

An Arabic layer over **FrameNet 1.7** (ICSI, Berkeley): Arabic names and definitions for all 1,221 frames and 11,416 frame elements, and 7,623 approved Arabic lexical units for 986 frames, each with root, wazn (morphological pattern) and part of speech.

طبقة عربية فوق FrameNet 1.7: أسماء وتعريفات عربية لكل الأطر (1221) وعناصرها (11416)، و7623 وحدة معجمية عربية معتمدة في 986 إطاراً، لكلٍّ منها الجذر والوزن وقسم الكلم.

## Releases · الإصدارات

| Tag | Content | MANIFEST sha256 |
|---|---|---|
| `release/layer1_v3` | 1,221 frames · 11,416 frame elements · 2,070 relations (Arabic) | `84c69ebbd0c125c2792d97b1f7b941c162d2dd6dd3dce433a72bdcd53c589cc1` |
| `release/layer2_v4` | 7,623 Arabic LUs (986 frames), many-to-many links to 13,572 FrameNet LUs | `0f2c3e3db20ef022ddd9991d744a6529da07c85e62ff4f5149fce8750e7da400` |

Releases are immutable; read them by fingerprint (`MANIFEST.json`). Every rule and decision behind them is logged in `01_glossary/APPROVAL_LOG.txt`.

## Quick start · البدء

```bash
python3 api/afn_api.py                     # http://127.0.0.1:8765  (test page at /)
curl -X POST localhost:8765/analyze -H 'Content-Type: application/json' -d '{"text":"غضب التاجر ولبس قميصه"}'
python3 api/afn_api.py --cli "غضب التاجر ولبس قميصه"
```

The API is a deterministic lookup over the releases (no AI at runtime, Python standard library only). It verifies every release file against its manifest before serving. See `HANDOFF_ARABIC_FRAMENET_USE.md` for schemas, usage rules and limits.

## Live example · مثال تفاعلي

`examples/index.html` is a self-contained page (no server, no AI) that runs the same lookup as the API in the browser:
analyse an Arabic sentence (exact or affix-stripping mode), see each target word's lemma, part of speech, root, wazn,
the frames it evokes with their Arabic definitions and frame elements, and browse all 986 frames that have Arabic LUs.
Open it locally, or enable GitHub Pages (Settings → Pages → `main` / root) and visit `/examples/`.
`node tests/parity_example_vs_api.js` checks that the page and `api/afn_api.py` return identical targets (2,188 cases, 0 mismatches at build time).

صفحة مستقلة تحلّل الجملة العربية في المتصفح بالفهرس وقواعد المطابقة نفسها التي في الـ API، وتعرض لكل كلمة هدف لفظها وقسمها وجذرها ووزنها، والأطر التي تستدعيها بتعريفاتها وعناصرها، مع متصفّح لـ986 إطاراً.

## Scope and limits · الحدود

- Arabic lexical units cover **986 of 1,221 frames** (1,073 frames have English LUs). A word not found is *not covered*, not "frameless".
- 3,664 LUs whose root is a «مكمِّل» root are excluded (EVIDENCE_GAP); 4 candidates are deferred to the owner (`03_lus_ar/l2_017_deferred.csv`); 5 English LUs are TODO.
- Part of speech comes from a closed list of 17 (the layer2_v4 README says 16 — a known text error; `pos_ar_closed.txt` in the release is authoritative).
- LUs outside the 50 pilot frames were drafted by a small model and approved by the owner in one review pass; flags from the automatic checks are kept in the `note` column.
- No Arabic annotated sentences or valence patterns yet, so no semantic-role assignment to sentence spans.
- Frames describe event types; they are not rulings.
- Matching rules in the API (orthographic normalization, affix stripping) are marked as not yet ratified.

## Repository layout

```
00_source/     FrameNet 1.7 frames, frame elements, relations (English source) + LICENSE.txt
01_glossary/   approved Arabic terms (frame names, FE names, grammar terms, relation types) + APPROVAL_LOG.txt
02_frames_ar/  Arabic frame / FE definitions (working files)
03_lus_ar/     Arabic lexical units (working files), POS list, wazn inventory
release/       frozen, fingerprinted releases (layer1_v3, layer2_v4)
api/           afn_api.py — HTTP/CLI lookup API
scripts/       build, check, freeze scripts (06_check_lus.py is the LU checker)
```

## License and attribution · الترخيص والإسناد

- **FrameNet 1.7 data** (ICSI, Berkeley) is used under the **Creative Commons Attribution 3.0 Unported** license — see `00_source/LICENSE.txt`.
  This work is derived from FrameNet Release 1.7, http://framenet.icsi.berkeley.edu.
  Reference: Fillmore, C. J. and Baker, C. F. (2010). *A Frame Semantic Approach to Linguistic Analysis.* In Heine & Narrog (eds.), *The Oxford Handbook of Linguistic Analysis.* OUP.
- English lexical-unit definitions that FrameNet quotes from the Concise Oxford Dictionary (`definition_source = COD`) are **not included** (blanked in `03_lus_ar/lus_template.csv`).
- A third-party bilingual-dictionary column used during drafting has been removed from all published glossaries.
- Arabic additions (translations, Arabic lexical units, glossaries, scripts): © Hussein Hiyassat (RULE_OWNER = DR_HUSSEIN). License for these additions: to be declared by the owner.
