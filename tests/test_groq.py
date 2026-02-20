import os
from groq import Groq

# Ваш API-ключ от Groq (через окружение)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in the environment")

client = Groq(api_key=GROQ_API_KEY)

# Проверка доступных моделей
models = client.models.list()
available_models = [m.id for m in models.data if 'qwen' in m.id.lower()]
print("Доступные Qwen модели на Groq:", available_models)


# Загрузка системного промпта из файла
with open('system.txt', 'r', encoding='utf-8') as f:
    system_prompt = f.read()

# Контент-снапшот (замените на актуальный текст о вашей компании, услугах и т.д.)
content_snapshot = """
# www.appleseedwealth.com

- Source: https://www.appleseedwealth.com
- Pages: 2

## Home | Appleseed Wealth Management

Source: https://www.appleseedwealth.com/

# Appleseed Wealth Management

## Wealth Management you can trust.

Our team is here to help you protect your future. Lets build your financial legacy together.

## Protect. Advise. Grow.

Our Mission is to protect your financial future, advise with strategic insights, and grow your wealth through personalized investment solutions.

### Investment Management
Build and protect your wealth with the help of our team.

### Financial Planning
Secure your financial future with a personalized roadmap.

### Trust Services
Protect and distribute your assets how you want.

## Contact Us

10301 Dawsons Creek Blvd, Ste B
Fort Wayne, IN 46825
info@appleseedwealth.com

<!-- ═══════════════════════════════════════════════════════════════
     NEWS & AI BRIEFING SECTION
     Adapt colors/fonts to match the site design.
     DO NOT modify any JavaScript or fetch() calls.
     ═══════════════════════════════════════════════════════════════ -->
<section id="market-intelligence" x-data="newsSection()" x-init="init()" class="py-20 bg-slate-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

    <!-- Section header -->
    <div class="mb-12">
      <h2 class="text-3xl font-bold text-gray-900 mb-3">Market Intelligence</h2>
      <p class="text-gray-500 text-lg">Stay current with the latest developments in retirement planning and fiduciary compliance.</p>
    </div>

    <!-- Loading state -->
    <template x-if="loading">
      <div class="flex items-center justify-center py-16 text-gray-400">
        <i class="fas fa-circle-notch fa-spin text-2xl mr-3"></i>
        <span>Loading market intelligence...</span>
      </div>
    </template>

    <!-- AI Executive Briefing -->
    <template x-if="!loading && briefing">
      <div class="rounded-2xl border border-slate-200 bg-white shadow-sm mb-10 overflow-hidden">
        <div class="p-8 md:p-10">
          <div class="flex items-start gap-4 mb-6">
            <div class="p-3 bg-blue-50 rounded-xl flex-shrink-0">
              <i class="fas fa-sparkles text-blue-600 text-xl"></i>
            </div>
            <div>
              <h3 class="text-xl font-bold text-gray-900 flex items-center gap-3">
                AI Executive Briefing
                <span class="text-xs font-normal text-gray-400 bg-gray-100 px-2.5 py-1 rounded-full border" x-text="'Generated ' + briefing.generatedDate"></span>
              </h3>
              <p class="text-gray-500 text-sm mt-1">Synthesized analysis for Plan Sponsors</p>
            </div>
          </div>
          <div class="grid md:grid-cols-2 gap-8">
            <div>
              <h4 class="font-semibold text-lg mb-3 text-gray-900">Key Takeaways</h4>
              <p class="text-gray-600 leading-relaxed" x-text="briefing.keyTakeaways"></p>
            </div>
            <div class="bg-slate-50 rounded-xl p-6 border border-slate-100">
              <h4 class="font-bold text-xs uppercase tracking-wider text-gray-500 mb-4 flex items-center gap-2">
                <i class="fas fa-circle-info text-blue-500"></i>
                Actionable Conclusions
              </h4>
              <ul class="space-y-3">
                <template x-for="item in parsedActionItems" :key="item">
                  <li class="flex items-start gap-2 text-sm text-gray-700">
                    <i class="fas fa-circle-check text-green-500 mt-0.5 flex-shrink-0"></i>
                    <span x-html="item"></span>
                  </li>
                </template>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- News cards grid -->
    <template x-if="!loading && articles.length > 0">
      <div class="grid md:grid-cols-3 gap-6">
        <template x-for="article in articles" :key="article.id">
          <div class="rounded-xl border bg-white shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col">
            <div class="p-6 flex flex-col flex-grow">
              <div class="flex justify-between items-start mb-4">
                <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-100" x-text="article.tag"></span>
                <span class="text-xs text-gray-400 ml-2 flex-shrink-0" x-text="article.date"></span>
              </div>
              <h4 class="font-bold text-lg leading-snug mb-2 text-gray-900" x-text="article.title"></h4>
              <p class="text-xs text-gray-400 uppercase tracking-wide font-medium mb-3" x-text="'Source: ' + article.source"></p>
              <p class="text-gray-600 text-sm leading-relaxed mb-6 flex-grow" x-text="article.summary"></p>
              <a :href="article.url" target="_blank" rel="noopener noreferrer"
                 class="inline-flex items-center text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors mt-auto group">
                Read Full Article
                <i class="fas fa-arrow-up-right-from-square ml-2 text-xs group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform"></i>
              </a>
            </div>
          </div>
        </template>
      </div>
    </template>

  </div>
</section>

<script>
function newsSection() {
  return {
    articles: [],
    briefing: null,
    loading: true,
    parsedActionItems: [],

    async init() {
      try {
        const res = await fetch('https://{{SITE_DOMAIN}}/api/get-news');
        if (!res.ok) throw new Error('Network error');
        const data = await res.json();
        this.articles = (data.articles || []).slice(0, 6);
        this.briefing = data.briefing || null;
        if (this.briefing?.actionItems) {
          try {
            const items = JSON.parse(this.briefing.actionItems);
            this.parsedActionItems = items.map(i =>
              i.replace(/\*\*(.*?)\*\*/g, '<strong class="text-gray-900">$1</strong>')
            );
          } catch { this.parsedActionItems = []; }
        }
      } catch (e) {
        console.error('Failed to load news:', e);
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<!-- ═══════════════════════════════════════════════════════════════
     RETIREMENT PLAN SEARCH + STRATEGY SECTION
     Adapt colors/fonts to match the site design.
     DO NOT modify any JavaScript or fetch() calls.
     ═══════════════════════════════════════════════════════════════ -->
<section id="plan-health-check" x-data="planSection()" class="py-20 bg-white">
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">

    <!-- Section header -->
    <div class="text-center mb-10">
      <h2 class="text-3xl font-bold text-gray-900 mb-3">Your Retirement Plan Health Check</h2>
      <p class="text-gray-500 text-lg max-w-2xl mx-auto">
        Get an instant assessment of your company's retirement plan.
        Search by company name or EIN to see personalized insights and recommendations.
      </p>
    </div>

    <!-- Search input -->
    <div class="relative max-w-2xl mx-auto mb-10">
      <div class="relative">
        <i class="fas fa-magnifying-glass absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
        <input
          type="text"
          x-model="query"
          @input.debounce.350ms="search()"
          @keydown.escape="results = []"
          placeholder="Search by company name or EIN..."
          class="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder-gray-400"
        />
        <i x-show="searching" class="fas fa-circle-notch fa-spin absolute right-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
      </div>

      <!-- Dropdown results -->
      <template x-if="results.length > 0">
        <div class="absolute z-20 w-full mt-2 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden">
          <div class="p-2 max-h-80 overflow-y-auto">
            <template x-for="plan in results" :key="plan.ackId">
              <button
                @click="selectPlan(plan)"
                class="w-full text-left p-4 hover:bg-slate-50 rounded-lg transition-colors flex items-center justify-between group"
              >
                <div>
                  <div class="font-semibold text-gray-900 flex items-center gap-2 text-sm">
                    <i class="fas fa-building text-blue-500 flex-shrink-0"></i>
                    <span x-text="plan.sponsorName"></span>
                  </div>
                  <div class="text-sm text-gray-500 mt-0.5 ml-5" x-text="plan.planName"></div>
                  <div class="text-xs text-gray-400 mt-0.5 ml-5">
                    <i class="fas fa-location-dot mr-1"></i>
                    <span x-text="plan.city + ', ' + plan.state"></span>
                  </div>
                </div>
                <i class="fas fa-chevron-right text-gray-300 group-hover:text-blue-500 transition-colors text-xs"></i>
              </button>
            </template>
          </div>
        </div>
      </template>
    </div>

    <!-- Strategy display area -->
    <template x-if="selectedPlan">
      <div>
        <!-- Plan title -->
        <div class="text-center mb-8">
          <h3 class="text-2xl font-bold text-gray-900" x-text="selectedPlan.sponsorName"></h3>
          <p class="text-gray-500 mt-1" x-text="selectedPlan.planName"></p>
        </div>

        <!-- Loading animation -->
        <template x-if="strategyLoading">
          <div class="flex flex-col items-center justify-center py-20 gap-5">
            <div class="relative w-20 h-20">
              <div class="absolute inset-0 rounded-full border-4 border-blue-100"></div>
              <div class="absolute inset-0 rounded-full border-4 border-t-blue-600 animate-spin"></div>
              <i class="fas fa-robot absolute inset-0 flex items-center justify-center text-blue-400 text-2xl" style="display:flex;align-items:center;justify-content:center;"></i>
            </div>
            <div class="text-center">
              <p class="font-semibold text-gray-700 text-lg">AI is analyzing your plan...</p>
              <p class="text-gray-400 text-sm mt-1">This typically takes 15–30 seconds</p>
            </div>
          </div>
        </template>

        <!-- Strategy cards -->
        <template x-if="strategy && !strategyLoading">
          <div class="grid md:grid-cols-3 gap-6">

            <!-- Strengths -->
            <div class="rounded-xl border-2 bg-emerald-50 border-emerald-200 shadow p-7">
              <div class="flex items-center gap-3 mb-5">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-md flex-shrink-0">
                  <i class="fas fa-star text-white text-lg"></i>
                </div>
                <div>
                  <h4 class="font-bold text-gray-900">Strengths</h4>
                  <span class="text-xs text-gray-500 uppercase tracking-wide">Plan strengths</span>
                </div>
              </div>
              <ul class="space-y-2.5">
                <template x-for="s in strategy.strengths" :key="s">
                  <li class="flex items-start gap-2 text-sm text-gray-700">
                    <span class="text-emerald-600 font-bold mt-0.5 flex-shrink-0">•</span>
                    <span x-text="s"></span>
                  </li>
                </template>
              </ul>
            </div>

            <!-- Deficiencies -->
            <div class="rounded-xl border-2 bg-red-50 border-red-200 shadow p-7">
              <div class="flex items-center gap-3 mb-5">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center shadow-md flex-shrink-0">
                  <i class="fas fa-triangle-exclamation text-white text-lg"></i>
                </div>
                <div>
                  <h4 class="font-bold text-gray-900">Areas to Improve</h4>
                  <span class="text-xs text-gray-500 uppercase tracking-wide">Deficiencies</span>
                </div>
              </div>
              <ul class="space-y-2.5">
                <template x-for="d in strategy.deficiencies" :key="d">
                  <li class="flex items-start gap-2 text-sm text-gray-700">
                    <span class="text-red-500 font-bold mt-0.5 flex-shrink-0">•</span>
                    <span x-text="d"></span>
                  </li>
                </template>
              </ul>
            </div>

            <!-- Action Steps -->
            <div class="rounded-xl border-2 bg-blue-50 border-blue-200 shadow p-7">
              <div class="flex items-center gap-3 mb-5">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-md flex-shrink-0">
                  <i class="fas fa-list-check text-white text-lg"></i>
                </div>
                <div>
                  <h4 class="font-bold text-gray-900">Action Plan</h4>
                  <span class="text-xs text-gray-500 uppercase tracking-wide">Next steps</span>
                </div>
              </div>
              <ol class="space-y-2.5">
                <template x-for="(step, idx) in strategy.actionSteps" :key="step">
                  <li class="flex items-start gap-2 text-sm text-gray-700">
                    <span class="text-blue-600 font-bold mt-0.5 flex-shrink-0 w-4" x-text="(idx + 1) + '.'"></span>
                    <span x-text="step"></span>
                  </li>
                </template>
              </ol>
            </div>

          </div>
        </template>

        <!-- Error state -->
        <template x-if="strategyError && !strategyLoading">
          <div class="text-center py-10 text-gray-400">
            <i class="fas fa-circle-xmark text-3xl mb-3 text-red-300"></i>
            <p>Could not load strategy analysis. Please try again.</p>
          </div>
        </template>
      </div>
    </template>

  </div>
</section>

<script>
function planSection() {
  return {
    query: '',
    results: [],
    searching: false,
    selectedPlan: null,
    strategy: null,
    strategyLoading: false,
    strategyError: false,

    async search() {
      if (this.query.length < 2) { this.results = []; return; }
      this.searching = true;
      try {
        const res = await fetch('https://{{SITE_DOMAIN}}/api/plan-search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: this.query, count: 10 })
        });
        const data = await res.json();
        this.results = data.records || [];
      } catch (e) {
        this.results = [];
      } finally {
        this.searching = false;
      }
    },

    async selectPlan(plan) {
      this.selectedPlan = plan;
      this.results = [];
      this.query = plan.sponsorName;
      this.strategy = null;
      this.strategyError = false;
      this.strategyLoading = true;
      try {
        const res = await fetch('https://{{SITE_DOMAIN}}/api/plan-strategy', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ein: plan.ein, pn: plan.pn, planName: plan.planName })
        });
        const data = await res.json();
        this.strategy = data;
      } catch (e) {
        this.strategyError = true;
      } finally {
        this.strategyLoading = false;
      }
    }
  }
}
</script>
"""

# Промпт для пользователя (описание стиля и контента)
user_prompt = f"""
corporate professional
"""

# Запрос к модели
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ],
    model="qwen/qwen3-32b",  # Точная модель на Groq[web:17]
    temperature=0.1,
    max_tokens=16384  # Для полного HTML
)

html_code = chat_completion.choices[0].message.content.strip()

# Сохранение в файл
with open('landing.html', 'w', encoding='utf-8') as f:
    f.write(html_code)

print("Сайт сгенерирован: landing.html")
print(html_code[:500] + "..." if len(html_code) > 500 else html_code)
