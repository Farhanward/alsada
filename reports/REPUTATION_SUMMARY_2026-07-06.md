# تقرير سمعة CarbonFlow في محرّكات الذكاء (الصدى) — 2026-07-06

**المحرّكات:** ChatGPT (`openai/gpt-4o:online`) + Gemini (`google/gemini-2.5-flash:online`) — كلاهما ببحث ويب حيّ عبر OpenRouter.
**العملاء المستهدَفون بالاستعلامات:** أصحاب أعمال، مؤسّسو شركات، مدراء تسويق — أسئلة نية شرائية عن الأتمتة/الذكاء في السعودية والخليج.

## النتيجة (قياس حقيقي)
| المحرّك | درجة الظهور | حصة الصوت | غير مرئيّ في | تنبيهات معلومات خاطئة |
|---|---|---|---|---|
| **ChatGPT** | 22.8 / 100 (ضعيف) | 60% | 7 / 10 | 0 |
| **Gemini** | 23.0 / 100 (ضعيف) | 30% | 7 / 10 | 1 |

## الخلاصة الحاسمة
- **CarbonFlow غير مرئيّ في كل أسئلة الاكتشاف** (أفضل شركة أتمتة، من يقدّم n8n/Cloudflare/SaaS/لوحات تحكم، بدائل Zapier، أفضل الوكالات لعام 2026). تظهر فقط حين يذكرها السائل بالاسم مباشرة.
- **المنافسون يهيمنون على مكانك:** حين تسأل ChatGPT/Gemini «أفضل شركة أتمتة AI في السعودية» يوصيان بـ **EIBSOL** و**Make** و**n8n** و**Zapier** — لا CarbonFlow.
- **الرادار:** 43 مصدراً يستشهد بها الذكاء (مواقع/أدلّة يجب إدراج CarbonFlow فيها)، وأعلى منافس Make، و7 فرص ظهور غائبة.
- Gemini سجّل **تنبيه معلومة خاطئة** واحد عن العلامة.

## آلية رفع السمعة (أصول GEO المولّدة — جاهزة)
`C:\Projects\alsada\generated\`:
- `llms.txt` — بطاقة تعريف CarbonFlow لمحرّكات الذكاء (وصف + لماذا + مناطق + الموقع الرسمي).
- `schema.jsonld` — Structured Data ليفهم الذكاء هويتك وخدماتك.
- `pages\*.md` — 7 صفحات «إجابة مباشرة» لكل موضوع غائب (ai_automation, n8n, cloudflare, saas, dashboards, alternative, top_agencies)، مصاغة ليقتبسها الذكاء ويذكر CarbonFlow.

## الخطوة التي ترفع السمعة فعلاً
نشر هذه الأصول على `carbonflows.store` (llms.txt + schema + الصفحات) ⇒ يبدأ ChatGPT/Gemini بإيجاد CarbonFlow واقتباسه في أسئلة الاكتشاف. ثم `alsada compare` يثبت الحركة قبل/بعد.

## التشغيل (بعد الضبط)
```
cd C:\Projects\alsada
python -m alsada.cli probe --engine chatgpt   # قياس على ChatGPT (ببحث ويب)
python -m alsada.cli probe --engine gemini     # قياس على Gemini
python -m alsada.cli report                    # تقرير آخر تشغيل
python -m alsada.cli radar                      # منافسون + مصادر + فرص
python -m alsada.cli generate                   # توليد أصول GEO
```
الإعداد في `.env.local` (مفتاح OpenRouter يخدم المحرّكين). لاستخدام مفتاح Gemini أصلي مجاني: ضع `GEMINI_API_KEY` من https://aistudio.google.com/apikey فيصبح محرّك `gemini` أصلياً تلقائياً.
