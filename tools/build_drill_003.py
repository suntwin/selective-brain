"""Drill 3 'Word Problem Workout': multi-part word problems (type: word).
Targets the vault's #1 cross-test habit: right method, wrong/unfinished final answer
(Mistake_Tracker 2026-07-10, 2026-07-17, topictest4). Every answer is computed/asserted here."""
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sb.drillspec import validate  # noqa: E402
from sb.answers import part_ok  # noqa: E402

Q = []


def word(id, topic, stem, parts, solution, technique, trap=None, source=None, difficulty=3, asks_for=None,
         seconds=None):
    q = {"id": id, "type": "word", "topic": topic, "difficulty": difficulty, "stem": stem, "parts": parts,
         "solution": solution, "technique": technique, "trap": trap, "source": source}
    if asks_for:
        q["asks_for"] = asks_for
    if seconds:
        q["seconds"] = seconds
    for p in parts:   # self-check: the stated answer must mark as correct
        assert part_ok(p, p["accept"][0] if p.get("accept") else str(p["answer"])), (id, p)
    Q.append(q)


# W1: ratio with a difference, then a changed ratio --------------------------------------------
unit = 120 / (5 - 3)
muf, cup = 3 * unit, 5 * unit
total = muf + cup
tue_muf = F(5, 8) * total
assert (muf, cup, total, tue_muf - muf) == (180, 300, 480, 120)
word("w1", "Ratio_Proportion",
     "A bakery sells cupcakes and muffins in the ratio 5 : 3. On Monday it sold 120 more cupcakes than muffins.",
     [{"label": "a", "prompt": "How many muffins were sold on Monday?", "answer": 180},
      {"label": "b", "prompt": "What fraction of all the items sold on Monday were cupcakes? (e.g. 2/7)", "answer": 0.625,
       "tolerance": 0.0005, "display": "5/8"},
      {"label": "c", "prompt": "On Tuesday it sold the same total number of items, but in the ratio 3 : 5. "
                               "How many MORE muffins were sold on Tuesday than on Monday?", "answer": 120}],
     ["Difference in units: 5 − 3 = 2 units = 120, so 1 unit = 60.",
      "Muffins = 3 units = 180. Cupcakes = 5 units = 300. Total = 480.",
      "(b) Cupcakes ÷ total = 300/480 = 5/8.",
      "(c) Tuesday muffins = 5/8 of 480 = 300. More than Monday: 300 − 180 = 120."],
     "Ratio + difference: the DIFFERENCE in units equals the given difference. Find 1 unit first.",
     trap="(c) asks for 'how many MORE', not Tuesday's muffins (300)",
     source="Mistake_Tracker 2026-07-10 P2 Q16 (3-day ratio problem left unfinished)",
     asks_for={"prompt": "Before you start: what does part (c) want?",
               "options": ["Muffins sold on Tuesday", "How many MORE muffins on Tuesday than Monday",
                           "Cupcakes sold on Tuesday"], "answer": 1})

# W2: fractions of a container -------------------------------------------------------------------
cap = 21 / (F(3, 4) - F(2, 5))
assert cap == 60 and cap * (1 - F(2, 5)) == 36
word("w2", "Fractions",
     "A water tank was 3/4 full. After Mia used 21 L, the tank was 2/5 full.",
     [{"label": "a", "prompt": "What is the capacity of the tank?", "answer": 60, "unit": "L"},
      {"label": "b", "prompt": "How many more litres are needed now to fill the tank to the top?", "answer": 36, "unit": "L"}],
     ["The 21 L she used = 3/4 − 2/5 of the tank = 15/20 − 8/20 = 7/20.",
      "7/20 = 21 L, so 1/20 = 3 L and the full tank (20/20) = 60 L.",
      "(b) It is 2/5 full, so 3/5 is empty: 3/5 × 60 = 36 L."],
     "Fraction change = amount used. Then re-read: capacity, water left, or space left?",
     trap="Writing the given 21 L as an answer, or giving the water still in the tank (24 L)",
     source="Mistake_Tracker 2026-07-10 P2 Q11 (container: right working, wrong final value)",
     asks_for={"prompt": "Part (b) asks for…", "options": ["The water in the tank now", "The space still empty",
                                                         "The full capacity"], "answer": 1})

# W3: algebra, wrong named quantity -------------------------------------------------------------
t = 180 / 9
assert t == 20 and 4 * t - 15 == 65 and t + 4 * t + 4 * t - 15 == 165
word("w3", "Algebra",
     "Tom, Ava and Leo collect stickers. Ava has 4 times as many as Tom. Leo has 15 fewer than Ava. "
     "Together they have 165 stickers.",
     [{"label": "a", "prompt": "How many stickers does Tom have?", "answer": 20},
      {"label": "b", "prompt": "How many stickers does Leo have?", "answer": 65}],
     ["Let Tom = t. Ava = 4t. Leo = 4t − 15.",
      "t + 4t + 4t − 15 = 165, so 9t = 180 and t = 20.",
      "Leo = 4 × 20 − 15 = 65. (Ava = 80.) Check: 20 + 80 + 65 = 165 ✓"],
     "Name each person with the same letter. At the end, underline WHO the question asks about.",
     trap="Giving Ava's number (80) for Leo", difficulty=2,
     source="Mistake_Tracker 2026-07-17 P2 Q6 (answered the wrong named person)",
     asks_for={"prompt": "Part (b) is about…", "options": ["Tom", "Ava", "Leo"], "answer": 2})

# W4: percentage chain --------------------------------------------------------------------------
final = 160 * 0.75 * 0.9
assert round(final, 2) == 108 and (160 - 108) / 160 * 100 == 32.5
word("w4", "Percentages",
     "A jacket costs $160. It is reduced by 25%. Then a further 10% is taken off the SALE price.",
     [{"label": "a", "prompt": "What is the final price?", "answer": 108, "unit": "$"},
      {"label": "b", "prompt": "What single percentage discount would give the same final price?", "answer": 32.5,
       "unit": "%"}],
     ["25% off: $160 × 0.75 = $120.", "10% off the sale price: $120 × 0.9 = $108.",
      "(b) Total saved = $160 − $108 = $52. $52 ÷ $160 × 100 = 32.5%. (Not 35%: the 10% came off a smaller amount.)"],
     "Percentage chains: each % comes off the NEW amount. Discounts don't simply add.",
     trap="Adding 25% + 10% = 35%", source="Maths_Brain Priority #3 (multi-step %); Mistake_Tracker 2026-07-17 P2 Q1")

# W5: contest scoring ---------------------------------------------------------------------------
c = next(k for k in range(26) if 4 * k - (25 - k) == 70)
assert c == 19 and 4 * c == 76
word("w5", "Quantitative_Reasoning",
     "In a 25-question quiz, a correct answer scores 4 points and a wrong answer loses 1 point. "
     "A blank scores 0. Zoe answered every question and scored 70.",
     [{"label": "a", "prompt": "How many questions did Zoe get right?", "answer": 19},
      {"label": "b", "prompt": "If she had left her wrong ones blank instead, what would her score have been?", "answer": 76}],
     ["If all 25 were right: 100 points. Each wrong one changes +4 into −1, which costs 5 points.",
      "100 − 70 = 30 points lost, and 30 ÷ 5 = 6 wrong. So 25 − 6 = 19 right.",
      "(b) 19 × 4 = 76, and the blanks cost nothing."],
     "Assume everything is right, then work out what each swap costs.",
     trap="Answering the number wrong (6)", source="Mistake_Tracker 2026-07-10 P2 Q13 (skipped entirely)")

# W6: tank volume + drain rate ------------------------------------------------------------------
vol_a = 60 * 30 * 30 / 1000
vol_10 = 60 * 30 * 10 / 1000
assert vol_a == 54 and (vol_a - vol_10) / 1.5 == 24
word("w6", "Money_Measurement",
     "A fish tank is 60 cm long, 30 cm wide and 40 cm high. It is filled with water to 3/4 of its height.",
     [{"label": "a", "prompt": "How many litres of water are in the tank?", "answer": 54, "unit": "L"},
      {"label": "b", "prompt": "Water drains out at 1.5 L per minute. How many minutes until the water is 10 cm deep?",
       "answer": 24, "unit": "min"}],
     ["Water height = 3/4 × 40 = 30 cm.", "Volume = 60 × 30 × 30 = 54 000 cm³ = 54 L.",
      "At 10 cm deep: 60 × 30 × 10 = 18 000 cm³ = 18 L.", "Water to drain = 54 − 18 = 36 L. 36 ÷ 1.5 = 24 minutes."],
     "Tank problems: use the WATER height, not the tank height. Then cm³ ÷ 1000 = L.",
     trap="Using the full 40 cm height (72 L), or draining it all (36 min)",
     source="Mistake_Tracker 2025-11-29 Q48 / 2025-12-05 Q47 (tank volume + rate)")

# W7: elapsed time + speed ----------------------------------------------------------------------
mins = (13 * 60 + 12) - (9 * 60 + 47)
assert mins == 205 and 246 / (mins / 60) == 72
word("w7", "Speed_Distance_Time",
     "A train leaves at 9:47 am and arrives at 1:12 pm. The trip is 246 km.",
     [{"label": "a", "prompt": "How long is the trip in minutes?", "answer": 205, "unit": "min"},
      {"label": "b", "prompt": "What is the train's average speed?", "answer": 72, "unit": "km/h"}],
     ["9:47 → 10:00 is 13 min. 10:00 → 1:00 pm is 3 h (180 min). 1:00 → 1:12 is 12 min.",
      "Total = 13 + 180 + 12 = 205 min.", "205 min = 205/60 h. Speed = 246 ÷ (205/60) = 246 × 60 ÷ 205 = 72 km/h."],
     "Elapsed time: count up to the next hour, then whole hours, then the leftover minutes.",
     trap="Subtracting 9.47 from 13.12 like decimals", difficulty=2, source="Oxford Yr8 8G (duration method)")

drill = {
    "id": "2026-10-05_word_problem_workout",
    "title": "Drill 3 · Word Problem Workout 📝",
    "drill_date": "2026-10-05",
    "subject": "Maths",
    "pace_seconds": 90,
    "focus": ["Finish every part", "Answer what's asked", "Ratio", "Fractions", "Percent chains"],
    "source_note": "Mistake_Tracker 2026-07-10, 2026-07-17, topictest4 cross-cutting pattern: right method, wrong or "
                   "unfinished final answer. Plus Maths_Brain Priority #3/#5 and Oxford Yr8 8G",
    "questions": Q,
}
errs = validate(drill)
assert not errs, errs
out = ROOT / "drills" / "2026-10-05_word_problem_workout.json"
out.write_text(json.dumps(drill, indent=1, ensure_ascii=False), encoding="utf-8")
from sb.answers import q_seconds  # noqa: E402
print("wrote", out.name, len(Q), "word problems,", round(sum(q_seconds(q, 90) for q in Q) / 60), "min")
