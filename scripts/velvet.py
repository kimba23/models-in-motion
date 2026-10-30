"""VELVET - the opposite of cutting. Stack the takes on top of each other.

Every frame is the average of the same frame in all the takes. Where the takes
agree, the picture stays sharp; where they disagree, it goes soft and ghosts.
The difference between the takes becomes the picture.

Put this file in a folder of takes. Change the settings below, save,
double-click RUN.bat.
"""
from pathlib import Path
import cv2
import numpy as np

# ---- settings ---------------------------------------------------------------
MODE = "mean"          # mean    all takes averaged: soft, ghosting
                       # median  the middle value: what most takes agree on, sharp
                       # ramp    starts as one take, ends as the average of all
                       # trail   the average, with a smear of the frames before
                       # breathe the average; on every x of RHYTHM it falls to ONE take
RHYTHM = "x..x..x."    # for breathe: x = fall to one take, . = rest
STEP = 7               # for breathe: frames per step of the rhythm
RELEASE = 14           # for breathe: frames to swell back to all the takes
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
print(f"{len(takes)} takes, {n} frames each, mode {MODE}")

# how many takes are in the stack at each frame (1 = only the first take, all = every take)
depth = [len(clips)] * n
if MODE == "ramp":
    depth = [1 + round((len(clips) - 1) * f / (n - 1)) for f in range(n)]
if MODE == "breathe":
    for step in range(n // STEP + 1):
        if RHYTHM[step % len(RHYTHM)] == "x":
            hit = step * STEP
            for k in range(RELEASE):                    # from one take back up to all of them
                if hit + k < n:
                    depth[hit + k] = min(depth[hit + k], 1 + round((len(clips) - 1) * k / RELEASE))

name = MODE if MODE != "breathe" else f"breathe {RHYTHM} step {STEP}"
h, w = clips[0][0].shape[:2]
writer = cv2.VideoWriter(str(OUT / f"{name}.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
trail = None
for f in range(n):
    stack = np.stack([c[f] for c in clips[:depth[f]]]).astype(np.float32)
    img = np.median(stack, axis=0) if MODE == "median" else stack.mean(axis=0)
    if MODE == "trail":
        trail = img if trail is None else trail * 0.72 + img * 0.28
        img = trail
    writer.write(img.astype(np.uint8))
writer.release()

(OUT / f"{name}.txt").write_text(
    f"MODE {MODE}  RHYTHM {RHYTHM}  STEP {STEP}  RELEASE {RELEASE}\n"
    f"{len(takes)} takes stacked, on average {sum(depth) / n:.1f} at a time",
    encoding="utf-8")
print(f"-> {OUT.name}\\{name}.mp4")
