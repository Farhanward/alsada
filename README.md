# الصدى (AL-SADA) — AI Visibility & Reputation Engine (MVP: Monitoring)

اعرف ماذا تقوله محرّكات الذكاء الاصطناعي عن علامتك — قِسه، واكشف الفجوات والمعلومات الخاطئة.

هذا هو **MVP المراقبة** (المرحلة 1): يستجوب محرّكات الذكاء بمجموعة برومبتات «نيّة شرائية»، يحلّل الإجابات (ذكر العلامة، المنافسون، الاستشهادات، النبرة، المعلومات الخاطئة)، يحسب **درجة الظهور**، ويُصدر تقريراً.

## التشغيل السريع (بلا تكلفة — وضع mock)
```bash
cd C:\Projects\alsada
python -m alsada.cli run --engine mock
# يطبع ملخّصاً ويحفظ تقريراً في reports\
```

## المحرّكات المتاحة
`mock` (تجربة) · `ollama` (محلي مجاني) · `openai` (ChatGPT) · `anthropic` (Claude) · `perplexity` (بحث ويب) · `openrouter` (**مفتاح واحد لكل النماذج** + بحث ويب) · `file` (تحليل إجابات مجلوبة مسبقاً).

```bash
# محلي مجاني (Ollama)
set ALSADA_OLLAMA_URL=http://127.0.0.1:11434
python -m alsada.cli run --engine ollama --model qwen2.5:3b

# OpenAI (مدفوع)
set OPENAI_API_KEY=sk-...
python -m alsada.cli run --engine openai --model gpt-4o-mini

# Claude (مدفوع)
set ANTHROPIC_API_KEY=sk-ant-...
python -m alsada.cli run --engine anthropic --model claude-haiku-4-5-20251001

# Perplexity — يبحث في الويب فعلياً (الأكثر تمثيلاً لما يقوله الذكاء عنك)
set PERPLEXITY_API_KEY=pplx-...
python -m alsada.cli run --engine perplexity --model sonar

# OpenRouter — مفتاح واحد لكل النماذج (موصى): perplexity/sonar للبحث، أو أضف ':online' لأي نموذج
set OPENROUTER_API_KEY=sk-or-...
python -m alsada.cli run --engine openrouter --model perplexity/sonar
# أمثلة نماذج: openai/gpt-4o-mini:online  ·  google/gemini-2.0-flash-exp:online  ·  anthropic/claude-3.5-haiku

# file — حلّل إجابات حقيقية مجلوبة مسبقاً (مثلاً من محرّك يصعب الوصول إليه مباشرة)
set ALSADA_ANSWERS_FILE=C:\Projects\alsada\data\answers.jsonl
set ALSADA_ANSWERS_MODEL=qwen2.5:3b
python -m alsada.cli run --engine file
```

## التركيب
- `config/client.json` — ملف العميل (CarbonFlow): الأسماء، المنافسون، الحقائق المرجعية.
- `config/prompts.json` — برومبتات الاستجواب (+ إجابات mock واقعية للتجربة).
- `alsada/providers.py` — محوّلات المحرّكات (mock / ollama / openai).
- `alsada/analyze.py` — استخراج: ذكر، منافسون، استشهادات، نبرة، معلومات خاطئة.
- `alsada/score.py` — حساب درجة الظهور وحصّة الصوت.
- `alsada/report.py` — توليد تقرير ماركداون.
- `alsada/cli.py` — `probe` / `report` / `run`.

## الحلقة الكاملة (المرحلة 2)
```bash
# 1) قِس قبل النشر
python -m alsada.cli run --engine openrouter --model perplexity/sonar

# 2) ولّد أصول الظهور (llms.txt + schema + صفحات للمواضيع الغائبة)
python -m alsada.cli generate

# 3) انشر الأصول على موقعك (وعلى المصادر التي يقرؤها الذكاء)، ثم امنح النماذج أياماً لإعادة الزحف.

# 4) قِس بعد النشر
python -m alsada.cli run --engine openrouter --model perplexity/sonar

# 5) أثبت الحركة (قبل ← بعد)
python -m alsada.cli compare

# (بالتوازي) الرادار — استخبارات المنافسين: من يفوز، أي مصادر يثق بها الذكاء، وأين الفرص
python -m alsada.cli radar
```

## الرادار (GEO Competitive Intelligence)
يعمل بالتوازي دون انتظار إعادة الزحف. من أي تشغيل يستخرج:
- **ترتيب المنافسين** وحصّة الصوت.
- **المصادر التي يستشهد بها الذكاء** (المواقع المُوثوقة لديه — استهدفها بذكر/استشهاد).
- **الفرص:** لكل استعلام أنت غائب فيه: من تهزم وأين تنشر، مع توصية.

## الناشر (Publisher — آمن)
```bash
python -m alsada.cli publish   # يحوّل أهداف الرادار إلى خطة نشر مصنّفة
```
يصنّف كل قناة وينتج المحتوى/المسوّدات في `generated/publish/`:
- **مملوكة** → محتوى جاهز لموقعك/ملفاتك (نشر آلي).
- **تسجيل ذاتي مقصود** (Khamsat، أدلّة…) → مسوّدة ملف/خدمة حقيقية.
- **مكتسَبة** (Reddit، منتديات…) → مسوّدات قيمة **للمراجعة البشرية** (لا سبام).
- **منافِسة/مرجعية** → ليست هدف نشر؛ بدلها صفحة مقارنة على موقعك.
> القاعدة: **نكسب الاستشهاد بصدق** — لا نشر آلي على مواقع الغير.

## الاختبارات
```bash
python -m pytest -q   # أو:  python tests\test_pipeline.py
```

## آخر تحسين إنتاجي (2026-07-04)
- الاختبارات المحلية: `python tests\test_pipeline.py` => 11/11 ناجحة.
- صار كشف المنافسين يعتمد على مطابقة أسماء مضبوطة بدل احتواء نصي خام؛ لذلك لا تُحسب كلمة شائعة مثل `make` كمنافس إلا عند وجود إشارة علامة حقيقية مثل `Make` أو `make.com`.
- صار إثبات الاستشهاد بالعميل يعتمد على تحليل نطاق الرابط (`host`) لا على احتواء النص؛ لذلك لا يُقبل رابط مزيف مثل `notcarbonflows.store.example` كاستشهاد لـ `carbonflows.store`.

## آلية العمل المختصرة
1. `run` يرسل برومبتات النية الشرائية إلى محرك AI (`mock`, `ollama`, `openai`, `anthropic`, `perplexity`, `openrouter`, أو `file`).
2. `analyze.py` يستخرج من كل إجابة: هل ذُكر العميل، النبرة، المنافسون، الاستشهادات، وأي ادعاء خطر مثل التسعير أو أن العلامة متوقفة.
3. `score.py` يحسب درجة ظهور لكل إجابة ثم يجمعها إلى حصة صوت، متوسط ظهور، إجابات غائبة، وسلبيات/تنبيهات.
4. `generate` ينتج أصول GEO مثل `llms.txt` و`schema.jsonld` وصفحات مواضيع غائبة.
5. `compare`, `radar`, و`publish` تغلق الحلقة: إثبات التحسن قبل/بعد، معرفة أين يظهر المنافسون، وتحويل الفرص إلى مسودات نشر آمنة.

المعمارية الكاملة في: `C:\Users\FARHAN\AI_PROJECTS_REFERENCE\DESIGN_ALSADA.md`

## التشغيل المؤسسي (Enterprise) — v1.0.0

- **خدمة GEO عبر HTTP**: `python -m alsada.cli serve` → `GET /api/client` و`POST /api/analyze {"answer"}` (نفس محرك التحليل المستخدم في القياس).
- **قرار أمني**: الاستجواب الحي (`run/probe`) عبر CLI فقط — الخدمة لا تستهلك مفاتيح مزودين خارجيين.
- **نقاط فحص**: `/api/health` (مفتوح) · `/api/version` · `/api/metrics` (p50/p95/p99).
- **تهيئة عبر البيئة**: متغيرات `ALSADA_*` — انظر `docs/OPERATIONS.md`.
- **مصادقة**: `ALSADA_API_KEY` → ترويسة `X-API-Key`. **سجلات JSON**: `logs\alsada.service.jsonl`. **سجل التغييرات**: `CHANGELOG.md`.
