import random

JOKES = [
    "And then this happened.",
    "Plot twist.",
    "Me, when I see the tutorial said 'easy'.",
    "At this point I stopped asking questions.",
    "Meanwhile, nothing makes sense.",
    "The tension is unreal.",
    "Subscribe and hit the bell (please).",
    "We don't talk about this part.",
    "Peak cinema.",
    "I have no idea what's going on either.",
    "Chapter 3: Regret.",
    "Somehow still going.",
    "This is fine.",
    "Wait for it...",
    "And that, kids, is how I met my mother.",
    "Nobody asked, but here we are.",
    "The algorithm blessed us with this.",
    "Skip to 0:00 for the real ending.",
    "Look at this absolute unit.",
    "Emotional damage.",
]


def random_caption(rng: random.Random | None = None, avoid: str = "") -> str:
    rng = rng or random.Random()
    choices = [j for j in JOKES if j != avoid]
    return rng.choice(choices)
