# CONTINUE_005 — جولة واحدة بلا إشراف على المتن الكامل (تُستدعى من scripts/run_until_done.sh full …)

البيئة تحدد النطاق: FRAMES_FILE=02_frames_ar/all_frames.txt و OUT_PREFIX=full مضبوطان من المشغِّل. الملفات المكتوبة هي full_frames_ar.jsonl و full_fes_ar.jsonl (لا pilot_*).

أنت في جلسة جديدة بلا مالك حاضر. لا تسأل، لا تنتظر رداً، لا تعرض خيارات. كل ما لا تحسمه القواعد أدناه → اكتب STOP_<سبب> في التقرير وانهِ الجلسة.

════════════════════════════════════════════
0. الدستور
════════════════════════════════════════════
- المالك DR_HUSSEIN؛ أنت تنفّذ وتقيس. الحكم بالسبب/الشرط/المانع: ACCEPT/DEFER/BLOCK.
- فجوة قواعد → STOP / NO_INFERENCE. لا قاعدة جديدة، لا استثناء، لا اختيار بين بدائل.
- MEASURED_NOT_PRESET: الأرقام من الفاحص فقط.
- محظور التعديل: 00_source/*، 01_glossary/fe_glossary.tsv، grammar_glossary.tsv، relation_types.tsv، frame_names.tsv، APPROVAL_LOG.txt، README.md، *.md، scripts/*، pilot_frames.txt، logs/*.
- مسموح الكتابة فقط: 02_frames_ar/full_frames_ar.jsonl، full_fes_ar.jsonl، 01_glossary/names_map.tsv. ملفات pilot_* محظورة (مرجع معتمد).

════════════════════════════════════════════
1. حراس الجلسة غير المُشرَفة (تُفحص أولاً)
════════════════════════════════════════════
- إن لم يوجد الملف 02_frames_ar/GATE_2_CLOSED → اطبع STOP_GATE2_OPEN وانهِ فوراً.
شغّل python3 scripts/04_check_pilot.py مرة واحدة (البيئة مضبوطة من المشغِّل؛ لا تغيّرها).
- إن لم يُطبع GATE_1 = CLOSED → اطبع STOP_GATE1 وانهِ.
- إن انهار الفاحص → اطبع STOP_CHECKER_CRASH مع آخر سطر خطأ وانهِ.
- إن frames_missing = 0 و fes_missing = 0 → اطبع DONE_NOTHING_TO_DO وانهِ.
- إن rejected > 0 قبل أن تكتب شيئاً → لا تصلح ما لم تكتبه أنت؛ اطبع STOP_PREEXISTING_REJECTS=<n> وانهِ.

════════════════════════════════════════════
2. القواعد النافذة
════════════════════════════════════════════
RULE_GLOSS: اسم عنصر يرد في الإنجليزية وهو عنصر في الإطار الحالي → owner_choice من fe_glossary.tsv حصراً.
RULE_TERM: المصطلح برسمه كاملاً. مسموح قبله و/ف/ب/ك. ممنوع لام الجر والإضافة المُسقِطة لـ«ال». التعريف بـ«ال» مقابل نكرة الأصل مقبول.
GRAMMAR: الوظائف النحوية حصراً من grammar_glossary.tsv: External Argument=الحجة الخارجية · Complement=المتمّم · PP Complement(s)=متمّم حرف الجر · Object=المفعول به · direct object=المفعول به المباشر · Dependent(نحوي)=المتعلِّق · Target/target=الكلمة الهدف · Genitive=المضاف إليه · Head noun=الاسم الرأس · Modifier=المعدِّل · Support verb=الفعل المساند · Null instantiation=التحقيق الصفري · DNI=التحقيق الصفري المحدَّد · INI=التحقيق الصفري غير المحدَّد · CNI=التحقيق الصفري التركيبي · Predicative use=الاستعمال الإسنادي · Attributive use=الاستعمال النعتي · Frame Element=عنصر الإطار.
RULE_FIDELITY: لا زيادة ولا حذف ولا تلخيص ولا شرح. «وهو/وهي + مصطلح» فقط مقابل بدل/عطف بيان في الأصل.
RULE_EX (v2): المثال العربي أولاً بلا علامات، ثم الأصل الإنجليزي بين ( )؛ أقواس داخلية → “ ”. لا «أي» رابطةً، لا « ».
RULE_NAMES: الأعلام من names_map.tsv برسم واحد؛ الجديد يُلحق قبل الاستعمال؛ لا استبدال بأسماء عربية.
RULE_FRAMENAME: ترجمة معنى اسم الإطار ثم الاسم الإنجليزي بين ( ).
RULE_LATIN: لا لاتيني خارج أسماء الأطر بين ( )، والأمثلة، والأدوات المشار إليها مثل (to).
RULE_EMPTY: definition_en فارغ → لا سجل.
RULE_NATURAL: «أي» بمعنى which والروابط الطبيعية تبقى.

════════════════════════════════════════════
3. صيغة السجلات
════════════════════════════════════════════
إطار: السجل الأصلي من frames.jsonl + "definition_ar" + "status":"DRAFT".
عنصر: السجل الأصلي من fes.jsonl + "definition_ar" + "status":"DRAFT".
سطر JSON لكل سجل، ensure_ascii=False، إلحاق فقط، لا تكرار معرّف.

════════════════════════════════════════════
4. الإجراء
════════════════════════════════════════════
1. اقرأ مرة واحدة: fe_glossary.tsv (fe_name, owner_choice)، names_map.tsv. لا غيرهما.
2. خذ next_frames_missing من الفاحص.
3. دفعات من 3 أطر: ترجم، ألحق، الفاحص مرة للدفعة.
4. rejected>0 → أصلح في حدود المسموح (استبدال مصطلح، إكمال نقص، إزالة لاتيني مخالف)، احذف القديم وأضف المصحَّح، أعد الفاحص. إن بقي مرفوضاً بعد محاولتين → اتركه، سجّله، تابع.
5. بعد كل دفعة سطر واحد: <ids> fes=<n> rejected=<n>.
6. الهدف: 10 أطر في الجلسة أو حتى frames_missing=0. لا توقف اختياري قبل ذلك؛ التوقف فقط عند عجز السياق فعلاً.
7. ضيق السياق أثناء إطار → ألحق ما اكتمل سجلاً سجلاً وتوقف.
8. لا مذكّرة ذاكرة، لا تعليق، لا سؤال.

════════════════════════════════════════════
5. التقرير (آخر شيء تطبعه، سطر أول ثابت)
════════════════════════════════════════════
ROUND_STATUS = OK | STOP_<reason>
PHASE          = 3 / full (agent-direct, unattended)
GATE_1         = CLOSED|FAILED
frames_in / frames_done / frames_ok / frames_missing = <n>/<n>/<n>/<n>
fes_in / fes_done / fes_ok / fes_missing             = <n>/<n>/<n>/<n>
source_empty   = <n>
rejected       = <n>  glossary_violation=<n> empty_or_short=<n> latin_leak=<n>
extra_or_dup   = <n>
frames_this_session = <n> (<ids>)
names_added_this_session = <n>
sha256 full_frames_ar.jsonl = <…>
sha256 full_fes_ar.jsonl    = <…>
sha256 full_rejected.jsonl  = <…>
sha256 names_map.tsv         = <…>
remaining_ids  = <…>
owner_items    = <سطر لكل STOP أو سجل مرفوض باقٍ أو قرار يستحق النظر؛ أو NONE>
