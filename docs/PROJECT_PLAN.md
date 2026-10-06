# arabic-net / FrameNet — خطة التعريب

RULE_OWNER = DR_HUSSEIN. الوكيل ينفّذ ويقيس؛ المصطلح والقرار من المالك.

## المصدر
FrameNet 1.7 عبر `nltk framenet_v17` — frames=1221 FEs=11428 (distinct_names=1285, core=3501) relations=2070 (10 types) LUs=13572.
حجم تعريفات الطبقة الأولى ≈ 331k كلمة إنجليزية.

## البنية
```
00_source/     frames.jsonl fes.jsonl relations.jsonl   (scripts/01)
01_glossary/   fe_glossary.tsv (1285) frame_names.tsv (1221) relation_types.tsv (10)
02_frames_ar/  التعريفات المعرَّبة (المرحلة 2)
03_lus_ar/     مرشحو الوحدات المعجمية (المرحلة 4)
04_corpus_ar/  الجمل العربية الموسومة (المرحلة 5)
scripts/       01_extract_layer1.py  02_macdict_lookup.py  03_agent_translate_defs.py
```

## البوابات
- G0.1 LICENSE: تأكيد ترخيص FN 1.7 من ICSI وحفظ نسخة هنا.
- G0.2 MAC_DICT: تشغيل scripts/02 يطبع القواميس المثبتة؛ سجّل اسم القاموس العربي المستخدم.
- G0.3 KEY: المفتاح = frame_id / fe_id الرقمي، لا الاسم.
- GATE_1: كل صف في fe_glossary.tsv له owner_choice و status=APPROVED — scripts/03 يرفض التشغيل قبل ذلك.
- GATE_2: تجربة 50 إطاراً يختارها المالك؛ يُقاس accepted/rejected/glossary_violations؛ عتبة القبول من المالك.

## أعمدة fe_glossary.tsv
fe_name | freq | sample_frame | sample_definition | mac_dict_candidate (scripts/02) | claude_draft (مقترح) | owner_choice (المعتمد) | status (PROPOSED→APPROVED)

## أزواج تحتاج قرار المالك (قاموس عام لا يفصل بينها)
Theme/Topic · Source/Origin · State/Situation/State_of_affairs · Agent/Actor · Judge/Evaluator/Assessor · Location/Place/Locale · Reason/Explanation/Cause · Part/Piece/Portion/Component

## ما هو خارج صلاحية الوكيل (STOP / OWNER_ALERT)
إنشاء مصطلح غير موجود في المعجم · إنشاء إطار أو تعديله · الانتماء النهائي لأي وحدة معجمية · تعديل هذا الملف.
