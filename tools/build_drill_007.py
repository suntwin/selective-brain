"""Drill 7 'Formula Power': one question per key formula on the Oxford Yr 7-10 formula sheet
(Practice/Printable_Drills/FormulaSheet_2026-10-08_Oxford_Yr7-10.pdf): SEHS-level (Yr 7-8) formulas plus the
Yr 9 ones her class has already met (Pythagoras, index laws). Each trap is a known slip from her Mistake Tracker.
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
def _ax(w=3.4, h=2.4):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def fig_trap():
    fig, ax = _ax()
    ax.add_patch(Polygon([(0, 0), (11, 0), (8, 6), (1, 6)], fc=FILL, ec=INK, lw=2))
    ax.plot([8, 8], [0, 6], color=PINK, lw=1.5, ls="--")
    ax.add_patch(Rectangle((7.4, 0), .6, .6, fc="none", ec=PINK, lw=1))
    ax.text(5.5, -1.1, "11 cm", ha="center", color=INK, fontsize=11)
    ax.text(4.5, 6.4, "7 cm", ha="center", color=INK, fontsize=11)
    ax.text(8.4, 3, "6 cm", color=PINK, fontsize=11)
    ax.set_xlim(-1, 12)
    ax.set_ylim(-1.8, 7.4)
    return png(fig)


def fig_para():
    fig, ax = _ax()
    ax.add_patch(Polygon([(0, 0), (12, 0), (15, 5), (3, 5)], fc=FILL, ec=INK, lw=2))
    ax.plot([3, 3], [0, 5], color=PINK, lw=1.5, ls="--")
    ax.add_patch(Rectangle((3, 0), .6, .6, fc="none", ec=PINK, lw=1))
    ax.text(6, -1.2, "12 cm", ha="center", color=INK, fontsize=11)
    ax.text(14.6, 2.1, "7 cm", color=INK, fontsize=11)
    ax.text(3.4, 2.4, "5 cm", color=PINK, fontsize=11)
    ax.set_xlim(-.5, 17)
    ax.set_ylim(-2, 6)
    return png(fig)


def fig_semi():
    fig, ax = _ax(3, 1.9)
    pts = [(10 * math.cos(math.radians(a)), 10 * math.sin(math.radians(a))) for a in range(0, 181, 3)]
    ax.add_patch(Polygon(pts, fc=FILL, ec=INK, lw=2))
    ax.text(0, -2.2, "20 cm", ha="center", color=INK, fontsize=11)
    ax.set_xlim(-11, 11)
    ax.set_ylim(-3.5, 11)
    return png(fig)


SH, MM, AG, IN, PC, SP, ST, AL = ("Circles_Composite_Shapes", "Money_Measurement", "Angles_Geometry", "Indices",
                                  "Percentages", "Speed_Distance_Time", "Statistics_Probability", "Algebra")
SRC = "FormulaSheet 2026-10-08 (Oxford Yr 7-10)"

# ---------------------------------------------------------------- area
v = F(1, 2) * (7 + 11) * 6
assert v == 54
mcq("p1", SH, "Find the area of this trapezium.", ["54 cm²", "108 cm²", "462 cm²", "36 cm²"], "54 cm²",
    "Trapezium: A = ½ × (a + b) × h = ½ × (7 + 11) × 6 = ½ × 18 × 6 = 54 cm².",
    "Trapezium = ½ × (sum of the PARALLEL sides) × perpendicular height.",
    trap="Forgetting the ½ (108)", source=SRC + " §11; Area_Perimeter_Drill (trapezium)", image=fig_trap())

assert 12 * 5 == 60
mcq("p2", SH, "Find the area of this parallelogram.", ["60 cm²", "84 cm²", "30 cm²", "38 cm²"], "60 cm²",
    "A = base × PERPENDICULAR height = 12 × 5 = 60 cm². The slanted 7 cm side is not the height.",
    "Parallelogram: base × the height that makes a right angle with the base.",
    trap="Using the slanted side (12 × 7 = 84)", source=SRC + " §11; Test_Analysis_2026-06-18 log Q32 (area formula)",
    image=fig_para())

assert F(1, 2) * 10 * 14 == 70
mcq("p3", SH, "A kite has diagonals of 10 cm and 14 cm. What is its area?", ["70 cm²", "140 cm²", "48 cm²", "24 cm²"],
    "70 cm²", "Kite: A = ½ × x × y = ½ × 10 × 14 = 70 cm².", "Kite or rhombus: half the product of the diagonals.",
    trap="Forgetting the ½ (140)", source=SRC + " §11 (Yr 8 kite/rhombus)")

c = r2(PI * 14)
assert c == 43.96
numeric("p4", SH, "A circle has a DIAMETER of 14 cm. Find its circumference. (Use π = 3.14)", c,
        "C = π × d = 3.14 × 14 = 43.96 cm.", "C = πd = 2πr. Check whether you're given r or d.",
        unit="cm", trap="Using 14 as the radius (87.92)", tolerance=0.01,
        source=SRC + " §11; Test_Analysis_2025-10-01 Circles Q9 (wrong circle measure)")

a = r2(PI * 5 ** 2)
assert a == 78.5
mcq("p5", SH, "Find the area of a circle with radius 5 cm. (Use π = 3.14)", ["78.5 cm²", "31.4 cm²", "15.7 cm²",
    "314 cm²"], "78.5 cm²", "A = πr² = 3.14 × 5 × 5 = 78.5 cm².",
    "Area has r² (the 2 is a POWER). Circumference has 2πr (the 2 is in front).",
    trap="Using 2πr (31.4), which is the circumference", source=SRC + " §11")

per = r2(PI * 10 + 20)
assert per == 51.4
mcq("p6", SH, "Find the PERIMETER of this semicircle. (Use π = 3.14)", ["51.4 cm", "31.4 cm", "62.8 cm", "82.8 cm"],
    "51.4 cm", "Curved part = half of πd = ½ × 3.14 × 20 = 31.4 cm. Add the straight diameter 20 cm: 51.4 cm.",
    "Semicircle perimeter = curved half + the straight diameter.",
    trap="Leaving out the straight edge (31.4)", source=SRC + " §11; Test_Analysis_2025-01-07 Q20-23", image=fig_semi())

arc = r2(2 * PI * 10 / 4)
assert arc == 15.7
mcq("p7", SH, "What is the length of the curved edge of a quarter circle with radius 10 cm? (Use π = 3.14)",
    ["15.7 cm", "7.85 cm", "31.4 cm", "78.5 cm"], "15.7 cm",
    "Quarter arc = 2πr ÷ 4 = 2 × 3.14 × 10 ÷ 4 = 15.7 cm.", "Arc = (fraction of the circle) × 2πr.",
    trap="πr ÷ 4 = 7.85 (the Term 3 slip)", source=SRC + " watch-outs; Test_Analysis_2026-10-02 P2 Q12a")

sec = r2(45 / 360 * PI * 8 ** 2)
assert sec == 25.12
numeric("p8", SH, "Find the area of a sector with radius 8 cm and angle 45°. (Use π = 3.14)", sec,
        "45° is 45/360 = 1/8 of the circle. Circle = 3.14 × 64 = 200.96. ÷ 8 = 25.12 cm².",
        "Sector = (angle ÷ 360) × πr².", unit="cm²", trap="Using 2πr instead of πr²", tolerance=0.01,
        source=SRC + " §11 (sector)")

# ---------------------------------------------------------------- volume & units
assert F(1, 2) * 6 * 4 * 10 == 120
mcq("p9", MM, "A triangular prism is 10 cm long. Its triangle end has base 6 cm and height 4 cm. What is its volume?",
    ["120 cm³", "240 cm³", "100 cm³", "60 cm³"], "120 cm³",
    "Cross-section = ½ × 6 × 4 = 12 cm². Volume = 12 × 10 = 120 cm³.",
    "Any prism: volume = area of the cross-section × length.", trap="Forgetting the ½ of the triangle (240)",
    source=SRC + " §12")

vc = r2(PI * 2 ** 2 * 10)
assert vc == 125.6
numeric("p10", MM, "A cylinder has radius 2 cm and height 10 cm. Find its volume. (Use π = 3.14)", vc,
        "V = πr²h = 3.14 × 4 × 10 = 125.6 cm³.", "Cylinder = circle area × height.", unit="cm³",
        trap="Using 2πr (circumference) instead of πr²", tolerance=0.01, source=SRC + " §12")

assert 30 * 20 * 10 / 1000 == 6
mcq("p11", MM, "A box is 30 cm × 20 cm × 10 cm. How many litres does it hold?", ["6 L", "60 L", "0.6 L", "600 L"],
    "6 L", "V = 30 × 20 × 10 = 6000 cm³. 1000 cm³ = 1 L, so 6000 ÷ 1000 = 6 L.", "cm³ → L: divide by 1000.",
    trap="Dividing by 100 (60 L)", source=SRC + " §12; Test_Analysis_2025-12-05 Q47 (L vs cm³)")

assert 2.5 * 10000 == 25000
mcq("p12", MM, "Convert 2.5 m² to cm².", ["25 000 cm²", "250 cm²", "2500 cm²", "250 000 cm²"], "25 000 cm²",
    "1 m = 100 cm, so 1 m² = 100 × 100 = 10 000 cm². 2.5 × 10 000 = 25 000 cm².",
    "Area units: square the length factor (100² = 10 000).", trap="Multiplying by 100 only (250)",
    source=SRC + " §11 (area units)")

# ---------------------------------------------------------------- angles & Pythagoras
each = (8 - 2) * 180 / 8
assert each == 135
mcq("p13", AG, "What is the size of each interior angle of a REGULAR octagon?", ["135°", "1080°", "45°", "120°"],
    "135°", "Angle sum = (8 − 2) × 180 = 1080°. Regular, so each = 1080 ÷ 8 = 135°.",
    "Polygon angle sum = (n − 2) × 180°. Regular → divide by n.", trap="Giving the angle sum (1080°) or the exterior angle (45°)",
    source=SRC + " §9")

assert math.sqrt(13 ** 2 - 5 ** 2) == 12
mcq("p14", AG, "A right-angled triangle has a hypotenuse of 13 cm and one short side of 5 cm. How long is the other "
    "short side?", ["12 cm", "13.9 cm", "8 cm", "18 cm"], "12 cm",
    "a² = c² − b² = 169 − 25 = 144, so a = 12 cm. (5-12-13 is a Pythagorean triple.)",
    "Finding a SHORTER side: subtract the squares.", trap="Adding the squares (√194 ≈ 13.9)",
    source=SRC + " §10; Test_Analysis_2026-05-15 Q13-16")

# ---------------------------------------------------------------- indices & algebra
assert 4 * 3 - 5 == 7
mcq("p15", IN, "Simplify (a⁴)³ ÷ a⁵", ["a⁷", "a²", "a¹²", "a¹⁷"], "a⁷",
    "(a⁴)³ = a¹² (multiply the powers). a¹² ÷ a⁵ = a⁷ (subtract the powers).",
    "Power of a power: multiply. Dividing: subtract.", trap="Adding 4 + 3 = 7 then subtracting 5 (a²)",
    source=SRC + " §5; Test_Analysis_2026-03-09 Q5a/Q7")

mcq("p16", AL, "Expand −2(x − 5)", ["−2x + 10", "−2x − 10", "−2x − 5", "2x + 10"], "−2x + 10",
    "−2 × x = −2x and −2 × (−5) = +10.", "A minus in front flips every sign inside.",
    trap="−2x − 10 (forgot negative × negative)", source=SRC + " §6; topictest4 Q1d/Q8d (sign errors)")

xs, ys = [0, 1, 2, 3], [5, 8, 11, 14]
assert all(y == 3 * x + 5 for x, y in zip(xs, ys))
mcq("p17", AL, "Which rule fits this table?  x: 0, 1, 2, 3  →  y: 5, 8, 11, 14", ["y = 3x + 5", "y = 5x + 3",
    "y = x + 3", "y = 3x"], "y = 3x + 5",
    "y goes up by 3 each time, so 3x. When x = 0, y = 5, so + 5: y = 3x + 5.",
    "Linear rule = (change in y each step) × x + (y when x = 0).", trap="Swapping the numbers (y = 5x + 3)",
    source=SRC + " §8 (Yr 8 linear rules)")

# ---------------------------------------------------------------- money
assert 800 * 0.05 * 3 == 120
mcq("p18", PC, "$800 is invested at 5% per year SIMPLE interest for 3 years. How much INTEREST is earned?",
    ["$120", "$40", "$920", "$126.10"], "$120", "I = PrT = 800 × 0.05 × 3 = $120.",
    "Simple interest I = P × r × T (r as a decimal).", trap="One year only ($40), the total ($920) or compound ($126.10)",
    source=SRC + " §3; Test_Analysis_2026-02-14 Q20-22")

assert (65 - 50) / 50 * 100 == 30
mcq("p19", PC, "A price rises from $50 to $65. What is the percentage increase?", ["30%", "23%", "15%", "130%"],
    "30%", "Increase = 15. % change = 15 ÷ ORIGINAL 50 × 100 = 30%.", "% change = change ÷ original × 100.",
    trap="Dividing by the new price (≈ 23%)", source=SRC + " §3; Test_Analysis_2026-07-10 P1 Q25")

assert (50 - 40) / 40 * 100 == 25
mcq("p20", PC, "A shop buys a toy for $40 and sells it for $50. What is the percentage PROFIT?", ["25%", "20%", "10%",
    "125%"], "25%", "Profit = $10. % profit = 10 ÷ COST 40 × 100 = 25%.", "% profit = profit ÷ cost price × 100.",
    trap="Dividing by the selling price (20%)", source=SRC + " §3")

# ---------------------------------------------------------------- speed & statistics
assert 150 / 2.5 == 60
mcq("p21", SP, "A car travels 150 km in 2 hours 30 minutes. What is its average speed?", ["60 km/h", "65 km/h",
    "50 km/h", "375 km/h"], "60 km/h", "2 h 30 min = 2.5 h. Speed = 150 ÷ 2.5 = 60 km/h.",
    "Speed = distance ÷ time, with time in HOURS for km/h.", trap="Using 2.3 h for 2 h 30 min (≈ 65)",
    source=SRC + " §13; Test_Analysis_2025-10-01 Speed Q10/19")

fifth = 5 * 84 - 330
assert fifth == 90
numeric("p22", ST, "Priya's mean mark over 5 tests is 84. Her first four marks add up to 330. What did she get on "
        "the fifth test?", fifth, "Total for 5 tests = 5 × 84 = 420. Fifth = 420 − 330 = 90.",
        "Total = mean × count. Then subtract what you know.", unit="marks", trap="Averaging 84 and 330 in some way",
        source=SRC + " §14; Test_Analysis_2026-10-02 P1 Q13 (average → total)")

assert 18 + 15 - 7 == 26
mcq("p23", ST, "In a class, 18 play football, 15 play tennis and 7 play both. How many play football OR tennis "
    "(or both)?", ["26", "33", "40", "19"], "26", "n(A or B) = 18 + 15 − 7 = 26. The 7 were counted twice.",
    "Venn: add the two groups, take away the overlap once.", trap="Adding without removing the overlap (33)",
    source=SRC + " §15; Test_Analysis_2026-05-15 (sets)")

# ---------------------------------------------------------------- write
drill = {
    "id": "2026-10-08_formula_power",
    "title": "Drill 7 · Formula Power ⚡",
    "drill_date": "2026-10-08",
    "subject": "Maths",
    "pace_seconds": 90,
    "focus": ["Area & circles", "Volume & units", "Angles & Pythagoras", "Index laws", "% formulas",
              "Speed & averages"],
    "source_note": "Formula sheet built from Oxford Maths Victoria Yr 7-10 (Practice/Printable_Drills/"
                   "FormulaSheet_2026-10-08_Oxford_Yr7-10.pdf). One question per key formula; traps from her "
                   "Mistake Tracker. π = 3.14.",
    "questions": Q,
}
errs = validate(drill)
assert not errs, errs
drill["minutes"] = round(sum(q_seconds(q, 90) for q in Q) / 60)
name = "2026-10-08_formula_power.json"
txt = json.dumps(drill, indent=1, ensure_ascii=False)
(ROOT / "drills" / name).write_text(txt, encoding="utf-8")
vault = ROOT.parent / "Siyonah Selective Brain Prep" / "Practice" / "App_Drills"
if vault.is_dir():
    (vault / name).write_text(txt, encoding="utf-8")
print("wrote", name, len(Q), "questions,", drill["minutes"], "min,", len(txt) // 1000, "KB")
