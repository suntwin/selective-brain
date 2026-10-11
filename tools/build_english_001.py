"""English baseline pack (SEHS block 2 Reading + Verbal Reasoning, block 3 Writing).
Three drills: Verbal Baseline (20 MCQ), Reading Baseline (2 original passages x 6 MCQ), Writing Baseline
(creative + persuasive, 20 min each, as in the 40-minute exam block). All passages and questions are original.
Vocabulary questions reuse words from her vault vocabulary bank (wiki/VocabularyWords.md).
Skills follow ACER's descriptions: Reading = "access and retrieve information" and "integrate, interpret,
reflect on and evaluate"; Verbal Reasoning = "thinking using words, concepts and logic"; Writing = "convey ideas
in precise language with ideas organised coherently"."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sb.drillspec import validate  # noqa: E402
from sb.answers import q_seconds  # noqa: E402

VAULT = ROOT.parent / "Siyonah Selective Brain Prep" / "Practice" / "App_Drills"
ACER = "ACER SEHS skill description"
BANK = "wiki/VocabularyWords.md (her vocab bank)"


def mcq(Q, id, topic, stem, options, correct, explanation, technique, trap=None, source=ACER, difficulty=2,
        passage=None):
    assert correct in options, (id, correct)
    assert len(set(options)) == len(options), id
    q = {"id": id, "type": "mcq", "topic": topic, "difficulty": difficulty, "stem": stem, "options": options,
         "answer": options.index(correct), "explanation": explanation, "technique": technique, "trap": trap,
         "source": source, "shuffle": True}
    if passage:
        q["passage"] = passage
    Q.append(q)


def save(drill):
    errs = validate(drill)
    assert not errs, errs
    pace = drill["pace_seconds"]
    drill["minutes"] = round(sum(q_seconds(q, pace) for q in drill["questions"]) / 60)
    name = drill["id"] + ".json"
    txt = json.dumps(drill, indent=1, ensure_ascii=False)
    (ROOT / "drills" / name).write_text(txt, encoding="utf-8")
    if VAULT.is_dir():
        (VAULT / name).write_text(txt, encoding="utf-8")
    print("wrote", name, len(drill["questions"]), "questions,", drill["minutes"], "min")


# ===================================================================== VERBAL
V = []
VO, AN, CL, CO, LO = "Verbal_Vocabulary", "Verbal_Analogies", "Verbal_Classify", "Verbal_Codes", "Verbal_Logic"

mcq(V, "v1", VO, "Which word is closest in meaning to WARILY?", ["cautiously", "angrily", "lazily", "cheerfully"],
    "cautiously", "Warily means carefully, because you think something might be dangerous or tricky.",
    "Put the word in a sentence you know: 'The cat crept warily towards the dog.'", source=BANK)
mcq(V, "v2", VO, "Which word is most nearly OPPOSITE in meaning to PLENTIFUL?", ["scarce", "abundant", "colourful",
    "generous"], "scarce", "Plentiful means there is lots of something. Scarce means there is very little.",
    "Opposite questions: first find a synonym (plentiful = lots), then look for 'very little'.",
    trap="Abundant is a SYNONYM, not an opposite — read the capital letters in the question", source=BANK)
mcq(V, "v3", VO, "Choose the best word for the gap: Tom stared at the jigsaw in complete ______; none of the "
    "pieces seemed to fit anywhere.", ["bewilderment", "recognition", "permission", "insistence"], "bewilderment",
    "Bewilderment means being confused and puzzled, which fits 'none of the pieces seemed to fit'.",
    "Look for the clue in the rest of the sentence, then test each word in the gap.", source=BANK)
mcq(V, "v4", VO, "INTRICATE most nearly means:", ["complicated and full of small details", "very old and valuable",
    "easy to break", "brightly coloured"], "complicated and full of small details",
    "Something intricate has many small, detailed parts, like an intricate pattern on a carpet.",
    "Think of phrases you've heard the word in: 'an intricate design'.", source=BANK)
mcq(V, "v5", VO, "Which word can go in front of all three of these to make new words?   ___ball   ___print   ___step",
    ["foot", "hand", "snow", "base"], "foot",
    "football, footprint, footstep. Hand works for handball and handprint but not 'handstep'; snow works only for snowball.",
    "Test the option with ALL three words, not just the first one.",
    trap="Stopping after the first word that works (snowball, handball)", difficulty=2)

mcq(V, "v6", AN, "Feather is to bird as scale is to …", ["fish", "weight", "music", "mountain"], "fish",
    "A bird is covered in feathers; a fish is covered in scales.",
    "Make a sentence for the first pair ('A bird is covered in feathers'), then use the SAME sentence for the second.",
    trap="'weight' uses a different meaning of scale (bathroom scales)")
mcq(V, "v7", AN, "Author is to novel as composer is to …", ["symphony", "orchestra", "piano", "concert"], "symphony",
    "An author writes a novel; a composer writes a symphony.",
    "Sentence test: 'An author WRITES a novel. A composer WRITES a ___.'",
    trap="Orchestra and piano are linked to music but aren't what a composer writes")
mcq(V, "v8", AN, "Thermometer is to temperature as odometer is to …", ["distance", "speed", "time", "fuel"], "distance",
    "A thermometer measures temperature; an odometer (in a car) measures the distance travelled.",
    "Sentence test: 'A thermometer MEASURES temperature.'",
    trap="Speed is measured by a speedometer, not an odometer")
mcq(V, "v9", AN, "Reluctantly is to eagerly as warily is to …", ["boldly", "cautiously", "nervously", "silently"],
    "boldly", "Reluctantly and eagerly are opposites. The opposite of warily (cautiously) is boldly.",
    "First decide what kind of link it is: same meaning, opposite, part of, used for…",
    trap="Cautiously means the SAME as warily, but the pair is opposites", source=BANK, difficulty=3)

mcq(V, "v10", CL, "Which word is the odd one out?", ["shout", "whisper", "murmur", "mutter", "mumble"], "shout",
    "Whisper, murmur, mutter and mumble are all ways of speaking quietly. Shout is loud.",
    "Find what MOST of the words have in common, then spot the one that breaks it.")
mcq(V, "v11", CL, "Which word is the odd one out?", ["granite", "sapphire", "emerald", "ruby", "diamond"], "granite",
    "Sapphire, emerald, ruby and diamond are gemstones. Granite is an ordinary rock used for building.",
    "Name the group the others belong to.")
mcq(V, "v12", CL, "Which word does NOT belong with the others?", ["ignored", "pondered", "considered", "reflected",
    "contemplated"], "ignored",
    "Pondered, considered, reflected and contemplated all mean thought carefully about something. Ignored means "
    "paid no attention.", "Group the words by meaning.", source=BANK)


def shift(word, k):
    return "".join(chr((ord(c) - 65 + k) % 26 + 65) for c in word)


assert shift("CAT", 1) == "DBU"
mcq(V, "v13", CO, "In a code, CAT is written as DBU. How is DOG written in the same code?",
    [shift("DOG", 1), "CNF", "EPF", "DPH"], shift("DOG", 1),
    "Each letter moves one place forward in the alphabet: C→D, A→B, T→U. So D→E, O→P, G→H: EPH.",
    "Compare each letter with its code letter and count the jump. Check the rule works for every letter.",
    trap="Moving letters backwards (CNF)")
seq = [chr(ord("B") + 3 * i) for i in range(5)]
assert seq == list("BEHKN")
mcq(V, "v14", CO, "What comes next in this series?   B, E, H, K, ?", ["N", "M", "O", "L"], "N",
    "Each letter jumps forward 3 places: B (+3) E (+3) H (+3) K (+3) N.",
    "Write the alphabet position under each letter (B=2, E=5, H=8, K=11) and look at the gaps.",
    trap="Jumping 2 (M) after miscounting")
assert "PLANT"[::-1] == "TNALP" and "BREAD"[::-1] == "DAERB"
mcq(V, "v15", CO, "In a code, PLANT is written as TNALP. How is BREAD written in the same code?",
    ["DAERB", "DEARB", "BDAER", "ERDAB"], "DAERB",
    "TNALP is PLANT written backwards. BREAD backwards is DAERB.",
    "Look for simple rules first: reversed, shifted, or letters swapped.")
pairs = [chr(65 + i) + chr(90 - i) for i in range(4)]
assert pairs == ["AZ", "BY", "CX", "DW"]
mcq(V, "v16", CO, "What comes next?   AZ, BY, CX, ?", ["DW", "DV", "EW", "DX"], "DW",
    "The first letter goes forward through the alphabet (A, B, C, D) and the second goes backwards from Z "
    "(Z, Y, X, W).", "Treat each position in the pair as its own series.")

mcq(V, "v17", LO, "All marsupials carry their young in a pouch. A wombat is a marsupial. Which statement MUST be true?",
    ["A wombat carries its young in a pouch.", "Every animal with a pouch is a marsupial.",
     "Only wombats carry their young in pouches.", "Wombats are the largest marsupials."],
    "A wombat carries its young in a pouch.",
    "Wombats belong to the group 'marsupials', and everything in that group carries young in a pouch.",
    "Only use what the statements say. Don't turn 'All A are B' around into 'All B are A'.",
    trap="Turning the rule around (every animal with a pouch is a marsupial)")
order = ["Mia", "Jo", "Sam", "Ana"]      # tallest -> shortest
mcq(V, "v18", LO, "Mia is taller than Jo. Jo is taller than Sam. Ana is shorter than Sam. Who is the SECOND shortest?",
    ["Sam", "Jo", "Ana", "Mia"], order[-2],
    "Line them up from tallest: Mia, Jo, Sam, Ana. The shortest is Ana, so the second shortest is Sam.",
    "Draw a quick line from tallest to shortest and place each person as you read.",
    trap="Answering the shortest (Ana)")
days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
place = {"Lee": "Wed", "Ravi": "Thu", "Sophie": "Tue"}
left = [x for x in days if x not in place.values()]
place["Kim"] = next(x for x in left if x != "Mon")
place["Zara"] = next(x for x in left if x != place["Kim"])
assert place["Zara"] == "Mon"
mcq(V, "v19", LO, "Five friends have birthdays on different days from Monday to Friday this week. Lee's is on "
    "Wednesday. Ravi's is the day after Lee's. Sophie's is the day before Lee's. Kim's is not on Monday. The fifth "
    "friend is Zara. Whose birthday is on Monday?", ["Zara", "Kim", "Sophie", "Ravi"], "Zara",
    "Lee Wed, Ravi Thu, Sophie Tue. Monday and Friday are left for Kim and Zara. Kim isn't Monday, so Zara is Monday.",
    "Make a 5-box table (Mon–Fri) and fill in the certain facts first.", difficulty=3)
mcq(V, "v20", LO, "Some pupils in the choir also play in the school band. Everyone in the band plays an instrument. "
    "Which statement MUST be true?",
    ["Some pupils in the choir play an instrument.", "All pupils in the choir play an instrument.",
     "Everyone who plays an instrument is in the band.", "No pupil in the choir plays an instrument."],
    "Some pupils in the choir play an instrument.",
    "The choir pupils who are in the band must play an instrument, so at least SOME choir pupils do.",
    "Draw two overlapping circles (choir, band). 'Some' means only the overlap is certain.",
    trap="Jumping from 'some' to 'all'", difficulty=3)

save({"id": "2026-10-08_verbal_baseline", "title": "English 1 · Verbal Baseline 🧠", "drill_date": "2026-10-08",
      "subject": "Verbal", "pace_seconds": 60,
      "focus": ["Word meanings", "Analogies", "Odd one out", "Codes & series", "Logic"],
      "source_note": "Baseline to find her verbal-reasoning gaps. Original questions in ACER's 'words, concepts and "
                     "logic' style; vocabulary items reuse her vault vocab bank.", "questions": V})

# ===================================================================== READING
PASSAGES = {
 "lantern": {"title": "The Lantern Keeper", "kind": "Story", "text":
  "Every evening at six, Mr Okafor wheeled his barrow of lanterns down Wattle Lane, and every evening Ruby "
  "watched him from the front step, pretending to read.\n\n"
  "He was not a real lamplighter. The lane had had electric streetlights for longer than Ruby had been alive. "
  "But in March a storm had wrestled with the lane and won, and three of the poles still leaned like tired "
  "giraffes, their bulbs dark. Until the repair crew came, Mr Okafor had appointed himself the keeper of the night.\n\n"
  "'Aren't you going to help him?' her brother Tom asked on the fourth evening, dropping his schoolbag on her book.\n\n"
  "'Help with what?' Ruby said, although she knew.\n\n"
  "She had not spoken to Mr Okafor since the business with the cricket ball and his front window. He had not "
  "shouted. That was the worst part. He had simply picked up the glass, piece by piece, while she stood on the "
  "footpath with her apology stuck somewhere behind her teeth.\n\n"
  "Now she watched him stop at the first dark pole. He set a lantern on the low brick wall beneath it, struck a "
  "match, and cupped the flame against the wind until the wick caught. A soft circle of gold spread across the "
  "footpath. He moved on to the second pole, then the third, his knees cracking each time he bent.\n\n"
  "On the fifth evening it rained. Ruby saw him come out with his barrow and an umbrella that kept trying to turn "
  "itself inside out. At the second pole the wind won. The umbrella flew, the match went out, and then the next "
  "one did too.\n\n"
  "Ruby was across the road before she had decided to go. Without a word she held her raincoat open like a tent, "
  "and in the dry space beneath it the third match caught.\n\n"
  "Mr Okafor looked at her for a long moment. Rain dripped from his eyebrows.\n\n"
  "'Steady hands,' he said at last. 'Better than mine. Same time tomorrow?'\n\n"
  "Ruby nodded. The apology was still stuck, but it no longer felt quite so heavy. Tomorrow, she thought, she "
  "might be able to say it.",
  "source": "Original story written for Selective Brain"},
 "shade": {"title": "Shade Makers", "kind": "Persuasive article", "text":
  "On a hot summer afternoon, the footpath outside a busy shopping strip can become hot enough to burn bare feet. "
  "Step a few metres into the shade of a large plane tree and the ground can be many degrees cooler. That "
  "difference is not just pleasant. For older people, babies and anyone who works outdoors, it can be the "
  "difference between an uncomfortable day and a dangerous one.\n\n"
  "Scientists call this the urban heat island effect. Roads, roofs and car parks soak up the sun's energy during "
  "the day and release it slowly at night, so cities stay hotter than the countryside around them. Suburbs with "
  "few trees can be noticeably warmer on summer nights than leafy suburbs only a few kilometres away.\n\n"
  "Trees fight back in two ways. Their canopies block sunlight before it reaches the ground, and their leaves "
  "release water vapour, which cools the air in much the same way that sweat cools your skin. A large, healthy "
  "tree quietly does cooling work that would otherwise need air-conditioners, without the power bill.\n\n"
  "Yet many suburbs are losing trees faster than they are planting them. Old trees are removed for new "
  "driveways, wider roads and bigger houses, and the young trees planted in their place can take twenty years "
  "to give real shade. Critics point out that trees drop leaves into gutters, crack footpaths with their roots "
  "and cost money to water and prune. These are real problems. But they are small compared with the cost of "
  "people falling ill in heatwaves, or of a suburb that becomes too hot to walk in.\n\n"
  "The solution is not complicated. Councils should set a target for how much of each suburb is shaded by trees, "
  "protect large old trees wherever possible, and choose species that suit a hotter, drier future. Residents can "
  "help too, by planting trees in their own gardens and watering young street trees through their first summers.\n\n"
  "We plant trees for the people who will be here in twenty years' time. The best time to start was twenty years "
  "ago. The second-best time is now.",
  "source": "Original article written for Selective Brain"},
}
R = []
RE, RI, RV, RP = "Reading_Retrieve", "Reading_Infer", "Reading_Vocab", "Reading_Purpose"
mcq(R, "r1", RE, "Why were three of the streetlights in Wattle Lane not working?",
    ["A storm had damaged the poles.", "The council had turned them off to save money.",
     "Ruby's cricket ball had broken them.", "The repair crew was replacing the bulbs."],
    "A storm had damaged the poles.",
    "Paragraph 2: 'in March a storm had wrestled with the lane and won, and three of the poles still leaned…'",
    "Retrieve questions: find the exact sentence in the passage before you choose.",
    trap="The cricket ball broke Mr Okafor's WINDOW, not the lights", passage="lantern")
mcq(R, "r2", RI, "Why had Ruby not spoken to Mr Okafor?",
    ["She felt guilty and embarrassed about breaking his window.", "He had shouted at her.",
     "She was too busy reading.", "Her brother had told her to stay away."],
    "She felt guilty and embarrassed about breaking his window.",
    "The 'business with the cricket ball and his front window', and her apology being 'stuck', show she felt bad. "
    "The story says he did NOT shout.", "Inference: the answer isn't written word for word, but clues point to it.",
    trap="'He had not shouted' — read the small words", passage="lantern", difficulty=2)
mcq(R, "r3", RV, "Mr Okafor 'had appointed himself the keeper of the night'. This means he had …",
    ["chosen to take on the job without being asked", "been paid by the council to do it",
     "been elected by his neighbours", "been ordered to do it by the repair crew"],
    "chosen to take on the job without being asked",
    "To appoint HIMSELF means he gave himself the job. Nobody else asked him.",
    "Words in context: replace the phrase with each option and see which keeps the meaning.", passage="lantern")
mcq(R, "r4", RI, "The words 'her apology stuck somewhere behind her teeth' suggest that Ruby …",
    ["wanted to say sorry but couldn't get the words out", "had something stuck in her teeth",
     "didn't think she needed to apologise", "had already apologised quietly"],
    "wanted to say sorry but couldn't get the words out",
    "This is figurative language: the apology was ready but she was too embarrassed to say it.",
    "Figurative language: ask what feeling or idea the picture is showing, not what it literally says.",
    trap="Taking the phrase literally", passage="lantern")
mcq(R, "r5", RI, "What does Mr Okafor's reply, 'Steady hands … Same time tomorrow?', show about him?",
    ["He accepts her help and gives her a way to make things right.", "He is still angry about the window.",
     "He wants Ruby to pay for the window.", "He doesn't recognise Ruby."],
    "He accepts her help and gives her a way to make things right.",
    "He praises her and invites her back, which opens the door to repairing their relationship.",
    "Character questions: what do their words and actions tell you about how they feel?",
    passage="lantern", difficulty=3)
mcq(R, "r6", RP, "Which sentence best describes the main message of the story?",
    ["Small acts of kindness can begin to mend a damaged relationship.",
     "Electric lights are better than lanterns.", "Children shouldn't play cricket near houses.",
     "Councils are slow to repair storm damage."],
    "Small acts of kindness can begin to mend a damaged relationship.",
    "The story is about Ruby helping Mr Okafor, and the apology feeling 'not quite so heavy' afterwards.",
    "Main message: which option is true of the WHOLE story, not just one detail?",
    trap="Picking a true detail (slow repairs) instead of the big idea", passage="lantern", difficulty=3)

mcq(R, "r7", RE, "According to the article, how do the leaves of trees help to cool the air?",
    ["They release water vapour.", "They reflect heat back into space.", "They store heat until night-time.",
     "They stop the wind from blowing."], "They release water vapour.",
    "Paragraph 3: 'their leaves release water vapour, which cools the air in much the same way that sweat cools "
    "your skin.'", "Find the sentence that answers the question, then match it to an option.", passage="shade")
mcq(R, "r8", RV, "In paragraph 3, the word 'canopies' most likely means …",
    ["the leafy tops of trees spread overhead", "the roots of trees under the ground",
     "plastic covers over a footpath", "the trunks of very old trees"],
    "the leafy tops of trees spread overhead",
    "The canopies 'block sunlight before it reaches the ground', so they must be the spreading tops of the trees.",
    "Use what the word DOES in the sentence to work out what it is.", passage="shade")
mcq(R, "r9", RE, "Why do some suburbs stay warmer at night, according to the article?",
    ["Hard surfaces release the day's heat slowly and there are few trees.",
     "They are closer to the sun.", "People run their air-conditioners all night.",
     "The countryside sends warm wind into them."],
    "Hard surfaces release the day's heat slowly and there are few trees.",
    "Paragraph 2: roads, roofs and car parks 'release it slowly at night', and suburbs 'with few trees' are warmer.",
    "Retrieve: combine two nearby sentences if the answer needs both.", passage="shade", difficulty=2)
mcq(R, "r10", RP, "Why does the writer mention that trees 'crack footpaths with their roots'?",
    ["To admit an argument against trees before showing it matters less.",
     "To prove that trees are dangerous.", "To explain how roots find water.",
     "To persuade councils to remove old trees."],
    "To admit an argument against trees before showing it matters less.",
    "The writer says 'These are real problems. But they are small compared with…' — a counter-argument, then a reply.",
    "Persuasive writers often mention the other side and then answer it. Look for 'But…' straight after.",
    trap="Thinking the writer agrees trees should go", passage="shade", difficulty=3)
mcq(R, "r11", RP, "What is the main purpose of the article?",
    ["To persuade readers that suburbs need more trees and to suggest what to do.",
     "To explain how air-conditioners work.", "To describe the history of plane trees.",
     "To warn people not to go outside in summer."],
    "To persuade readers that suburbs need more trees and to suggest what to do.",
    "It gives reasons, answers objections and says what 'councils should' and 'residents can' do — that's persuasion.",
    "Purpose: inform, persuade, entertain or instruct? Words like 'should' are clues to persuasion.",
    passage="shade")
mcq(R, "r12", RI, "The last sentence, 'The second-best time is now', suggests that …",
    ["we should start planting trees straight away, even though it is late", "planting trees is a waste of time",
     "trees planted now will give shade next summer", "twenty years ago was a bad time to plant trees"],
    "we should start planting trees straight away, even though it is late",
    "The best time has passed (twenty years ago), so the next best choice is to begin now.",
    "Endings of persuasive texts are often a call to action. What does the writer want readers to DO?",
    trap="'next summer' — the article says young trees take about twenty years to give real shade",
    passage="shade", difficulty=3)

save({"id": "2026-10-08_reading_baseline", "title": "English 2 · Reading Baseline 📖", "drill_date": "2026-10-08",
      "subject": "Reading", "pace_seconds": 110, "passages": PASSAGES,
      "focus": ["Find the information", "Read between the lines", "Words in context", "Author's purpose"],
      "source_note": "Baseline to find her reading gaps. Two original passages (story, persuasive article), 6 questions "
                     "each, covering ACER's retrieve / interpret / reflect-and-evaluate skills.", "questions": R})

# ===================================================================== WRITING
W = []
CHECK = ["I spent 2–3 minutes planning first", "I used paragraphs", "I used at least three precise, interesting words",
         "I varied how my sentences start", "I checked spelling and punctuation at the end"]
W.append({"id": "w1", "type": "writing", "topic": "Writing_Creative", "difficulty": 3, "seconds": 1200,
          "stem": "Write a story that begins with this sentence:\n\n"
                  "“The door had been locked for as long as anyone could remember, until this morning.”",
          "tips": ["Plan: who is the main character, what's the problem, how does it end?",
                   "Show feelings through actions ('her hands shook') instead of naming them ('she was scared').",
                   "One strong setting detail beats five weak ones.",
                   "Finish the story: a rushed or missing ending loses marks."],
          "checklist": CHECK + ["My story has a clear beginning, problem and ending"],
          "technique": "Plan, write, check: 3 min / 15 min / 2 min.",
          "source": ACER + ": Writing, two tasks in 40 minutes"})
W.append({"id": "w2", "type": "writing", "topic": "Writing_Persuasive", "difficulty": 3, "seconds": 1200,
          "stem": "Some people think students should be allowed to use their mobile phones at school during "
                  "lunchtime. Others think phones should stay switched off all day.\n\n"
                  "Write a persuasive piece giving YOUR opinion. Try to convince the reader.",
          "tips": ["Say your opinion clearly in the first paragraph.",
                   "Give 2–3 reasons, each in its own paragraph, with an example.",
                   "Answer one argument from the other side ('Some people say… however…').",
                   "End with a strong conclusion that restates your view."],
          "checklist": CHECK + ["I answered one argument from the other side"],
          "technique": "Opinion, reasons with examples, counter-argument, conclusion.",
          "source": ACER + ": Writing, two tasks in 40 minutes"})

save({"id": "2026-10-08_writing_baseline", "title": "English 3 · Writing Baseline ✍️", "drill_date": "2026-10-08",
      "subject": "Writing", "pace_seconds": 90,
      "focus": ["Creative story", "Persuasive piece", "20 minutes each"],
      "source_note": "Baseline writing sample: one creative and one persuasive task, 20 minutes each like the "
                     "40-minute exam block. Marked by Claude with wiki/English/Writing_Rubric.md after export.",
      "questions": W})
