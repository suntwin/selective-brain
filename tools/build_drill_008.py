"""Drill 8 'Sunday Spiral': spaced revisit (new numbers) of the Mistake Map's Active areas -- circles (shaded
corners, composite perimeter, sectors), percentages (% of a changing total, reverse chains, fraction of the
remaining), ratio (ratio change, overlap), algebra (DOPS with a bracket, fraction signs, transfers) -- plus the
Recheck areas (indices, tank volume/rate, average speed) and older slips (negatives, repeating patterns).
pi = 3.14 as in her tests. Every answer is computed/asserted here."""
import base64
import io
import itertools
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
    assert part_ok(q, str(answer)), id
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




# ------------------------------------------------------------------ diagrams
def _ax(w=3.2, h=3.0):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def arc_pts(cx, cy, r, a0, a1, n=80):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def fig_corner():
    fig, ax = _ax()
    ax.add_patch(Rectangle((0, 0), 10, 10, fc="#ffe3f1", ec=INK, lw=2))
    ax.add_patch(Polygon([(0, 0)] + arc_pts(0, 0, 10, 0, 90), fc="white", ec=INK, lw=2))
    ax.text(5, -1.2, "10 cm", ha="center", color=INK, fontsize=11)
    ax.text(-1.4, 5, "10 cm", va="center", rotation=90, color=INK, fontsize=11)
    ax.set_xlim(-2.2, 11)
    ax.set_ylim(-2.2, 11)
    return png(fig)


def fig_rect_semi():
    fig, ax = _ax(3.8, 2.6)
    pts = [(0, 0), (12, 0)] + arc_pts(12, 4, 4, -90, 90) + [(0, 8)]
    ax.add_patch(Polygon(pts, fc=FILL, ec=INK, lw=2))
    ax.plot([12, 12], [0, 8], color=INK, lw=1, ls=":")
    ax.text(6, -1.3, "12 cm", ha="center", color=INK, fontsize=11)
    ax.text(-1.4, 4, "8 cm", va="center", rotation=90, color=INK, fontsize=11)
    ax.set_xlim(-2.2, 17)
    ax.set_ylim(-2.4, 9)
    return png(fig)


def fig_parallel():
    fig, ax = _ax(4.2, 2.8)
    h = 3.0
    dx = h / math.tan(math.radians(70))
    P, Qp, R = (3.0, h), (3.0 - dx, 0.0), (3.0 + dx, 0.0)
    ax.plot([-0.5, 6.5], [h, h], color=INK, lw=2)
    ax.plot([-0.5, 6.5], [0, 0], color=INK, lw=2)
    ax.add_patch(Polygon([P, Qp, R], fc="#ffe3f1", ec=PINK, lw=2))
    for (x0, y0) in [(5.6, h), (5.6, 0)]:
        ax.annotate("", xy=(x0 + .35, y0), xytext=(x0, y0), arrowprops=dict(arrowstyle="->", color=INK, lw=1.5))
    ax.text(-0.7, h, "A", ha="right", va="center", fontsize=12, color=INK, weight="bold")
    ax.text(6.7, h, "B", va="center", fontsize=12, color=INK, weight="bold")
    ax.text(-0.7, 0, "C", ha="right", va="center", fontsize=12, color=INK, weight="bold")
    ax.text(6.7, 0, "D", va="center", fontsize=12, color=INK, weight="bold")
    ax.text(P[0], P[1] + .3, "P", ha="center", fontsize=12, color=INK, weight="bold")
    ax.text(Qp[0], -.45, "Q", ha="center", fontsize=12, color=INK, weight="bold")
    ax.text(R[0], -.45, "R", ha="center", fontsize=12, color=INK, weight="bold")
    ax.add_patch(Arc(P, 1.4, 1.4, theta1=180, theta2=250, color=INK, lw=1.6))
    ax.text(P[0] - 1.05, P[1] - .45, "70°", fontsize=11, color=INK, weight="bold")
    ax.add_patch(Arc(P, .9, .9, theta1=250, theta2=290, color=PINK, lw=1.6))
    ax.text(P[0], P[1] - .85, "x", ha="center", fontsize=12, color=PINK, weight="bold")
    ax.text(3.0, -1.05, "PQ = PR", ha="center", fontsize=10, color=GREY)
    ax.set_xlim(-1.4, 7.4)
    ax.set_ylim(-1.4, 3.8)
    return png(fig)


GREY = "#6b6880"
SH, PC, RA, AL, IN, AG, ST, MM, SP, NU, QR = (
    "Circles_Composite_Shapes", "Percentages", "Ratio_Proportion", "Algebra", "Indices", "Angles_Geometry",
    "Statistics_Probability", "Money_Measurement", "Speed_Distance_Time", "Number", "Quantitative_Reasoning")

# ================================================================ circles (Active #1)
shaded = r2(10 * 10 - PI * 10 ** 2 / 4)
assert shaded == 21.5
mcq("c1", SH, "A quarter circle of radius 10 cm is cut from a 10 cm square, centred on one corner. Find the area of "
    "the shaded part that is left. (Use π = 3.14)", ["21.5 cm²", "78.5 cm²", "68.6 cm²", "50 cm²"], "21.5 cm²",
    "Square = 10 × 10 = 100 cm². Quarter circle = 3.14 × 10 × 10 ÷ 4 = 78.5 cm². Shaded = 100 − 78.5 = 21.5 cm².",
    "Shaded corner pieces: whole square − quarter circle. Write the fraction (¼) before you calculate.",
    trap="Giving the quarter circle (78.5), or taking away the arc length (100 − 31.4 = 68.6)",
    source="Test_Analysis_2026-10-02 P2 Q12b (quarter-circle design area, blank); spaced revisit of Drills 4/5",
    image=fig_corner())

per = r2(12 + 12 + 8 + PI * 4)
assert per == 44.56
numeric("c2", SH, "A semicircle is joined to the 8 cm end of a 12 cm × 8 cm rectangle. Find the PERIMETER of the "
        "whole shape. (Use π = 3.14)", per,
        "Straight edges: 12 + 12 + 8 = 32 cm (the 8 cm side inside the shape doesn't count). Curved edge = half of "
        "πd = ½ × 3.14 × 8 = 12.56 cm. Perimeter = 32 + 12.56 = 44.56 cm.",
        "Trace the OUTSIDE edge with your finger. A side that's now inside the shape isn't perimeter.",
        unit="cm", trap="Adding the hidden 8 cm side (52.56) or using a full circle", tolerance=0.01,
        source="Test_Analysis_2026-10-02 P1 Q27 (perimeter of shaded parts, skipped)", image=fig_rect_semi())

sp_ = r2(2 * 9 + 60 / 360 * 2 * PI * 9)
assert sp_ == 27.42
mcq("c3", SH, "A sector has radius 9 cm and angle 60°. What is its PERIMETER? (Use π = 3.14)",
    ["27.42 cm", "9.42 cm", "42.39 cm", "36.42 cm"], "27.42 cm",
    "Arc = 60/360 × 2 × 3.14 × 9 = 1/6 × 56.52 = 9.42 cm. Add the two radii: 9 + 9 = 18. Perimeter = 27.42 cm.",
    "Sector perimeter = arc + 2 radii. Arc = (angle ÷ 360) × 2πr.",
    trap="Only the arc (9.42), or the sector AREA (42.39)", source="Maths_Brain Priority #2; Test_Analysis_2025-12-05 Q43")

# ================================================================ percentages (Active #2)
girls, total = 0.4 * 60, 60 - 10
assert girls == 24 and total == 50 and girls / total == 0.48
mcq("p1", PC, "A club has 60 members and 40% are girls. Then 10 boys leave the club. What percentage of the club are "
    "girls now?", ["48%", "40%", "44%", "52%"], "48%",
    "Girls = 40% of 60 = 24, and that doesn't change. The club now has 60 − 10 = 50 members. 24 ÷ 50 = 48%.",
    "People leaving changes the TOTAL. Keep the part that stays the same, divide by the NEW total.",
    trap="Thinking nothing changed for the girls (40%)",
    source="Test_Analysis_2026-10-02 P1 Q14 (% of a changing whole); 3rd spaced revisit")

orig = 108 / (1.2 * 0.9)
assert abs(orig - 100) < 1e-9
mcq("p2", PC, "A bike's price went UP by 20%, then the new price went DOWN by 10%. It now costs $108. What was the "
    "price at the start?", ["$100", "$98", "$110", "$97.20"], "$100",
    "Each change multiplies: × 1.2 then × 0.9 = × 1.08 overall. Start = $108 ÷ 1.08 = $100. Check: 100 → 120 → 108 ✓",
    "Reverse a % chain: turn each change into a multiplier, multiply them, then DIVIDE.",
    trap="Thinking +20% − 10% = +10% (≈ $98), or taking 10% off $108",
    source="Maths_Brain Priority #3 (multi-step %); Drill 5 q14 (chains)", difficulty=3)

start = 135 / ((1 - 0.4) * (1 - 0.25))
cap = start * 0.6 * 0.25
assert round(start) == 300 and round(cap) == 45
word("w1", PC, "Leo spent 40% of his money on shoes. Then he spent 1/4 of the REMAINING money on a cap. He had $135 "
     "left.",
     [{"label": "a", "prompt": "How much money did Leo have at the start?", "answer": 300, "unit": "$"},
      {"label": "b", "prompt": "How much did the cap cost?", "answer": 45, "unit": "$"}],
     ["After the shoes: 100% − 40% = 60% is left.",
      "The cap is 1/4 of that 60%, so 3/4 of the 60% is left: 3/4 × 60% = 45% of his money.",
      "45% = $135, so 1% = $3 and 100% = $300.",
      "(b) After the shoes: 60% of 300 = $180. Cap = 1/4 of 180 = $45. Check: 300 − 120 − 45 = 135 ✓"],
     "Bar model: cut off 40%, then split ONLY the leftover part into quarters.",
     trap="Taking 1/4 of ALL his money (25%), giving 35% left",
     source="Test_Analysis_2026-10-02 P2 Q10 (fraction of the remaining); 3rd spaced revisit",
     asks_for={"prompt": "The 1/4 is a quarter of…", "options": ["All of Leo's money", "The money left after the shoes",
                                                               "The $135"], "answer": 1})

# ================================================================ ratio (Active #3)
k = 16
assert (3 * k + 12) * 4 == 5 * k * 3
word("w2", RA, "At a camp, the ratio of boys to girls is 3 : 5. Then 12 more boys arrive, and the ratio of boys to "
     "girls becomes 3 : 4. (No girls arrive or leave.)",
     [{"label": "a", "prompt": "How many girls are at the camp?", "answer": 5 * k},
      {"label": "b", "prompt": "How many campers are there altogether AFTER the boys arrive?", "answer": 3 * k + 12 + 5 * k}],
     ["The girls don't change, so make the girls' units match: 3 : 5 = 12 : 20 and 3 : 4 = 15 : 20.",
      "Boys went from 12 units to 15 units: 3 units = 12 boys, so 1 unit = 4.",
      "(a) Girls = 20 units = 80.",
      "(b) Boys after = 15 units = 60. Total = 60 + 80 = 140. Check: 60 : 80 = 3 : 4 ✓"],
     "Ratio change: find the quantity that stays the SAME and make its units equal in both ratios.",
     trap="Adding 12 to the ratio number, or giving the total BEFORE the boys arrived (128)",
     source="Ratio_Proportion common mistakes (ratio changes partway); Mistake_Tracker 2024-04-28 Q46",
     asks_for={"prompt": "Which group stays the same?", "options": ["The boys", "The girls", "The total"], "answer": 1})

neither = 50 - (30 + 25 - 10)
assert neither == 5
mcq("r1", RA, "In a class of 50, 30 students like art, 25 like music and 10 like both. How many like NEITHER?",
    ["5", "15", "0", "10"], "5",
    "Art or music = 30 + 25 − 10 = 45 (the 10 were counted twice). Neither = 50 − 45 = 5.",
    "Overlap: add the groups, take the overlap away ONCE. A Venn diagram helps.",
    trap="Forgetting the overlap: 30 + 25 = 55 > 50 looks impossible", source="Test_Analysis_2026-10-02 P2 Q5 (overlap counted once)")

# ================================================================ algebra (Active #4)
def poly_eq(f, g):
    return all(abs(f(t) - g(t)) < 1e-9 for t in (-3, -1, 0, 2, 5))


assert poly_eq(lambda t: (t + 4) ** 2 - 9, lambda t: (t + 1) * (t + 7))
assert not poly_eq(lambda t: (t + 4) ** 2 - 9, lambda t: (t - 1) * (t + 7))
mcq("a1", AL, "Factorise (x + 4)² − 9", ["(x + 1)(x + 7)", "(x − 1)(x + 7)", "(x + 13)(x − 5)", "(x + 4)(x − 5)"],
    "(x + 1)(x + 7)",
    "9 = 3², so this is a difference of two squares: (x + 4 − 3)(x + 4 + 3) = (x + 1)(x + 7).",
    "Bracket² − number²: (bracket − number)(bracket + number). Keep the whole bracket together.",
    trap="Sign slip inside the bracket: (x − 1)(x + 7)",
    source="Test_Analysis_2026-topictest4 Q3e ((x−3)² − 121 abandoned); Drill 5 q28")

assert poly_eq(lambda t: (t + 2) / 3 - (t - 4) / 5, lambda t: (2 * t + 22) / 15)
mcq("a2", AL, "Simplify (x + 2)/3 − (x − 4)/5", ["(2x + 22)/15", "(2x − 2)/15", "(8x − 2)/15", "(2x + 22)/8"],
    "(2x + 22)/15",
    "Common denominator 15: 5(x + 2) − 3(x − 4) = 5x + 10 − 3x + 12 = 2x + 22. So (2x + 22)/15.",
    "Put the second top in BRACKETS before subtracting: − 3(x − 4) = − 3x + 12.",
    trap="− 3x − 12 (the minus not reaching the −4) → (2x − 2)/15",
    source="Test_Analysis_2026-topictest4 Q8d (sign error subtracting fractions)")

n = 30
ana, ben = n - n / 3, n + n / 3
gift = ben / 4
ben, cara = ben - gift, n + gift
assert (ana, ben, cara) == (20, 30, 40) and cara - ana == 20
word("w3", AL, "Ana, Ben and Cara each had n marbles. Ana gave 1/3 of her marbles to Ben. Then Ben gave 1/4 of ALL "
     "his marbles to Cara. In the end, Cara had 20 more marbles than Ana.",
     [{"label": "a", "prompt": "Find n.", "answer": 30},
      {"label": "b", "prompt": "How many marbles did Ben have in the end?", "answer": 30},
      {"label": "c", "prompt": "How many marbles did Cara have in the end?", "answer": 40}],
     ["Ana gives n/3: Ana = 2n/3, Ben = n + n/3 = 4n/3, Cara = n.",
      "Ben gives 1/4 of 4n/3 = n/3: Ben = 4n/3 − n/3 = n, Cara = n + n/3 = 4n/3.",
      "Cara − Ana = 4n/3 − 2n/3 = 2n/3 = 20, so n = 30.",
      "(b) Ben = n = 30. (c) Cara = 4/3 × 30 = 40.",
      "Check: 30, 30, 30 → Ana gives 10 → 20, 40, 30 → Ben gives 10 → 20, 30, 40. 40 − 20 = 20 ✓"],
     "Table: one row per step, one column per person. Keep it in n until the last line.",
     trap="Taking 1/4 of Ben's ORIGINAL n marbles", difficulty=4,
     source="Test_Analysis_2026-10-02 P2 Q17 (transfer algebra, not reached); 3rd spaced revisit",
     asks_for={"prompt": "Part (c) asks about…", "options": ["Ana", "Ben", "Cara"], "answer": 2})

# ================================================================ indices (Recheck)
mcq("i1", IN, "Simplify (2x³y)² ÷ (4x²y)", ["x⁴y", "x³y", "4x⁴y", "x⁴"], "x⁴y",
    "(2x³y)² = 4x⁶y² (the 2 is squared too, and 3 × 2 = 6). 4x⁶y² ÷ 4x²y = x⁴y.",
    "Square EVERYTHING inside the bracket, multiply the powers, then subtract powers when dividing.",
    trap="Forgetting to square the 2 (gives 2x⁶y² ÷ 4x²y)", source="Test_Analysis_2026-03-09 Q5a/Q7/Q8b")
assert 3 ** -2 * 9 == 1
mcq("i2", IN, "Work out 3⁻² × 9", ["1", "−81", "1/81", "−1"], "1",
    "3⁻² = 1/3² = 1/9. 1/9 × 9 = 1.", "A negative index means 'one over', not a negative number.",
    trap="Treating 3⁻² as −9 (giving −81)", source="Test_Analysis_2026-03-09 Q6b/Q10d")
assert abs(3.2e-3 - 0.0032) < 1e-12
mcq("i3", IN, "Write 3.2 × 10⁻³ as an ordinary number.", ["0.0032", "0.032", "3200", "0.00032"], "0.0032",
    "× 10⁻³ moves the decimal point 3 places LEFT: 3.2 → 0.32 → 0.032 → 0.0032.",
    "Negative power of 10 = a small number; count the jumps.", trap="Moving the point the wrong way (3200)",
    source="Test_Analysis_2026-03-19 Q9c/Q11b (scientific notation)")

# ================================================================ angles (Watch)
x = 180 - 2 * 70
assert x == 40
mcq("g1", AG, "AB is parallel to CD and PQ = PR. Find angle x.", ["40°", "70°", "110°", "55°"], "40°",
    "Alternate angles (Z): ∠PQR = 70°. PQ = PR, so the triangle is isosceles and ∠PRQ = 70° too. "
    "x = 180 − 70 − 70 = 40°.",
    "Parallel lines first (alternate / corresponding), then look for equal sides.",
    trap="Stopping at 70° (that's ∠PQR, not x)", source="Maths_Brain Priority #4 (angles in composite figures)",
    difficulty=3, image=fig_parallel())
assert 360 / 24 == 15
mcq("g2", AG, "Each exterior angle of a regular polygon is 24°. How many sides does it have?", ["15", "24", "13", "18"],
    "15", "Exterior angles add up to 360°. 360 ÷ 24 = 15 sides.", "Regular polygon: number of sides = 360 ÷ exterior angle.",
    trap="Using 180 instead of 360", source="Angles_Geometry (polygons)")

# ================================================================ statistics
oldest = 4 * 12 - (9 + 10 + 11)
assert oldest == 18
mcq("s1", ST, "Four children have an average age of 12. Their ages are DIFFERENT whole numbers and nobody is younger "
    "than 9. What is the oldest the oldest child could be?", ["18", "21", "19", "15"], "18",
    "Total = 4 × 12 = 48. Make the other three as young as possible, but different: 9 + 10 + 11 = 30. Oldest = 48 − 30 = 18.",
    "Underline 'different' and 'at least/no younger than' before you start.",
    trap="9 + 9 + 9 = 27 → 21 (ignores 'different')",
    source="Test_Analysis_2026-10-02 P1 Q13 (missed 'different'); 3rd spaced revisit")
freq = {1: 4, 2: 7, 3: 5, 4: 3, 5: 1}
vals = [s for s, f in freq.items() for _ in range(f)]
med = (vals[9] + vals[10]) / 2
assert med == 2
mcq("s2", ST, "A quiz was scored out of 5. Scores: 1 (4 students), 2 (7 students), 3 (5 students), 4 (3 students), "
    "5 (1 student). What is the MEDIAN score?", ["2", "3", "2.5", "7"], "2",
    "20 students, so the median is between the 10th and 11th scores. Count up: scores of 1 are 1st–4th, scores of 2 "
    "are 5th–11th. Both the 10th and 11th are 2, so the median is 2.",
    "Frequency table: use a running total to find which score the middle position lands in.",
    trap="Picking the middle score in the list (3), the mean (2.5) or the highest frequency (7)",
    source="Test_Analysis_2026-05-22 Q9/Q10 (reading frequency data)")

# ================================================================ measurement & speed (Recheck)
litres = 50 * 40 * 30 / 1000
mins = (litres / 2) / 2
assert litres == 60 and mins == 15
numeric("m1", MM, "A full fish tank is 50 cm long, 40 cm wide and 30 cm high. Water drains out at 2 L per minute. "
        "How many minutes until the tank is HALF full?", mins,
        "Volume = 50 × 40 × 30 = 60 000 cm³ = 60 L. Half = 30 L must drain. 30 ÷ 2 = 15 minutes.",
        "cm³ ÷ 1000 = L. Then re-read: empty, or half?", unit="min",
        trap="Draining all 60 L (30 min), or forgetting to convert to litres",
        source="Test_Analysis_2025-11-29 Q48 / 2025-12-05 Q47 (tank volume and rate)")
avg = 120 / (60 / 60 + 60 / 40)
assert avg == 48
mcq("sp1", SP, "Mia's family drives 60 km to the beach at 60 km/h and drives home the same way at 40 km/h. What is "
    "the AVERAGE speed for the whole trip?", ["48 km/h", "50 km/h", "45 km/h", "52 km/h"], "48 km/h",
    "There: 60 ÷ 60 = 1 h. Home: 60 ÷ 40 = 1.5 h. Total 120 km in 2.5 h. 120 ÷ 2.5 = 48 km/h.",
    "Average speed = TOTAL distance ÷ TOTAL time, never the average of the two speeds.",
    trap="Averaging 60 and 40 (50 km/h)", source="Speed_Distance_Time (recheck area, Mistake Map)", difficulty=3)

# ================================================================ number & reasoning
val = -3 * (4 - 7) ** 2 / 9 + 5
assert val == 2
mcq("n1", NU, "Work out −3 × (4 − 7)² ÷ 9 + 5", ["2", "8", "−2", "14"], "2",
    "Brackets: 4 − 7 = −3. Square: (−3)² = 9. Then −3 × 9 = −27, ÷ 9 = −3, + 5 = 2.",
    "BIDMAS, and a negative number squared is positive.", trap="Losing the minus in front (8)",
    source="Mistake_Tracker 2026-02-14 Q1a/Q1d; Test 1 log (negatives)")
word_ = "MATHS"
assert word_[(2026 - 1) % 5] == "M"
mcq("q1", QR, "The letters MATHS repeat over and over: MATHSMATHSMATHS… What is the 2026th letter?", ["M", "A", "S", "H"],
    "M", "The block is 5 letters. 2026 ÷ 5 = 405 remainder 1. Remainder 1 → the 1st letter of the block, M.",
    "Repeating patterns: divide by the block length and use the REMAINDER (remainder 0 = last letter).",
    trap="Treating remainder 1 as the last letter (S)", source="Mistake_Tracker 2026-07-10 P1 Q15 (repeating pattern)")

# ---------------------------------------------------------------- write
drill = {
    "id": "2026-10-11_sunday_spiral",
    "title": "Drill 8 · Sunday Spiral 🌀",
    "drill_date": "2026-10-11",
    "subject": "Maths",
    "pace_seconds": 90,
    "focus": ["Circles: shaded & perimeter", "% of the new total", "Fraction of the remaining", "Ratio change",
              "Factorising & signs", "Indices recheck"],
    "source_note": "Spaced revisit (new numbers) of the Active areas from the Mistake Map: circles, percentages, "
                   "ratio, algebra; plus the Recheck areas (indices, measurement, speed) and older slips. "
                   "No new app results or tests since Drill 7. π = 3.14.",
    "questions": Q,
}
errs = validate(drill)
assert not errs, errs
drill["minutes"] = round(sum(q_seconds(q, 90) for q in Q) / 60)
name = drill["id"] + ".json"
txt = json.dumps(drill, indent=1, ensure_ascii=False)
(ROOT / "drills" / name).write_text(txt, encoding="utf-8")
vault = ROOT.parent / "Siyonah Selective Brain Prep" / "Practice" / "App_Drills"
if vault.is_dir():
    (vault / name).write_text(txt, encoding="utf-8")
print("wrote", name, len(Q), "questions,", drill["minutes"], "min,", len(txt) // 1000, "KB")
