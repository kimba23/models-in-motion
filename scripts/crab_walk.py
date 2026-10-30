"""CRAB WALK - a take walked three frames forward and one back.

Nothing is blended: every frame on screen is a real frame of a take.
The only thing invented is the ORDER.
SALAD: the steps back come from OTHER takes - the crab steps back into a
moment that never happened. Works best on water, smoke, crowds, leaves.

Put this file in a folder of takes. Change the settings below, save,
double-click RUN.bat.
"""
from pathlib import Path
import random
import cv2

# ---- settings ---------------------------------------------------------------
FORWARD = 3              # frames forward each time
BACK = 1                 # frames back each time (smaller than FORWARD)
TAKE = 0                 # which take walks: 0 = the first one in the folder
SALAD = "no"             # "no"    = only that take
                         # "back"  = every step back comes from another take
                         # "every" = a different take on every frame
SEED = 0                 # another number = other takes chosen for the salad
# -----------------------------------------------------------------------------

HERE = Path(__file__).parent
OUT = HERE / Path(__file__).stem
OUT.mkdir(exist_ok=True)


def read_frames(path):
    video = cv2.VideoCapture(str(path))
    fps = video.get(cv2.CAP_PROP_FPS) or 24
    frames = []
    while True:
        ok, frame = video.read()
        if not ok:
            return frames, fps
        frames.append(frame)


SALAD = {"yes": "back", "y": "back", "true": "back", "": "no", "false": "no"}.get(str(SALAD).lower(), str(SALAD).lower())
if SALAD not in ("no", "back", "every"):
    raise SystemExit(f'SALAD must be "no", "back" or "every" (you wrote "{SALAD}")')

takes = sorted(HERE.glob("*.mp4"))
if SALAD == "no":
    takes = [takes[TAKE]]
else:
    takes.insert(0, takes.pop(TAKE))            # the walking take first, the others for the salad
clips = []
for t in takes:
    frames, fps = read_frames(t)
    clips.append(frames)
n = min(len(c) for c in clips)
print(f"{takes[0].name} walks, {n} frames, salad: {SALAD} ({len(takes) - 1} other takes)")

# the walk: (frame number, which take) in the order they will be shown
rnd = random.Random(SEED)


def pick(stepping_back):
    if SALAD == "every" or (SALAD == "back" and stepping_back):
        return rnd.randrange(1, len(clips)) if len(clips) > 1 else 0
    return 0


f = 0
order = [(f, 0)]
while True:
    for _ in range(FORWARD):
        f += 1
        if f >= n:
            break
        order.append((f, pick(False)))
    if f >= n:
        break
    for _ in range(BACK):
        f -= 1
        order.append((f, pick(True)))

name = f"forward {FORWARD} back {BACK}" + ("" if SALAD == "no" else f" salad {SALAD}")
h, w = clips[0][0].shape[:2]
writer = cv2.VideoWriter(str(OUT / f"{name}.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
for i, t in order:
    writer.write(clips[t][i])
writer.release()

# where every frame came from (RUN rebuilds the sound from this list: the steps back play backwards)
(OUT / f"{name}.frames").write_text("".join(f"{i}\t{takes[t].name}\n" for i, t in order), encoding="utf-8")

(OUT / f"{name}.txt").write_text(
    f"FORWARD {FORWARD}  BACK {BACK}  SALAD {SALAD}  SEED {SEED}  walking take {takes[0].name}\n"
    f"{n} frames became {len(order)}\n\nframe  take\n" + "\n".join(f"{i:5d}  {takes[t].name}" for i, t in order),
    encoding="utf-8")
print(f"{n} frames became {len(order)} -> {OUT.name}\\{name}.mp4")
