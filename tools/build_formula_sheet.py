"""Formula revision sheet: every formula/rule across Oxford Maths Victoria Years 7-10 (all chapters except
Computational thinking), grouped by topic with a year tag. Yr 7-8 = SEHS level (starred); Yr 9-10 = extension.
Sources: raw/OxfordBooks tables of contents (all 4 books), Practice/Foundation_Maths_Test_Formulas.md,
Practice/Formula_Reference.md, wiki/Topics/*, Mistake Tracker (watch-outs)."""
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
                                KeepTogether, FrameBreak, NextPageTemplate, PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

D = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", D + "DejaVuSansCondensed.ttf"))
pdfmetrics.registerFont(TTFont("DVB", D + "DejaVuSansCondensed-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVI", D + "DejaVuSansCondensed-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("DVBI", D + "DejaVuSansCondensed-BoldOblique.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily  # noqa: E402
registerFontFamily("DV", normal="DV", bold="DVB", italic="DVI", boldItalic="DVBI")

INK = colors.HexColor("#2b1d4a")
PINK = colors.HexColor("#d6336c")
LAV = colors.HexColor("#6f52d9")
SOFT = colors.HexColor("#f3eefc")
GREY = colors.HexColor("#6b6880")
TAGC = {"7": colors.HexColor("#d6336c"), "8": colors.HexColor("#e8590c"),
        "9": colors.HexColor("#5f6fd6"), "10": colors.HexColor("#3d7a8c")}

H = ParagraphStyle("h", fontName="DVB", fontSize=10.5, textColor=colors.white, leading=13)
B = ParagraphStyle("b", fontName="DV", fontSize=7.9, leading=9.9, textColor=INK, alignment=TA_LEFT)
BX = ParagraphStyle("bx", parent=B, textColor=GREY)
TITLE = ParagraphStyle("t", fontName="DVB", fontSize=20, leading=24, textColor=INK)
SUB = ParagraphStyle("s", fontName="DV", fontSize=9, leading=12, textColor=GREY)
SMALL = ParagraphStyle("sm", fontName="DV", fontSize=7, leading=9, textColor=GREY)


def sup(s):
    return f"<super>{s}</super>"


S2, S3 = sup("2"), sup("3")

# (year, text, extension?)  text uses ReportLab mini-HTML. Yr 7/8 = core (SEHS level), 9/10 = extension.
TOPICS = [
 ("1 · Numbers, integers & order of operations", [
  ("7", "<b>Place value</b>: 32 456 = 3×10 000 + 2×1000 + 4×100 + 5×10 + 6. Round: look at the next digit, 5 or more rounds up."),
  ("7", "<b>Order of operations (BIDMAS)</b>: Brackets → Indices/roots → × and ÷ left to right → + and − left to right."),
  ("7", "<b>Divisibility</b>: 2 even · 3 digit sum ÷3 · 4 last two digits ÷4 · 5 ends 0/5 · 6 both 2 and 3 · 8 last three ÷8 · 9 digit sum ÷9 · 10 ends 0."),
  ("7", "<b>HCF</b> = biggest shared factor. <b>LCM</b> = smallest shared multiple. With prime factors: HCF = shared primes (lowest power), LCM = all primes (highest power)."),
  ("7", "<b>Prime</b> = exactly 2 factors. 1 is not prime. Prime factorisation, e.g. 360 = 2" + S3 + " × 3" + S2 + " × 5."),
  ("7", "<b>Number patterns</b>: find the rule (+, ×, squares, cubes, triangular). Repeating pattern: position ÷ block length, use the REMAINDER."),
  ("8", "<b>Integers</b>: same signs × or ÷ → +; different signs → −. a − (−b) = a + b. (−2)" + S2 + " = 4 but −2" + S2 + " = −4; (−2)" + S3 + " = −8."),
  ("8", "<b>Estimate</b>: round every number (often to 1 significant figure) before calculating."),
 ]),
 ("2 · Fractions & decimals", [
  ("7", "<b>Equivalent / simplify</b>: divide top AND bottom by the SAME number (the HCF does it in one step)."),
  ("7", "<b>+ and −</b>: common denominator first. <b>×</b>: top×top over bottom×bottom (cancel first). <b>÷</b>: keep, change, flip."),
  ("7", "<b>Mixed ↔ improper</b>: 2¾ = (2×4+3)/4 = 11/4. 27/6 = 4 r 3 = 4 3/6 = 4½."),
  ("7", "<b>Fraction of a quantity</b>: ¾ of 60 = 60 ÷ 4 × 3 = 45. <b>Fraction of the REMAINDER</b>: work on what is left, e.g. spend ¼ then ½ of the rest → ¾ × ½ = 3/8 left."),
  ("7", "<b>Decimals</b>: line up the points to + or −. × : multiply as whole numbers, then count total decimal places. ÷ by a decimal: move both points until the divisor is whole."),
  ("8", "<b>Terminating vs recurring</b>: a simplified fraction terminates only if the denominator's prime factors are just 2s and 5s. 1/3 = 0.333…, 0.4666… = 7/15."),
  ("8", "<b>Rational</b> = can be written as a fraction (incl. recurring decimals). <b>Irrational</b> = never ends, never repeats (π, √2)."),
 ]),
 ("3 · Percentages & money", [
  ("7", "<b>% ↔ fraction ↔ decimal</b>: 35% = 35/100 = 0.35. <b>X% of Y</b> = X/100 × Y. Find 10% (÷10) then build up."),
  ("8", "<b>% change</b> = change ÷ ORIGINAL × 100%. Increase by r% → × (1 + r/100); decrease → × (1 − r/100)."),
  ("8", "<b>Reverse %</b>: after 20% off it costs $96 → $96 ÷ 0.8 = $120. GST 10%: price incl. GST ÷ 1.1 = price before GST."),
  ("8", "<b>Profit</b> = selling price − cost price. <b>% profit</b> = profit ÷ COST × 100%. Mark-up: SP = CP × (1 + m). Discount: SP = MP × (1 − d)."),
  ("8", "<b>Chains</b>: each % works on the NEW amount. 25% off then 10% off ≠ 35% off (it is 32.5%)."),
  ("8", "<b>% of a changing whole</b>: when people join/leave, the part AND the total change → new part ÷ NEW total."),
  ("9", "<b>Simple interest</b>: I = PrT (r as a decimal per year, T in years). A = P + I. Rearrange: P = I/(rT), T = I/(Pr)."),
  ("10", "<b>Compound interest</b>: A = P(1 + R)" + sup("n") + " (R per period, n periods). Interest = A − P. Depreciation: V = P(1 − R)" + sup("n") + "."),
  ("9", "<b>Wages</b>: overtime ×1.5 (time-and-a-half) or ×2. Best buy: price ÷ quantity, smaller unit price wins."),
 ]),
 ("4 · Ratios, rates & proportion", [
  ("7", "<b>Ratio</b>: same units, whole numbers, in the order asked. Simplify by the HCF. 1.5 m : 90 cm = 150 : 90 = 5 : 3."),
  ("8", "<b>Share in a ratio</b>: total parts → value of 1 part → multiply. Difference of parts = given difference → find 1 part."),
  ("8", "<b>Combine ratios</b>: A:B = 2:3, B:C = 4:5 → make B the same (8:12:15)."),
  ("8", "<b>Ratio change</b>: find the quantity that stays the SAME and match its units before/after."),
  ("8", "<b>Ratio from fractions</b>: ⅔ of boys = ¾ of girls → make tops equal (6/9 = 6/8) → boys : girls = 9 : 8."),
  ("8", "<b>Rate</b> = one quantity per one of another (km/h, $/kg, L/min). <b>Unitary method</b>: find 1 unit first."),
  ("9", "<b>Direct proportion</b>: y = kx (straight line through the origin, k = y/x). <b>Inverse</b> (Yr 10): y = k/x."),
 ]),
 ("5 · Indices, roots, surds & logs", [
  ("7", "a" + S2 + " = a×a, a" + S3 + " = a×a×a, √ undoes squaring (√49 = 7), ∛ undoes cubing (∛64 = 4)."),
  ("8", "<b>Index laws</b>: a" + sup("m") + " × a" + sup("n") + " = a" + sup("m+n") + " · a" + sup("m") + " ÷ a" + sup("n") + " = a" + sup("m−n") + " · (a" + sup("m") + ")" + sup("n") + " = a" + sup("mn") + " (MULTIPLY) · a" + sup("0") + " = 1."),
  ("8", "<b>Brackets</b>: (2a" + S3 + ")" + S3 + " = 8a" + sup("9") + " (the 2 is cubed too) but 2(a" + S3 + ")" + S3 + " = 2a" + sup("9") + ". (5y)" + sup("0") + " = 1 but 5y" + sup("0") + " = 5."),
  ("9", "<b>Negative index</b>: a" + sup("−n") + " = 1/a" + sup("n") + " (2" + sup("−3") + " = 1/8). <b>Scientific notation</b>: a × 10" + sup("n") + ", 1 ≤ a < 10; small numbers → negative n (0.00045 = 4.5 × 10" + sup("−4") + ")."),
  ("9", "<b>Surds</b>: √ab = √a × √b; simplify √18 = 3√2; add only like surds (2√3 + 5√3 = 7√3)."),
  ("10", "<b>Fractional index</b>: a" + sup("1/n") + " = ⁿ√a, a" + sup("m/n") + " = (ⁿ√a)" + sup("m") + ". <b>Rationalise</b>: x/√y = x√y/y."),
  ("10", "<b>Logs</b>: a" + sup("x") + " = y ⇔ log<sub>a</sub>y = x. log(mn) = log m + log n; log(m/n) = log m − log n; log m" + sup("p") + " = p log m."),
 ]),
 ("6 · Algebra", [
  ("7", "<b>Words</b>: variable (letter), term (joined by × ÷), coefficient (number in front), like terms (same letters, same powers)."),
  ("7", "<b>Substitution</b>: replace the letter with the number in brackets, then BIDMAS. If x = −2: 3x" + S2 + " = 3 × 4 = 12."),
  ("8", "<b>Expand</b>: a(b + c) = ab + ac; −a(b − c) = −ab + ac (a minus in front flips every sign)."),
  ("8", "<b>Factorise with the HCF</b>: take out the number AND the letters: 6x" + S2 + "y + 9xy = 3xy(2x + 3)."),
  ("9", "<b>Two brackets</b>: (a + b)(c + d) = ac + ad + bc + bd. (a + b)" + S2 + " = a" + S2 + " + 2ab + b" + S2 + " (don't drop 2ab)."),
  ("9", "<b>Difference of two squares</b>: a" + S2 + " − b" + S2 + " = (a + b)(a − b). (x − 3)" + S2 + " − 121 = (x − 3 − 11)(x − 3 + 11) = (x − 14)(x + 8)."),
  ("9", "<b>x" + S2 + " + bx + c</b>: two numbers that MULTIPLY to c AND ADD to b. Check by expanding. Grouping (4 terms): pair, factor, common bracket."),
  ("10", "<b>Algebraic fractions</b>: factorise, cancel; + or − over the LCD, put a subtracted top in brackets. Completing the square: x" + S2 + " + bx = (x + b/2)" + S2 + " − (b/2)" + S2 + "."),
 ]),
 ("7 · Equations & inequalities", [
  ("7", "<b>Solve</b>: undo operations in reverse order, same thing to both sides. Always check by substituting back."),
  ("8", "<b>Unknown on both sides</b>: move the smaller x-term first: 5x + 3 = 2x + 18 → 3x = 15 → x = 5."),
  ("8", "<b>Word problems</b>: let x = one person; write the others in terms of x; solve; then answer for the person ASKED."),
  ("9", "<b>Quadratics</b>: make = 0, factorise, null factor law (ab = 0 → a = 0 or b = 0). Never divide by x."),
  ("10", "<b>Inequalities</b>: solve like equations, but FLIP the sign when you × or ÷ by a negative. <b>Simultaneous</b>: substitute or eliminate."),
  ("10", "<b>Quadratic formula</b>: x = (−b ± √(b" + S2 + " − 4ac)) / 2a. Discriminant b" + S2 + " − 4ac: >0 two, =0 one, <0 no solutions."),
 ]),
 ("8 · Graphs: linear & non-linear", [
  ("7", "<b>Cartesian plane</b>: (x, y) – across then up. Quadrants 1 to 4 anticlockwise from top right."),
  ("8", "<b>Linear rule</b> from a table: y = (change in y ÷ change in x) × x + (y when x = 0)."),
  ("9", "<b>Gradient</b> m = rise/run = (y<sub>2</sub> − y<sub>1</sub>)/(x<sub>2</sub> − x<sub>1</sub>). <b>y = mx + c</b>: c = y-intercept. x-intercept: put y = 0."),
  ("9", "<b>Midpoint</b> = ((x<sub>1</sub> + x<sub>2</sub>)/2, (y<sub>1</sub> + y<sub>2</sub>)/2). <b>Length</b> = √((x<sub>2</sub> − x<sub>1</sub>)" + S2 + " + (y<sub>2</sub> − y<sub>1</sub>)" + S2 + ")."),
  ("10", "<b>Parallel</b>: same m. <b>Perpendicular</b>: m<sub>1</sub> × m<sub>2</sub> = −1. Line through (x<sub>1</sub>, y<sub>1</sub>): y − y<sub>1</sub> = m(x − x<sub>1</sub>)."),
  ("9", "<b>Parabola</b> y = a(x − h)" + S2 + " + k: turning point (h, k). y = ax" + S2 + " + bx + c: axis x = −b/2a. <b>Circle</b>: x" + S2 + " + y" + S2 + " = r" + S2 + "."),
  ("10", "<b>Hyperbola</b> y = k/x. <b>Exponential</b> y = a" + sup("x") + ". <b>Polynomials</b>: remainder theorem – P(x) ÷ (x − a) leaves P(a); P(a) = 0 → (x − a) is a factor."),
 ]),
 ("9 · Angles, shapes & geometry", [
  ("7", "Straight line 180° · around a point 360° · vertically opposite angles equal · right angle 90°."),
  ("7", "<b>Parallel lines</b>: alternate equal (Z), corresponding equal (F), co-interior add to 180° (C)."),
  ("7", "<b>Triangle</b> angles = 180°; exterior angle = sum of the two opposite interior angles. Isosceles: base angles equal. Equilateral: all 60°."),
  ("7", "<b>Quadrilaterals</b> add to 360°. Square, rectangle, rhombus, parallelogram, kite, trapezium – know their sides, angles, diagonals."),
  ("7", "<b>Polygon</b> angle sum = (n − 2) × 180°; regular polygon: each angle = sum ÷ n; exterior angles add to 360°."),
  ("7", "<b>3D</b>: Euler F + V − E = 2. Cube net: in a strip of 4 squares, every SECOND square is opposite. Plans & elevations: top, front, side views."),
  ("7", "<b>Compass</b>: N 0°, E 90°, S 180°, W 270°. Clockwise = add, anticlockwise = subtract. ¾ turn = 270°."),
  ("7", "<b>Transformations</b>: translate, reflect, rotate (order matters). Symmetry: lines of symmetry; order of rotational symmetry."),
  ("8", "<b>Congruent triangles</b>: SSS, SAS, AAS, RHS (not AAA, not SSA)."),
  ("9", "<b>Similar figures</b>: SSS, SAS, AAA, RHS. Scale factor k = image ÷ original; areas × k" + S2 + ", volumes × k" + S3 + "."),
  ("10", "<b>Circle geometry</b>: angle at centre = 2 × angle at circumference · angle in a semicircle = 90° · cyclic quadrilateral: opposite angles add to 180° · radius ⊥ chord bisects it."),
 ]),
 ("10 · Pythagoras & trigonometry", [
  ("9", "<b>Pythagoras</b> c" + S2 + " = a" + S2 + " + b" + S2 + " (c = hypotenuse, opposite the right angle). Shorter side: a" + S2 + " = c" + S2 + " − b" + S2 + ". Triples: 3-4-5, 5-12-13, 8-15-17, 7-24-25."),
  ("9", "<b>3D diagonal</b> of a box = √(l" + S2 + " + w" + S2 + " + h" + S2 + ") (use Pythagoras twice)."),
  ("9", "<b>SOH CAH TOA</b>: sin θ = O/H, cos θ = A/H, tan θ = O/A. Angle: θ = sin" + sup("−1") + "(O/H) etc."),
  ("10", "<b>Sine rule</b> a/sin A = b/sin B. <b>Cosine rule</b> c" + S2 + " = a" + S2 + " + b" + S2 + " − 2ab cos C. <b>Area</b> = ½ab sin C."),
  ("10", "<b>Exact values</b>: sin 30° = ½, cos 60° = ½, tan 45° = 1, sin 45° = cos 45° = 1/√2, sin 60° = cos 30° = √3/2."),
 ]),
 ("11 · Length, area & circles", [
  ("7", "<b>Perimeter</b> = all edges (same units). <b>Rectangle</b> A = lw. <b>Parallelogram</b> A = bh (PERPENDICULAR height). <b>Triangle</b> A = ½bh."),
  ("8", "<b>Trapezium</b> A = ½(a + b)h. <b>Kite / rhombus</b> A = ½xy (diagonals)."),
  ("8", "<b>Circle</b>: C = 2πr = πd, A = πr" + S2 + ". Use π = 3.14 unless told."),
  ("8", "<b>Semicircle</b>: ½ area; perimeter = πr + d. <b>Quarter circle</b>: ¼ area; arc = 2πr ÷ 4 = πr/2 (not πr/4!); perimeter = arc + 2r."),
  ("9", "<b>Sector</b> A = (θ/360) × πr" + S2 + "; <b>arc</b> = (θ/360) × 2πr. <b>Ring</b> A = πR" + S2 + " − πr" + S2 + "."),
  ("9", "<b>Composite</b>: add or subtract pieces. Overlap: A + B − overlap. Shaded perimeter: trace every edge that touches the shading."),
  ("8", "<b>Area units</b>: 1 cm" + S2 + " = 100 mm" + S2 + ", 1 m" + S2 + " = 10 000 cm" + S2 + ", 1 ha = 10 000 m" + S2 + "."),
 ]),
 ("12 · Surface area & volume", [
  ("7", "<b>Cuboid</b> V = lwh; TSA = 2(lw + lh + wh). <b>Cube</b> V = s" + S3 + ", TSA = 6s" + S2 + "."),
  ("7", "<b>Capacity</b>: 1 cm" + S3 + " = 1 mL, 1000 cm" + S3 + " = 1 L, 1 m" + S3 + " = 1000 L = 1 kL."),
  ("8", "<b>Any prism</b> V = area of cross-section × length. Water in a tank: use the WATER height."),
  ("9", "<b>Cylinder</b> V = πr" + S2 + "h; TSA = 2πr" + S2 + " + 2πrh."),
  ("10", "<b>Pyramid</b> V = ⅓ × base × h. <b>Cone</b> V = ⅓πr" + S2 + "h, TSA = πr" + S2 + " + πrs. <b>Sphere</b> V = 4/3 πr" + S3 + ", TSA = 4πr" + S2 + "."),
 ]),
 ("13 · Time, speed & units", [
  ("8", "<b>Speed</b> = distance ÷ time; distance = speed × time; time = distance ÷ speed (units must match)."),
  ("8", "<b>Average speed</b> = TOTAL distance ÷ TOTAL time. Towards each other: add speeds; same direction: subtract."),
  ("8", "<b>Decimal hours</b>: 2.35 h = 2 h + 0.35 × 60 min = 2 h 21 min. 45 min = 0.75 h."),
  ("8", "<b>Elapsed time</b>: count to the next hour, then whole hours, then minutes. 24-h time: 3:15 pm = 15:15."),
  ("7", "<b>Length</b>: 10 mm = 1 cm, 100 cm = 1 m, 1000 m = 1 km. <b>Mass</b>: 1000 g = 1 kg, 1000 kg = 1 t. <b>Volume</b>: 1000 mL = 1 L."),
  ("8", "<b>Rates in & out</b>: net rate = in − out. Convert to the unit the question asks for at the END."),
 ]),
 ("14 · Statistics", [
  ("7", "<b>Mean</b> = total ÷ count (so total = mean × count). <b>Median</b> = middle of ordered data. <b>Mode</b> = most common. <b>Range</b> = max − min."),
  ("7", "<b>Graphs</b>: read every bar/point against the scale first. Stem-and-leaf: key 2|4 = 24."),
  ("8", "<b>Combined mean</b> = (n<sub>1</sub>×mean<sub>1</sub> + n<sub>2</sub>×mean<sub>2</sub>) ÷ (n<sub>1</sub> + n<sub>2</sub>), not the average of the averages."),
  ("8", "<b>Conditions</b> (e.g. different whole numbers): make the others as small/large as the rules allow."),
  ("9", "<b>Frequency table</b> mean = Σ(score × freq) ÷ Σfreq. Histograms: no gaps. Skewed data → use the median."),
  ("10", "<b>Quartiles</b>: Q1 = middle of lower half, Q3 = middle of upper half; IQR = Q3 − Q1. Box plot = min, Q1, median, Q3, max. Outlier: beyond Q1 − 1.5×IQR or Q3 + 1.5×IQR."),
  ("10", "Standard deviation measures spread from the mean. Scatterplots: positive/negative, strong/weak; line of best fit."),
 ]),
 ("15 · Probability", [
  ("7", "<b>P(event)</b> = favourable ÷ total, between 0 and 1. <b>P(not A)</b> = 1 − P(A). Experimental: relative frequency = times ÷ trials."),
  ("8", "<b>Two-way tables & Venn</b>: n(A or B) = n(A) + n(B) − n(A and B). Read 'only A', 'neither' carefully."),
  ("9", "<b>Two steps</b>: multiply ALONG branches, ADD paths. WITH replacement: same fractions; WITHOUT: top and bottom drop by 1."),
  ("10", "<b>Conditional</b>: P(A | B) = P(A and B) ÷ P(B). <b>Independent</b>: P(A and B) = P(A) × P(B)."),
 ]),
]

WATCH = [
 ("Quarter arc", "2πr ÷ 4 = πr/2. You wrote πr/4 in Term 3 Test 1 (answer came out exactly half)."),
 ("% of WHAT?", "'Of the remaining' → work on what is LEFT. People join → divide by the NEW total."),
 ("Overlap", "Whole figure = A + B − overlap. Count the shared part once."),
 ("Condition words", "Underline different, each, at least, more than, remaining before you start."),
 ("Last line", "Re-read the question: right person? right unit? the thing asked, not an in-between number?"),
 ("Power of a power", "(x" + S3 + ")" + sup("4") + " = x" + sup("12") + " – MULTIPLY the powers. (3x)" + sup("0") + " = 1."),
 ("Factor pairs", "x" + S2 + " − 5x − 14: numbers must MULTIPLY to −14 AND add to −5 → (x − 7)(x + 2)."),
 ("Simplify", "Divide top and bottom by the SAME number: 6/45 = 2/15 (not 3/15)."),
 ("Cuts vs pieces", "A straight ribbon in 10 pieces needs 9 cuts; fence posts = gaps + 1."),
 ("Never blank", "Stuck? Write part (a), star it, move on, come back. Every part can earn marks."),
]


def topic_block(title, rows):
    head = Table([[Paragraph(title, H)]], colWidths=[88 * mm])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), INK), ("LEFTPADDING", (0, 0), (-1, -1), 5),
                              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                              ("ROUNDEDCORNERS", [3, 3, 0, 0])]))
    data = []
    for yr, txt in rows:
        tag = Paragraph(f'<font color="#ffffff"><b>{"★" if yr in ("7", "8") else ""}Y{yr}</b></font>',
                        ParagraphStyle("tg", fontName="DVB", fontSize=6.6, leading=8, alignment=TA_CENTER))
        data.append([tag, Paragraph(txt, B if yr in ("7", "8") else BX)])
    body = Table(data, colWidths=[9 * mm, 79 * mm])
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 3),
          ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 2.2),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2), ("LINEBELOW", (0, 0), (-1, -2), .3, colors.HexColor("#e2dcf2")),
          ("BOX", (0, 0), (-1, -1), .6, INK)]
    for i, (yr, _) in enumerate(rows):
        st.append(("BACKGROUND", (0, i), (0, i), TAGC[yr]))
        if yr in ("7", "8"):
            st.append(("BACKGROUND", (1, i), (1, i), SOFT))
    body.setStyle(TableStyle(st))
    return KeepTogether([head, body, Spacer(1, 4.5 * mm)])


def watch_block():
    head = Table([[Paragraph("Siyonah's watch-outs (from your own tests)", H)]], colWidths=[88 * mm])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PINK), ("LEFTPADDING", (0, 0), (-1, -1), 5),
                              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    rows = [[Paragraph(f"<b>{a}</b>", B), Paragraph(b, B)] for a, b in WATCH]
    body = Table(rows, colWidths=[22 * mm, 66 * mm])
    body.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), .6, PINK),
                              ("LINEBELOW", (0, 0), (-1, -2), .3, colors.HexColor("#f5c2d4")),
                              ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff3f7")),
                              ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2)]))
    return KeepTogether([head, body])


def on_page(c, doc):
    c.saveState()
    c.setFont("DV", 7)
    c.setFillColor(GREY)
    c.drawString(12 * mm, 8 * mm, "Siyonah's Formula Sheet · Oxford Maths Victoria Years 7–10 · ★ = SEHS level (Yr 7–8), "
                 "grey = Yr 9–10 extension")
    c.drawRightString(A4[0] - 12 * mm, 8 * mm, f"Page {doc.page}")
    c.restoreState()


def build(out):
    W, Hh = A4
    m = 11 * mm
    gap = 6 * mm
    colw = (W - 2 * m - gap) / 2
    first_top = 32 * mm
    title_frame = Frame(m, Hh - m - 24 * mm, W - 2 * m, 24 * mm, id="title", leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)
    c1 = Frame(m, m + 6 * mm, colw, Hh - 2 * m - 6 * mm - first_top + 6 * mm, id="c1", leftPadding=0,
               rightPadding=0, topPadding=0, bottomPadding=0)
    c2 = Frame(m + colw + gap, m + 6 * mm, colw, Hh - 2 * m - 6 * mm - first_top + 6 * mm, id="c2",
               leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    d1 = Frame(m, m + 6 * mm, colw, Hh - 2 * m - 6 * mm, id="d1", leftPadding=0, rightPadding=0, topPadding=0,
               bottomPadding=0)
    d2 = Frame(m + colw + gap, m + 6 * mm, colw, Hh - 2 * m - 6 * mm, id="d2", leftPadding=0, rightPadding=0,
               topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(out, pagesize=A4, title="Siyonah's Formula Sheet (Oxford Maths Yr 7-10)",
                          author="Selective Brain")
    doc.addPageTemplates([PageTemplate(id="first", frames=[title_frame, c1, c2], onPage=on_page),
                          PageTemplate(id="rest", frames=[d1, d2], onPage=on_page)])
    story = [Paragraph("Siyonah's Formula Sheet", TITLE),
             Paragraph("Every formula and rule from Oxford Maths Victoria Years 7, 8, 9 and 10, grouped by topic. "
                       "<font color='#d6336c'><b>★ Y7/Y8</b></font> lines are SEHS level – know these by heart. "
                       "<font color='#6b6880'>Grey Y9/Y10 lines</font> are extension: read them, don't stress.", SUB),
             FrameBreak(), NextPageTemplate("rest")]
    for t, rows in TOPICS:
        story.append(topic_block(t, rows))
    story.append(watch_block())
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Sources: Oxford Maths Victoria Yr 7–10 contents (all chapters except Computational "
                           "thinking); vault Practice/Foundation_Maths_Test_Formulas.md and Formula_Reference.md; "
                           "watch-outs from Mistake_Tracker and Test_Analysis_2026-10-02. Built 8 Oct 2026.", SMALL))
    doc.build(story)


if __name__ == "__main__":
    build(sys.argv[1])
