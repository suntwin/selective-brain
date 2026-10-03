"""Marking logic shared by the drill player, review, notebook and vault export.

Question types
  mcq      options + answer (0-based index)
  numeric  answer (+ tolerance, unit)
  word     multi-part word problem: parts=[{label, prompt, answer | accept, unit, tolerance}], solution=[steps]
"""
from __future__ import annotations

import json
import re
from fractions import Fraction

_NUM = re.compile(r"-?\d+(?:\.\d+)?(?:\s+\d+/\d+|/\d+(?:\.\d+)?)?")


def parse_num(s) -> float | None:
    """'1,250' → 1250, '$3.75' → 3.75, '45 L' → 45, '3/4' → 0.75, '2 1/4' → 2.25, '-7' → -7."""
    if s is None:
        return None
    t = str(s).replace(",", "").replace("$", "").replace("−", "-").strip()
    m = _NUM.search(t)
    if not m:
        return None
    tok = m.group(0)
    try:
        if " " in tok:                       # mixed number
            whole, frac = tok.split()
            w = float(whole)
            f = float(Fraction(frac))
            return w - f if w < 0 else w + f
        if "/" in tok:
            return float(Fraction(tok))
        return float(tok)
    except (ValueError, ZeroDivisionError):
        return None


def _norm(s) -> str:
    return re.sub(r"\s+", "", str(s or "")).lower().replace("−", "-")


def part_ok(part: dict, given) -> bool:
    if given in (None, ""):
        return False
    if part.get("accept"):                   # text answers such as ratios "3:5" or times "2:30pm"
        return _norm(given) in {_norm(a) for a in part["accept"]}
    v = parse_num(given)
    return v is not None and abs(v - float(part["answer"])) <= float(part.get("tolerance", 0.001))


def part_answer_text(part: dict) -> str:
    if part.get("display"):
        return str(part["display"])
    if part.get("accept"):
        return str(part["accept"][0])
    a = part["answer"]
    a = int(a) if float(a).is_integer() else a
    if part.get("unit") == "$":
        return f"${a}"
    return f'{a} {part.get("unit", "")}'.strip()


def word_given(chosen) -> dict:
    if isinstance(chosen, dict):
        return chosen
    try:
        v = json.loads(chosen) if chosen else {}
        return v if isinstance(v, dict) else {}
    except (TypeError, ValueError):
        return {}


def word_results(q: dict, chosen) -> list[dict]:
    given = word_given(chosen)
    out = []
    for p in q["parts"]:
        g = given.get(p["label"], "")
        out.append({"label": p["label"], "prompt": p.get("prompt", ""), "given": g,
                    "correct": part_answer_text(p), "ok": part_ok(p, g), "unit": p.get("unit", "")})
    return out


def is_correct(q: dict, chosen) -> bool:
    t = q.get("type", "mcq")
    if t == "word":
        return all(r["ok"] for r in word_results(q, chosen))
    if t == "numeric":
        return part_ok(q, chosen)
    try:
        return int(chosen) == int(q["answer"])
    except (TypeError, ValueError):
        return False


def answer_text(q: dict, chosen) -> str:
    if chosen in (None, "", "None"):
        return "—"
    t = q.get("type", "mcq")
    if t == "word":
        return "; ".join(f'({r["label"]}) {r["given"] or "—"}' for r in word_results(q, chosen))
    if t == "numeric":
        return f'{chosen} {q.get("unit", "")}'.strip()
    try:
        return str(q["options"][int(chosen)])
    except (ValueError, IndexError, KeyError, TypeError):
        return str(chosen)


def correct_text(q: dict) -> str:
    t = q.get("type", "mcq")
    if t == "word":
        return "; ".join(f'({p["label"]}) {part_answer_text(p)}' for p in q["parts"])
    if t == "numeric":
        return part_answer_text(q)
    return str(q["options"][int(q["answer"])])


def q_seconds(q: dict, pace: int) -> int:
    """Time budget for one question: word problems carry their own 'seconds'."""
    if q.get("seconds"):
        return int(q["seconds"])
    if q.get("type") == "word":
        return int(pace) * max(2, len(q.get("parts", [])))
    return int(pace)
