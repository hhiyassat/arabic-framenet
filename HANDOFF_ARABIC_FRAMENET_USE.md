# HANDOFF — استعمال Arabic FrameNet (للوكيل المستهلِك)

RULE_OWNER = DR_HUSSEIN · كُتب 2026-10-05 · يُقرأ كاملاً قبل أي استعمال.
المالك يشرّع؛ الوكيل ينفّذ ويقيس. هذا الملف يصف **كيف تُقرأ** الإصدارات، لا كيف تُعدَّل.

---

## 0. الحكم الدستوري (يسري على كل استعمال)

- كل قرار يُوزن بـ **السبب / الشرط / المانع** → ACCEPT / DEFER / BLOCK. DEFER ≠ BLOCK.
- فجوة قواعد → **STOP / OWNER_ALERT / NO_INFERENCE**: لا قاعدة جديدة، لا استثناء، لا اختيار بين بدائل نيابةً عن المالك.
- **MEASURED_NOT_PRESET**: كل رقم يُقاس من تشغيل فعلي. يُذكر ما لم يُنجز صراحةً.
- لا يُعلن `FULL_TESTS_PASS=YES` مع أي إخفاق في الشجرة كلها.
- `CORROBORATION_NEVER_RAISES_RANK` · `SKELETON_MATCH_IS_NOT_A_ROOT_PROOF`.

---

## 1. أين يقع

```
PROJECT = /Users/husseinhiyassat/arabic-net/FrameNet/FrameNet
اقرأ فقط من:
  release/layer1_v3/   الأطر وعناصرها وعلاقاتها (عربي)          MANIFEST sha256 = 84c69ebbd0c125c2792d97b1f7b941c162d2dd6dd3dce433a72bdcd53c589cc1
  release/layer2_v2/   الوحدات المعجمية العربية (50 إطاراً)       MANIFEST sha256 = a79899005837802c0afb004fb9f87502d2f058a553a08082216cad545d7a4a99
```

- `layer1_v3` = `layer1_v2` بلا عمود `mac_dict_candidate` (معجم طرف ثالث)؛ استعمل v3.
- `layer1_v1` و`layer2_v1` مطابقان في المحتوى بايتاً ببايت لكنهما **بلا ترخيص** (`license_verified=false`) — لا تستعملهما للتوزيع.
- `02_frames_ar/` و`03_lus_ar/` و`scripts/` ملفات عمل للمالك، **ليست واجهة استهلاك**. لا تقرأ منها نتائج نهائية.
- الإصدارات **غير قابلة للتعديل**. أي تصحيح = وسم جديد (`layer2_v3`…) بقرار المالك. الوكيل المستهلِك لا يكتب في `release/` أبداً.

---

## 2. التحقق قبل الاستعمال (إلزامي، وإلا STOP)

```python
import hashlib, json, pathlib
REL = pathlib.Path("/Users/husseinhiyassat/arabic-net/FrameNet/FrameNet/release")
PIN = {"layer1_v3": "84c69ebbd0c125c2792d97b1f7b941c162d2dd6dd3dce433a72bdcd53c589cc1",
       "layer2_v2": "a79899005837802c0afb004fb9f87502d2f058a553a08082216cad545d7a4a99"}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for tag, h in PIN.items():
    d = REL / tag
    assert sha(d / "MANIFEST.json") == h, f"STOP: {tag} MANIFEST changed"
    m = json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))
    bad = [f for f, fh in m["files"].items() if sha(d / f) != fh]
    assert not bad and m["license_verified"] is True, f"STOP: {tag} {bad}"
print("VERIFIED")
```

---

## 3. الطبقة الأولى — `release/layer1_v3/`

| الملف | المحتوى | المفتاح |
|---|---|---|
| `frames_ar.jsonl` | 1221 إطاراً: `frame_id, name, name_ar, definition_en, definition_ar, fe_names, lu_count, status` | `frame_id` |
| `frame_elements_ar.jsonl` | 11416 عنصراً: `fe_id, frame_id, frame, name, name_ar, core_type, sem_type, definition_en, definition_ar, status` | `fe_id` |
| `frame_relations.jsonl` | 2070 علاقة: `rel_id, type, super_frame_id, sub_frame_id, super, sub, type_ar, super_ar, sub_ar` | `rel_id` |
| `fe_glossary.tsv` | 1285 اسم عنصر → `owner_choice` (العربي المعتمد) | `fe_name` |
| `frame_names.tsv` | 1221 اسم إطار → `owner_choice` | `frame_id` |
| `relation_types.tsv` | 10 أنواع علاقات (Inheritance=الوراثة …) | `relation_type` |
| `grammar_glossary.tsv` | 17 مصطلحاً نحوياً (DNI، External Argument …) | `term` |
| `names_map.tsv` | 2044 اسم علم ورد في التعريفات | `en` |

- **المفاتيح أرقام FrameNet 1.7** (`frame_id`, `fe_id`, `lu_id`). الأسماء العربية **تسميات لا مفاتيح**.
- 12 عنصراً تعريفها الإنجليزي فارغ في المصدر مستبعدة عمداً (`fe_count` في المصدر أكبر بها).
- 7 أسماء عربية مشتركة بين إملاءين إنجليزيين لاسم واحد (Traveler/Traveller …) — مقصودة.
- عمود `mac_dict_candidate` (معجم طرف ثالث) محذوف في v3؛ استعمل `owner_choice`.

---

## 4. الطبقة الثانية — `release/layer2_v2/`

### 4.1 `lus_ar.csv` — 2641 وحدة عربية، كلها `status=APPROVED`

| العمود | المعنى |
|---|---|
| `ar_lu_id` | معرّف داخلي ثابت `AR#####` |
| `lemma_ar` | اللفظ مضبوطاً (الفعل ماضٍ مفرد مذكر؛ الاسم مفرد بلا تنوين ولا ال) |
| `pos_ar` | من القائمة المغلقة (16) في `pos_ar_closed.txt` |
| `frame_id` | إطار الطبقة الأولى |
| `en_lu_ids` | وحدات FrameNet الإنجليزية المقابلة، مفصولة بـ `;` — **قد يكون فارغاً** (وحدة عربية بلا مقابل) |
| `definition_ar` | تعريف عربي مستقل |
| `root` | الجذر بحروفه (الهمزة ء)؛ فارغ للتركيب/الحرف/المبني/الدخيل |
| `wazn` | من مخزون الأوزان المعتمد (`wazn_nouns_inventory.csv` للأسماء، أوزان الأفعال الـ 37 + 3 للمالك) |
| `wazn_note` | وصف حين لا يكون للفظ وزن في المخزون (2 فقط: مثنى، مصدر صناعي) |
| `evidence_primary` | **مؤشر** `roots-4662:<جذر>:المحكم — المعاني` أو `v21:<جذر>:…` — ليس نصاً |
| `evidence_frame_level` | مؤشر إلى مقاييس اللغة (المحور، وإلا النص) — يرشّح الإطار الأم فقط |
| `metaphor_flag` | مؤشر إلى «الأساس — المجاز» للجذر — **وجود مدخل مجاز للجذر، لا حكم بأن الوحدة مجازية** |
| `owner_choice` | = `lemma_ar` بتفويض المالك (OWNER_DELEGATION_L2_001) |
| `note` | علامات القرارات (L2_005 … L2_015، POS_L2_007:X …) |

**المفتاح الفريد** = `(lemma_ar, pos_ar, frame_id)`. اللفظ الواحد في إطارين = وحدتان.

### 4.2 `lus_en_status.csv` — 4007 وحدة إنجليزية في الأطر الخمسين

| الحالة | العدد | المعنى |
|---|---|---|
| `MAPPED` | 3023 | لها وحدة عربية معتمدة واحدة على الأقل |
| `NO_ARABIC_EQUIVALENT` | 243 | لا لفظ عربي طبيعي في هذا الإطار — حالة مشروعة، **لا تخترع مقابلاً** |
| `EVIDENCE_GAP_ONLY` | 741 | لها مقابل عربي لكنه مستبعد من الإصدار (جذر «مكمِّل»، قرار D2) |

`en_lu_id` = `lu_id` في FrameNet 1.7. اللفظ الإنجليزي ليس في الإصدار؛ مصدره القالب `03_lus_ar/lus_template.csv` (sha256 `5616d5fa…`) أو FrameNet 1.7 نفسها.

### 4.3 ملفات القواعد المرافقة

`pos_ar_closed.txt` (16 قسماً) · `pos_glossary.tsv` (وسوم FN الإنجليزية → عربي) · `wazn_nouns_inventory.csv` (941 وزناً مع مصدر كلٍّ) · `wazn_owner_l2_015.csv` · `wazn_rules.py` (مطابقة الأوزان: `key()`) · `root_alert_waived.txt` (12 جذراً بلا مصدر أعفاها المالك) · `v21_roots_index.csv` · `06_check_lus.py` (المدقّق كما جُمِّد) · `APPROVAL_LOG.txt` (كل القرارات).

---

## 5. حدود الاستعمال (BLOCK إن خولفت)

1. **frame ≠ ruling**: الإطار يصف نوع حدث، لا حكماً شرعياً ولا قانونياً. لا تستنتج حكماً من إطار.
2. **لفظ عربي → إطار** يُسمح به **فقط** عبر وحدة `APPROVED` في `layer2_v2/lus_ar.csv`. لا ربط من الجذر وحده (الجذر يتوزع على أطر كثيرة)، ولا من تشابه الهيكل (`SKELETON_MATCH_IS_NOT_A_ROOT_PROOF`).
3. **التغطية 50 إطاراً فقط** من 1221 (قائمة `02_frames_ar/pilot_frames.txt`). غياب اللفظ ≠ عدم انتمائه للإطار؛ في الأطر الأخرى النتيجة = `NOT_COVERED` لا «لا يوجد».
4. **EVIDENCE_GAP** (1307 وحدة) ليست في الإصدار؛ لا تستعملها ولا تستعِد قيمتها من ملفات العمل.
5. **evidence_* مؤشرات**: لاسترجاع النص اقرأ المصدر المجمَّد بالبصمة عبر وسيط؛ **لا تنسخ المصادر داخل المشروع ولا تعدّلها**:
   - `roots-4662-meaning.csv` sha256 `1a711ffe9cc3286d87276b04a836b26756b67f3657f8a0904a0c7b4ac4d020da`
   - `v21-معاني-حسب-الحرف/README.json` sha256 `ab0d42b4b205ee460bc3c4331e3c4fffe032c19c56d7a8a8f593cd5ca97e735d`
   - (كلاهما في `/Users/husseinhiyassat/hokom-local-validation/taaqol-executor-wt/data/`)
6. **الجذر**: مطابقة الجذور بمفتاح K (أإآؤئء→ء، ى→ي). التحاق جذر بمصدر لا يرفع رتبته (`CORROBORATION_NEVER_RAISES_RANK`).
7. **التعريفات**: `definition_ar` في الطبقة الثانية مستقلة (لا ترجمة لتعريفات COD/أكسفورد). تعريفات COD الإنجليزية ملك OUP: لا تُترجم ولا يُعاد نشرها.
8. **الترخيص**: بيانات FrameNet 1.7 تحت CC BY 3.0 Unported (`LICENSE.txt`). أي منتج/خدمة يجب أن يذكر FrameNet ورابطها `http://framenet.icsi.berkeley.edu` والمرجع Fillmore & Baker (2010).
9. **Hokom/Taaqol**: FrameNet مخزون خانات (slot inventory) فقط؛ الربط بالأحكام ممنوع.

---

## 6. وصفات استعمال

```python
import csv, json, pathlib, collections
R = pathlib.Path("/Users/husseinhiyassat/arabic-net/FrameNet/FrameNet/release")
frames = {j["frame_id"]: j for j in map(json.loads, open(R/"layer1_v3/frames_ar.jsonl", encoding="utf-8"))}
fes = collections.defaultdict(list)
for j in map(json.loads, open(R/"layer1_v3/frame_elements_ar.jsonl", encoding="utf-8")): fes[j["frame_id"]].append(j)
lus = list(csv.DictReader(open(R/"layer2_v2/lus_ar.csv", encoding="utf-8")))

# (أ) لفظ عربي → أطره (بالمطابقة التامة للفظ المضبوط؛ لا تطبيع ولا تخمين)
def frames_of(lemma):
    return [(r["ar_lu_id"], r["pos_ar"], frames[int(r["frame_id"])]["name_ar"]) for r in lus if r["lemma_ar"] == lemma]

# (ب) إطار → وحداته العربية وخاناته (عناصره)
def frame_card(frame_id):
    f = frames[frame_id]
    return {"name_ar": f["name_ar"], "lus": [r["lemma_ar"] for r in lus if int(r["frame_id"]) == frame_id],
            "core": [e["name_ar"] for e in fes[frame_id] if e["core_type"] == "Core"],
            "non_core": [e["name_ar"] for e in fes[frame_id] if e["core_type"] != "Core"]}

# (ج) جذر → وحدات (للعائلة الاشتقاقية فقط؛ ليس دليلاً على إطار)
def lus_of_root(root): return [(r["lemma_ar"], r["pos_ar"], r["frame_id"]) for r in lus if r["root"] == root]
```

- البحث بلفظ غير مضبوط أو بصيغة مصرّفة: **ليس من وظيفة هذا الإصدار** (لا محلل صرفي مدمج). إن احتجت تطبيعاً فهو قرار مالك جديد → STOP / OWNER_ALERT.
- نتيجة فارغة = `NOT_FOUND_IN_RELEASE`، وليست «لا إطار له».

---

## 7. ما لم يُنجز (صريحاً)

- 1171 إطاراً بلا وحدات عربية (لا توسّع قبل قرار المالك).
- لا جمل معلَّمة ولا أنماط تكافؤ (valence) عربية.
- اختيار الألفاظ والتعريفات مرشَّح آلياً ومعتمد بتفويض المالك بعد مراجعته؛ لم يُقَس مقابل مدوّنة.
- 149 وحدة دليلها من v21 لا من roots-4662؛ 16 وحدة بلا دليل (معفاة بقرار L2_012).
- قرار D2 (استبعاد الجذور «المكمِّلة») قابل لإعادة النظر من المالك فقط → وسم جديد.

## 8. خط القرارات

كل قرار مرقّم في `release/layer2_v2/APPROVAL_LOG.txt` (OWNER_DECISION_L2_001 … L2_016، OWNER_REVIEW_L2_001، OWNER_DELEGATION_L2_001).
قرارات ما بعد التجميد (LAYER2_FROZEN، G0.1، RELEASES_RELICENSED، LAYER1_CHECK_FULL) في `01_glossary/APPROVAL_LOG.txt`.
