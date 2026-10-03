"""Build Drill 001 'Sparkle Start' from vault priorities; every answer is checked by code."""
import json
import math
from fractions import Fraction as F
from pathlib import Path

Q = []


def mcq(id, topic, stem, options, correct, explanation, technique, trap=None, source=None, difficulty=2,
        short=None, shuffle=True):
    assert correct in options, (id, correct, options)
    assert len(set(options)) == len(options), id
    Q.append({"id": id, "type": "mcq", "topic": topic, "difficulty": difficulty, "stem": stem,
              "short": short, "options": options, "answer": options.index(correct),
              "explanation": explanation, "technique": technique, "trap": trap, "source": source,
              "shuffle": shuffle})


# ---------------- Indices (Priority #1) ----------------
assert 3 * 4 == 12
mcq("ind1", "Indices", "Simplify (x³)⁴", ["x⁷", "x¹²", "x⁸¹", "4x³"], "x¹²",
    "Power of a power: multiply the indices. (x³)⁴ = x³ × x³ × x³ × x³ = x³⁺³⁺³⁺³ = x¹².",
    "Power of a power → MULTIPLY. If unsure, write it out the long way.",
    trap="Adding the indices (3 + 4 = 7)", source="Mistake_Tracker 2026-03-09 Q5a/Q7", short="(x³)⁴")
assert 2 ** 3 == 8
mcq("ind2", "Indices", "Simplify (2a³)³", ["2a⁹", "6a⁹", "8a⁹", "8a⁶"], "8a⁹",
    "The outer power applies to EVERYTHING inside: 2³ × (a³)³ = 8 × a⁹.",
    "Bracket to a power: raise the number AND each letter.",
    trap="Leaving the 2 alone, or doing 2×3", source="Mistake_Tracker 2026-03-09 Q8b/Q8c", short="(2a³)³")
mcq("ind3", "Indices", "Work out (5y)⁰ + 5y⁰", ["1", "2", "6", "5y + 1"], "6",
    "(5y)⁰ = 1 because the whole bracket is to the power 0. In 5y⁰ only the y is to the power 0, so 5 × 1 = 5. Total 1 + 5 = 6.",
    "Power 0 makes whatever it touches equal 1. Check what's inside the bracket.",
    trap="Treating both terms the same", source="Mistake_Tracker 2026-03-19 Q4e/Q6b", difficulty=3, short="(5y)⁰ + 5y⁰")
assert F(1, 2 ** 3) == F(1, 8)
mcq("ind4", "Indices", "What is 2⁻³ ?", ["−8", "−6", "1/8", "1/6"], "1/8",
    "A negative index means 'one over': 2⁻³ = 1/2³ = 1/8.",
    "Negative index → flip it (reciprocal). It never makes the answer negative.",
    trap="Thinking a negative index makes a negative number", source="Mistake_Tracker 2026-03-09 Q6b/Q10d", short="2⁻³")
assert 5 - 2 - 2 == 1
mcq("ind5", "Indices", "Simplify 3⁵ × 3⁻² ÷ 3²", ["3", "9", "1/3", "27"], "3",
    "Same base: add the indices when multiplying, subtract when dividing. 5 + (−2) − 2 = 1, so 3¹ = 3.",
    "Same base: × → add indices, ÷ → subtract indices.", source="Topics/Indices", short="3⁵ × 3⁻² ÷ 3²")

# ---------------- Percentages (Priority #3, #7) ----------------
orig = 96 / 0.8
assert orig == 120
mcq("pct1", "Percentages", "After a 20% discount, a jacket costs $96. What was the original price?",
    ["$115.20", "$116", "$120", "$76.80"], "$120",
    "After a 20% discount you pay 80% of the price. 80% = $96, so 1% = $1.20 and 100% = $120.",
    "Reverse %: find what percent you HAVE (100 − 20 = 80%), then work back to 100%.",
    trap="Adding 20% of $96 (gives $115.20)", source="Maths_Brain Priority #3 (reverse percentage)", difficulty=2)
assert round(200 * 1.1 * 0.9, 2) == 198
mcq("pct2", "Percentages", "A $200 bike goes up in price by 10%. Then the new price goes down by 10%. What does it cost now?",
    ["$200", "$198", "$202", "$180"], "$198",
    "$200 × 1.1 = $220. Then 10% of $220 is $22, so $220 − $22 = $198. The second 10% is taken from a bigger number.",
    "Percentage chains: each % is taken from the NEW amount. Write down the base each time.",
    trap="Thinking +10% then −10% cancels out", source="Mistake_Tracker 2026-02-08 Q15", difficulty=2)
ci = 1000 * 1.1 ** 2 - 1000
assert round(ci, 2) == 210
mcq("pct3", "Percentages", "Mum invests $1000 at 10% per year COMPOUND interest for 2 years. How much INTEREST does she earn?",
    ["$200", "$210", "$1210", "$1200"], "$210",
    "Year 1: $1000 + $100 = $1100. Year 2: $1100 + $110 = $1210. The interest is $1210 − $1000 = $210.",
    "Compound = interest on the interest (× 1.1 each year). Simple = the same amount every year. Then re-read: interest or total?",
    trap="Simple interest ($200), or giving the total ($1210) when it asked for interest",
    source="Mistake_Tracker 2026-02-14 Q20–22", difficulty=3)
assert (92 - 80) / 80 * 100 == 15
mcq("pct4", "Percentages", "A plant grew from 80 cm to 92 cm. What is the percentage increase?",
    ["12%", "13.04%", "15%", "92%"], "15%",
    "Increase = 12 cm. Percentage increase = 12 ÷ 80 (the ORIGINAL) × 100 = 15%.",
    "% change = change ÷ ORIGINAL × 100. Circle the original number first.",
    trap="Dividing by the new value (12 ÷ 92)", source="Mistake_Tracker 2026-07-10 P1 Q25", difficulty=2)

# ---------------- Ratio (Priority #5) ----------------
# 3:5 → 7:5 with Ben unchanged; 4 units = 12 → unit 3; Amy first = 9
unit = 12 / (7 - 3)
assert 3 * unit == 9 and 5 * unit == 15
mcq("rat1", "Ratio_Proportion",
    "Amy and Ben have marbles in the ratio 3 : 5. Amy is given 12 more marbles, and now the ratio is 7 : 5. "
    "How many marbles did AMY have at first?",
    ["9", "15", "21", "12"], "9",
    "Ben didn't change, so he stays 5 units. Amy went from 3 units to 7 units, so she gained 4 units. 4 units = 12, which makes 1 unit = 3. Amy at first = 3 × 3 = 9.",
    "Ratio change: draw before and after bars. Keep the person who DIDN'T change the same.",
    trap="Answering Ben's number (15) or Amy's number after (21)", source="ClassNotes 2023-11-26 / 2024-02-04 (ratio-with-change)",
    difficulty=3)
a, b, c = 2 * 4, 3 * 4, 3 * 5  # A:B=2:3, B:C=4:5 → 8:12:15
assert math.gcd(a, c) == 1
mcq("rat2", "Ratio_Proportion", "A : B = 2 : 3 and B : C = 4 : 5. What is A : C?",
    ["2 : 5", "8 : 15", "8 : 12", "10 : 12"], "8 : 15",
    "Make B the same in both: 2:3 = 8:12 and 4:5 = 12:15. So A:B:C = 8:12:15, which gives A:C = 8:15.",
    "Combining ratios: make the shared letter match (use the LCM), then read across.",
    trap="Just joining the outside numbers (2:5)", source="Mistake_Tracker 2026-07-10 P1 Q11", difficulty=3)
share = 360 / 9
assert 4 * share - 2 * share == 80
mcq("rat3", "Ratio_Proportion", "Ria, Sam and Tia share $360 in the ratio 2 : 3 : 4. How much MORE does Tia get than Ria?",
    ["$80", "$160", "$40", "$120"], "$80",
    "Total units = 9, so 1 unit = $40. Tia = 4 units = $160 and Ria = 2 units = $80. Difference = $80.",
    "Find 1 unit first. Then re-read the question: 'how much more' means a difference.",
    trap="Giving Tia's share ($160)", source="Topics/Ratio_Proportion", difficulty=2)

# ---------------- Algebra (Priority #5 + wrong-named-quantity habit) ----------------
n = 70 / 7
assert n == 10 and 3 * n == 30
mcq("alg1", "Algebra",
    "Mia has n stickers. Leo has 3 times as many as Mia. Zoe has 6 more than Leo. Altogether they have 76 stickers. "
    "How many stickers does LEO have?",
    ["10", "30", "36", "70"], "30",
    "n + 3n + (3n + 6) = 76, so 7n = 70 and n = 10. Leo = 3n = 30. (Mia = 10, Zoe = 36.)",
    "Last step: underline WHO the question asks about, then give that person's number.",
    trap="Stopping at n = 10 (Mia), or giving Zoe's number", source="Mistake_Tracker 2026-07-17 P2 Q6", difficulty=2)
x = 17
assert 3 * (x - 4) == 2 * x + 5
mcq("alg2", "Algebra", "Solve 3(x − 4) = 2x + 5", ["x = 17", "x = 9", "x = −7", "x = 1"], "x = 17",
    "Expand: 3x − 12 = 2x + 5. Take 2x from both sides: x − 12 = 5, so x = 17. Check: 3(13) = 39 and 2(17) + 5 = 39 ✓",
    "Expand the bracket to EVERY term inside. Then substitute your answer back to check.",
    trap="Only multiplying the x (3x − 4) gives 9", source="Topics/Algebra", difficulty=2)
# (x+1)/3 − (x−2)/4 = (4x+4 −3x +6)/12 = (x+10)/12
for xv in (0, 1, 5):
    assert F(xv + 1, 3) - F(xv - 2, 4) == F(xv + 10, 12)
mcq("alg3", "Algebra", "Simplify (x + 1)/3 − (x − 2)/4",
    ["(x + 10)/12", "(x − 2)/12", "(x + 6)/12", "(7x − 2)/12"], "(x + 10)/12",
    "Common denominator 12: 4(x + 1) − 3(x − 2) over 12. That's 4x + 4 − 3x + 6 = x + 10. Note that −3 × −2 = +6.",
    "Put brackets round the second numerator. The minus multiplies EVERY term inside.",
    trap="Sign slip: −3 × −2 written as −6", source="Mistake_Tracker topictest4 Q8d", difficulty=3)

# ---------------- Circles & composite (Priority #2) ----------------
per = 3 * 10 + 3.14 * 10 / 2
assert round(per, 2) == 45.7
mcq("cir1", "Circles_Composite_Shapes",
    "A shape is a square with side 10 cm, with a semicircle stuck on the outside of one side. "
    "Find the PERIMETER of the whole shape (use π = 3.14).",
    ["45.7 cm", "55.7 cm", "61.4 cm", "40.7 cm"], "45.7 cm",
    "The outside edge is 3 sides of the square (30 cm) plus a semicircle arc: half of π × 10 = 15.7 cm. 30 + 15.7 = 45.7 cm. The side where they join is INSIDE, so it doesn't count.",
    "Perimeter = trace the outside with your finger. Decide first: full, half or quarter circle.",
    trap="Counting the hidden 4th side (55.7) or a whole circle (61.4)", source="Maths_Brain Priority #2", difficulty=3)
area = 3.14 * 8 ** 2 / 4
assert round(area, 2) == 50.24
mcq("cir2", "Circles_Composite_Shapes", "Find the area of a QUARTER circle with radius 8 cm (use π = 3.14).",
    ["50.24 cm²", "200.96 cm²", "100.48 cm²", "25.12 cm²"], "50.24 cm²",
    "Full circle = π r² = 3.14 × 64 = 200.96. A quarter is ÷ 4 = 50.24 cm².",
    "Area = π r² × fraction (1, ½ or ¼). Write the fraction down before you calculate.",
    trap="Forgetting to take a quarter", source="Test_Analysis 2025-10-01", difficulty=2)

# ---------------- Angles (Priority #4) ----------------
assert (180 - 40) / 2 == 70
mcq("ang1", "Angles_Geometry", "In an isosceles triangle, the angle between the two equal sides is 40°. What size is each of the other two angles?",
    ["40°", "70°", "100°", "140°"], "70°",
    "The two base angles are equal and the angles add to 180°. So (180 − 40) ÷ 2 = 70°.",
    "Name the rule first: 'triangle = 180°, isosceles → base angles equal'.",
    trap="Making the 40° one of the equal angles", source="Maths_Brain Priority #4", difficulty=2)
assert 125 - 48 == 77
mcq("ang2", "Angles_Geometry",
    "An exterior angle of a triangle is 125°. One of the two opposite interior angles is 48°. Find the other opposite interior angle.",
    ["55°", "77°", "103°", "132°"], "77°",
    "Exterior angle = sum of the two opposite interior angles. 125 − 48 = 77°.",
    "Exterior angle rule: outside angle = the two far inside angles added together.",
    trap="Using 180 instead (gives 55° or 132°)", source="Test_Analysis 2024-12-10", difficulty=2)

# ---------------- Fractions ----------------
M = 30 / (F(3, 4) - F(3, 4) * F(2, 3))
assert M == 120
mcq("fra1", "Fractions",
    "Ella spent 1/4 of her money on a book, then 2/3 of what was LEFT on shoes. She now has $30. How much did she have at first?",
    ["$120", "$90", "$360", "$72"], "$120",
    "After the book, 3/4 is left. Shoes = 2/3 of 3/4 = 1/2 of everything. So she has 3/4 − 1/2 = 1/4 left. 1/4 = $30, so all of it = $120.",
    "'Of the remainder': draw a bar, cut it into quarters, then cut what's left into thirds.",
    trap="Taking 2/3 of the whole amount", source="ClassNotes 2024-02-11 (fraction of remainder)", difficulty=3)
C = 6 / (F(2, 3) - F(1, 4))
assert float(C) == 14.4
mcq("fra2", "Fractions", "A tank is 2/3 full. After 6 L is used, it is 1/4 full. What is the CAPACITY of the tank?",
    ["14.4 L", "6 L", "24 L", "9.6 L"], "14.4 L",
    "2/3 − 1/4 = 8/12 − 3/12 = 5/12 of the tank is 6 L. So 1/12 = 1.2 L, and 12/12 = 14.4 L.",
    "Finished? Re-read the question. Is your answer the thing it asks for, or just a number it gave you?",
    trap="Writing the given 6 L as the answer", source="Mistake_Tracker 2026-07-10 P2 Q11", difficulty=3)

# ---------------- Money & Measurement / Speed ----------------
assert 1500 * 7 / 250 == 42
mcq("mea1", "Money_Measurement", "Each bottle holds 1.5 L. How many 250 mL glasses can be filled from 7 bottles?",
    ["42", "6", "26.25", "420"], "42",
    "Change to the same unit: 1.5 L = 1500 mL. 7 × 1500 = 10 500 mL. Then 10 500 ÷ 250 = 42 glasses.",
    "Units first! Change everything to the SAME unit before you calculate.",
    trap="Mixing L and mL", source="ClassNotes 2024-08-11 (unit conversion inside problems)", difficulty=1)
assert 150 / 2.5 == 60
mcq("spd1", "Speed_Distance_Time", "A car travels 150 km in 2 hours 30 minutes. What is its average speed?",
    ["60 km/h", "75 km/h", "65 km/h", "50 km/h"], "60 km/h",
    "2 h 30 min = 2.5 h, not 2.3 h. Speed = 150 ÷ 2.5 = 60 km/h.",
    "Minutes → hours: divide by 60. (30 min = 0.5 h)", trap="Using 2.3 hours, or ignoring the 30 minutes",
    source="Test_Analysis 2025-10-01", difficulty=2)

# ---------------- Number ----------------
assert (-3) ** 2 - 4 * (-2) ** 3 == 41
mcq("num1", "Number", "Calculate (−3)² − 4 × (−2)³", ["41", "−23", "23", "−41"], "41",
    "(−3)² = 9 and (−2)³ = −8. Then 4 × −8 = −32. So 9 − (−32) = 9 + 32 = 41.",
    "Powers first, then ×, then − . Subtracting a negative = adding.", trap="9 − 32 = −23 (sign slip)",
    source="Mistake_Tracker 2026-02-14 Q1a/Q1d", difficulty=2)

# ---------------- Quantitative reasoning ----------------
assert 420 // 35 - 1 == 11
mcq("qr1", "Quantitative_Reasoning", "A 4.2 m ribbon is cut into pieces that are each 35 cm long. How many CUTS are needed?",
    ["11", "12", "13", "120"], "11",
    "420 cm ÷ 35 = 12 pieces. A straight ribbon needs one cut fewer than the number of pieces, so 11 cuts.",
    "Cuts vs pieces: on a straight line, cuts = pieces − 1. Draw 3 pieces to check.",
    trap="Answering the number of pieces (12)", source="Mistake_Tracker 2026-07-10 P1 Q20", difficulty=2)
word = "SPARKLE"
assert word[(100 - 1) % 7] == "P"
mcq("qr2", "Quantitative_Reasoning", "The letters SPARKLE repeat: SPARKLESPARKLESPARK… What is the 100th letter?",
    ["S", "P", "K", "E"], "P",
    "The block is 7 letters long. 100 ÷ 7 = 14 remainder 2, so the 100th letter is the 2nd letter, P.",
    "Repeating patterns: find the block length, then the remainder tells you the position.",
    trap="Remainder 0 means the LAST letter, not the first", source="Mistake_Tracker 2026-07-10 P1 Q15", difficulty=2,
    shuffle=False)
cnt = sum(1 for k in range(10, 100) if (k // 10) % 2 == 1 and (k % 10) % 2 == 1)
assert cnt == 25
mcq("qr3", "Quantitative_Reasoning", "How many two-digit numbers have BOTH digits odd?",
    ["20", "25", "45", "50"], "25",
    "Tens digit: 1, 3, 5, 7, 9 (5 choices). Units digit: 1, 3, 5, 7, 9 (5 choices). 5 × 5 = 25.",
    "Counting: choices for the 1st digit × choices for the 2nd. Don't list them all.",
    trap="Undercounting a list", source="Mistake_Tracker 2026-07-17 P2 Q12", difficulty=2)
cc = next(k for k in range(21) if 5 * k - 2 * (20 - k) == 58)
assert cc == 14
mcq("qr4", "Quantitative_Reasoning",
    "In a quiz you get +5 for a right answer and −2 for a wrong one. Priya answered all 20 questions and scored 58. "
    "How many did she get RIGHT?",
    ["14", "12", "16", "6"], "14",
    "If all 20 were right she'd have 100. Each wrong one costs 5 + 2 = 7 points. 100 − 58 = 42, and 42 ÷ 7 = 6 wrong. So 14 right.",
    "Assume they're all right, then find how many points each swap costs.",
    trap="Giving the number wrong (6)", source="Mistake_Tracker 2026-07-10 P2 Q13", difficulty=3)

# --------------------------------------------------------------------------------
order = ["pct1", "ind1", "rat3", "alg2", "qr1", "cir2", "ind2", "fra1", "num1", "pct2", "alg1", "ang1", "qr2",
         "ind4", "rat1", "mea1", "cir1", "pct4", "ind3", "qr3", "alg3", "spd1", "rat2", "fra2", "ang2", "pct3",
         "ind5", "qr4"]
qm = {q["id"]: q for q in Q}
assert sorted(order) == sorted(qm), set(qm) ^ set(order)
for q in Q:
    q.pop("short") if q.get("short") is None else None
drill = {
    "id": "2026-10-04_sparkle_start",
    "title": "Drill 1 · Sparkle Start ✨",
    "drill_date": "2026-10-04",
    "subject": "Maths",
    "minutes": 42,
    "pace_seconds": 90,
    "focus": ["Indices", "Final-answer check", "Reverse %", "Ratio change", "Circles", "Cuts vs pieces"],
    "source_note": "Maths_Brain Priority Topics #1–#7 + Mistake_Tracker 2026-02 → 2026-07 (each 'trap' mirrors a logged error)",
    "questions": [qm[i] for i in order],
}
out = Path(__file__).resolve().parent.parent / "drills" / "2026-10-04_sparkle_start.json"
out.write_text(json.dumps(drill, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", out, len(drill["questions"]), "questions")
