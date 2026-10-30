"""BREATHING CUT - many takes of one shot, cut where the picture moves.

Put this file in a folder of takes (same shot, same size, different seeds).
The first take plays. Where the picture moves a lot, the cuts come close
together; where it is still, the edit rests. Result: a new folder named
after this file.

Change the settings below, save, double-click RUN.bat.
"""
from pathlib import Path
import random
import numpy as np
import cv2

# ---- settings ---------------------------------------------------------------
MAX_CUTS_PER_SECOND = 4.0    # cuts per second where the picture moves the most
MIN_CUTS_PER_SECOND = 0.25   # cuts per second where it is still (0 = full rest)
SMOOTH = 12                  # frames averaged into the motion curve - higher = slower breath
LENGTH = 1                   # how many frames each cut lasts
WINDOW = (0, 99)             # only cut between these seconds - the dose
SEED = 0                     # another number = other takes chosen
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


def motion_curve(frames):
    """How much the picture changes from one frame to the next, from 0 (still) to 1 (moving most)."""
    gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames]
    change = np.zeros(len(frames))
    for f in range(1, len(frames)):
        change[f] = np.abs(gray[f] - gray[f - 1]).mean()
    # average over neighbouring frames so the curve breathes instead of jittering
    change = np.convolve(change, np.ones(SMOOTH) / SMOOTH, mode="same")
    # the 95th percentile is "a strong movement": anything above it counts as 1
    top = np.percentile(change, 95)
    if top <= 0:
        return np.zeros(len(frames))
    return np.clip(change / top, 0, 1)


takes = sorted(HERE.glob("*.mp4"))
clips = []
fps = None
for t in takes:
    frames, take_fps = read_frames(t)
    clips.append(frames)
    if fps is None:
        fps = take_fps  # the base take sets the speed
n = min(len(c) for c in clips)
print(f"{len(takes)} takes, {n} frames each, base = {takes[0].name}")

# how much the base take moves, frame by frame
motion = motion_curve(clips[0][:n])
print(f"motion curve ready: strongest at frame {int(np.argmax(motion))}")

# which take every frame comes from: 0 = the base take
source = [0] * n
rnd = random.Random(SEED)
credit = 0.0  # builds up while the picture moves; a cut is paid out at 1
cuts = 0
for f in range(n):
    in_window = WINDOW[0] * fps <= f < WINDOW[1] * fps
    if not in_window:
        credit = 0.0
        continue
    # more movement = more cuts per second
    rate = MIN_CUTS_PER_SECOND + (MAX_CUTS_PER_SECOND - MIN_CUTS_PER_SECOND) * motion[f]
    credit += rate / fps
    if credit >= 1:
        credit -= 1
        other = rnd.randrange(1, len(clips))
        for g in range(f, min(f + LENGTH, n)):
            source[g] = other
        cuts += 1

name = f"breath {MIN_CUTS_PER_SECOND}-{MAX_CUTS_PER_SECOND} smooth {SMOOTH} length {LENGTH}"
h, w = clips[0][0].shape[:2]
writer = cv2.VideoWriter(str(OUT / f"{name}.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
for f in range(n):
    writer.write(clips[source[f]][f])
writer.release()

# where every frame came from (RUN rebuilds the sound from this list)
(OUT / f"{name}.frames").write_text("".join(f"{f}\t{takes[source[f]].name}\n" for f in range(n)), encoding="utf-8")

# the recipe, next to the video, so anyone can see how it was made
changed = sum(1 for s in source if s)
lines = [f"MIN {MIN_CUTS_PER_SECOND}  MAX {MAX_CUTS_PER_SECOND}  SMOOTH {SMOOTH}  LENGTH {LENGTH}  WINDOW {WINDOW}  SEED {SEED}",
         f"{cuts} cuts, {changed} of {n} frames from other takes", "", "frame  take"]
lines += [f"{f:5d}  {takes[s].name}" for f, s in enumerate(source) if s]
(OUT / f"{name}.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"{cuts} cuts, {changed} of {n} frames from other takes -> {OUT.name}\\{name}.mp4")
