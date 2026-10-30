"""PULSE CUT - many takes of one shot, cut on a rhythm.

Put this file in a folder of takes (same shot, same size, different seeds).
The first take plays. On every hit of the rhythm, a few frames come from
another take instead. Result: a new folder named after this file.

Change the settings below, save, double-click RUN.bat.
"""
from pathlib import Path
import random
import cv2

# ---- settings ---------------------------------------------------------------
RHYTHM = "x..x..x."      # x = cut, . = rest. "x..x..x." is the tresillo (3-3-2)
STEP = 6                 # frames per step (24 fps: 6 frames = a quarter second)
LENGTH = 1               # how many frames each cut lasts
WINDOW = (0, 99)         # only cut between these seconds - the dose
SEED = 0                 # another number = other takes chosen
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


takes = sorted(HERE.glob("*.mp4"))
clips = []
for t in takes:
    frames, fps = read_frames(t)
    clips.append(frames)
n = min(len(c) for c in clips)
print(f"{len(takes)} takes, {n} frames each, base = {takes[0].name}")

# which take every frame comes from: 0 = the base take
source = [0] * n
rnd = random.Random(SEED)
for step in range(n // STEP + 1):
    start = step * STEP
    in_window = WINDOW[0] * fps <= start < WINDOW[1] * fps
    if RHYTHM[step % len(RHYTHM)] == "x" and in_window:
        other = rnd.randrange(1, len(clips))
        for f in range(start, min(start + LENGTH, n)):
            source[f] = other

name = f"rhythm {RHYTHM} step {STEP} length {LENGTH}"
h, w = clips[0][0].shape[:2]
writer = cv2.VideoWriter(str(OUT / f"{name}.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
for f in range(n):
    writer.write(clips[source[f]][f])
writer.release()

# where every frame came from (RUN rebuilds the sound from this list)
(OUT / f"{name}.frames").write_text("".join(f"{f}\t{takes[source[f]].name}\n" for f in range(n)), encoding="utf-8")

# the recipe, next to the video, so anyone can see how it was made
changed = sum(1 for s in source if s)
lines = [f"RHYTHM {RHYTHM}  STEP {STEP}  LENGTH {LENGTH}  WINDOW {WINDOW}  SEED {SEED}",
         f"{changed} of {n} frames from other takes", "", "frame  take"]
lines += [f"{f:5d}  {takes[s].name}" for f, s in enumerate(source) if s]
(OUT / f"{name}.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"{changed} of {n} frames from other takes -> {OUT.name}\\{name}.mp4")
