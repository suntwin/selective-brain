"""Drill 4 'Term 3 Fix-Up': built from Test_Analysis_2026-10-02 (Year 7 Term 3 Test 1, 74/100).
Targets every question that lost marks: P1 Q13 (average + 'different'), P1 Q14 (% of a changing whole),
P2 Q10 (fraction of the REMAINING), P2 Q5 (overlap counted once), P2 Q12a (quarter arc = pi*r/2),
P2 Q9 / Q12b / P1 Q27 (composite circle area + perimeter of shaded parts), P1 Q28 (three squares angle chase),
P2 Q17 (card transfers algebra). pi = 3.14 throughout, as in her tests.
Every answer is computed/asserted here; diagrams are drawn with matplotlib and embedded as data URIs."""
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
    for p in parts:   # self-check: the stated answer must mark as correct
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
    ax.add_patch(Rectangle((3.4, 1.0), 3.6, 4.0, fc=SHADE, ec=INK, lw=2, hatch="//"))
    ax.add_patch(Rectangle((3.4, 1.0), 1.6, 3.0, fc="white", ec=INK, lw=2))
    ax.text(1.6, 1.8, "P", fontsize=16, color=INK, weight="bold")
    ax.text(5.9, 4.3, "Q", fontsize=16, color=INK, weight="bold")
    ax.text(4.2, 2.5, "over-\nlap", fontsize=8, color=INK, ha="center", va="center")
    ax.text(3.5, -0.6, "Not drawn to scale", fontsize=8, color="grey", ha="center")
    ax.set_xlim(-0.3, 7.3)
    ax.set_ylim(-0.8, 5.3)
    return png(fig)


def fig_quarter():
    fig, ax = canvas(3.0, 3.0)
    pts = [(0, 0)] + arc_pts(0, 0, 14, 0, 90)
    ax.add_patch(Polygon(pts, fc=FILL, ec=INK, lw=2))
    ax.text(7, -1.6, "14 cm", ha="center", fontsize=11, color=INK)
    ax.text(-1.4, 7, "14 cm", ha="center", va="center", rotation=90, fontsize=11, color=INK)
    ax.set_xlim(-3, 16)
    ax.set_ylim(-3, 16)
    return png(fig)


def fig_leaf():
    fig, ax = canvas(3.2, 3.2)
    ax.add_patch(Rectangle((0, 0), 20, 20, fc="white", ec=INK, lw=2))
    lens = arc_pts(0, 0, 20, 0, 90) + arc_pts(20, 20, 20, 180, 270)
    ax.add_patch(Polygon(lens, fc=SHADE, ec=PINK, lw=2))
    ax.text(10, -2.5, "20 cm", ha="center", fontsize=11, color=INK)
    ax.text(-2.5, 10, "20 cm", ha="center", va="center", rotation=90, fontsize=11, color=INK)
    ax.set_xlim(-4, 22)
    ax.set_ylim(-4, 22)
    return png(fig)


def fig_yinyang():
    fig, ax = canvas(3.4, 3.4)
    ax.add_patch(Polygon(arc_pts(0, 0, 20, 0, 360), fc="white", ec=INK, lw=2))
    # shaded = upper half of big circle, minus upper-left small semicircle, plus lower-right small semicircle
    pts = arc_pts(0, 0, 20, 0, 180) + arc_pts(-10, 0, 10, 180, 0) + arc_pts(10, 0, 10, 180, 360)
    ax.add_patch(Polygon(pts, fc=SHADE, ec=PINK, lw=2))
    ax.plot([-20, 20], [-24, -24], color=INK, lw=1)
    ax.text(0, -27.5, "40 cm", ha="center", fontsize=11, color=INK)
    ax.plot([-20, -20], [-25, -23], color=INK, lw=1)
    ax.plot([20, 20], [-25, -23], color=INK, lw=1)
    ax.set_xlim(-23, 23)
    ax.set_ylim(-30, 22)
    return png(fig)


def fig_square_semis():
    fig, ax = canvas(3.2, 3.2)
    ax.add_patch(Rectangle((0, 0), 40, 40, fc=SHADE, ec=INK, lw=2))
    ax.add_patch(Polygon(arc_pts(0, 20, 20, -90, 90), fc="white", ec=INK, lw=2))
    ax.add_patch(Polygon(arc_pts(40, 20, 20, 90, 270), fc="white", ec=INK, lw=2))
    ax.text(20, -4.5, "40 cm", ha="center", fontsize=11, color=INK)
    ax.set_xlim(-5, 45)
    ax.set_ylim(-7, 43)
    return png(fig)


def fig_three_squares():
    """Three identical squares share corner P on a straight line. Each square has sides along rays at
    angles t and t+90 (measured from the right-hand base line). Sq1: 0/90, Sq3: 30/120, Sq2: 50/140."""
    fig, ax = canvas(5.2, 3.8)
    s = 3.0
    cols = [("#e0457b", 0), ("#7a5cff", 50), ("#1f8fd6", 30)]
    for c, t in cols:
        u = (s * math.cos(math.radians(t)), s * math.sin(math.radians(t)))
        v = (s * math.cos(math.radians(t + 90)), s * math.sin(math.radians(t + 90)))
        ax.add_patch(Polygon([(0, 0), u, (u[0] + v[0], u[1] + v[1]), v], fc="none", ec=c, lw=2.2))
    ax.plot([-4.2, 4.6], [0, 0], color=INK, lw=2)
    ax.text(0, -0.45, "P", ha="center", fontsize=12, color=INK, weight="bold")

    def mark(a0, a1, r, label, col=PINK):
        ax.add_patch(Arc((0, 0), 2 * r, 2 * r, theta1=a0, theta2=a1, color=col, lw=2))
        m = math.radians((a0 + a1) / 2)
        ax.text((r + 0.38) * math.cos(m), (r + 0.38) * math.sin(m), label, ha="center", va="center",
                fontsize=12, color=col, weight="bold")

    mark(140, 180, 1.1, "40°", INK)
    mark(30, 50, 1.9, "20°", INK)
    mark(90, 120, 1.1, "x", "#d4006a")
    ax.set_xlim(-4.4, 4.8)
    ax.set_ylim(-0.9, 4.6)
    return png(fig)


ST, PC, FR, RA, SH, AG, AL = ("Statistics_Probability", "Percentages", "Fractions", "Ratio_Proportion",
                              "Circles_Composite_Shapes", "Angles_Geometry", "Algebra")

# ================================================================ A. condition words in averages (P1 Q13)
tot = 3 * 15
heaviest = tot - (12 + 13)
assert heaviest == 20 and tot - 24 == 21
mcq("f1", ST,
    "Three boxes have an average mass of 15 kg. Each box has a DIFFERENT whole-number mass, and each is at "
    "least 12 kg. What is the greatest possible mass of the heaviest box?",
    ["20 kg", "21 kg", "19 kg", "33 kg"], "20 kg",
    "Total = 3 × 15 = 45 kg. To make the heaviest as big as possible, make the other two as SMALL as possible, "
    "but they must be different: 12 kg and 13 kg = 25 kg. Heaviest = 45 − 25 = 20 kg.",
    "Underline every condition word first: 'different', 'at least', 'whole number'. Then make the others "
    "as small (or as big) as the conditions allow.",
    trap="Using 12 + 12 (21 kg) — that ignores 'different'",
    source="Test_Analysis_2026-10-02 P1 Q13 (missed 'different masses')", difficulty=3)

tot = 4 * 10
youngest = tot - (13 + 12 + 11)
assert youngest == 4 and tot - 39 == 1
mcq("f2", ST,
    "Four children have an average age of 10 years. Their ages are all DIFFERENT whole numbers, and nobody is "
    "older than 13. What is the youngest that the youngest child could be?",
    ["4 years", "1 year", "7 years", "10 years"], "4 years",
    "Total = 4 × 10 = 40. To make the youngest as small as possible, make the other three as OLD as possible, "
    "but all different: 13 + 12 + 11 = 36. Youngest = 40 − 36 = 4 years.",
    "Smallest possible one → make the others as big as the conditions allow (and different!).",
    trap="Using 13 + 13 + 13 = 39 (1 year) — ignores 'different'",
    source="Test_Analysis_2026-10-02 P1 Q13 (same idea, reversed)", difficulty=3)

big = 5 * 8 - (1 + 2 + 3 + 4)
assert big == 30
mcq("f3", ST,
    "Five different positive whole numbers have an average of 8. What is the largest possible value of the "
    "biggest number?",
    ["30", "36", "32", "26"], "30",
    "Total = 5 × 8 = 40. Make the other four as small as possible AND different: 1 + 2 + 3 + 4 = 10. "
    "Largest = 40 − 10 = 30.",
    "Average × count = total. Then 'different' means 1, 2, 3, 4 … not 1, 1, 1, 1.",
    trap="Using 1 + 1 + 1 + 1 (36)",
    source="Test_Analysis_2026-10-02 P1 Q13")

# ================================================================ B. % of a changing whole (P1 Q14)
girls, total = 0.35 * 80 + 20, 80 + 20
assert girls == 48 and total == 100 and abs(48 / 80 - 0.6) < 1e-9
mcq("f4", PC,
    "A club has 80 members and 35% of them are girls. Then 20 more girls join the club. What percentage of the "
    "club are girls now?",
    ["48%", "60%", "55%", "35%"], "48%",
    "Girls at first: 35% of 80 = 28. After: 28 + 20 = 48 girls. But the club ALSO grew: 80 + 20 = 100 members. "
    "48 out of 100 = 48%.",
    "When people join or leave, BOTH the part and the total change. Write 'new part ÷ NEW total'.",
    trap="48 ÷ 80 = 60% (dividing by the old total)",
    source="Test_Analysis_2026-10-02 P1 Q14 (66/120 instead of 66/132)", difficulty=2)

boys = 0.6 * 30
new_total = boys / 0.45
assert boys == 18 and abs(new_total - 40) < 1e-9
numeric("f5", PC,
        "A class has 30 students and 60% are boys. Some new girls join (no boys join). Now boys make up 45% of "
        "the class. How many girls joined?",
        10,
        "Boys = 60% of 30 = 18, and that does not change. Now 18 is 45% of the new total: 18 ÷ 0.45 = 40 "
        "students. Girls who joined = 40 − 30 = 10.",
        "Find the thing that stays the SAME (the boys), then use it to find the new total.",
        unit="girls", trap="Giving the new total (40) instead of how many joined",
        source="Test_Analysis_2026-10-02 P1 Q14 (changing whole)", difficulty=3)

red, tot = 0.25 * 40 - 4, 40 - 4
assert red == 6 and tot == 36 and abs(red / tot * 100 - 50 / 3) < 1e-9
mcq("f6", PC,
    "A bag has 40 marbles and 25% of them are red. Sam takes out 4 red marbles. What percentage of the marbles "
    "left in the bag are red?",
    ["16 2/3 %", "15%", "20%", "10%"], "16 2/3 %",
    "Red at first: 25% of 40 = 10. After: 10 − 4 = 6 red. Marbles left: 40 − 4 = 36. 6/36 = 1/6 = 16 2/3 %.",
    "Taking things OUT also changes the total. New part ÷ new total.",
    trap="6 ÷ 40 = 15% (the old total)", source="Test_Analysis_2026-10-02 P1 Q14", difficulty=3)

# ================================================================ C. fraction of the REMAINING (P2 Q10)
left = (1 - F(1, 4)) * (1 - F(1, 2))
assert left == F(3, 8)
mcq("f7", FR,
    "Lily spent 1/4 of her money on a book and then 1/2 of the REMAINING money on lunch. What fraction of her "
    "money did she have left?",
    ["3/8", "1/4", "1/8", "5/8"], "3/8",
    "After the book she has 3/4 left. Lunch = 1/2 of 3/4 = 3/8. Left = 3/4 − 3/8 = 3/8. "
    "(Quick way: 3/4 × 1/2 = 3/8.)",
    "'Of the remaining' → work on what is LEFT, not the whole. Draw a bar model.",
    trap="1 − 1/4 − 1/2 = 1/4 (taking 1/2 of the whole)",
    source="Test_Analysis_2026-10-02 P2 Q10; Fractions topic (fraction of remainder)")

frac_left = (1 - F(25, 100)) * (1 - F(2, 3))
start = 180 / frac_left
after_bag = start * F(3, 4)
shoes = after_bag * F(2, 3)
assert frac_left == F(1, 4) and start == 720 and shoes == 360 and after_bag - shoes == 180
word("w1", PC,
     "Priya spent 25% of her money on a bag. Then she spent 2/3 of the REMAINING money on shoes. "
     "She had $180 left.",
     [{"label": "a", "prompt": "What fraction of her ORIGINAL money did she have left? (e.g. 2/7)",
       "answer": 0.25, "tolerance": 0.0005, "display": "1/4"},
      {"label": "b", "prompt": "How much money did she have at first?", "answer": 720, "unit": "$"},
      {"label": "c", "prompt": "How much did the shoes cost?", "answer": 360, "unit": "$"}],
     ["After the bag: 100% − 25% = 75% = 3/4 of her money is left.",
      "Shoes = 2/3 of that 3/4, so 1/3 of the 3/4 is left: 1/3 × 3/4 = 1/4 of her original money.",
      "(b) 1/4 = $180, so her money at first = 4 × $180 = $720.",
      "(c) After the bag: 3/4 × 720 = $540. Shoes = 2/3 × 540 = $360. Check: 720 − 180 − 360 = 180 ✓"],
     "Bar model: draw the whole, cut off 25%, then split ONLY the leftover part into thirds.",
     trap="Treating 2/3 as 2/3 of ALL the money (25% + 66.7% > 90%)",
     source="Test_Analysis_2026-10-02 P2 Q10 (Robin: 3/5 of the remaining)",
     asks_for={"prompt": "Before you start: the 2/3 is a fraction of…",
               "options": ["All of her money", "The money left after the bag", "The $180"], "answer": 1})

total_eggs = 150 / ((1 - F(3, 8)) * (1 - F(40, 100)))
mon = total_eggs * F(3, 8)
tue = (total_eggs - mon) * F(40, 100)
assert total_eggs == 400 and mon == 150 and tue == 100 and total_eggs - mon - tue == 150
word("w2", FR,
     "A farmer sold 3/8 of his eggs on Monday. On Tuesday he sold 40% of the REMAINING eggs. "
     "He then had 150 eggs left.",
     [{"label": "a", "prompt": "How many eggs did he have at first?", "answer": 400, "unit": "eggs"},
      {"label": "b", "prompt": "How many eggs did he sell on Tuesday?", "answer": 100, "unit": "eggs"}],
     ["After Monday: 1 − 3/8 = 5/8 of the eggs are left.",
      "Tuesday he sells 40% of that 5/8, so 60% of 5/8 is left: 0.6 × 5/8 = 3/8 of all the eggs.",
      "3/8 = 150, so 1/8 = 50 and all the eggs = 400.",
      "(b) After Monday: 5/8 × 400 = 250. Tuesday = 40% of 250 = 100. Check: 400 − 150 − 100 = 150 ✓"],
     "Fraction then percentage of the remainder: turn each step into 'what fraction is LEFT', then multiply.",
     trap="Taking 40% of all 400 eggs (160)",
     source="Test_Analysis_2026-10-02 P2 Q10",
     asks_for={"prompt": "The 40% on Tuesday is 40% of…",
               "options": ["All the eggs at the start", "The eggs left after Monday", "The 150 eggs at the end"],
               "answer": 1})

# ================================================================ D. overlap counted once (P2 Q5)
A, B = 5, 3          # scale so overlap is a whole number of units: overlap = 1/3 of B
ov = F(1, 3) * B
fig_area = A + B - ov
assert ov == 1 and fig_area == 7
mcq("f8", RA,
    "Square A and square B overlap. Area of A : area of B = 5 : 3. The overlap is 1/3 of the area of B. "
    "What is the ratio of the overlap to the area of the WHOLE figure?",
    ["1 : 7", "1 : 8", "1 : 5", "1 : 3"], "1 : 7",
    "Let A = 5 units, B = 3 units. Overlap = 1/3 of 3 = 1 unit. The whole figure = 5 + 3 − 1 = 7 units "
    "(the overlap is inside BOTH squares, so take it away once). Overlap : figure = 1 : 7.",
    "Whole figure = A + B − overlap. The overlap must only be counted once.",
    trap="5 + 3 = 8 units (1 : 8), counting the overlap twice",
    source="Test_Analysis_2026-10-02 P2 Q5; Test_Analysis_2026-07-17 P1 Q14", difficulty=3)

P, Qa = 20, 16       # P : Q = 5 : 4, scaled so 1/4 of Q is whole
overlap = Qa - F(3, 4) * Qa
shaded = F(3, 4) * Qa
unshaded = (P - overlap) + overlap
assert overlap == 4 and shaded == 12 and unshaded == 20 and F(overlap, P) == F(1, 5)
assert F(shaded, unshaded) == F(3, 5)
word("w3", RA,
     "Rectangles P and Q overlap (see the picture). Area of P : area of Q = 5 : 4. The SHADED part is the part of "
     "Q that is NOT inside P, and it is 3/4 of the area of Q.",
     [{"label": "a", "prompt": "What fraction of rectangle P is the overlap? (e.g. 2/7)",
       "answer": 0.2, "tolerance": 0.0005, "display": "1/5"},
      {"label": "b", "prompt": "What is the ratio of the shaded area to the unshaded area of the whole figure? "
                               "(type like 2:7)",
       "accept": ["3:5", "3 : 5", "12:20"]}],
     ["Scale the ratio so the fractions are whole: P = 20 units, Q = 16 units.",
      "Shaded (Q only) = 3/4 × 16 = 12 units. Overlap = 16 − 12 = 4 units.",
      "(a) Overlap ÷ P = 4/20 = 1/5.",
      "(b) Unshaded = all of P = 20 units (P only 16 + overlap 4). Whole figure = 20 + 16 − 4 = 32 = 12 + 20 ✓.",
      "Shaded : unshaded = 12 : 20 = 3 : 5."],
     "Pick a number of units that both fractions divide into. Label the 3 regions: P only, overlap, Q only.",
     trap="Counting the overlap in both P and Q (12 : 24 = 1 : 2)",
     source="Test_Analysis_2026-10-02 P2 Q5 (answered 1:10; correct 5:12)",
     asks_for={"prompt": "The unshaded part of the figure is…",
               "options": ["Only the overlap", "All of rectangle P (including the overlap)", "P and Q added"],
               "answer": 1},
     image=fig_overlap())

# ================================================================ E. circles & composite shapes (P2 Q12, Q9, P1 Q27)
arc = r2(2 * PI * 20 / 4)
assert arc == 31.4
mcq("f9", SH,
    "A quarter circle has a radius of 20 cm. How long is its CURVED edge? (Use π = 3.14)",
    ["31.4 cm", "15.7 cm", "62.8 cm", "314 cm"], "31.4 cm",
    "Whole circumference = 2 × π × r = 2 × 3.14 × 20 = 125.6 cm. A quarter of it = 125.6 ÷ 4 = 31.4 cm. "
    "(Short cut: quarter arc = π × r ÷ 2.)",
    "Arc = fraction × 2πr. Quarter arc = 2πr ÷ 4 = πr ÷ 2. Don't forget the 2!",
    trap="π × r ÷ 4 = 15.7 cm (forgot the 2 in 2πr) — exactly the Term 3 slip",
    source="Test_Analysis_2026-10-02 P2 Q12a (used πr/4; answer came out exactly half)", difficulty=2)

per = r2(2 * 14 + 2 * PI * 14 / 4)
assert per == 49.98
numeric("f10", SH,
        "Find the PERIMETER of this quarter circle. (Use π = 3.14)",
        49.98,
        "Curved edge = 2 × 3.14 × 14 ÷ 4 = 21.98 cm. Plus the two straight radii: 14 + 14 = 28 cm. "
        "Perimeter = 21.98 + 28 = 49.98 cm.",
        "Perimeter of a sector = curved arc + the straight edges. Trace the edge with your pencil.",
        unit="cm", trap="Giving only the arc (21.98) or using πr/4 (10.99 + 28 = 38.99)",
        source="Test_Analysis_2026-10-02 P2 Q12a", difficulty=2, tolerance=0.01, image=fig_quarter())

one_arc = r2(2 * PI * 20 / 4)
leaf_per = r2(2 * one_arc)
leaf_area = r2(2 * (PI * 20 * 20 / 4) - 20 * 20)
assert (one_arc, leaf_per, leaf_area) == (31.4, 62.8, 228)
word("w4", SH,
     "A square has sides of 20 cm. Two quarter circles are drawn inside it, centred at opposite corners, each "
     "with radius 20 cm. They make the shaded 'leaf'. (Use π = 3.14)",
     [{"label": "a", "prompt": "How long is ONE of the curved arcs?", "answer": 31.4, "unit": "cm", "tolerance": 0.01},
      {"label": "b", "prompt": "What is the perimeter of the shaded leaf?", "answer": 62.8, "unit": "cm",
       "tolerance": 0.01},
      {"label": "c", "prompt": "What is the area of the shaded leaf?", "answer": 228, "unit": "cm²",
       "tolerance": 0.01}],
     ["(a) Quarter arc = 2 × 3.14 × 20 ÷ 4 = 31.4 cm.",
      "(b) The leaf's edge is just the two arcs: 2 × 31.4 = 62.8 cm (no straight sides!).",
      "(c) One quarter circle = 3.14 × 20 × 20 ÷ 4 = 314 cm². Two quarter circles = 628 cm².",
      "Together they cover the whole square (400 cm²) and the leaf is covered TWICE.",
      "Leaf = 628 − 400 = 228 cm²."],
     "Overlap trick: two shapes added together − the whole square = the part counted twice.",
     trap="(b) adding square sides to the leaf's perimeter; (a) using πr/4",
     source="Test_Analysis_2026-10-02 P2 Q12a/b (quarter-circle design: arc formula + area left blank)",
     asks_for={"prompt": "The perimeter of the leaf is made of…",
               "options": ["2 curved arcs only", "2 arcs + 2 sides of the square", "The 4 sides of the square"],
               "answer": 0},
     image=fig_leaf())

big_r, small_r = 20, 10
yy_area = r2(PI * big_r ** 2 / 2 - PI * small_r ** 2 / 2 + PI * small_r ** 2 / 2)
yy_per = r2(PI * big_r + PI * small_r + PI * small_r)
assert yy_area == 628 and yy_per == 125.6
word("w5", SH,
     "A circle has a diameter of 40 cm. Two semicircles, each with a diameter of 20 cm, are drawn along its "
     "diameter to make the shaded shape. (Use π = 3.14)",
     [{"label": "a", "prompt": "What is the area of the shaded part?", "answer": 628, "unit": "cm²", "tolerance": 0.01},
      {"label": "b", "prompt": "What is the perimeter of the shaded part?", "answer": 125.6, "unit": "cm",
       "tolerance": 0.01}],
     ["(a) Start with the top half of the big circle: 3.14 × 20 × 20 ÷ 2 = 628 cm².",
      "The small semicircle cut OUT on the left is the same size as the small semicircle ADDED on the right "
      "(both 3.14 × 10 × 10 ÷ 2 = 157 cm²).",
      "So the shaded area = 628 − 157 + 157 = 628 cm² — exactly half the big circle.",
      "(b) Trace the edge: big semicircle arc = 3.14 × 20 = 62.8 cm, plus two small semicircle arcs = "
      "3.14 × 10 = 31.4 cm each.",
      "Perimeter = 62.8 + 31.4 + 31.4 = 125.6 cm."],
     "Move pieces: a bit cut out on one side + an equal bit added on the other cancels out. "
     "For perimeter, trace the edge with your finger and add every curve.",
     trap="Using the diameter (40) as the radius; adding the straight diameter to the perimeter",
     source="Test_Analysis_2026-10-02 P2 Q9 (circle + semicircles, left blank) and P1 Q27 (perimeter of shaded parts)",
     image=fig_yinyang())

sq_per = r2(2 * 40 + 2 * (PI * 20))
assert sq_per == 205.6
mcq("f11", SH,
    "A square has sides of 40 cm. A semicircle is cut out from the left side and another from the right side "
    "(each diameter = 40 cm). What is the perimeter of the shaded part? (Use π = 3.14)",
    ["205.6 cm", "125.6 cm", "285.6 cm", "165.6 cm"], "205.6 cm",
    "The shaded edge is: top side 40 + bottom side 40 = 80 cm, plus two semicircle arcs. Each arc = "
    "3.14 × 20 = 62.8 cm, so both = 125.6 cm. Perimeter = 80 + 125.6 = 205.6 cm.",
    "Perimeter of shaded part: only the edges that touch the shading. The left and right sides of the square "
    "are no longer on the edge.",
    trap="Adding all 4 sides (285.6) or only the arcs (125.6)",
    source="Test_Analysis_2026-10-02 P1 Q27 (perimeter of shaded parts, skipped)", difficulty=3,
    image=fig_square_semis())

# ================================================================ F. three squares angle chase (P1 Q28)
sq2_lower = 180 - 40 - 90
sq3_lower = sq2_lower - 20
sq3_upper = sq3_lower + 90
x = sq3_upper - 90
assert (sq2_lower, sq3_lower, x) == (50, 30, 30) and x == 90 - 40 - 20
mcq("f12", AG,
    "Three identical squares share the corner P, which is on a straight line. Use the angles marked to find x.",
    ["30°", "20°", "40°", "50°"], "30°",
    "Measure every side from the right-hand line at P. Middle square: 180 − 40 − 90 = 50°, so its lower side is "
    "at 50°. The next square sits 20° lower: 50 − 20 = 30°, so its other side is at 30 + 90 = 120°. "
    "The first square's side is straight up (90°). x = 120 − 90 = 30°. Short cut: x = 90 − 40 − 20 = 30°.",
    "Squares → every corner is 90°. Write the angle of each side from ONE base line and subtract.",
    trap="Copying a marked angle (20° or 40°) without the chase",
    source="Test_Analysis_2026-10-02 P1 Q28 (three squares, abandoned; answer 27°)", difficulty=3,
    image=fig_three_squares())

# ================================================================ G. transfers algebra (P2 Q17)
p = 28
a, b, s = p, p, p
give1 = F(1, 4) * a
a, b = a - give1, b + give1
give2 = F(2, 5) * b
b, s = b - give2, s + give2
assert (a, b, s) == (21, 21, 42) and s - b == 21 and give2 == 14
assert F(3, 4) * p == 21      # S − B = 3p/2 − 3p/4 = 3p/4
word("w6", AL,
     "Ajay, Blair and Simon each had p cards. Ajay gave 1/4 of his cards to Blair. Then Blair gave 2/5 of ALL "
     "his cards to Simon. In the end, Simon had 21 more cards than Blair.",
     [{"label": "a", "prompt": "Find p.", "answer": 28},
      {"label": "b", "prompt": "How many cards did Simon have in the end?", "answer": 42, "unit": "cards"},
      {"label": "c", "prompt": "How many cards did Blair give to Simon?", "answer": 14, "unit": "cards"}],
     ["Ajay gives p/4: Ajay = 3p/4, Blair = p + p/4 = 5p/4, Simon = p.",
      "Blair gives 2/5 of 5p/4 = p/2: Blair = 5p/4 − p/2 = 3p/4, Simon = p + p/2 = 3p/2.",
      "Simon − Blair = 3p/2 − 3p/4 = 3p/4 = 21, so p = 28.",
      "(b) Simon = 3/2 × 28 = 42. (c) Blair gave p/2 = 14.",
      "Check with numbers: 28,28,28 → Ajay gives 7 → 21,35,28 → Blair gives 14 → 21,21,42. 42 − 21 = 21 ✓"],
     "Make a table: one row per step, one column per person. Keep everything in p until the last step.",
     trap="Taking 2/5 of Blair's ORIGINAL p cards instead of all his cards after the gift",
     source="Test_Analysis_2026-10-02 P2 Q17 (5-mark card-transfer algebra, not reached)", difficulty=4,
     asks_for={"prompt": "Part (b) is about whose cards?", "options": ["Ajay", "Blair", "Simon"], "answer": 2})

# ---------------------------------------------------------------- write
drill = {
    "id": "2026-10-05_term3_fix_up",
    "title": "Drill 4 · Term 3 Fix-Up 🔍",
    "drill_date": "2026-10-05",
    "subject": "Maths",
    "pace_seconds": 90,
    "focus": ["Underline condition words", "% of the NEW total", "Fraction of the remaining",
              "Overlap counted once", "Quarter arc = πr/2", "Composite circles"],
    "source_note": "Test_Analysis_2026-10-02 (Year 7 Term 3 Test 1, 74/100): every question that lost marks — "
                   "P1 Q13, Q14, Q27, Q28; P2 Q5, Q9, Q10, Q12a/b, Q17. π = 3.14 as in her tests.",
    "questions": Q,
}
errs = validate(drill)
assert not errs, errs
mins = round(sum(q_seconds(q, 90) for q in Q) / 60)
drill["minutes"] = mins
name = "2026-10-05_term3_fix_up.json"
txt = json.dumps(drill, indent=1, ensure_ascii=False)
out = ROOT / "drills" / name
out.write_text(txt, encoding="utf-8")
vault = ROOT.parent / "Siyonah Selective Brain Prep" / "Practice" / "App_Drills"
if vault.is_dir():
    (vault / name).write_text(txt, encoding="utf-8")
if len(sys.argv) > 1:   # optional extra output dir (sandbox testing)
    Path(sys.argv[1], name).write_text(txt, encoding="utf-8")
print("wrote", name, len(Q), "questions,", mins, "min,", len(txt) // 1000, "KB")
