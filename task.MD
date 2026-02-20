у меня есть задача - есть текст скачанных сайтов в MD формате (snapshot.md) - заголовки, ссылки, таблицы, несколько страниц. 
Мне надо сделать новый дизайн сайта (только html/css/inline js) чтобы этот сайт содержал всю текстовую информацию из snapshot.md
Чтобы обрабатывать сотни (возможно тысячи)сайтов.  Как бы ты это сделал?

я хочу запускать инстанс сервиса на Vast.ai, там в шаблоне есть возможность указывать стартап скрипт и подтягивать переменные окружения. 
Сам код сервиса и если понадобится snippets HTML кода я хочу хранить в публичном репе Гитхаба. Также у меня есть HF_TOKEN если он нужен для скорости скачивания моделей

Я готов развернуть на Vast.ai GPU какую-то open source модель. 
например Qwen2.5-Coder-32B   2× A100 40GB (или если надо 80GB)

пример использования сервиса -
```
snapshot_text = read_snapshot_text(
    r"D:\Work\ML\Rix_sites\SiteSnpashot\out-text\www.appleseedwealth.com\snapshot.md"
)

job = requests.post(f"{BASE_URL}/start", json={"snapshot": snapshot_text})
assert job.ok, job.text

website_id = job.json()["website_id"]
print(f"Job started: {website_id}")

# 2. Поллить статус
while True:
    status = requests.get(f"{BASE_URL}/status/{website_id}").json()
    print(f"Status: {status['status']}")
    if status["status"] == "done":
        break
    time.sleep(10)

# 3. Скачать результат
response = requests.get(f"{BASE_URL}/download/{website_id}")
assert response.ok

with open(f"{website_id}.zip", "wb") as f:
    f.write(response.content)

print(f"Downloaded: {website_id}.zip")
```
также нужна админка - смотреть сколько и каких сайтов сделали, какие можно скачать (эти zip хранятся локально) и чтобы была возможность удалить zip.


Ниже - просто мои идеи. Это не догмы - Проанализируй их критически и оставь то, что нужно для качественного решения задачи.

Сгенерированные сайты не должны быть однотипными (но должны содержать в уместных местах сайта 3 обязательных элемента - 
- раздел новостей и брифинг
- Поиск плана
- Стратегии плана
).

Derive стиль из контента
python# В промпте:
"""
Before designing, analyze the content and determine:
- Industry/niche of this website
- Target audience  
- Emotional tone (professional/fun/urgent/calm)
Then choose a design that fits. Do NOT use generic blue corporate style.
"""
или что-то такое - # Генерируй "дизайн-бриф" детерминировано от домена сайта, Но обязательно учитывать Industry Домен. 
(Сайт финтека не должен быть в стиле форума сноубордеров)

import hashlib

styles = ["minimalist brutalist", "warm editorial", "dark tech", 
          "playful colorful", "luxury minimal", "corporate clean",
          "retro 90s web", "glassmorphism", "earthy organic"]

layouts = ["asymmetric grid", "full-width sections", "magazine layout",
           "single column editorial", "bento grid"]

typography = ["large expressive headings", "tight monospace", 
              "serif editorial", "system font stack"]

def get_design_seed(site_id: str) -> dict:
    h = int(hashlib.md5(site_id.encode()).hexdigest(), 16)
    return {
        "style": styles[h % len(styles)],
        "layout": layouts[h % len(layouts)],
        "accent_hue": h % 360  # HSL hue
    }
```

Один и тот же сайт всегда получит одинаковый дизайн, но разные сайты — разные.

## Самый эффективный промпт против однотипности
```
You are a creative web designer. Each website you create must look 
DISTINCTLY DIFFERENT from a typical template.

Rules:
- Analyze the content industry and audience first
- Choose a design direction that feels native to that industry  
- NEVER use generic blue (#3B82F6) as primary color unless it fits
- Vary the layout structure: not every section needs to be centered text + image
- Use unexpected but tasteful color combinations
- Make the hero section unique: full-screen video bg / split layout / 
  oversized typography / illustration — pick what fits

Current design constraints: {random_style_from_seed}

Подключай CDN библиотеки в генерируемом HTML:
html<!-- Tailwind для стилей -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Или готовые UI компоненты -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.css">
```
Добавляй Alpine.js если нужна интерактивность (план-оптимайзер и т.д.):
html<script src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js"></script>

**2. В системном промпте явно указывай стек:**
```
Use Tailwind CSS via CDN for styling. 
Use modern design: gradients, cards with shadows, 
smooth hover effects, responsive grid layout.
Color scheme: derive from the site's industry/content.

В итоговом дизайне (пока мы делаем в основном сайты финтек компаний, поэтому там эти разделы уместны) должны быть разделы:

1) Новостей и брифинга (код HTML дан просто для примера)
GET https://{site}/api/get-news
{
  "success": true,
  "articles": [
    {
      "id": 148,
      "title": "Case of the Week: ADP Failures and Roth Catchups",
      "summary": "Recordkeeper errors like ADP's in implementing mandatory Roth catch-ups highlight operational vulnerabilities ahead of 2026 deadlines. Sponsors bear fiduciary responsibility for vendor oversight, risking DOL penalties and participant harm from failed contributions. Conduct vendor audits and contingency planning to ensure seamless compliance transitions.",
      "source": "NAPA-Net",
      "url": "https://www.napa-net.org/news/2026/2/case-of-the-week-adp-failures-and-roth-catchups/",
      "date": "2026-02-11",
      "tag": "Compliance",
      "createdAt": "20260211055251"
    },
    {
      "id": 147,
      "title": "Judge Allows 401(k) Forfeiture Complaint Against Illinois Tool Works to Proceed",
      "summary": "A court ruling permits a 401(k) forfeiture class action against Illinois Tool Works to advance, heightening scrutiny on escheatment and forfeiture practices. Plan sponsors face elevated fiduciary risks and potential costs from similar suits alleging improper handling of unclaimed accounts. Immediate review of forfeiture policies and compliance with state escheat laws is essential to minimize liability.",
      "source": "PLANSPONSOR",
      "url": "https://www.plansponsor.com",
      "date": "2026-02-11",
      "tag": "Litigation",
      "createdAt": "20260211055251"
    },
....
  ],
  "briefing": {
    "id": 25,
    "generatedDate": "Feb 11, 2026",
    "keyTakeaways": "Plan sponsors face a pivotal 2026 with mandatory Roth catch-up contributions reshaping plan designs and operations, demanding immediate compliance reviews to avoid contribution barriers for higher-income workers. Litigation risks escalate from court advancements in forfeiture cases like Illinois Tool Works and recordkeeper failures such as ADP's, alongside EBSA's sponsor-friendly shifts in pleading standards. Emerging market pressures for private markets and guaranteed income solutions introduce fiduciary challenges around illiquidity, participant satisfaction, and decumulation security.\n\nFiduciaries must prioritize vendor oversight and documentation to counter heightened scrutiny, while evaluating income-focused options like annuities in target-date funds to meet participant demands amid equity concentration risks. These developments signal a more complex regulatory landscape, balancing innovation opportunities with amplified legal and operational costs. Proactive engagement with legal experts and recordkeepers will be crucial to mitigate exposures.",
    "actionItems": "[\"**Compliance Review:** Audit 401(k) plans for Roth availability and update designs for mandatory catch-up rules by Q1 2026.\", \"**Litigation Prep:** Review forfeiture and escheatment policies in light of recent court rulings and strengthen fiduciary documentation.\", \"**Vendor Audit:** Assess recordkeepers for operational readiness on Roth catch-ups and error resolution protocols.\", \"**Income Evaluation:** Survey participants and model guaranteed income solutions to address decumulation risks.\", \"**Risk Assessment:** Conduct due diligence on private market options, weighing litigation and liquidity concerns.\"]",
    "createdAt": "20260211055251"
  },
  "needsRefresh": false
}
<div class="p-8 md:p-10">
    <div class="flex items-start gap-4 mb-6">
        <div class="p-3 bg-secondary/10 rounded-xl">
            <svg
                xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sparkles w-6 h-6 text-secondary" aria-hidden="true">
                <path d="M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"></path>
                <path d="M20 2v4"></path>
                <path d="M22 4h-4"></path>
                <circle cx="4" cy="20" r="2"></circle>
            </svg>
        </div>
        <div>
            <h4 class="text-xl font-bold text-primary flex items-center gap-2">AI Executive Briefing
                <span class="text-xs font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded-full border">Generated Feb 11, 2026</span>
            </h4>
            <p class="text-gray-500 text-sm mt-1">Synthesized analysis for Plan Sponsors</p>
        </div>
    </div>
    <div class="grid md:grid-cols-2 gap-8">
        <div>
            <h5 class="font-serif font-bold text-lg mb-3 text-gray-900">Key Takeaways</h5>
            <p class="text-gray-600 leading-relaxed mb-4">Plan sponsors face a pivotal 2026 with mandatory Roth catch-up contributions reshaping plan designs and operations, demanding immediate compliance reviews to avoid contribution barriers for higher-income workers. Litigation risks escalate from court advancements in forfeiture cases like Illinois Tool Works and recordkeeper failures such as ADP's, alongside EBSA's sponsor-friendly shifts in pleading standards. Emerging market pressures for private markets and guaranteed income solutions introduce fiduciary challenges around illiquidity, participant satisfaction, and decumulation security.

Fiduciaries must prioritize vendor oversight and documentation to counter heightened scrutiny, while evaluating income-focused options like annuities in target-date funds to meet participant demands amid equity concentration risks. These developments signal a more complex regulatory landscape, balancing innovation opportunities with amplified legal and operational costs. Proactive engagement with legal experts and recordkeepers will be crucial to mitigate exposures.</p>
        </div>
        <div class="bg-slate-50 rounded-xl p-6 border border-slate-100">
            <h5 class="font-bold text-sm uppercase tracking-wider text-primary mb-4 flex items-center gap-2">
                <svg
                    xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-alert w-4 h-4 text-secondary" aria-hidden="true">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" x2="12" y1="8" y2="12"></line>
                    <line x1="12" x2="12.01" y1="16" y2="16"></line>
                </svg>Actionable Conclusions
            </h5>
            <ul class="space-y-3">
                <li class="flex items-start gap-3 text-sm text-gray-700">
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-check w-5 h-5 text-green-600 shrink-0" aria-hidden="true">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="m9 12 2 2 4-4"></path>
                    </svg>
                    <span>
                        <strong class="text-gray-900">Compliance Review:</strong> Audit 401(k) plans for Roth availability and update designs for mandatory catch-up rules by Q1 2026.
                    </span>
                </li>
                <li class="flex items-start gap-3 text-sm text-gray-700">
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-check w-5 h-5 text-green-600 shrink-0" aria-hidden="true">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="m9 12 2 2 4-4"></path>
                    </svg>
                    <span>
                        <strong class="text-gray-900">Litigation Prep:</strong> Review forfeiture and escheatment policies in light of recent court rulings and strengthen fiduciary documentation.
                    </span>
                </li>
                <li class="flex items-start gap-3 text-sm text-gray-700">
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-check w-5 h-5 text-green-600 shrink-0" aria-hidden="true">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="m9 12 2 2 4-4"></path>
                    </svg>
                    <span>
                        <strong class="text-gray-900">Vendor Audit:</strong> Assess recordkeepers for operational readiness on Roth catch-ups and error resolution protocols.
                    </span>
                </li>
                <li class="flex items-start gap-3 text-sm text-gray-700">
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-check w-5 h-5 text-green-600 shrink-0" aria-hidden="true">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="m9 12 2 2 4-4"></path>
                    </svg>
                    <span>
                        <strong class="text-gray-900">Income Evaluation:</strong> Survey participants and model guaranteed income solutions to address decumulation risks.
                    </span>
                </li>
                <li class="flex items-start gap-3 text-sm text-gray-700">
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-check w-5 h-5 text-green-600 shrink-0" aria-hidden="true">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="m9 12 2 2 4-4"></path>
                    </svg>
                    <span>
                        <strong class="text-gray-900">Risk Assessment:</strong> Conduct due diligence on private market options, weighing litigation and liquidity concerns.
                    </span>
                </li>
            </ul>
        </div>
    </div>
</div>


<div class="grid md:grid-cols-3 gap-8">
    <div style="opacity: 1; transform: none;">
        <div class="rounded-xl border bg-card text-card-foreground shadow h-full hover:shadow-lg transition-shadow duration-300 border-t-4 border-t-secondary flex flex-col" data-testid="card-news-145">
            <div class="flex flex-col space-y-1.5 p-6">
                <div class="flex justify-between items-start mb-4">
                    <div class="whitespace-nowrap inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 hover-elevate border-transparent bg-blue-50 text-blue-700 hover:bg-blue-100 border-none">Compliance</div>
                    <span class="text-xs text-gray-400 font-medium whitespace-nowrap ml-2">2026-02-11</span>
                </div>
                <div class="font-semibold tracking-tight font-serif text-xl leading-snug mb-2 group-hover:text-primary transition-colors">401(k) Changes in 2026: What Every Saver and Sponsor Needs to Know</div>
                <div class="flex items-center gap-1 text-xs uppercase tracking-wide font-semibold text-gray-400">Source: JD Supra</div>
            </div>
            <div class="p-6 pt-0 flex-grow flex flex-col justify-between">
                <p class="text-gray-600 text-sm leading-relaxed mb-6">Mandatory Roth .....</p>
                <a href="https://www.jdsupra.com/legalnews/401-k-changes-in-2026-what-every-saver-1319915/" target="_blank" rel="noopener noreferrer" class="inline-flex items-center text-sm font-semibold text-primary hover:text-secondary transition-colors group mt-auto" data-testid="link-news-145">Read Full Article 
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-external-link ml-2 h-3 w-3" aria-hidden="true">
                        <path d="M15 3h6v6"></path>
                        <path d="M10 14 21 3"></path>
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    </svg>
                </a>
            </div>
        </div>
    </div>
    <div style="opacity: 1; transform: none;">
        <div class="rounded-xl border bg-card text-card-foreground shadow h-full hover:shadow-lg transition-shadow duration-300 border-t-4 border-t-secondary flex flex-col" data-testid="card-news-144">
            <div class="flex flex-col space-y-1.5 p-6">
                <div class="flex justify-between items-start mb-4">
                    <div class="whitespace-nowrap inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 hover-elevate border-transparent bg-blue-50 text-blue-700 hover:bg-blue-100 border-none">Market</div>
                    <span class="text-xs text-gray-400 font-medium whitespace-nowrap ml-2">2026-02-11</span>
                </div>
                <div class="font-semibold tracking-tight font-serif text-xl leading-snug mb-2 group-hover:text-primary transition-colors">Plan Sponsors, Participants May Target Income Solutions in 2026</div>
                <div class="flex items-center gap-1 text-xs uppercase tracking-wide font-semibold text-gray-400">Source: 401(k) Specialist Magazine</div>
            </div>
            <div class="p-6 pt-0 flex-grow flex flex-col justify-between">
                <p class="text-gray-600 text-sm leading-relaxed mb-6">Rising demand ...</p>
                <a href="https://401kspecialistmag.com/plan-sponsors-participants-may-target-income-solutions-in-2026/" target="_blank" rel="noopener noreferrer" class="inline-flex items-center text-sm font-semibold text-primary hover:text-secondary transition-colors group mt-auto" data-testid="link-news-144">Read Full Article 
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-external-link ml-2 h-3 w-3" aria-hidden="true">
                        <path d="M15 3h6v6"></path>
                        <path d="M10 14 21 3"></path>
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    </svg>
                </a>
            </div>
        </div>
    </div>
    <div style="opacity: 1; transform: none;">
        <div class="rounded-xl border bg-card text-card-foreground shadow h-full hover:shadow-lg transition-shadow duration-300 border-t-4 border-t-secondary flex flex-col" data-testid="card-news-143">
            <div class="flex flex-col space-y-1.5 p-6">
                <div class="flex justify-between items-start mb-4">
                    <div class="whitespace-nowrap inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 hover-elevate border-transparent bg-blue-50 text-blue-700 hover:bg-blue-100 border-none">Litigation</div>
                    <span class="text-xs text-gray-400 font-medium whitespace-nowrap ml-2">2026-02-11</span>
                </div>
                <div class="font-semibold tracking-tight font-serif text-xl leading-snug mb-2 group-hover:text-primary transition-colors">Fitting Private Markets Into 401(k) Plans</div>
                <div class="flex items-center gap-1 text-xs uppercase tracking-wide font-semibold text-gray-400">Source: Goodwin Law</div>
            </div>
            <div class="p-6 pt-0 flex-grow flex flex-col justify-between">
                <p class="text-gray-600 text-sm leading-relaxed mb-6">Plan sponsors ....</p>
                <a href="https://www.goodwinlaw.com/en/insights/publications/2026/02/insights-finance-fs-fitting-private-markets-into-401k-plans" target="_blank" rel="noopener noreferrer" class="inline-flex items-center text-sm font-semibold text-primary hover:text-secondary transition-colors group mt-auto" data-testid="link-news-143">Read Full Article 
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-external-link ml-2 h-3 w-3" aria-hidden="true">
                        <path d="M15 3h6v6"></path>
                        <path d="M10 14 21 3"></path>
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    </svg>
                </a>
            </div>
        </div>
    </div>
</div>

2) Поиск пенсионных планов (вводим в input (Caption = Your Retirement Plan Health Check
Get an instant assessment of your company's retirement plan. Search by company name or EIN to see personalized insights and recommendations.)
название компании и по каждой кнопке ищем (инкрементный поиск))

curl 'https://{site_domain}/api/plan-search' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9,ru;q=0.8,mt;q=0.7' \
  -H 'content-type: application/json' \
  -b '_ga=GA1.1.1100712891.1583756908; _ga_KNVTSNG51Q=GS2.1.s1753690621$o1$g0$t1753690707$j60$l0$h0; _ga_JV1GZGPL9G=GS2.1.s1763007209$o16$g0$t1763007211$j58$l0$h0; _gcl_au=1.1.1480377669.1765886106; _ga_D2PQSCR80Y=GS2.1.s1765894080$o3$g0$t1765894080$j60$l0$h303153550; twk_uuid_5d49cef27d27204601c99db5=%7B%22uuid%22%3A%221.H3MTqtrnFPDsvDnHQL4leROjc7PiWu5UzFH6xVCRlYM7esPGHJFy0YdxSr2t3eydNqyZ1muNvyLDDS7zcf71kRqEGuVeG97dg5bUtDBsIrj02tUXff9hiCgCOS993iQlhlvUq3ApSpIZWJ46%22%2C%22version%22%3A3%2C%22domain%22%3A%22rixtrema.net%22%2C%22ts%22%3A1770871054892%7D' \
  -H 'origin: https://testadv11.rixtrema.net' \
  -H 'priority: u=1, i' \
  -H 'referer: https://testadv11.rixtrema.net/' \
  -H 'sec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36' \
  --data-raw '{"query":"hugo","count":10}'
{
    "records": [
        {
            "ackId": "20250514220139NAL0014363811063",
            "planName": "HUGO 401(K) PLAN",
            "sponsorName": "HUGO INC",
            "ein": "521613309",
            "pn": "001",
            "state": "MD",
            "country": "US",
            "city": "KENSINGTON"
        },
        {
            "ackId": "20240503140841NAL0029831921001",
            "planName": "HUGO CREATIVE 401(K) PLAN",
            "sponsorName": "HUGO CREATIVE",
            "ein": "273604450",
            "pn": "001",
            "state": "VA",
            "country": "US",
            "city": "ARLINGTON"
        },....
    ]
}
Результат поиска можно показать примерно так - 
<div class="rounded-xl bg-card text-card-foreground absolute z-10 w-full mt-2 shadow-xl border-0">
    <div class="p-2">
        <button class="w-full text-left p-4 hover:bg-slate-50 rounded-lg transition-colors flex items-center justify-between group" data-testid="plan-result-843862462">
            <div>
                <div class="font-semibold text-primary flex items-center gap-2">
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-building2 lucide-building-2 h-4 w-4" aria-hidden="true">
                        <path d="M10 12h4"></path>
                        <path d="M10 8h4"></path>
                        <path d="M14 21v-3a2 2 0 0 0-4 0v3"></path>
                        <path d="M6 10H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2"></path>
                        <path d="M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"></path>
                    </svg>BIRD AND PUP, INC.
                </div>
                <div class="text-sm text-gray-600 mt-1">BIRD AND PUP, INC. 401(K) PROFIT SHARING PLAN</div>
                <div class="text-xs text-gray-400 mt-1 flex items-center gap-1">
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-map-pin h-3 w-3" aria-hidden="true">
                        <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"></path>
                        <circle cx="12" cy="10" r="3"></circle>
                    </svg>PEQUANNOCK, NJ
                </div>
            </div>
            <svg
                xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-right h-5 w-5 text-gray-400 group-hover:text-primary transition-colors" aria-hidden="true">
                <path d="m9 18 6-6-6-6"></path>
            </svg>
        </button>
        <button class="w-full text-left p-4 hover:bg-slate-50 rounded-lg transition-colors flex items-center justify-between group" data-testid="plan-result-364360254">
            <div>
                <div class="font-semibold text-primary flex items-center gap-2">
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-building2 lucide-building-2 h-4 w-4" aria-hidden="true">
                        <path d="M10 12h4"></path>
                        <path d="M10 8h4"></path>
                        <path d="M14 21v-3a2 2 0 0 0-4 0v3"></path>
                        <path d="M6 10H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2"></path>
                        <path d="M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"></path>
                    </svg>BIRD AND VAN DYKE
                </div>
                <div class="text-sm text-gray-600 mt-1">BIRD AND VAN DYKE 401(K) SAVINGS PLAN</div>
                <div class="text-xs text-gray-400 mt-1 flex items-center gap-1">
                    <svg
                        xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-map-pin h-3 w-3" aria-hidden="true">
                        <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"></path>
                        <circle cx="12" cy="10" r="3"></circle>
                    </svg>STOCKTON, CA
                </div>
            </div>
            <svg
                xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-right h-5 w-5 text-gray-400 group-hover:text-primary transition-colors" aria-hidden="true">
                <path d="m9 18 6-6-6-6"></path>
            </svg>
        </button>
    </div>
</div>

3) Стратегии плана. (запрос долгий и надо показать какую-то анимацию и просьбу подождать пока работает ИИ)
curl 'https://{site}/api/plan-strategy' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'Referer: https://testadv11.rixtrema.net/' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"' \
  -H 'Content-Type: application/json' \
  -H 'sec-ch-ua-mobile: ?0' \
  --data-raw '{"ein":"843862462","pn":"001","planName":"BIRD AND PUP, INC. 401(K) PROFIT SHARING PLAN"}'

{
    "strategy": "{\"planName\":\"Bird & Pup, Inc. 401(k) Profit‑Sharing Plan\",\"strengths\":[\"The plan charges a 0\u202F% administrative fee, which is significantly better than the 0.34\u202F% industry benchmark and leaves all returns to participants.\",\"Participant count increased from 3 in 2023 to 5 in 2025, representing 100\u202F% growth in plan participation.\",\"The plan is not a participant‑directed plan, which reduces statutory 404(c) exposure and some types of fiduciary risk associated with participant‑directed accounts.\",\"Admin fees are well below the monitoring target of ≤0.5\u202F%, indicating strong cost control and fee neutrality.\",\"The plan has a defined monitoring framework with targets for participation rate (≥90\u202F%), rate of return (≥+5\u202F%), employer contribution (≥$1,500/year), and admin fee (≤0.5\u202F%), which supports ongoing fiduciary oversight.\"],\"deficiencies\":[\"The plan’s rate of return is –66.9\u202F%, compared to an industry benchmark of +10.1\u202F%, representing a critical shortfall and catastrophic negative performance.\",\"The employer provides zero contributions, compared with an industry average of $1,672 per participant per year, creating a huge deficiency in participant benefit.\",\"The overall plan rating is 25 on a 1–100 scale, signaling a plan significantly below the median and indicative of mismanagement or insufficient participant benefit.\",\"The plan has no automatic enrollment and no QDIA, likely leaving an estimated 33\u202F% of eligible employees unenrolled and increasing the risk of poor retirement outcomes.\",\"The plan lacks a formal 404(c) election, which may signal a gap in documented fiduciary safeguards even though current participant‑directed exposure is low.\",\"The profit‑sharing approach does not use a new comparability design, resulting in flat, non‑optimized contributions that lag competitive practices.\",\"Multiple key red‑flag and risk couplings are present, including negative returns, absent employer contributions, and low overall rating, putting the plan in a precarious fiduciary state.\"],\"actionSteps\":[\"Deploy a Qualified Default Investment Alternative (QDIA), such as a low‑cost target‑date or diversified index fund with an 80\u202F% equity / 20\u202F% fixed‑income default allocation, to reduce investment risk and improve aggregated returns.\",\"Implement automatic enrollment with an initial automatic deferral rate of 5–10\u202F% and clear opt‑out procedures to drive participation toward 85–90\u202F%.\",\"Reinstate a competitive employer match or profit‑sharing formula, for example a 3\u202F% employer match on up to 5\u202F% of salary, and consider a new comparability design to improve fairness and incentives.\",\"Conduct a comprehensive review of the investment portfolio, including asset allocation, manager oversight, and fees, to address the –66.9\u202F% return and achieve at least benchmark‑level, risk‑adjusted performance.\",\"File a formal 404(c) election, update plan documents to reflect participant‑directed provisions for future growth, and train advisors on 404(c) compliance to enhance fiduciary protection.\",\"Enhance participant education and engagement through bi‑annual webinars, one‑on‑one sessions, and a mobile app, targeting ≥70\u202F% attendance or engagement per session.\",\"Evaluate and potentially transition to a Pooled Employer Plan (PEP) or independent third‑party administrator to access institutional‑share investments, reduce administrative burden, and lower cost per participant below 5\u202F%.\",\"Establish a benchmark‑based performance review process with quarterly reports comparing returns and fees to industry benchmarks and presenting results to the plan advisory committee.\",\"Execute the action plan timeline: form a plan advisory committee in month 1, submit 404(c) and QDIA adoption in month 2, launch auto‑enrollment in month 3, engage actuary and consultant in month 4, roll out the competitive employer match in month 5, deploy education in month 6, and transition to a PEP or TPA by month 7.\"]}",
    "planName": "Bird & Pup, Inc. 401(k) Profit‑Sharing Plan",
    "strengths": [
        "The plan charges a 0\u202F% administrative fee, which is significantly better than the 0.34\u202F% industry benchmark and leaves all returns to participants.",
        "Participant count increased from 3 in 2023 to 5 in 2025, representing 100\u202F% growth in plan participation.",
        "The plan is not a participant‑directed plan, which reduces statutory 404(c) exposure and some types of fiduciary risk associated with participant‑directed accounts.",
        "Admin fees are well below the monitoring target of ≤0.5\u202F%, indicating strong cost control and fee neutrality.",
        "The plan has a defined monitoring framework with targets for participation rate (≥90\u202F%), rate of return (≥+5\u202F%), employer contribution (≥$1,500/year), and admin fee (≤0.5\u202F%), which supports ongoing fiduciary oversight."
    ],
    "deficiencies": [
        "The plan’s rate of return is –66.9\u202F%, compared to an industry benchmark of +10.1\u202F%, representing a critical shortfall and catastrophic negative performance.",
        "The employer provides zero contributions, compared with an industry average of $1,672 per participant per year, creating a huge deficiency in participant benefit.",
        "The overall plan rating is 25 on a 1–100 scale, signaling a plan significantly below the median and indicative of mismanagement or insufficient participant benefit.",
        "The plan has no automatic enrollment and no QDIA, likely leaving an estimated 33\u202F% of eligible employees unenrolled and increasing the risk of poor retirement outcomes.",
        "The plan lacks a formal 404(c) election, which may signal a gap in documented fiduciary safeguards even though current participant‑directed exposure is low.",
        "The profit‑sharing approach does not use a new comparability design, resulting in flat, non‑optimized contributions that lag competitive practices.",
        "Multiple key red‑flag and risk couplings are present, including negative returns, absent employer contributions, and low overall rating, putting the plan in a precarious fiduciary state."
    ],
    "actionSteps": [
        "Deploy a Qualified Default Investment Alternative (QDIA), such as a low‑cost target‑date or diversified index fund with an 80\u202F% equity / 20\u202F% fixed‑income default allocation, to reduce investment risk and improve aggregated returns.",
        "Implement automatic enrollment with an initial automatic deferral rate of 5–10\u202F% and clear opt‑out procedures to drive participation toward 85–90\u202F%.",
        "Reinstate a competitive employer match or profit‑sharing formula, for example a 3\u202F% employer match on up to 5\u202F% of salary, and consider a new comparability design to improve fairness and incentives.",
        "Conduct a comprehensive review of the investment portfolio, including asset allocation, manager oversight, and fees, to address the –66.9\u202F% return and achieve at least benchmark‑level, risk‑adjusted performance.",
        "File a formal 404(c) election, update plan documents to reflect participant‑directed provisions for future growth, and train advisors on 404(c) compliance to enhance fiduciary protection.",
        "Enhance participant education and engagement through bi‑annual webinars, one‑on‑one sessions, and a mobile app, targeting ≥70\u202F% attendance or engagement per session.",
        "Evaluate and potentially transition to a Pooled Employer Plan (PEP) or independent third‑party administrator to access institutional‑share investments, reduce administrative burden, and lower cost per participant below 5\u202F%.",
        "Establish a benchmark‑based performance review process with quarterly reports comparing returns and fees to industry benchmarks and presenting results to the plan advisory committee.",
        "Execute the action plan timeline: form a plan advisory committee in month 1, submit 404(c) and QDIA adoption in month 2, launch auto‑enrollment in month 3, engage actuary and consultant in month 4, roll out the competitive employer match in month 5, deploy education in month 6, and transition to a PEP or TPA by month 7."
    ]
}

Пример отрисовки - 
<div class="text-center mb-4"><h3 class="text-2xl font-serif font-bold text-primary">BIRD AND PUP, INC.</h3><p class="text-gray-600">BIRD AND PUP, INC. 401(K) PROFIT SHARING PLAN</p></div>
<div class="rounded-xl text-card-foreground border-2 bg-emerald-50 border-emerald-200 shadow-lg min-h-[420px] flex flex-col">
    <div class="p-8 flex flex-col h-full">
        <div class="flex items-start gap-4 mb-4">
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-lg flex-shrink-0">
                <svg
                    xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-star h-7 w-7 text-white" aria-hidden="true">
                    <path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"></path>
                </svg>
            </div>
            <div>
                <h4 class="text-xl font-bold text-gray-900">Strengths</h4>
                <span class="text-xs uppercase tracking-wide text-gray-500 font-medium">Plan Strength</span>
            </div>
        </div>
        <div class="flex-grow">
            <p class="text-gray-700 leading-relaxed mb-4">Your plan excels in these key areas:</p>
            <ul class="space-y-2">
                <li class="flex items-start gap-2 text-sm text-gray-700">
                    <span class="font-bold mt-0.5 text-emerald-600">•</span>
                    <span>The plan charges a 0 % administrative fee, which is significantly better than the 0.34 % industry benchmark and leaves all returns to participants.</span>
                </li>
                <li class="flex items-start gap-2 text-sm text-gray-700">
                    <span class="font-bold mt-0.5 text-emerald-600">•</span>
                    <span>Participant count increased from 3 in 2023 to 5 in 2025, representing 100 % growth in plan participation.</span>
                </li>
                <li class="flex items-start gap-2 text-sm text-gray-700">
                    <span class="font-bold mt-0.5 text-emerald-600">•</span>
                    <span>The plan is not a participant‑directed plan, which reduces statutory 404(c) exposure and some types of fiduciary risk associated with participant‑directed accounts.</span>
                </li>
                <li class="flex items-start gap-2 text-sm text-gray-700">
                    <span class="font-bold mt-0.5 text-emerald-600">•</span>
                    <span>Admin fees are well below the monitoring target of ≤0.5 %, indicating strong cost control and fee neutrality.</span>
                </li>
                <li class="flex items-start gap-2 text-sm text-gray-700">
                    <span class="font-bold mt-0.5 text-emerald-600">•</span>
                    <span>The plan has a defined monitoring framework with targets for participation rate (≥90 %), rate of return (≥+5 %), employer contribution (≥$1,500/year), and admin fee (≤0.5 %), which supports ongoing fiduciary oversight.</span>
                </li>
            </ul>
        </div>
        <div class="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-400 flex justify-between items-center">
            <span>Insight 1 of 4</span>
            <span class="text-primary font-medium">Swipe for more →</span>
        </div>
    </div>
</div>



Preprocessor
  (чистка, разбивка если > лимит контекста (см ниже))
  Chunking — если MD > 20k токенов, сначала суммаризировать секции отдельно, потом собирать.
Postprocessor
  (валидация HTML, fallback если сломан)
  Валидация на выходе — парсить через html.parser из Python stdlib. Если невалидный — retry с температурой 0.

Что делать если сайт большой?
Это реальная проблема для крупных сайтов. Стратегия:
1. Pre-filter снапшота — самое важное. Перед подачей в LLM убирать:
python# Убрать дублированные страницы (у тебя в снапшоте home дублировался!)
# Убрать навигационные повторы
# Убрать footer/header со всех страниц кроме одной
# Убрать FAILED pages
```

**2. Иерархический подход** для больших сайтов (>8 страниц):
```
Pass 1: подать только главную + структуру → получить каркас HTML
Pass 2: подать каждую секцию отдельно → заполнить контентом
Pass 3: финальный pass → выровнять стили
```

**3. Summarize before design** — если контент просто длинный текст:
```
Сначала попросить модель: "summarize this MD into key sections and content"
pre-filter + truncate по приоритету страниц (главная > контакты > услуги > прочее).
Потом дизайн по summary


Если snapshot.md не содержит скачанного сайта, а что то нерелевантное типа такого 
```
# www.proverbswealthmanagement.com

- Source: https://www.proverbswealthmanagement.com
- Generated: 2026-01-15T13:01:40.306Z
- Pages: 1

## Pages
- [BLOCKED (Cloudflare): https://www.proverbswealthmanagement.com/](#page-f16ec2af7214)

## BLOCKED (Cloudflare): https://www.proverbswealthmanagement.com/
<a id="page-f16ec2af7214"></a>
```
то надо выдавать ошибку


Шаблон инстанса vast.ai содержит стартап скрипт. Он ограничен 2000 символами,
поэтому все нужное можно забрать из Гита так (просто пример)-
```
#!/bin/bash
set -e

command -v curl >/dev/null 2>&1 || (apt-get update -qq && apt-get install -y -qq curl)

URL="https://raw.githubusercontent.com/greenbutton75/SiteTemplate/main/...........?ts=$(date +%s)"
curl -fsSL -H "Cache-Control: no-cache" -H "Pragma: no-cache" "$URL" -o /tmp/vast_startup.sh
chmod +x /tmp/vast_startup.sh
exec /tmp/vast_startup.sh
```
а переменные из шаблона забираются так - 

```
# Фоллбек: берем из текущего окружения
env | grep -E 'STITCH_API_KEY|HF_TOKEN' >> /etc/webgen.env || true

set -a
source /etc/webgen.env 2>/dev/null || true
set +a

# Проверка обязательных переменных
if [ -z "$STITCH_API_KEY" ]; then
    echo "ERROR: STITCH_API_KEY is not set. Add it to Vast.ai environment variables."
    exit 1
fi
```

Делаем Add SSH keys, добавляем 
ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAQEA17hNg7cjwFUhCY0oVVc8xsBO5yuadnN7+7wG0zrZQ7xw1GKtI9i0UnwXwmfXGcFlvxgXw87VYkC6nXg/HdnHpUGae5KonVnJ44+9XSGNMWH3a//JiSQ2LFhETHmeYKrlzLo36NL8v9Im28LwtBxQ0bgUjDTxZPlBg3vwF4xBK5pnnjySaVZHJ38BKd/EfPJnV1vyLR2MvPzons/rVBZkhD+HcL1YmqEbUbtE7dKkgmdFMDZZmFR4mKBWtpLw8doOg5Ks2kwQm2DaOQjRwC3yi1k5ls0jBxNYmSXJ98wX2+4+lxtavkzwLPEMykyXd4UR5xLNQLb29g6sH4aLhUzCHQ==

ЗАБИРАЕМ ОТТУДА ssh -p 57626 root@24.124.32.70 -L 8080:localhost:8080
и выполняем его в PowerShell (подожди, пока машина стартует)

Затем нажимаем на инстансе на синий IP адрес - он показывает на какие эфемерные порты проброшен 8000
типа 24.124.32.70:57950 -> 8000/tcp

207.180.148.74:45070 -> 7860/tcp
