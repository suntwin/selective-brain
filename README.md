# 🦄 Selective Brain

Siyonah's sparkly daily practice app for the Victorian Selective Entry High School exam (sitting ~June 2027).

**The daily loop**
1. **Check in (1 min):** energy, mood and time available set today's size: Full, Normal, Light or Rest.
2. **Drill:** questions built from the Obsidian vault, with an exam-style countdown and a pace marker ("2 ahead of exam pace"). XP for every answer, a speed bonus and a streak.
3. **Fix-it:** each wrong answer gets a reason (concept, careless, misread, time) and a one-line fix in her own words. Each one becomes a card in her **Mistake & Technique Notebook**.
4. **Recall:** notebook cards come back after 1, 2, 4, 7, 14 and 30 days until they're mastered.
5. **Back to the vault:** Parent Hub → Export gives Markdown results for `Practice/Results/`. Claude then updates `Mistake_Tracker` and `Maths_Brain` and builds the next drill.

---

## One-time setup (about 20 minutes)

### 1. Supabase
1. https://supabase.com → **New project** (any name, e.g. `selective-brain`). Region: Sydney.
2. **SQL Editor → New query**: paste all of `supabase/schema.sql` and **Run**.
3. **Authentication → Users → Add user** twice, ticking **Auto Confirm User** each time:
   - Siyonah: her email (or something like `siyonah.brain@gmail.com`) plus a password she can type.
   - You: `nitesh.chawla@atturra.com` plus a password.
4. **SQL Editor**: open `supabase/seed_family.sql`, replace `siyonah@example.com` with her email, and **Run**. The last line should list both profiles.
5. **Project Settings → API**: copy the **Project URL** and the **anon public** key. Never use the `service_role` key in the app.

### 2. GitHub
```bash
cd selective-brain
git init && git add . && git commit -m "Selective Brain v1"
gh repo create selective-brain --private --source . --push     # or create it on github.com and push
```

### 3. Streamlit Community Cloud
1. https://share.streamlit.io → **Create app** → choose the `selective-brain` repo, branch `main`, file `app.py`.
2. **Advanced settings → Secrets**, then paste:
   ```toml
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_ANON_KEY = "eyJ..."
   ```
3. Deploy. Bookmark the URL on her laptop.
4. Log in as yourself → **Parent Hub → Publish a drill** → upload `drills/2026-10-04_sparkle_start.json`.

> Without secrets the app runs in **demo mode**, which stores data in a local file. Use it for trying things out, never for real use on Cloud: Cloud deletes local files whenever the app restarts.

### Run locally
```bash
pip install -r requirements.txt
streamlit run app.py          # demo mode, or add .streamlit/secrets.toml for Supabase
```

---

## Making new drills (from the vault)

Ask Claude, in the *Siyonah Selective Brain* project with the vault folder connected, something like:
> "Build tomorrow's 40-min maths drill from the vault, focusing on what she missed in the last export."

Claude writes `Practice/App_Drills/<date>_<name>.json` into the vault. Upload it in **Parent Hub → Publish a drill**.

### Drill JSON format
```json
{
  "id": "2026-10-04_sparkle_start",
  "title": "Drill 1 · Sparkle Start ✨",
  "drill_date": "2026-10-04",
  "pace_seconds": 90,
  "focus": ["Indices", "Final-answer check"],
  "source_note": "Maths_Brain priorities + Mistake_Tracker",
  "questions": [
    {
      "id": "ind1",
      "type": "mcq",
      "topic": "Indices",
      "difficulty": 2,
      "stem": "Simplify (x³)⁴",
      "options": ["x⁷", "x¹²", "x⁸¹", "4x³"],
      "answer": 1,
      "explanation": "Power of a power: multiply the indices…",
      "technique": "Power of a power → MULTIPLY.",
      "trap": "Adding the indices",
      "source": "Mistake_Tracker 2026-03-09"
    },
    { "id": "n1", "type": "numeric", "topic": "Fractions", "stem": "3/4 of 20 = ?", "answer": 15, "tolerance": 0.01, "unit": "" }
  ]
}
```
### Word problems (`"type": "word"`)
She works on paper, then types the final answer for each part. Every part is auto-marked: a fraction like `5/8`, a mixed number, `$`, `%`, a unit such as `45 L`, and commas are all accepted. After answering she sees which parts were right, and the review shows the full worked solution.
```json
{
  "id": "w1", "type": "word", "topic": "Ratio_Proportion", "difficulty": 3,
  "stem": "A bakery sells cupcakes and muffins in the ratio 5 : 3. On Monday it sold 120 more cupcakes than muffins.",
  "parts": [
    {"label": "a", "prompt": "How many muffins were sold?", "answer": 180},
    {"label": "b", "prompt": "What fraction were cupcakes?", "answer": 0.625, "display": "5/8"},
    {"label": "c", "prompt": "Simplest ratio of cupcakes to total?", "accept": ["5:8", "5 : 8"]}
  ],
  "solution": ["Difference 2 units = 120, so 1 unit = 60", "…"],
  "asks_for": {"prompt": "What does part (c) want?", "options": ["…", "…"], "answer": 1},
  "seconds": 270
}
```
- `accept` holds text answers such as ratios or times. `display` controls how the answer is shown. `unit: "$"` shows `$108`.
- `asks_for` is optional. It's a "what is this question really asking?" check before she answers, worth +3 XP. It trains the habit of answering the wrong quantity.
- `seconds` is the time allowed. The default is 90 s per part, with at least 2 parts.
- XP: +6 per correct part, +6 if all parts are right, plus the usual speed bonus.

- `answer` for MCQ is the **0-based index** of the right option. Options are shuffled per attempt unless `"shuffle": false`.
- `topic` must be one of: Fractions, Ratio_Proportion, Percentages, Indices, Algebra, Angles_Geometry, Circles_Composite_Shapes, Statistics_Probability, Speed_Distance_Time, Money_Measurement, Number, Quantitative_Reasoning. These match the vault's `wiki/Topics/` pages.
- Session sizes serve 100%, 75% or 40% of the questions (Full, Normal, Light). The time limit is questions × `pace_seconds`.

## Mistake Map (Parent Hub → 🗺️ Mistake Map, Notebook → 🎯 My focus)

Claude builds the map from every test mistake in the vault and saves it as
`Practice/App_Insights/<date>_mistake_map.json`. Upload it in **Parent Hub → 🗺️ Mistake Map → Update the Mistake Map**.
Uploading again replaces the old map. The format is described at the top of `sb/insights.py`.

- **Parent view:** ranked problem areas, with an "In the app" column showing her live accuracy per topic. Also how she loses marks, cross-topic habits, and the full filterable list.
- **Her view (🎯 My focus):** her top 4 focus areas with tips and progress bars, wins so far, and "super-power habits" she can add to her notebook with one tap (+XP).
- **One-time setup:** run `supabase/003_mistake_map.sql` in Supabase → SQL Editor. It creates the `insights` table. New installs get it from `schema.sql`.

## Where things live
| | |
|---|---|
| `app.py` | Login and navigation (child pages vs parent pages) |
| `views/` | `home` (check-in, plan, topic map), `drill` (player, timer, fix-it), `notebook`, `stars`, `parent` |
| `sb/gamify.py` | XP rules, levels, streak (rest days allowed), badges, spaced-recall intervals |
| `sb/drillspec.py` | Drill validation and the Markdown export for the vault |
| `sb/store.py` | Supabase backend, plus a local JSON backend for demo mode |
| `supabase/` | Schema with Row Level Security (each family sees only its own rows) |
| `tools/` | `build_drill_001.py` (how Drill 1 was generated and answer-checked), `e2e_test.py` |

## Tweaking the game
All XP values, level names and badges are at the top of `sb/gamify.py`. The exam date is the `exam_date` field on her profile row (currently the estimate 2027-06-19). Update it when ACER publishes the 2028-entry dates.
