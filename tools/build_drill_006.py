"""Drill 6 'Throwback Mix': revisits mistakes from her WHOLE test history (2023-2026), not just Term 3.
Built from the vault's Mistake Tracker / Mistake Map register, choosing logged mistakes that Drills 1-5 have
not covered yet: compass turns, nets, bar-graph reading, weighted averages, quartiles, probability with
replacement, 3D Pythagoras, recurring decimals, simplifying with one common factor, the factor-pair product
check, ages, coins, equalising transfers, working backwards, net fill rates, meeting problems, fractional
hours, wages, remainders/LCM, digit puzzles, ratios from fractions of different wholes, isosceles angle
chasing and sector area. pi = 3.14 as in her tests. Every answer is computed/asserted here."""
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
def fig_net():
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    ax.set_aspect("equal")
    ax.axis("off")
    cells = {"A": (1, 2), "B": (0, 1), "C": (1, 1), "D": (2, 1), "E": (3, 1), "F": (1, 0)}
    for lab, (x, y) in cells.items():
        ax.add_patch(Rectangle((x, y), 1, 1, fc=FILL, ec=INK, lw=2))
        ax.text(x + .5, y + .5, lab, ha="center", va="center", fontsize=16, color=INK, weight="bold")
    ax.set_xlim(-.2, 4.2)
    ax.set_ylim(-.2, 3.2)
    return png(fig)


BOOKS = {"Mon": 12, "Tue": 18, "Wed": 9, "Thu": 15, "Fri": 21}


def fig_bars():
    fig, ax = plt.subplots(figsize=(4.4, 2.9))
    ax.bar(list(BOOKS), list(BOOKS.values()), color=LAV, edgecolor=INK, width=.6)
    ax.set_yticks(range(0, 25, 3))
    ax.set_ylim(0, 24)
    ax.grid(axis="y", color="#ddd", lw=.8)
    ax.set_axisbelow(True)
    ax.set_ylabel("Books borrowed", color=INK)
    ax.set_title("Library books borrowed", color=INK, fontsize=11)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return png(fig)


def fig_square_eq():
    fig, ax = plt.subplots(figsize=(3.0, 3.0))
    ax.set_aspect("equal")
    ax.axis("off")
    A, B, C, D = (0, 0), (4, 0), (4, 4), (0, 4)
    E = (2, 2 * math.sqrt(3))
    ax.add_patch(Polygon([A, B, C, D], fc="white", ec=INK, lw=2))
    ax.add_patch(Polygon([A, B, E], fc="#ffe3f1", ec=PINK, lw=2))
    ax.plot([D[0], E[0]], [D[1], E[1]], color=INK, lw=1.6, ls="--")
    for p, lab, dx, dy in [(A, "A", -.3, -.3), (B, "B", .3, -.3), (C, "C", .3, .3), (D, "D", -.3, .3),
                           (E, "E", .05, .32)]:
        ax.text(p[0] + dx, p[1] + dy, lab, ha="center", va="center", fontsize=13, color=INK, weight="bold")
    t_d = math.degrees(math.atan2(D[1] - E[1], D[0] - E[0]))
    t_a = math.degrees(math.atan2(A[1] - E[1], A[0] - E[0])) % 360
    ax.add_patch(Arc(E, 1.1, 1.1, theta1=t_d, theta2=t_a, color=PINK, lw=1.8))
    mid = math.radians((t_d + t_a) / 2)
    ax.text(E[0] + .85 * math.cos(mid), E[1] + .85 * math.sin(mid), "x", fontsize=13, color=PINK, weight="bold",
            ha="center", va="center")
    ax.set_xlim(-.7, 4.7)
    ax.set_ylim(-.7, 4.7)
    return png(fig)


AG, ST, FR, AL, QR, MM, SP, NU, RA, SH = ("Angles_Geometry", "Statistics_Probability", "Fractions", "Algebra",
                                         "Quantitative_Reasoning", "Money_Measurement", "Speed_Distance_Time",
                                         "Number", "Ratio_Proportion", "Circles_Composite_Shapes")

# ================================================================ compass & nets
COMPASS = {0: "North", 45: "North-East", 90: "East", 135: "South-East", 180: "South", 225: "South-West",
           270: "West", 315: "North-West"}
face = (45 + 135 - 90) % 360
assert COMPASS[face] == "East"
mcq("t1", AG, "Mia faces North-East. She turns 135° clockwise, then 90° anticlockwise. Which way is she facing now?",
    ["East", "West", "South", "North-West"], "East",
    "Give each direction a bearing: North-East = 45°. Clockwise adds: 45 + 135 = 180° (South). Anticlockwise "
    "takes away: 180 − 90 = 90°, which is East.",
    "Turn directions into degrees (N = 0°, E = 90°, S = 180°, W = 270°). Clockwise = add, anticlockwise = subtract.",
    trap="Turning the wrong way for 'anticlockwise' (West)",
    source="Mistake_Tracker 2023-12-16 Q5 (135° cw then 90° acw), 2023-12-03 Q27, 2025-12-13 Q21")

mcq("t2", AG, "Town B is 4 km south and 4 km west of town A. In which direction is town A from town B?",
    ["North-East", "South-West", "North-West", "South-East"], "North-East",
    "Stand at B and look back at A. To get from B to A you go 4 km north and 4 km east, so A is North-East of B.",
    "“A from B” means: stand at B, then point to A. Draw a quick sketch.",
    trap="Answering where B is from A (South-West)",
    source="Mistake_Tracker 2023-08-20 Q28 (compass directions, relative position)")

# cube net: strip B C D E (B opposite D, C opposite E), A and F attached to C (A opposite F)
opp = {"B": "D", "D": "B", "C": "E", "E": "C", "A": "F", "F": "A"}
mcq("t3", AG, "This net is folded to make a cube. Which face is OPPOSITE face D?",
    ["B", "A", "E", "F"], opp["D"],
    "In a row of four squares (B, C, D, E), faces that are one apart end up opposite: B is opposite D and C is "
    "opposite E. A and F (above and below C) are opposite each other.",
    "In a straight strip of squares, every SECOND square is the opposite face. Faces that touch on the net can "
    "never be opposite.",
    trap="Picking a face that touches D on the net (E)",
    source="Test_Analysis_2025-07-27 Nets Q2/Q6/Q10/Q13/Q15/Q16/Q17 (7 of 7 wrong)", image=fig_net())

# ================================================================ statistics
more14 = sum(v for v in BOOKS.values() if v > 14)
assert more14 == 54
numeric("t4", ST, "Look at the graph. How many books were borrowed altogether on the days when MORE than 14 books "
        "were borrowed?", more14,
        "Read each bar: Mon 12, Tue 18, Wed 9, Thu 15, Fri 21. More than 14: Tue, Thu and Fri. "
        "18 + 15 + 21 = 54.",
        "Read every bar against the grid lines first and write the numbers on the bars. Then do the sum.",
        unit="books", trap="Including Monday (12) or misreading a bar between grid lines",
        source="Mistake_Tracker 2023-02-19 Q38/39, 2023-08-13 Q9/10, 2023-12-10 Q30-32 (bar-graph reading)",
        image=fig_bars())

avg = F(12 * 70 + 18 * 80, 30)
assert avg == 76
mcq("t5", ST, "In a class, the 12 boys have an average test mark of 70 and the 18 girls have an average of 80. "
    "What is the average mark for the whole class?",
    ["76", "75", "74", "77"], "76",
    "Total marks: boys 12 × 70 = 840, girls 18 × 80 = 1440. Together 2280 marks for 30 students. "
    "2280 ÷ 30 = 76.",
    "Averages of groups: turn each average back into a TOTAL (average × count), add, then divide by everyone.",
    trap="Averaging the two averages (75), which ignores that there are more girls",
    source="Mistake_Tracker 2024-11-24 Q40 (weighted average by gender)", difficulty=3)

data = [3, 5, 7, 8, 10, 12, 13, 15, 18, 20, 24]
lower, upper = data[:5], data[6:]
q1, q3 = lower[2], upper[2]
assert (q1, q3, q3 - q1) == (7, 18, 11)
mcq("t6", ST, "Find the interquartile range (IQR) of this data: 3, 5, 7, 8, 10, 12, 13, 15, 18, 20, 24",
    ["11", "21", "12", "13"], "11",
    "11 values, so the median is the 6th value, 12. Lower half: 3, 5, 7, 8, 10, so Q1 = 7. "
    "Upper half: 13, 15, 18, 20, 24, so Q3 = 18. IQR = 18 − 7 = 11.",
    "Odd number of values: take out the median first, then find the middle of each half. IQR = Q3 − Q1.",
    trap="Giving the range (21), or keeping the median in both halves",
    source="Test_Analysis_2026-05-22 Q10b (upper quartile)")

p_diff = 2 * F(4, 10) * F(6, 10)
assert p_diff == F(12, 25) and 1 - p_diff == F(13, 25)
mcq("t7", ST, "A bag has 4 red and 6 blue marbles. Jo takes one, looks at it and PUTS IT BACK. Then she takes "
    "another. What is the probability that the two marbles are DIFFERENT colours?",
    ["12/25", "6/25", "13/25", "1/2"], "12/25",
    "Red then blue: 4/10 × 6/10 = 24/100. Blue then red: 6/10 × 4/10 = 24/100. Add the two paths: "
    "48/100 = 12/25.",
    "Tree diagram: multiply ALONG a branch, then ADD the branches that fit. 'Different' has two branches.",
    trap="Counting only red-then-blue (6/25), or finding 'the same colour' (13/25)",
    source="Test_Analysis_2026-05-15 Q6b/Q6c/Q7b (tree diagrams)", difficulty=3)

# ================================================================ Pythagoras (3D)
face_d2 = 12 ** 2 + 4 ** 2
space = math.sqrt(face_d2 + 3 ** 2)
assert space == 13
numeric("t8", AG, "A box is 12 cm long, 4 cm wide and 3 cm high. How long is the longest straight stick that fits "
        "inside, from one bottom corner to the opposite top corner?", 13,
        "Bottom diagonal: 12² + 4² = 144 + 16 = 160. Then up the corner: 160 + 3² = 169. √169 = 13 cm.",
        "3D Pythagoras: do it twice, or use √(l² + w² + h²). Draw each right-angled triangle on its own.",
        unit="cm", trap="Stopping at the bottom diagonal (√160 ≈ 12.6)",
        source="Test_Analysis_2026-05-15 Q13/Q14/Q16 (Pythagoras incl. 3D diagonal)", difficulty=3)

# ================================================================ fractions & decimals
assert F(7, 15) == F(4, 10) + F(6, 90)          # 0.4666... = 0.4 + 0.0666...
assert abs(7 / 15 - 0.4666666) < 1e-6
mcq("t9", FR, "Which fraction is equal to the recurring decimal 0.4666… (the 6 repeats)?",
    ["7/15", "23/50", "4/9", "46/99"], "7/15",
    "0.4666… = 0.4 + 0.0666…. 0.0666… is 1/15 (because 1/15 = 0.0666…). So 0.4 + 1/15 = 6/15 + 1/15 = 7/15. "
    "Check: 7 ÷ 15 = 0.4666…",
    "Check each option by dividing. 46/99 = 0.4646… (46 repeats, not just the 6).",
    trap="46/99 (that would be 0.464646…) or 23/50 (= 0.46 exactly)",
    source="Test_Analysis_2026-02-14 Q4c/Q10 (recurring decimal ↔ fraction ↔ %)", difficulty=3)

assert F(18, 42) == F(3, 7)
mcq("t10", FR, "Simplify 18/42 FULLY.", ["3/7", "9/21", "6/21", "3/14"], "3/7",
    "HCF of 18 and 42 is 6. 18 ÷ 6 = 3 and 42 ÷ 6 = 7, so 3/7.",
    "Divide the top AND the bottom by the SAME number. Use the HCF to do it in one step.",
    trap="6/21: dividing the top by 3 but the bottom by 2 (different numbers)",
    source="Mistake_Tracker drill log 2026-07-06 (simplified 6/45 to 3/15)")

# ================================================================ algebra
m, n = -7, 4
assert m * n == -28 and m + n == -3
mcq("t11", AL, "Factorise x² − 3x − 28", ["(x − 7)(x + 4)", "(x + 7)(x − 4)", "(x − 14)(x + 2)", "(x − 7)(x − 4)"],
    "(x − 7)(x + 4)",
    "Need two numbers that MULTIPLY to −28 and ADD to −3: −7 and +4. So (x − 7)(x + 4). "
    "Check: x² + 4x − 7x − 28 = x² − 3x − 28 ✓",
    "List the factor pairs of the constant first (1×28, 2×14, 4×7), then choose signs to get the middle term.",
    trap="(x + 7)(x − 4) adds to +3; (x − 14)(x + 2) multiplies right but adds to −12",
    source="Mistake_Tracker drill log 2026-07-06 (x² − 5x − 14: checked the sum but not the product)")

a = 12
assert 4 * a + 6 == 3 * (a + 6)
word("w1", AL,
     "Mum is 4 times as old as Anya. In 6 years' time, Mum will be 3 times as old as Anya.",
     [{"label": "a", "prompt": "How old is Anya now?", "answer": 12, "unit": "years"},
      {"label": "b", "prompt": "How old will Mum be in 6 years' time?", "answer": 54, "unit": "years"}],
     ["Let Anya = a now, so Mum = 4a.",
      "In 6 years: Mum = 4a + 6 and Anya = a + 6. So 4a + 6 = 3(a + 6) = 3a + 18.",
      "4a − 3a = 18 − 6, so a = 12. Anya is 12 and Mum is 48 now.",
      "(b) Mum in 6 years = 48 + 6 = 54. Check: Anya will be 18, and 3 × 18 = 54 ✓"],
     "Ages: add the SAME number of years to EVERYONE. Write a table: now / in 6 years.",
     trap="Giving Mum's age NOW (48) for part (b)",
     source="Mistake_Tracker 2024-12-01 Q40(b) (missed the 'in 6 years' step), 2023-12-03 Q10, 2023-12-10 Q34",
     asks_for={"prompt": "Part (b) wants…", "options": ["Mum's age now", "Mum's age in 6 years",
                                                         "Anya's age in 6 years"], "answer": 1})

fifty = next(x for x in range(37) if F(1, 2) * x + (36 - x) == 27)
assert fifty == 18
numeric("t12", AL, "A jar has only 50c coins and $1 coins. There are 36 coins altogether and they are worth $27. "
        "How many 50c coins are there?", 18,
        "If all 36 were $1 coins they'd be worth $36. That's $9 too much. Each 50c coin instead of a $1 coin "
        "takes off 50c, so 9 ÷ 0.5 = 18 coins are 50c. Check: 18 × 0.5 + 18 × 1 = 9 + 18 = $27 ✓",
        "Assume they're all the bigger coin, then work out what each swap changes. Or use two equations.",
        unit="coins", trap="Giving the number of $1 coins, or guessing round numbers",
        source="Mistake_Tracker 2023-02-19 Q42, 2023-08-20 Q40, 2023-12-10 Q39 (coin problems)", difficulty=3)

# ================================================================ word-problem reasoning
give = (74 - 38) // 2
assert 74 - give == 38 + give
mcq("t13", QR, "Ali has 74 marbles and Ben has 38. How many marbles must Ali give Ben so that they both have the "
    "same number?", ["18", "36", "56", "9"], "18",
    "The difference is 74 − 38 = 36. To make them equal, Ali gives HALF the difference: 36 ÷ 2 = 18. "
    "Then both have 56.",
    "Equalising: give half the difference (giving takes from one AND adds to the other).",
    trap="Giving the whole difference (36), or the equal amount (56)",
    source="Mistake_Tracker 2023-08-20 Q41 (equalising by transfer); 2024-07-15 P1 Q19 (repeated transfer)")

start = ((29 - 5) / F(2, 3) - 8) * 2
after1 = start / 2 + 8
assert start == 56 and after1 == 36 and after1 - after1 / 3 + 5 == 29
word("w2", QR,
     "A bus left the depot with some passengers. At stop 1, half of the passengers got off and 8 got on. "
     "At stop 2, one-third of the passengers got off and 5 got on. There were then 29 passengers.",
     [{"label": "a", "prompt": "How many passengers were on the bus when it left the depot?", "answer": 56},
      {"label": "b", "prompt": "How many passengers were on the bus just after stop 1?", "answer": 36}],
     ["Work backwards from the 29 and undo each step.",
      "Undo '5 got on': 29 − 5 = 24. Undo 'one-third got off': 24 is the 2/3 left, so before stop 2 there were "
      "24 ÷ 2 × 3 = 36.",
      "(b) So 36 were on the bus just after stop 1.",
      "Undo '8 got on': 36 − 8 = 28. Undo 'half got off': 28 × 2 = 56 at the start.",
      "Check forwards: 56 → 28 + 8 = 36 → 36 − 12 + 5 = 29 ✓"],
     "Working backwards: start at the END, undo each step in reverse order (+ becomes −, 'half left' becomes ×2).",
     trap="Doing the steps forwards, or undoing 'one-third got off' by adding a third of 24",
     source="Mistake_Tracker 2023-08-20 Q45 (multi-stage bus problem, incomplete), 2024-10-13 Q28 (working backwards)",
     asks_for={"prompt": "Where should you start?", "options": ["At the depot", "With the 29 at the end", "At stop 1"],
               "answer": 1})

# ================================================================ rates, time and money
t = 600 / (40 - 10)
assert t == 20
mcq("t14", MM, "An empty 600 L tank is filled by a tap at 40 L per minute, but a leak lets out 10 L per minute. "
    "How long does it take to fill the tank?", ["20 minutes", "15 minutes", "12 minutes", "30 minutes"], "20 minutes",
    "Each minute the tank gains 40 − 10 = 30 L. 600 ÷ 30 = 20 minutes.",
    "In and out at the same time: use the NET rate (in − out).",
    trap="Ignoring the leak (15 min) or adding the rates (12 min)",
    source="Mistake_Tracker 2024-12-01 Q48 (tank leak/fill rate, unattempted)")

meet = 360 / (70 + 50)
assert meet == 3
mcq("t15", SP, "Two cars start 360 km apart and drive TOWARDS each other, one at 70 km/h and the other at 50 km/h. "
    "After how long do they meet?", ["3 hours", "18 hours", "6 hours", "2 hours"], "3 hours",
    "Driving towards each other, the gap closes by 70 + 50 = 120 km every hour. 360 ÷ 120 = 3 hours.",
    "Towards each other: ADD the speeds. Same direction: SUBTRACT them.",
    trap="Subtracting the speeds (18 hours)",
    source="Mistake_Tracker 2025-11-29 Q44 (two-object distance), 2025-10-01 Speed Q24a (relative distance)",
    difficulty=3)

mins = round(0.35 * 60)
assert mins == 21
mcq("t16", SP, "A trip takes 2.35 hours. How long is that in hours and minutes?",
    ["2 h 21 min", "2 h 35 min", "2 h 3.5 min", "2 h 15 min"], "2 h 21 min",
    "The 0.35 is a part of an HOUR, not minutes. 0.35 × 60 = 21 minutes. So 2 h 21 min.",
    "Decimal hours → minutes: multiply the decimal part by 60.",
    trap="Reading .35 as 35 minutes", source="Test_Analysis_2025-10-01 Speed Q23 (fractional hours format)")

hours = ((15 * 60 + 15) - (7 * 60 + 45) - 30) / 60
assert hours == 7 and hours * 22 == 154
numeric("t17", MM, "Sam works from 7:45 am to 3:15 pm, with a 30-minute UNPAID lunch break. He earns $22 per hour. "
        "How much does he earn for the day?", 154,
        "7:45 am to 3:15 pm: 7:45 → 8:00 is 15 min, 8:00 → 3:00 pm is 7 h, 3:00 → 3:15 is 15 min. Total 7 h 30 min. "
        "Take off the 30-minute lunch: 7 hours. 7 × $22 = $154.",
        "Count time in stages (to the next hour, whole hours, leftover minutes), then take off unpaid breaks.",
        unit="$", trap="Forgetting the unpaid break ($165)",
        source="Test_Analysis_2025-12-13 Q36/Q36a/Q36b (elapsed time and pay)")

# ================================================================ number
lcm = math.lcm(4, 5, 6)
ans = lcm + 1
assert ans == 61 and all(ans % d == 1 for d in (4, 5, 6))
numeric("t18", NU, "Mrs Lee has a bag of sweets. When she shares them equally among 4, 5 or 6 children, there is "
        "always exactly 1 sweet left over. What is the SMALLEST number of sweets (more than 1) she could have?", 61,
        "The number minus 1 must divide exactly by 4, 5 and 6. The LCM of 4, 5 and 6 is 60. So 60 + 1 = 61.",
        "'Same remainder each time' → find the LCM, then add the remainder.",
        unit="sweets", trap="Multiplying 4 × 5 × 6 = 120 (not the LOWEST common multiple) → 121",
        source="Test_Analysis_2024-10-13 Q27 (remainder/LCM, incomplete)", difficulty=3)

nums = sorted(int("".join(p)) for p in itertools.permutations("5074") if p[0] != "0" and int(p[-1]) % 2 == 1)
assert nums[0] == 4057
mcq("t19", NU, "Using each of the digits 5, 0, 7 and 4 once, what is the SMALLEST odd 4-digit number you can make?",
    ["4057", "4075", "0457", "5047"], "4057",
    "It must end in 5 or 7 (odd) and can't start with 0. Ending in 7: 4057. Ending in 5: 4075. 4057 is smaller.",
    "Try BOTH odd endings and compare. A 4-digit number can't start with 0.",
    trap="Always ending with the smallest odd digit (4075), or starting with 0 (0457 isn't 4-digit)",
    source="Mistake_Tracker 2023-02-19 Q6, 2023-08-20 Q23 (smallest odd number from digits)", difficulty=3)

# ================================================================ ratio
ratio = F(3, 4) / F(2, 3)     # boys / girls when (2/3) boys = (3/4) girls
assert ratio == F(9, 8)
mcq("t20", RA, "In a school choir, 2/3 of the boys is the SAME number as 3/4 of the girls. What is the ratio of "
    "boys to girls?", ["9 : 8", "8 : 9", "2 : 3", "3 : 4"], "9 : 8",
    "(2/3) × boys = (3/4) × girls. Make the fractions' tops the same: 6/9 of the boys = 6/8 of the girls. "
    "So 1/9 of the boys = 1/8 of the girls: boys are 9 units and girls are 8 units. Boys : girls = 9 : 8.",
    "Make the numerators equal, then the denominators give the units.",
    trap="Flipping the ratio (8 : 9), or just writing the fractions as a ratio",
    source="Mistake_Tracker 2024-11-24 Q28 (ratio from fractions of different wholes)", difficulty=3)

# ================================================================ angles
dae = 90 - 60
aed = (180 - dae) / 2
assert aed == 75
mcq("t21", AG, "ABCD is a square. ABE is an equilateral triangle drawn inside it. Find angle x = ∠AED.",
    ["75°", "60°", "30°", "45°"], "75°",
    "AE = AB (equilateral) and AB = AD (square), so AE = AD: triangle ADE is ISOSCELES. "
    "∠DAE = 90° − 60° = 30°. The two equal base angles share 180 − 30 = 150°, so x = 75°.",
    "Look for equal lengths you're not told directly: a side shared by a square and an equilateral triangle.",
    trap="Using 60° from the triangle, or stopping at ∠DAE = 30°",
    source="Mistake_Tracker 2024-12-01 Q34 (two isosceles triangles), 2023-12-03 Q31 (angle in square)",
    difficulty=4, image=fig_square_eq())

# ================================================================ circles
sector = r2(120 / 360 * PI * 6 ** 2)
assert sector == 37.68
numeric("t22", SH, "A sector of a circle has radius 6 cm and angle 120°. What is its area? (Use π = 3.14)", 37.68,
        "A 120° sector is 120/360 = 1/3 of the circle. Circle area = 3.14 × 6 × 6 = 113.04 cm². "
        "1/3 of that = 37.68 cm².",
        "Sector = (angle ÷ 360) × πr². Write the fraction first.",
        unit="cm²", trap="Using the diameter, or 2πr (that's the circumference)", tolerance=0.01,
        source="Test_Analysis_2025-12-05 Q43(a) (circle sector area)")

# ---------------------------------------------------------------- write
drill = {
    "id": "2026-10-08_throwback_mix",
    "title": "Drill 6 · Throwback Mix 🔄",
    "drill_date": "2026-10-08",
    "subject": "Maths",
    "pace_seconds": 90,
    "focus": ["Old mistakes, new numbers", "Compass & nets", "Graphs & averages", "Work backwards",
              "Rates & time", "Number puzzles"],
    "source_note": "Whole-history Mistake Tracker / Mistake Map register (2023-02-19 to 2026-10-02): logged "
                   "mistakes not yet covered by Drills 1-5. π = 3.14 as in her tests.",
    "questions": Q,
}
errs = validate(drill)
assert not errs, errs
drill["minutes"] = round(sum(q_seconds(q, 90) for q in Q) / 60)
name = "2026-10-08_throwback_mix.json"
txt = json.dumps(drill, indent=1, ensure_ascii=False)
(ROOT / "drills" / name).write_text(txt, encoding="utf-8")
vault = ROOT.parent / "Siyonah Selective Brain Prep" / "Practice" / "App_Drills"
if vault.is_dir():
    (vault / name).write_text(txt, encoding="utf-8")
print("wrote", name, len(Q), "questions,", drill["minutes"], "min,", len(txt) // 1000, "KB")
