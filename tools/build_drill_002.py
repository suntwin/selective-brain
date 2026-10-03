"""Drill 2 'Measure Magic': measurement drill built from wiki/Topics/Money_Measurement.md + Mistake_Tracker.
Every answer is computed/asserted here; diagrams are drawn with matplotlib and embedded as data URIs."""
import base64
import io
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sb.drillspec import validate  # noqa: E402

INK, PINK, LAV, FILL = "#3b2257", "#ff4fa0", "#9b7bff", "#f3ecff"
Q = []


def png(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor="white")
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


def numeric(id, topic, stem, answer, explanation, technique, unit="", trap=None, source=None, difficulty=2):
    Q.append({"id": id, "type": "numeric", "topic": topic, "difficulty": difficulty, "stem": stem,
              "answer": answer, "tolerance": 0.001, "unit": unit, "explanation": explanation,
              "technique": technique, "trap": trap, "source": source})


MM = "Money_Measurement"
SH = "Circles_Composite_Shapes"

# ------------------------------------------------------------------ diagrams
def fig_cuboid(l, w, h):
    fig, ax = plt.subplots(figsize=(4.2, 3))
    dx, dy = 1.6, 1.1
    front = [(0, 0), (l, 0), (l, h), (0, h)]
    ax.add_patch(Polygon(front, fc=FILL, ec=INK, lw=2))
    ax.add_patch(Polygon([(0, h), (dx, h + dy), (l + dx, h + dy), (l, h)], fc="#e6dcff", ec=INK, lw=2))
    ax.add_patch(Polygon([(l, 0), (l + dx, dy), (l + dx, h + dy), (l, h)], fc="#ddd0ff", ec=INK, lw=2))
    ax.text(l / 2, -0.55, f"{l * 10} cm", ha="center", fontsize=12, color=INK)
    ax.text(l + dx / 2 + 0.25, dy / 2 - 0.2, f"{w * 10} cm", fontsize=12, color=INK)
    ax.text(-0.35, h / 2, f"{h * 10} cm", ha="right", va="center", fontsize=12, color=INK)
    ax.set_xlim(-1.6, l + dx + 1.8); ax.set_ylim(-1, h + dy + 0.3); ax.set_aspect("equal"); ax.axis("off")
    return png(fig)


def fig_obtuse_triangle():
    fig, ax = plt.subplots(figsize=(4.6, 3))
    A, B, C = (0, 0), (6, 0), (8.5, 5)
    ax.add_patch(Polygon([A, B, C], fc=FILL, ec=INK, lw=2))
    ax.plot([6, 8.5], [0, 0], ls="--", color=LAV, lw=1.5)
    ax.plot([8.5, 8.5], [0, 5], ls="--", color=PINK, lw=2)
    ax.add_patch(Polygon([(8.5, 0), (8.1, 0), (8.1, 0.4), (8.5, 0.4)], fill=False, ec=PINK, lw=1.2))
    ax.text(3, -0.6, "6 cm", ha="center", fontsize=12, color=INK)
    ax.text(8.75, 2.5, "5 cm", fontsize=12, color=PINK)
    ax.text(7.45, 1.7, "5.6 cm", fontsize=10, color=INK, ha="left", rotation=63)
    ax.text(3.6, 3.0, "9.9 cm", fontsize=11, color=INK, ha="right")
    ax.set_xlim(-0.5, 10); ax.set_ylim(-1, 5.6); ax.set_aspect("equal"); ax.axis("off")
    return png(fig)


def fig_L_shape():
    fig, ax = plt.subplots(figsize=(4, 3.4))
    pts = [(0, 0), (10, 0), (10, 5), (6, 5), (6, 8), (0, 8)]
    ax.add_patch(Polygon(pts, fc=FILL, ec=INK, lw=2))
    ax.text(5, -0.7, "10 cm", ha="center", fontsize=12, color=INK)
    ax.text(-0.4, 4, "8 cm", ha="right", va="center", fontsize=12, color=INK)
    ax.text(8, 5.3, "4 cm", ha="center", fontsize=11, color=PINK)
    ax.text(6.25, 6.5, "3 cm", va="center", fontsize=11, color=PINK)
    ax.set_xlim(-2, 11); ax.set_ylim(-1.3, 8.6); ax.set_aspect("equal"); ax.axis("off")
    return png(fig)


def fig_trapezium():
    fig, ax = plt.subplots(figsize=(4.4, 2.8))
    pts = [(0, 0), (15, 0), (11, 6), (2, 6)]
    ax.add_patch(Polygon(pts, fc=FILL, ec=INK, lw=2))
    ax.plot([5, 5], [0, 6], ls="--", color=PINK, lw=2)
    ax.text(7.5, -1.1, "15 cm", ha="center", fontsize=12, color=INK)
    ax.text(6.5, 6.4, "9 cm", ha="center", fontsize=12, color=INK)
    ax.text(5.3, 3, "6 cm", fontsize=12, color=PINK)
    ax.set_xlim(-1, 16); ax.set_ylim(-1.8, 7.2); ax.set_aspect("equal"); ax.axis("off")
    return png(fig)


def fig_path():
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.add_patch(Polygon([(0, 0), (14, 0), (14, 10), (0, 10)], fc="#ffe3f1", ec=INK, lw=2))
    ax.add_patch(Polygon([(1, 1), (13, 1), (13, 9), (1, 9)], fc="#d9fbe9", ec=INK, lw=2))
    ax.text(7, 5, "lawn\n12 m × 8 m", ha="center", va="center", fontsize=12, color=INK)
    ax.text(7, 0.3, "path 1 m wide", ha="center", fontsize=10, color=PINK)
    ax.set_xlim(-0.5, 14.5); ax.set_ylim(-0.5, 10.5); ax.set_aspect("equal"); ax.axis("off")
    return png(fig)


# ------------------------------------------------------------------ A. conversion inside word problems
left = 2400 - 6 * 180
assert left == 1320
mcq("m1", MM, "A jug holds 2.4 L of juice. Mia pours out 6 cups of 180 mL each. How much juice is left in the jug?",
    ["1.32 L", "2.22 L", "1.08 L", "0.132 L"], "1.32 L",
    "Change to mL first: 2.4 L = 2400 mL. Poured out 6 × 180 = 1080 mL. Left: 2400 − 1080 = 1320 mL, which is 1.32 L.",
    "Write the target unit first, then convert everything to the SAME unit before you add or subtract.",
    trap="Taking away only one cup (2.22 L) or giving the amount poured out (1.08 L)",
    source="Topics/Money_Measurement: unit conversion is the most repeated test error", difficulty=1)
tot = 3 * 0.75 + 2 * 1.2
assert round(tot, 2) == 4.65
mcq("m2", MM, "A box holds 3 packets of rice, each 750 g, and 2 bags of flour, each 1.2 kg. What is the total mass in kg?",
    ["4.65 kg", "3.15 kg", "1.95 kg", "46.5 kg"], "4.65 kg",
    "Rice: 3 × 750 g = 2250 g = 2.25 kg. Flour: 2 × 1.2 = 2.4 kg. Total 2.25 + 2.4 = 4.65 kg.",
    "Watch the multipliers: '3 packets of 750 g' is 3 × 750 g, not 750 g.",
    trap="Counting only one packet of rice (3.15 kg)", source="Topics/Money_Measurement: quantity multipliers")
assert 360 - 8 * 35 == 80
mcq("m3", MM, "A ribbon is 3.6 m long. Sam cuts off 8 pieces that are each 35 cm long. How much ribbon is left?",
    ["80 cm", "3.25 m", "0.8 cm", "280 cm"], "80 cm",
    "3.6 m = 360 cm. Cut off 8 × 35 = 280 cm. Left: 360 − 280 = 80 cm.",
    "m → cm: × 100. Do the conversion BEFORE you subtract.",
    trap="Giving the cut-off length (280 cm) as the answer", source="Test_Analysis_2024-10-06 (dense conversion cluster)")
assert 30 / 2.5 + 1 == 13
mcq("m4", "Quantitative_Reasoning", "A straight fence is 30 m long. A post goes at each end and every 2.5 m along it. How many posts are there?",
    ["13", "12", "11", "75"], "13",
    "30 ÷ 2.5 = 12 gaps. A straight line with posts at both ends needs one more post than gaps: 13.",
    "Fence posts on a straight line: posts = gaps + 1. (Cuts on a ribbon: cuts = pieces − 1.) Draw a tiny one to check.",
    trap="Counting gaps instead of posts (12)", source="Mistake_Tracker 2026-07-10 P1 Q20 (fencepost / cuts vs pieces)")

# ------------------------------------------------------------------ B. area & volume units
assert 3.5 * 100 * 100 == 35000
mcq("m5", MM, "Convert 3.5 m² into cm².", ["350 cm²", "3 500 cm²", "35 000 cm²", "350 000 cm²"], "35 000 cm²",
    "1 m = 100 cm, so 1 m² = 100 cm × 100 cm = 10 000 cm². Then 3.5 × 10 000 = 35 000 cm².",
    "Squared units: multiply by the conversion TWICE (100 × 100 = 10 000).",
    trap="Multiplying by 100 only once (350 cm²)", difficulty=2)
mcq("m6", MM, "A container holds 24 000 cm³ of water. How many litres is that?",
    ["24 L", "240 L", "2.4 L", "2 400 L"], "24 L",
    "1 L = 1000 cm³ (1 mL = 1 cm³). So 24 000 ÷ 1000 = 24 L.",
    "Remember: 1 cm³ = 1 mL, and 1000 cm³ = 1 L.", trap="Dividing by 100 instead of 1000",
    source="Test_Analysis_2025-12-05 Q47 (L vs cm³)")

# ------------------------------------------------------------------ D. volume / capacity / rates
vol = 50 * 40 * 30
assert vol == 60000
mcq("m7", MM, "This tank is a cuboid. What is its capacity in litres?",
    ["60 L", "6 L", "600 L", "120 L"], "60 L",
    "Volume = 50 × 40 × 30 = 60 000 cm³. Since 1000 cm³ = 1 L, that's 60 L.",
    "Volume of a cuboid = length × width × height. Then cm³ ÷ 1000 = litres.",
    trap="Wrong power of ten when converting", source="ClassNotes_2025-Term3_Block-MeasurementMixed (tank volume)",
    image=fig_cuboid(5, 4, 3))
depth = 15000 / (40 * 25)
assert depth == 15
mcq("m8", MM, "A tank has a rectangular base 40 cm by 25 cm. It holds 15 L of water. How deep is the water?",
    ["15 cm", "1.5 cm", "150 cm", "37.5 cm"], "15 cm",
    "15 L = 15 000 cm³. Base area = 40 × 25 = 1000 cm². Depth = volume ÷ base area = 15 000 ÷ 1000 = 15 cm.",
    "Working backwards: height = volume ÷ base area. Change litres to cm³ first.",
    trap="Forgetting to change L to cm³", source="ClassNotes_2024-11-03 (back-solving volume, 2/4)", difficulty=3)
need = 60 * 3 / 4
assert need / 12 == 3.75
mcq("m9", MM, "The 60 L tank is already ¼ full. A tap pours in 12 L per minute. How long until the tank is full?",
    ["3 min 45 s", "5 min", "3 min 75 s", "1 min 15 s"], "3 min 45 s",
    "¼ full means ¾ is still empty: ¾ × 60 = 45 L. Then 45 ÷ 12 = 3.75 min. 0.75 min is 0.75 × 60 = 45 s, so the answer is 3 min 45 s.",
    "Fill problems: find what's still EMPTY first. Decimal minutes × 60 gives the seconds.",
    trap="Filling the whole tank (5 min), or reading 3.75 min as 3 min 75 s",
    source="ClassNotes_2025-Term3_Block-MeasurementMixed (rate + fractional fill)", difficulty=3)
mins = 18000 / 250
assert mins == 72
mcq("m10", MM, "A pool holds 18 000 L. It drains at 250 L per minute. How long does it take to empty?",
    ["1 h 12 min", "1 h 20 min", "72 h", "7 h 12 min"], "1 h 12 min",
    "18 000 ÷ 250 = 72 minutes. 72 min = 60 min + 12 min = 1 h 12 min.",
    "Minutes → hours: take out groups of 60. Don't treat 1.2 h as 1 h 20 min.",
    trap="Reading 1.2 hours as 1 h 20 min", source="Test_Analysis_2025-11-29 Q48 (tank rate)")
cups = math.floor(2000 / 150)
assert cups == 13
numeric("m11", MM, "How many 150 mL cups can be filled COMPLETELY from a 2 L bottle? (Type a whole number.)", 13,
        "2 L = 2000 mL. 2000 ÷ 150 = 13.33… Only 13 cups can be filled all the way. The 14th would only be partly full.",
        "When the answer must be 'complete' things, round DOWN.",
        trap="Rounding up to 14", source="ClassNotes_2024-03-17 (rounding in context: weak)", difficulty=2)

# ------------------------------------------------------------------ C. perimeter & area
w = 84 / 12
assert w == 7 and 2 * (12 + 7) == 38
mcq("m12", SH, "A rectangle has an area of 84 cm² and a length of 12 cm. What is its PERIMETER?",
    ["38 cm", "19 cm", "84 cm", "96 cm"], "38 cm",
    "Width = 84 ÷ 12 = 7 cm. Perimeter = 2 × (12 + 7) = 38 cm.",
    "Back-solve the missing side first, then re-read: area or perimeter?",
    trap="Adding only one length and one width (19 cm)", source="ClassNotes_2023-10-15 (working backward from perimeter)")
assert 6 * 5 / 2 == 15
mcq("m13", SH, "Find the area of the shaded triangle. The dashed pink line is the perpendicular height.",
    ["15 cm²", "29.7 cm²", "30 cm²", "16.8 cm²"], "15 cm²",
    "Area = ½ × base × perpendicular height = ½ × 6 × 5 = 15 cm². The height must be at a right angle to the base, even when it falls outside the triangle. The slanted sides are not the height.",
    "Height = the line that makes a right angle (90°) with the base. Look for the little square.",
    trap="Using a slanted side as the height (29.7 or 16.8)", source="ClassNotes_2024-04-28 / 05-05 (base–height identification: weak)",
    difficulty=3, image=fig_obtuse_triangle())
perim = 2 * (10 + 8)
assert perim == 36
mcq("m14", SH, "Find the PERIMETER of this shape. All corners are right angles.",
    ["36 cm", "29 cm", "68 cm", "43 cm"], "36 cm",
    "Walk around the outside edge: 10 + 5 + 4 + 3 + 6 + 8 = 36 cm. The two missing sides are 8 − 3 = 5 cm and 10 − 4 = 6 cm. A notch in a corner doesn't change the perimeter of the rectangle around it: 2 × (10 + 8) = 36.",
    "Perimeter: trace the outside with your finger and label every missing side before adding.",
    trap="Subtracting the notch's sides, or giving the area (68)", source="Topics/Circles_Composite_Shapes (composite perimeter)",
    difficulty=3, image=fig_L_shape())
assert (9 + 15) / 2 * 6 == 72
mcq("m15", SH, "Find the area of this trapezium.", ["72 cm²", "144 cm²", "54 cm²", "90 cm²"], "72 cm²",
    "Area = ½ × (sum of parallel sides) × height = ½ × (9 + 15) × 6 = ½ × 24 × 6 = 72 cm².",
    "Trapezium: average the two parallel sides, then × height.",
    trap="Forgetting the ½ (144)", source="Practice/Area_Perimeter_Drill.md (trapezium)", image=fig_trapezium())
path = 14 * 10 - 12 * 8
assert path == 44
mcq("m16", SH, "A path 1 m wide goes around the OUTSIDE of a 12 m by 8 m lawn. What is the area of the path?",
    ["44 m²", "40 m²", "140 m²", "22 m²"], "44 m²",
    "Big rectangle (lawn + path) = 14 m × 10 m = 140 m². The path adds 1 m on EACH side. Take away the lawn: 140 − 96 = 44 m².",
    "Border/path area = big outside rectangle − inside rectangle. Each side grows by 2 × the path width.",
    trap="Perimeter × width (40), forgetting the corners", difficulty=3, image=fig_path())

# ------------------------------------------------------------------ E. time
assert (14 * 60 + 20) - (10 * 60 + 45) == 3 * 60 + 35
mcq("m17", MM, "A train leaves at 10:45 am and arrives at 2:20 pm. How long is the trip?",
    ["3 h 35 min", "4 h 25 min", "3 h 25 min", "4 h 35 min"], "3 h 35 min",
    "Count up: 10:45 → 11:00 is 15 min. 11:00 → 2:00 pm is 3 h. 2:00 → 2:20 is 20 min. Total 3 h 35 min.",
    "Elapsed time: jump to the next whole hour, then whole hours, then the leftover minutes.",
    trap="Subtracting times like ordinary decimals", source="Oxford Yr8 8G (duration method); Test_Analysis_2025-12-05 Q46")
end = (19 * 60 + 40 + 2 * 60 + 35) % (24 * 60)
assert end == 22 * 60 + 15
mcq("m18", MM, "A movie starts at 19:40 and runs for 2 h 35 min. What time does it finish, in 12-hour time?",
    ["10:15 pm", "10:15 am", "9:15 pm", "11:15 pm"], "10:15 pm",
    "19:40 + 2 h = 21:40. Add 35 min: 21:40 + 20 min = 22:00, + 15 min = 22:15. 22:15 is 10:15 pm.",
    "24-hour → 12-hour: afternoon/evening times subtract 12 and add 'pm'.",
    trap="Forgetting pm (10:15 am)", source="Oxford Yr8 8G (12/24-hour time)")
mcq("m19", MM, "Melbourne is on UTC+10 and Perth is on UTC+8 (no daylight saving). It's 4:30 pm in Melbourne. What time is it in Perth?",
    ["2:30 pm", "6:30 pm", "4:30 pm", "12:30 pm"], "2:30 pm",
    "Perth is 2 hours BEHIND Melbourne (8 is less than 10). 4:30 pm − 2 h = 2:30 pm.",
    "Time zones: a bigger UTC number is further ahead. West of us = earlier.",
    trap="Adding the difference instead of subtracting", source="Oxford Yr8 8G (time zones)")
assert 200 / 2.5 == 80
mcq("m20", "Speed_Distance_Time", "A car leaves at 9:50 am and arrives at 12:20 pm. It travels 200 km. What is its average speed?",
    ["80 km/h", "83.3 km/h", "66.7 km/h", "100 km/h"], "80 km/h",
    "9:50 → 12:20 is 2 h 30 min = 2.5 h. Speed = 200 ÷ 2.5 = 80 km/h.",
    "Clock times → duration first. 30 min = 0.5 h, not 0.3 h.", trap="Using 2.4 h or 3 h",
    source="Oxford Yr8 8G cross-reference to Speed_Distance_Time")

# ------------------------------------------------------------------ F. money & rates
a, b = 4.50 / 0.75, 6.60 / 1.2
assert round(a, 2) == 6.00 and round(b, 2) == 5.50
mcq("m21", MM, "Which is the better buy? A: 750 g of cereal for $4.50. B: 1.2 kg of cereal for $6.60.",
    ["B: $5.50 per kg", "A: $6.00 per kg", "They cost the same per kg", "A: $0.60 per kg"], "B: $5.50 per kg",
    "Compare price per kg. A: $4.50 ÷ 0.75 kg = $6.00/kg. B: $6.60 ÷ 1.2 kg = $5.50/kg. B is cheaper per kg.",
    "Best buy: change to the same unit (per kg or per 100 g), THEN compare.",
    trap="Comparing the sticker prices only", source="ClassNotes_2026-01-30 (best-buy: 1/5)", shuffle=True)
pay = 38 * 24 + 4 * 24 * 1.5
assert pay == 1056
mcq("m22", MM, "Ella earns $24 per hour. One week she works 38 normal hours, plus 4 hours of overtime at time-and-a-half. What is her pay for the week?",
    ["$1056", "$1008", "$1104", "$1152"], "$1056",
    "Normal: 38 × $24 = $912. Overtime rate = 1.5 × $24 = $36. Overtime: 4 × $36 = $144. Total $912 + $144 = $1056.",
    "Time-and-a-half = rate × 1.5. Double time = rate × 2. Work out each part separately.",
    trap="Paying all 42 hours at the normal rate ($1008)", source="ClassNotes_2026-02-06 (wages & overtime)")
km = (36.45 - 4.20) / 2.15
assert round(km, 6) == 15
mcq("m23", MM, "A taxi charges $4.20 to start, plus $2.15 for every km. Jai's fare was $36.45. How far did he travel?",
    ["15 km", "16.95 km", "17 km", "13 km"], "15 km",
    "Take off the starting charge: $36.45 − $4.20 = $32.25. Then $32.25 ÷ $2.15 = 15 km. Check: 4.20 + 15 × 2.15 = 36.45 ✓",
    "Working backwards: undo the steps in REVERSE order (subtract the fixed fee first, then divide).",
    trap="Dividing the whole fare by $2.15", source="ClassNotes_2026-04-03 (reverse rate-table: 0/1)", difficulty=3)

# ------------------------------------------------------------------ G. estimation / scale / mass
mcq("m24", "Number", "Which is the best ESTIMATE of 49.7 × 0.205?", ["10", "1", "100", "0.1"], "10",
    "49.7 ≈ 50 and 0.205 ≈ 0.2. 50 × 0.2 = 10. (The exact answer is 10.1885.)",
    "Estimate: round each number to one easy figure first, then multiply.", trap="Losing track of the decimal place",
    source="ClassNotes_2024-03-17 (rounding/estimation: 11/18)", shuffle=False)
assert 6.4 * 25000 / 100000 == 1.6
mcq("m25", MM, "A map has a scale of 1 : 25 000. Two towns are 6.4 cm apart on the map. How far apart are they in real life?",
    ["1.6 km", "16 km", "0.16 km", "160 km"], "1.6 km",
    "6.4 × 25 000 = 160 000 cm. 160 000 cm = 1600 m = 1.6 km (÷ 100 for m, then ÷ 1000 for km).",
    "cm → km: ÷ 100 000 (÷ 100 for m, then ÷ 1000 for km).", trap="Dropping a zero when converting",
    difficulty=3)
apple = (450 - 200) / (3 - 2)
assert apple == 250
mcq("m26", MM, "3 identical apples and a 200 g weight balance exactly with 2 of the same apples and a 450 g weight. What is the mass of ONE apple?",
    ["250 g", "650 g", "125 g", "0.25 g"], "250 g",
    "Take 2 apples off both sides: 1 apple + 200 g = 450 g. So 1 apple = 450 − 200 = 250 g.",
    "Balance problems: remove the SAME thing from both sides until one item is left alone.",
    source="ClassNotes_2023-08-27 Q28 (balance-scale mass)", difficulty=2)

# ------------------------------------------------------------------ assemble
order = ["m1", "m6", "m12", "m17", "m4", "m2", "m13", "m21", "m5", "m9", "m18", "m14", "m11", "m22", "m3",
         "m7", "m24", "m19", "m15", "m23", "m8", "m20", "m26", "m16", "m10", "m25"]
qm = {q["id"]: q for q in Q}
assert sorted(order) == sorted(qm), set(qm) ^ set(order)
drill = {
    "id": "2026-10-04_measure_magic",
    "title": "Drill 2 · Measure Magic 📏",
    "drill_date": "2026-10-04",
    "subject": "Maths",
    "minutes": 39,
    "pace_seconds": 90,
    "focus": ["Unit conversion", "Volume & tanks", "Area & perimeter", "Time", "Best buy & rates"],
    "source_note": "wiki/Topics/Money_Measurement.md (most-repeated test error: unit conversion) + Area/Perimeter drill + "
                   "ClassNotes 2024-03-17, 2024-04-28, 2024-11-03, 2025-T3 MeasurementMixed, 2026-01-30, 2026-04-03 + Oxford Yr8 8G",
    "questions": [qm[i] for i in order],
}
errs = validate(drill)
assert not errs, errs
out = ROOT / "drills" / "2026-10-04_measure_magic.json"
out.write_text(json.dumps(drill, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", out, len(drill["questions"]), "questions,", round(out.stat().st_size / 1024), "KB")
