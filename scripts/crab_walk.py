"""CRAB WALK - one take, walked three frames forward and one back.

Nothing is blended and nothing is swapped: every frame on screen is a real
frame of the take. The only thing invented is the ORDER.
Works best on things without a clear subject: water, smoke, crowds, leaves.

Put this file in a folder of takes. It walks the first take.
Change the settings below, save, double-click RUN.bat.
"""
from pathlib import Path
import cv2

# ---- settings ---------------------------------------------------------------
FORWARD = 3              # frames forward each time
BACK = 1                 # frames back each time (smaller than FORWARD)
TAKE = 0                 # which take walks: 0 = the first one in the folder
# -----------------------------------------------------------------------------

HERE = Path(__file__).parent
OUT = HERE / Path(__file__).stem
OUT.mkdir(exist_ok=True)

take = sorted(HERE.glob("*.mp4"))[TAKE]
video = cv2.VideoCapture(str(take))
fps = video.get(cv2.CAP_PROP_FPS) or 24
frames = []
while True:
    ok, frame = video.read()
    if not ok:
        break
    frames.append(frame)
print(f"{take.name}: {len(frames)} frames")

# the walk: a list of frame numbers, the order they will be shown in
f = 0
order = [f]
while True:
    for _ in range(FORWARD):
        f += 1
        if f >= len(frames):
            break
        order.append(f)
    if f >= len(frames):
        break
    for _ in range(BACK):
        f -= 1
        order.append(f)

name = f"forward {FORWARD} back {BACK}"
h, w = frames[0].shape[:2]
writer = cv2.VideoWriter(str(OUT / f"{name}.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
for i in order:
    writer.write(frames[i])
writer.release()

(OUT / f"{name}.txt").write_text(
    f"FORWARD {FORWARD}  BACK {BACK}  take {take.name}\n"
    f"{len(frames)} frames became {len(order)}\n\norder:\n" + " ".join(map(str, order)),
    encoding="utf-8")
print(f"{len(frames)} frames became {len(order)} -> {OUT.name}\\{name}.mp4")
