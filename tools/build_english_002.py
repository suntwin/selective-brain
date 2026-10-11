"""Writing 2 'Sunday Writing': two 20-minute tasks (the 40-minute SEHS Writing block): a narrative built on a
choice/dilemma, and a persuasive piece. Marked by Claude after export with wiki/English/Writing_Rubric.md.
Original prompts."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sb.drillspec import validate  # noqa: E402
from sb.answers import q_seconds  # noqa: E402

VAULT = ROOT.parent / "Siyonah Selective Brain Prep" / "Practice" / "App_Drills"
SRC = "ACER SEHS Writing block: two tasks in 40 minutes; marked with wiki/English/Writing_Rubric.md"
CHECK = ["I spent 2–3 minutes planning first", "I used paragraphs", "I used at least three precise, interesting words",
         "I varied how my sentences start", "I checked spelling and punctuation at the end"]

W = [
    {"id": "w1", "type": "writing", "topic": "Writing_Creative", "difficulty": 3, "seconds": 1200,
     "stem": "Write a story in which a character finds something that does NOT belong to them.\n\n"
             "What is it? What do they decide to do, and what happens because of that choice?",
     "tips": ["Start in the middle of the moment they find it, not with 'One day…'.",
              "The heart of the story is the CHOICE: show them hesitate (hands, breath, thoughts).",
              "Use one or two lines of dialogue, with speech marks and a new line for each speaker.",
              "End by showing how the choice changed something, even something small."],
     "checklist": CHECK + ["My character makes a clear choice, and the ending shows what it led to"],
     "technique": "Plan, write, check: 3 min / 15 min / 2 min.", "source": SRC},
    {"id": "w2", "type": "writing", "topic": "Writing_Persuasive", "difficulty": 3, "seconds": 1200,
     "stem": "“Every student in Years 7 and 8 should learn to cook at school.”\n\n"
             "Do you agree or disagree? Write a persuasive piece to convince your principal.",
     "tips": ["Decide your side in the first minute and say it clearly in your opening paragraph.",
              "Give 2–3 reasons, each in its own paragraph, with a real example (a meal, a skill, a cost).",
              "Answer one argument from the other side: 'Some people say… However…'.",
              "You're writing to the principal: be polite and confident, not chatty. End with a strong last line."],
     "checklist": CHECK + ["I answered one argument from the other side", "I wrote for my audience (the principal)"],
     "technique": "Opinion → reasons with examples → counter-argument → conclusion.", "source": SRC},
]

drill = {"id": "2026-10-11_sunday_writing", "title": "Writing 2 · Sunday Writing ✍️", "drill_date": "2026-10-11",
         "subject": "Writing", "pace_seconds": 90,
         "focus": ["Story with a choice", "Persuade the principal", "20 minutes each"],
         "source_note": "Two 20-minute tasks like the 40-minute exam block. Marked by Claude with "
                        "wiki/English/Writing_Rubric.md after export.",
         "questions": W}
errs = validate(drill)
assert not errs, errs
drill["minutes"] = round(sum(q_seconds(q, 90) for q in W) / 60)
name = drill["id"] + ".json"
txt = json.dumps(drill, indent=1, ensure_ascii=False)
(ROOT / "drills" / name).write_text(txt, encoding="utf-8")
if VAULT.is_dir():
    (VAULT / name).write_text(txt, encoding="utf-8")
print("wrote", name, len(W), "tasks,", drill["minutes"], "min")
