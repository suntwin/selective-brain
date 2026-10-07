"""Drill 5 'Friday Ready': 30-question mixed revision for the class test on Fri 2026-10-09.
Spaced revisit (new numbers) of every Term 3 Test 1 error from Test_Analysis_2026-10-02, plus the older
Priority Topics in Maths_Brain (indices, factorising/algebraic fractions, % chains, ratio change/combining,
interest, angles, stats/probability, speed, time, order of operations) and the 'wrong named quantity' habit.
pi = 3.14 throughout, as in her tests. Every answer is computed/asserted here."""
import base64
import io
import json
import math
import sys
from fractions import Fraction as F
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon, Rectangle, Arc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sb.drillspec import validate  # noqa: E402
from sb.answers import part_ok, q_seconds  # noqa: E402

INK, PINK, LAV, FILL = "#3b2257", "#ff4fa0", "#9b7bff", "#f3ecff"
SHADE = "#ffc2dd"
PI = 3.14
Q = []


def r2(x):
    return round(x + 1e-9, 2)


def png(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def mcq(id, topic, stem, options, correct, explanation, technique, trap=None, source=None, difficulty=2,
        image=None, shuffle=True):
    assert correct in options, (id, correct, options)
    assert len(set(options)) == len(options), id
    q = {"id": id, "type": "mcq", "topic": topic, "difficulty": difficulty, "stem": stem, "options": options,
         "answer": options.index(correct), "explanation": explanation, "technique": technique, "trap": trap,
         "source": source, "shuffle": shuffle}
    if image:
        q["image"] = image
    Q.append(q)


def numeric(id, topic, stem, answer, explanation, technique, unit="", trap=None, source=None, difficulty=2,
            tolerance=0.001, image=None):
    q = {"id": id, "type": "numeric", "topic": topic, "difficulty": difficulty, "stem": stem,
         "answer": answer, "tolerance": tolerance, "unit": unit, "explanation": explanation,
         "technique": technique, "trap": trap, "source": source}
    if image:
        q["image"] = image
    Q.append(q)


def word(id, topic, stem, parts, solution, technique, trap=None, source=None, difficulty=3, asks_for=None,
         image=None):
    q = {"id": id, "type": "word", "topic": topic, "difficulty": difficulty, "stem": stem, "parts": parts,
         "solution": solution, "technique": technique, "trap": trap, "source": source}
    if asks_for:
        q["asks_for"] = asks_for
    if image:
        q["image"] = image
    for p in parts:
        assert part_ok(p, p["accept"][0] if p.get("accept") else str(p["answer"])), (id, p)
    Q.append(q)


def canvas(w=4.0, h=3.2):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def arc_pts(cx, cy, r, a0, a1, n=80):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


# ------------------------------------------------------------------ diagrams
def fig_overlap():
    fig, ax = canvas(4.4, 2.8)
    ax.add_patch(Rectangle((0, 0), 5, 4, fc="white", ec=INK, lw=2))
    ax.add_patch(Rectangle((3.2, 1.2), 3.8, 3.8, fc=SHADE, ec=INK, lw=2, hatch="//"))
    ax.add_patch(Rectangle((3.2, 1.2), 1.8, 2.8, fc="white", ec=INK, lw=2))
    ax.text(1.5, 1.8, "A", fontsize=16, color=INK, weight="bold")
    ax.text(6.1, 4.3, "B", fontsize=16, color=INK, weight="bold")
    ax.text(3.5, -0.6, "Not drawn to scale", fontsize=8, color="grey", ha="center")
    ax.set_xlim(-0.3, 7.3)
    ax.set_ylim(-0.8, 5.3)
    return png(fig)


def fig_corner_cut():
    fig, ax = canvas(3.0, 3.0)
    ax.add_patch(Rectangle((0, 0), 12, 12, fc=SHADE, ec=INK, lw=2))
    ax.add_patch(Polygon([(0, 0)] + arc_pts(0, 0, 12, 0, 90), fc="white", ec=INK, lw=2))
    ax.text(6, -1.4, "12 cm", ha="center", fontsize=11, color=INK)
    ax.text(13.4, 6, "12 cm", ha="center", va="center", rotation=90, fontsize=11, color=INK)
    ax.set_xlim(-1.5, 15)
    ax.set_ylim(-2.5, 13.5)
    return png(fig)


def fig_ring():
    fig, ax = canvas(3.0, 3.0)
    ax.add_patch(Polygon(arc_pts(0, 0, 10, 0, 360), fc=SHADE, ec=INK, lw=2))
    ax.add_patch(Polygon(arc_pts(0, 0, 6, 0, 360), fc="white", ec=INK, lw=2))
    ax.plot([0, 10], [0, 0], color=INK, lw=1.5)
    ax.text(5, 0.6, "10 cm", ha="center", fontsize=9, color=INK)
    ax.plot([0, 0], [0, -6], color=PINK, lw=1.5)
    ax.text(0.4, -3.4, "6 cm", ha="left", fontsize=9, color=PINK)
    ax.plot(0, 0, "o", color=INK, ms=3)
    ax.set_xlim(-11, 11)
    ax.set_ylim(-11, 11)
    return png(fig)


def fig_three_squares():
    """Squares at P: Sq1 sides at 90/180, Sq2 at 60/150, Sq3 at 35/125 (degrees from the right-hand line)."""
    fig, ax = canvas(5.2, 3.8)
    s = 3.0
    for c, t in [("#e0457b", 90), ("#7a5cff", 60), ("#1f8fd6", 35)]:
        u = (s * math.cos(math.radians(t)), s * math.sin(math.radians(t)))
        v = (s * math.cos(math.radians(t + 90)), s * math.sin(math.radians(t + 90)))
        ax.add_patch(Polygon([(0, 0), u, (u[0] + v[0], u[1] + v[1]), v], fc="none", ec=c, lw=2.2))
    ax.plot([-4.2, 0.4], [0, 0], color=INK, lw=2)
    ax.text(0.15, -0.45, "P", ha="center", fontsize=12, color=INK, weight="bold")

    def mark(a0, a1, r, label, col=INK):
        ax.add_patch(Arc((0, 0), 2 * r, 2 * r, theta1=a0, theta2=a1, color=col, lw=2))
        m = math.radians((a0 + a1) / 2)
        ax.text((r + 0.4) * math.cos(m), (r + 0.4) * math.sin(m), label, ha="center", va="center",
                fontsize=12, color=col, weight="bold")

    mark(150, 180, 1.1, "30°")
    mark(35, 60, 1.9, "25°")
    mark(90, 125, 1.3, "x", "#d4006a")
    ax.set_xlim(-4.4, 4.0)
    ax.set_ylim(-0.9, 4.4)
    return png(fig)


def fig_ext_angle():
    fig, ax = canvas(4.4, 2.8)
    B, C, D = (0, 0), (4, 0), (6.5, 0)
    A = (2, 2 * math.tan(math.radians(66)))
    ax.add_patch(Polygon([A, B, C], fc=FILL, ec=INK, lw=2))
    ax.plot([C[0], D[0]], [0, 0], color=INK, lw=2)
    for (x, y), t, off in [(A, "A", (0, 0.35)), (B, "B", (-0.35, -0.2)), (C, "C", (0, -0.4)), (D, "D", (0.3, -0.2))]:
        ax.text(x + off[0], y + off[1], t, fontsize=12, color=INK, weight="bold", ha="center")
    ax.add_patch(Arc(A, 1.4, 1.4, theta1=246, theta2=294, color=PINK, lw=2))
    ax.text(A[0], A[1] - 1.1, "48°", ha="center", fontsize=10, color=PINK, weight="bold")
    ax.add_patch(Arc(C, 1.2, 1.2, theta1=0, theta2=114, color="#d4006a", lw=2))
    ax.text(C[0] + 0.55, 0.75, "?", fontsize=13, color="#d4006a", weight="bold")
    # equal-side ticks
    for P1 in (B, C):
        mx, my = (A[0] + P1[0]) / 2, (A[1] + P1[1]) / 2
        ax.plot([mx - 0.12, mx + 0.12], [my - 0.05, my + 0.05], color=INK, lw=2)
    ax.set_xlim(-0.8, 7.2)
    ax.set_ylim(-0.8, A[1] + 0.8)
    return png(fig)


ST, PC, FR, RA, SH, AG, AL, IN, NU, SP, MM = (
    "Statistics_Probability", "Percentages", "Fractions", "Ratio_Proportion", "Circles_Composite_Shapes",
    "Angles_Geometry", "Algebra", "Indices", "Number", "Speed_Distance_Time", "Money_Measurement")
T3 = "Test_Analysis_2026-10-02"

# ---------------------------------------------------------------- 1. average + 'different' (P1 Q13)
tot = 4 * 25
heaviest = tot - (20 + 21 + 22)
assert heaviest == 37 and tot - 60 == 40
mcq("q1", ST,
    "Four dogs have an average mass of 25 kg. Each dog has a DIFFERENT whole-number mass, and each is at "
    "least 20 kg. What is the greatest possible mass of the heaviest dog?",
    ["37 kg", "40 kg", "38 kg", "25 kg"], "37 kg",
    "Total = 4 × 25 = 100 kg. Make the other three as light as possible AND different: 20 + 21 + 22 = 63 kg. "
    "Heaviest = 100 − 63 = 37 kg.",
    "Underline condition words first: 'different', 'at least', 'whole number'.",
    trap="Using 20 + 20 + 20 = 60 (40 kg), which ignores 'different'",
    source=T3 + " P1 Q13 (missed 'different masses'); revisit of Drill 4 f1", difficulty=3)

# ---------------------------------------------------------------- 2. % of the NEW total (P1 Q14)
g0 = 0.4 * 150
assert g0 == 60 and F(90, 180) == F(1, 2) and F(90, 150) == F(3, 5)
mcq("q2", PC,
    "A school has 150 pupils and 40% of them are girls. Then 30 more girls join the school. What percentage "
    "of the pupils are girls now?",
    ["50%", "60%", "40%", "45%"], "50%",
    "Girls at first: 40% of 150 = 60. After: 60 + 30 = 90 girls. The school grew too: 150 + 30 = 180 pupils. "
    "90 out of 180 = 50%.",
    "People join or leave → the part AND the total change. New part ÷ NEW total.",
    trap="90 ÷ 150 = 60% (old total)", source=T3 + " P1 Q14 (66/120 instead of 66/132)")

# ---------------------------------------------------------------- 3. fraction of the REMAINING (P2 Q10)
left = F(70, 100) * (1 - F(3, 7))
start = 480 / left
jacket = start * F(70, 100) * F(3, 7)
assert left == F(2, 5) and start == 1200 and jacket == 360 and start - start * F(3, 10) - jacket == 480
word("q3", PC,
     "Ken spent 30% of his savings on a phone. Then he spent 3/7 of the REMAINING money on a jacket. "
     "He had $480 left.",
     [{"label": "a", "prompt": "How much were his savings at first?", "answer": 1200, "unit": "$"},
      {"label": "b", "prompt": "How much did the jacket cost?", "answer": 360, "unit": "$"}],
     ["After the phone: 100% − 30% = 70% is left.",
      "The jacket takes 3/7 of that 70%, so 4/7 of the 70% is left: 4/7 × 70% = 40%.",
      "(a) 40% = $480, so 10% = $120 and 100% = $1200.",
      "(b) Money after the phone = 70% of 1200 = $840. Jacket = 3/7 × 840 = $360.",
      "Check: 1200 − 360 (phone) − 360 (jacket) = 480 ✓"],
     "Bar model: cut off 30%, then split ONLY the leftover part into sevenths.",
     trap="Taking 3/7 of ALL his savings (30% + 43% gone)",
     source=T3 + " P2 Q10 (Robin, 3/5 of the remaining); spaced revisit of Drill 4 w1/w2",
     asks_for={"prompt": "Before you start: the 3/7 is a fraction of…",
               "options": ["All his savings", "The money left after the phone", "The $480"], "answer": 1})

# ---------------------------------------------------------------- 4. indices: power of a product
assert 3 ** 3 == 27 and 2 * 3 == 6
mcq("q4", IN, "Simplify (3x²)³",
    ["27x⁶", "9x⁶", "3x⁶", "27x⁵"], "27x⁶",
    "The power goes on EVERYTHING inside the bracket: 3³ × (x²)³ = 27 × x⁶ = 27x⁶.",
    "Power of a power: MULTIPLY the indices. The number gets the power too: 3³ = 27, not 3 × 3.",
    trap="9x⁶ (3 × 3), 3x⁶ (forgot the 3), or x⁵ (added the indices)",
    source="Maths_Brain Priority #1 (Indices); Test_Analysis_2026-03-19, 2026-03-09")

# ---------------------------------------------------------------- 5. overlap counted once (P2 Q5)
A, B = 12, 9                  # A : B = 4 : 3
sh = F(2, 3) * B
ov = B - sh
unsh = A
assert (sh, ov) == (6, 3) and F(sh, unsh) == F(1, 2) and A + B - ov == sh + unsh
mcq("q5", RA,
    "Rectangles A and B overlap. Area of A : area of B = 4 : 3. The SHADED part is the part of B that is NOT "
    "inside A, and it is 2/3 of the area of B. What is the ratio of the shaded area to the unshaded area of "
    "the whole figure?",
    ["1 : 2", "2 : 5", "2 : 7", "1 : 3"], "1 : 2",
    "Let A = 12 units, B = 9 units. Shaded = 2/3 × 9 = 6 units, overlap = 9 − 6 = 3 units. The unshaded part "
    "is all of A (overlap included) = 12 units. Shaded : unshaded = 6 : 12 = 1 : 2.",
    "Split the figure into 3 regions FIRST: A only, overlap, B only. The overlap is counted once.",
    trap="Using A + B = 21 as the whole (6 : 15 = 2 : 5), counting the overlap twice",
    source=T3 + " P2 Q5 (answered 1:10, correct 5:12)", difficulty=3, image=fig_overlap())

# ---------------------------------------------------------------- 6. order of operations with negatives
val = -12 / -3 + 4 * (-2) ** 2
assert val == 20
mcq("q6", NU, "Work out: −12 ÷ (−3) + 4 × (−2)²",
    ["20", "−12", "12", "−20"], "20",
    "Powers first: (−2)² = 4. Then ÷ and ×: −12 ÷ −3 = 4 and 4 × 4 = 16. Then add: 4 + 16 = 20.",
    "BIDMAS, and (−2)² = (−2) × (−2) = +4. Negative ÷ negative = positive.",
    trap="Treating (−2)² as −4 (gives −12) or −12 ÷ −3 as −4 (gives 12)",
    source="Mistake_Tracker Test 1 (2026-06-18) negative numbers / order of operations")

# ---------------------------------------------------------------- 7. quarter circle cut out (P2 Q12a/b, P1 Q27)
arc = r2(2 * PI * 12 / 4)
per = r2(12 + 12 + arc)
area = r2(12 * 12 - PI * 12 * 12 / 4)
assert (arc, per, area) == (18.84, 42.84, 30.96)
word("q7", SH,
     "A quarter circle of radius 12 cm is cut out of a 12 cm square, centred at one corner. The shaded part is "
     "what is left. (Use π = 3.14)",
     [{"label": "a", "prompt": "Find the perimeter of the shaded part.", "answer": 42.84, "unit": "cm",
       "tolerance": 0.01},
      {"label": "b", "prompt": "Find the area of the shaded part.", "answer": 30.96, "unit": "cm²",
       "tolerance": 0.01}],
     ["(a) Trace the shaded edge: two straight sides of the square (12 + 12 = 24 cm) and the curved arc.",
      "Quarter arc = 2 × 3.14 × 12 ÷ 4 = 18.84 cm (that's πr ÷ 2, not πr ÷ 4).",
      "Perimeter = 24 + 18.84 = 42.84 cm.",
      "(b) Square = 12 × 12 = 144 cm². Quarter circle = 3.14 × 12 × 12 ÷ 4 = 113.04 cm².",
      "Shaded = 144 − 113.04 = 30.96 cm²."],
     "Perimeter: trace the edge of the SHADED part with your finger. Quarter arc = 2πr ÷ 4.",
     trap="Using πr/4 = 9.42 for the arc; adding all 4 square sides",
     source=T3 + " P2 Q12a (πr/4 slip), Q12b (area blank), P1 Q27 (perimeter of shaded parts)",
     asks_for={"prompt": "The perimeter of the shaded part is made of…",
               "options": ["2 sides of the square + the curved arc", "All 4 sides of the square",
                           "The curved arc only"], "answer": 0},
     image=fig_corner_cut())

# ---------------------------------------------------------------- 8. factorise fully
for x, y in [(1, 2), (3, -1), (-2, 5)]:
    assert 6 * x * x * y + 9 * x * y == 3 * x * y * (2 * x + 3)
mcq("q8", AL, "Factorise FULLY: 6x²y + 9xy",
    ["3xy(2x + 3)", "3(2x²y + 3xy)", "3x(2xy + 3y)", "xy(6x + 9)"], "3xy(2x + 3)",
    "HCF of the numbers: 3. HCF of the letters: x and y are in both terms. HCF = 3xy. "
    "6x²y ÷ 3xy = 2x and 9xy ÷ 3xy = 3. So 6x²y + 9xy = 3xy(2x + 3).",
    "Fully = take out the number AND every letter they share. Check: nothing left inside has a common factor.",
    trap="Taking out only the number 3 (or only x, or only xy)",
    source="Test_Analysis_2026-topictest4-datetbd Q3c (only factored out the numeral)")

# ---------------------------------------------------------------- 9. three squares (P1 Q28)
sq2_low = 180 - 30 - 90
sq3_low = sq2_low - 25
x = sq3_low + 90 - 90
assert (sq2_low, sq3_low, x) == (60, 35, 35) and x == 90 - 30 - 25
mcq("q9", AG,
    "Three identical squares share the corner P. The bottom side of the left square lies on a straight line. "
    "Use the marked angles to find x.",
    ["35°", "25°", "30°", "45°"], "35°",
    "Name the small slices at P from left to right: 30°, a, x, b, 25°. Each square's corner is 90°: "
    "left square 30 + a + x = 90, middle square a + x + b = 90, right square x + b + 25 = 90. "
    "The first two give b = 30. Then x + 30 + 25 = 90, so x = 35°. (Short cut: x = 90 − 30 − 25.)",
    "Label every slice at the shared corner (a, b, x) and write one '= 90' equation per square.",
    trap="Copying one of the marked angles (25° or 30°)",
    source=T3 + " P1 Q28 (three squares, abandoned; answer 27°); revisit of Drill 4 f12", difficulty=3,
    image=fig_three_squares())

# ---------------------------------------------------------------- 10. reverse GST
assert abs(143 / 1.1 - 130) < 1e-9 and r2(143 * 0.9) == 128.7
mcq("q10", PC, "A toaster costs $143 including 10% GST. What is its price BEFORE GST?",
    ["$130", "$128.70", "$133", "$157.30"], "$130",
    "Price with GST = 110% of the price before GST. 110% = $143, so 10% = $13 and 100% = $130.",
    "Reverse percentage: the $143 is 110%, not 100%. Divide by 110, times 100.",
    trap="Taking 10% off $143 ($128.70)", source="Maths_Brain Priority #3 (reverse %); Test_Analysis_2026-07-17 P2 Q1 (GST)")

# ---------------------------------------------------------------- 11. algebraic fractions, sign
for xv in [0, 1, 5, -3]:
    assert F(xv + 3, 4) - F(xv - 1, 6) == F(xv + 11, 12)
mcq("q11", AL, "Simplify: (x + 3)/4 − (x − 1)/6",
    ["(x + 11)/12", "(x + 7)/12", "(5x + 7)/12", "(x + 2)/2"], "(x + 11)/12",
    "Common denominator 12: 3(x + 3)/12 − 2(x − 1)/12 = (3x + 9 − 2x + 2)/12 = (x + 11)/12. "
    "The minus goes on BOTH terms of 2(x − 1): −2x and +2.",
    "Put the second numerator in brackets before subtracting: − (2x − 2) = −2x + 2.",
    trap="−2x − 2 (sign not distributed) gives (x + 7)/12",
    source="Test_Analysis_2026-topictest4-datetbd Q8d (sign error subtracting fractions)", difficulty=3)

# ---------------------------------------------------------------- 12. annulus
ring = r2(PI * (10 ** 2 - 6 ** 2))
assert ring == 200.96 and r2(PI * 4 ** 2) == 50.24
mcq("q12", SH, "Find the area of the shaded ring. (Use π = 3.14)",
    ["200.96 cm²", "50.24 cm²", "113.04 cm²", "314 cm²"], "200.96 cm²",
    "Big circle = 3.14 × 10 × 10 = 314 cm². Small circle = 3.14 × 6 × 6 = 113.04 cm². "
    "Ring = 314 − 113.04 = 200.96 cm².",
    "Ring = big circle − small circle. Square each radius separately; don't subtract the radii first.",
    trap="3.14 × (10 − 6)² = 50.24", source="Circles_Composite_Shapes common mistakes; Test_Analysis_2025-10-01 Q17/Q20 (annulus)",
    image=fig_ring())

# ---------------------------------------------------------------- 13. wrong named quantity
n = F(68 - 8, 5)
assert n == 12 and 2 * n == 24 and 2 * n + 8 == 32 and n + 2 * n + 2 * n + 8 == 68
mcq("q13", AL,
    "Ben has some cards. Cal has twice as many as Ben. Dan has 8 more than Cal. Altogether they have 68 cards. "
    "How many cards does CAL have?",
    ["24", "12", "32", "36"], "24",
    "Let Ben = x. Cal = 2x, Dan = 2x + 8. x + 2x + 2x + 8 = 68, so 5x = 60 and x = 12. "
    "But the question asks for CAL: 2 × 12 = 24.",
    "Circle WHO the question asks about before you start, and check it again before you write the answer.",
    trap="Answering with x = 12 (Ben) or Dan's 32",
    source="Test_Analysis_2026-07-17 P2 Q6 (answered for the wrong person)")

# ---------------------------------------------------------------- 14. two % changes
p1 = 80 * 1.2 * 0.75
assert abs(p1 - 72) < 1e-9 and abs((p1 - 80) / 80 + 0.10) < 1e-9
mcq("q14", PC,
    "A $80 game goes UP in price by 20%. Later the new price goes DOWN by 25%. What is the overall change "
    "compared with the original $80?",
    ["10% decrease", "5% decrease", "No change", "5% increase"], "10% decrease",
    "After +20%: 80 × 1.2 = $96. After −25%: 96 × 0.75 = $72. Change = 72 − 80 = −$8, and 8 ÷ 80 = 10%. "
    "So a 10% decrease.",
    "Each new percentage is of the NEW price. Work it out in dollars, then compare with the ORIGINAL.",
    trap="20 − 25 = 5% decrease (adding the percentages)",
    source="Percentages common mistakes (multi-step chains); Maths_Brain Priority #3", difficulty=3)

# ---------------------------------------------------------------- 15. card transfers (P2 Q17)
n = 18
m, no, z = n, n, n
g1 = F(1, 3) * m
m, no = m - g1, no + g1
g2 = F(1, 4) * no
no, z = no - g2, z + g2
assert (m, no, z) == (12, 18, 24) and z - m == 12 and F(2, 3) * n == 12
word("q15", AL,
     "Mia, Noah and Zara each had n stickers. Mia gave 1/3 of her stickers to Noah. Then Noah gave 1/4 of ALL "
     "his stickers to Zara. In the end, Zara had 12 more stickers than Mia.",
     [{"label": "a", "prompt": "Find n.", "answer": 18},
      {"label": "b", "prompt": "How many stickers did Zara have in the end?", "answer": 24, "unit": "stickers"}],
     ["Make a table. Start: Mia n, Noah n, Zara n.",
      "Mia gives n/3: Mia = 2n/3, Noah = 4n/3, Zara = n.",
      "Noah gives 1/4 of 4n/3 = n/3: Noah = n, Zara = 4n/3.",
      "Zara − Mia = 4n/3 − 2n/3 = 2n/3 = 12, so n = 18.",
      "(b) Zara = 4/3 × 18 = 24. Check: 18,18,18 → 12,24,18 → 12,18,24. 24 − 12 = 12 ✓"],
     "One row per step, one column per person. Keep everything in n until the end.",
     trap="Taking 1/4 of Noah's ORIGINAL n instead of all his stickers after Mia's gift",
     source=T3 + " P2 Q17 (5-mark transfer problem, not reached); revisit of Drill 4 w6", difficulty=4,
     asks_for={"prompt": "Part (b) asks about whose stickers?", "options": ["Mia", "Noah", "Zara"], "answer": 2})

# ---------------------------------------------------------------- 16. % increase, divide by ORIGINAL
assert F(16, 64) == F(1, 4) and F(16, 80) == F(1, 5)
mcq("q16", PC, "A puppy's mass went from 6.4 kg to 8 kg. What is the percentage increase?",
    ["25%", "20%", "16%", "125%"], "25%",
    "Increase = 8 − 6.4 = 1.6 kg. Percentage increase = 1.6 ÷ 6.4 × 100% = 25%.",
    "Percentage change = change ÷ ORIGINAL × 100%. Copy the given numbers carefully.",
    trap="Dividing by the new value 8 (20%)",
    source="Test_Analysis_2026-07-10 P1 Q25 (misread the given number); Mistake_Tracker 2026-07-10")

# ---------------------------------------------------------------- 17. ratio change
k = 12 // (5 - 3)
assert k == 6 and 5 * k - 12 == 3 * k and 3 * k == 18
mcq("q17", RA,
    "At a camp, the ratio of boys to girls is 5 : 3. After 12 boys go home, there are the same number of boys "
    "and girls. How many GIRLS are at the camp?",
    ["18", "30", "12", "6"], "18",
    "Girls don't change. Boys 5 units, girls 3 units. Boys − 12 = girls, so 2 units = 12 and 1 unit = 6. "
    "Girls = 3 × 6 = 18.",
    "Find what stays the same (the girls). The change (12) matches the difference in units (5 − 3 = 2).",
    trap="Giving the boys (30) or one unit (6)",
    source="Ratio_Proportion common mistakes (ratio changes partway); Maths_Brain Priority #5")

# ---------------------------------------------------------------- 18. scientific notation
assert abs(4.5e-4 - 0.00045) < 1e-15
mcq("q18", IN, "Write 0.00045 in scientific notation.",
    ["4.5 × 10⁻⁴", "4.5 × 10⁴", "45 × 10⁻⁵", "4.5 × 10⁻³"], "4.5 × 10⁻⁴",
    "Move the decimal point 4 places right to get 4.5 (a number from 1 to 10). The number is small, so the "
    "power is negative: 4.5 × 10⁻⁴.",
    "Small number (less than 1) → negative power. The front number must be between 1 and 10.",
    trap="Positive power (10⁴), or 45 × 10⁻⁵ (front number not between 1 and 10)",
    source="Test_Analysis_2026-03-09 / 2026-03-19 (scientific notation sign errors)")

# ---------------------------------------------------------------- 19. exterior angle of isosceles triangle
base = (180 - 48) / 2
assert base == 66 and 180 - base == 114
mcq("q19", AG, "In triangle ABC, AB = AC and ∠BAC = 48°. BC is extended to D. Find ∠ACD.",
    ["114°", "66°", "132°", "124°"], "114°",
    "AB = AC, so the base angles are equal: (180 − 48) ÷ 2 = 66°. ∠ACB = 66°. "
    "∠ACD is on a straight line with ∠ACB: 180 − 66 = 114°.",
    "Spot the equal sides (tick marks) → equal base angles. Then use the straight line.",
    trap="Stopping at the base angle (66°)",
    source="Maths_Brain Priority #4 (angle geometry in composite figures)", image=fig_ext_angle())

# ---------------------------------------------------------------- 20. simple interest, total amount
si = 500 * 0.04 * 3
assert abs(si - 60) < 1e-9
numeric("q20", PC,
        "Zoe puts $500 in the bank at 4% per year SIMPLE interest. How much money will she have in the bank "
        "after 3 years (savings + interest)?",
        560,
        "Interest each year = 4% of $500 = $20. For 3 years: 3 × $20 = $60. Total = $500 + $60 = $560.",
        "Simple interest: the same amount every year (I = P × r × T). Read whether they want the interest "
        "or the TOTAL.",
        unit="$", trap="Answering only the interest ($60) or using compound interest ($562.43)",
        source="Test_Analysis_2026-02-14 Q20-22 (simple vs compound); Maths_Brain Priority #7", tolerance=0.01)

# ---------------------------------------------------------------- 21. combine two ratios
assert F(3, 4) * F(6, 5) == F(9, 10)
mcq("q21", RA, "A : B = 3 : 4 and B : C = 6 : 5. If C = 50, what is A?",
    ["45", "30", "60", "40"], "45",
    "Make B the same in both: A : B = 9 : 12 and B : C = 12 : 10. So A : B : C = 9 : 12 : 10. "
    "C = 10 units = 50, so 1 unit = 5 and A = 9 × 5 = 45.",
    "To join two ratios, make the shared letter (B) the same number using the LCM.",
    trap="Treating A : C as 3 : 5 (gives 30)",
    source="Test_Analysis_2026-07-10 P1 Q11 (didn't combine the second ratio); Ratio common mistakes", difficulty=3)

# ---------------------------------------------------------------- 22. fraction of fractions
glasses = F(2, 5) * F(3, 4) + F(3, 5) * F(1, 3)
assert glasses == F(1, 2)
mcq("q22", FR,
    "In a class, 2/5 of the pupils are girls. 3/4 of the girls and 1/3 of the boys wear glasses. What fraction "
    "of the WHOLE class wears glasses?",
    ["1/2", "3/10", "13/24", "1/4"], "1/2",
    "Girls with glasses = 3/4 of 2/5 = 3/10. Boys are 3/5 of the class, so boys with glasses = 1/3 of 3/5 = 1/5. "
    "Total = 3/10 + 2/10 = 5/10 = 1/2.",
    "'of' means × . Each fraction is of a DIFFERENT group, so change each to a fraction of the whole class first.",
    trap="Adding 3/4 and 1/3 or averaging them (13/24); forgetting the boys (3/10)",
    source="Fractions common mistakes (fraction-of-remainder / combinations, class notes 2024-06-30)", difficulty=3)

# ---------------------------------------------------------------- 23. speed in km/h from minutes
assert 18 / (45 / 60) == 24
mcq("q23", SP, "A cyclist rides 18 km in 45 minutes. What is her average speed in km/h?",
    ["24 km/h", "0.4 km/h", "13.5 km/h", "40 km/h"], "24 km/h",
    "45 minutes = 3/4 hour. Speed = 18 ÷ 3/4 = 18 × 4/3 = 24 km/h. (Or: 18 km in 45 min → 6 km per 15 min → "
    "24 km per 60 min.)",
    "Change minutes to hours BEFORE dividing.",
    trap="18 ÷ 45 = 0.4 (minutes not changed to hours)", source="Speed_Distance_Time (recheck area, Mistake Map)")

# ---------------------------------------------------------------- 24. 24-hour time over midnight
start_m = 21 * 60 + 35 + 3 * 60 + 50
assert start_m % (24 * 60) == 1 * 60 + 25
mcq("q24", MM, "A bus leaves at 21:35 and the trip takes 3 h 50 min. What time does it arrive (12-hour time)?",
    ["1:25 am", "1:25 pm", "12:25 am", "11:25 pm"], "1:25 am",
    "21:35 + 3 h = 00:35. 00:35 + 50 min = 01:25, which is 1:25 am the next morning.",
    "Add hours, then minutes; carry 60 minutes into an hour. After 24:00 it is the next day (am).",
    trap="Writing pm, or not carrying the hour (12:25 am)",
    source="Money_Measurement (time and 24-hour time, Drill 2 follow-up)")

# ---------------------------------------------------------------- 25. regular polygon
assert 360 // (180 - 140) == 9
mcq("q25", AG, "Each interior angle of a regular polygon is 140°. How many sides does it have?",
    ["9", "8", "7", "10"], "9",
    "Exterior angle = 180 − 140 = 40°. The exterior angles add to 360°, so the number of sides = 360 ÷ 40 = 9.",
    "Interior + exterior = 180°. Number of sides = 360 ÷ exterior angle.",
    trap="Dividing 360 by 140, or guessing 8", source="Angles_Geometry (polygons), mixed revision")

# ---------------------------------------------------------------- 26. mean after removing a number
assert 5 * 12 - 4 * 10 == 20
mcq("q26", ST,
    "The mean of 5 numbers is 12. One number is removed and the mean of the 4 numbers left is 10. "
    "Which number was removed?",
    ["20", "2", "22", "10"], "20",
    "Total of 5 numbers = 5 × 12 = 60. Total of 4 numbers = 4 × 10 = 40. Removed = 60 − 40 = 20.",
    "Means → change to TOTALS first (mean × how many), then compare the totals.",
    trap="12 − 10 = 2 (subtracting the means)", source=T3 + " P1 Q13 (average → total); Statistics topic")

# ---------------------------------------------------------------- 27. probability without replacement
p = F(3, 10) * F(2, 9)
assert p == F(1, 15)
mcq("q27", ST,
    "A bag has 3 red, 5 blue and 2 green balls. Two balls are taken out one after the other WITHOUT putting the "
    "first one back. What is the probability that both are red?",
    ["1/15", "9/100", "1/5", "3/10"], "1/15",
    "First red: 3/10. Now 9 balls are left and 2 are red: 2/9. Both red = 3/10 × 2/9 = 6/90 = 1/15.",
    "Without replacement → the second fraction has one fewer on top AND bottom. Multiply along the branches.",
    trap="3/10 × 3/10 = 9/100 (as if the ball was put back)",
    source="Test_Analysis_2026-05-15 Q6b/c (tree-diagram probability)", difficulty=3)

# ---------------------------------------------------------------- 28. DOPS
for xv in [0, 1, 7, -4]:
    assert (xv + 2) ** 2 - 49 == (xv - 5) * (xv + 9)
mcq("q28", AL, "Factorise: (x + 2)² − 49",
    ["(x − 5)(x + 9)", "(x + 5)(x − 9)", "(x − 5)(x − 9)", "(x + 2 − 49)(x + 2 + 49)"], "(x − 5)(x + 9)",
    "49 = 7². Difference of two squares: a² − b² = (a − b)(a + b) with a = x + 2 and b = 7. "
    "(x + 2 − 7)(x + 2 + 7) = (x − 5)(x + 9).",
    "a² − b² = (a − b)(a + b). Find b by square-rooting the number.",
    trap="Forgetting to square-root 49, or mixing up the signs",
    source="Test_Analysis_2026-topictest4-datetbd Q3e ((x−3)² − 121 abandoned)", difficulty=3)

# ---------------------------------------------------------------- 29. tickets (assumption) + final-line check
a = (446 - 8 * 40) // (15 - 8)
c = 40 - a
assert a == 18 and c == 22 and 15 * a + 8 * c == 446 and 15 * a - 8 * c == 94
word("q29", MM,
     "A school concert sold 40 tickets: adult tickets cost $15 and child tickets cost $8. The total takings were "
     "$446.",
     [{"label": "a", "prompt": "How many CHILD tickets were sold?", "answer": 22, "unit": "tickets"},
      {"label": "b", "prompt": "How much MORE money came from adult tickets than from child tickets?",
       "answer": 94, "unit": "$"}],
     ["Suppose all 40 were child tickets: 40 × $8 = $320. That is $446 − $320 = $126 short.",
      "Each adult ticket adds $15 − $8 = $7 more, so adult tickets = 126 ÷ 7 = 18.",
      "(a) Child tickets = 40 − 18 = 22.",
      "(b) Adults: 18 × 15 = $270. Children: 22 × 8 = $176. Difference = 270 − 176 = $94.",
      "Check: 270 + 176 = 446 ✓"],
     "Assumption method: pretend they are all one kind, then swap one at a time.",
     trap="(a) giving the adult tickets (18); (b) giving a total instead of the difference",
     source="Test_Analysis_2026-07-10 P2 Q13 (assumption/contest problem skipped); wrong-quantity habit",
     asks_for={"prompt": "Part (b) asks for…",
               "options": ["The total money", "Adult money − child money", "The number of adult tickets"],
               "answer": 1})

# ---------------------------------------------------------------- 30. % of new total, people leave
r0 = 0.25 * 80
assert r0 == 20 and F(20, 80 - 16) == F(5, 16) and F(20, 64) * 100 == F(125, 4)
numeric("q30", PC,
        "A swimming club has 80 members, and 25% are under 10. Then 16 members who are 10 or OLDER leave the "
        "club. What percentage of the club is under 10 now?",
        31.25,
        "Under 10: 25% of 80 = 20 (this does not change). Members now: 80 − 16 = 64. 20 ÷ 64 × 100% = 31.25%.",
        "Leaving changes the total. Part that stays the same ÷ NEW total.",
        unit="%", trap="Keeping 25%, or 20 ÷ 80", source=T3 + " P1 Q14 (changing whole, reversed)",
        difficulty=3, tolerance=0.01)

# ---------------------------------------------------------------- write
assert len(Q) == 30 and len({q["id"] for q in Q}) == 30
drill = {
    "id": "2026-10-07_friday_ready",
    "title": "Drill 5 · Friday Ready 🚀",
    "drill_date": "2026-10-07",
    "subject": "Maths",
    "pace_seconds": 90,
    "focus": ["Term 3 mistakes, new numbers", "Condition words", "% of the NEW total", "Fraction of the remaining",
              "Circles: arc = 2πr ÷ 4", "Indices & factorising", "Who does the question ask about?"],
    "source_note": "Revision for the class test on Fri 2026-10-09. Spaced revisit of every Test_Analysis_2026-10-02 "
                   "error (P1 Q13, Q14, Q27, Q28; P2 Q5, Q9, Q10, Q12, Q17) with new numbers, plus Maths_Brain "
                   "Priority Topics and older logged slips (topictest4, 2026-07-10, 2026-07-17, 2026-05-15, "
                   "2026-03, 2026-02-14). π = 3.14.",
    "questions": Q,
}
errs = validate(drill)
assert not errs, errs
mins = round(sum(q_seconds(q, 90) for q in Q) / 60)
drill["minutes"] = mins
name = "2026-10-07_friday_ready.json"
txt = json.dumps(drill, indent=1, ensure_ascii=False)
(ROOT / "drills" / name).write_text(txt, encoding="utf-8")
vault = ROOT.parent / "Siyonah Selective Brain Prep" / "Practice" / "App_Drills"
if vault.is_dir():
    (vault / name).write_text(txt, encoding="utf-8")
if len(sys.argv) > 1:
    Path(sys.argv[1], name).write_text(txt, encoding="utf-8")
print("wrote", name, len(Q), "questions,", mins, "min,", len(txt) // 1000, "KB")
