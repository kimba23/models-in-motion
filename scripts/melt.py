"""MELT - redraw every frame with a small diffusion model, the way Deforum did.

Each frame is mixed with the last redrawn frame, then redrawn by sd-turbo:
    frame in  = this frame * (1 - FEEDBACK) + last output * FEEDBACK
    frame out = redraw(frame in, STRENGTH, PROMPT)
Because the last output flows into the next, the picture drifts and dissolves.

Uses the GPU: close ComfyUI first. About a minute per 6-second video.
Put this file in a folder of takes. Change the settings below, save,
double-click RUN.bat.
"""
from pathlib import Path
import sys
import cv2
import numpy as np

# ---- settings ---------------------------------------------------------------
PROMPT = "a young woman running along the edge of a wide beach, late afternoon light"
                         # describe what is IN the video. A wrong prompt looks absurd.
STRENGTH = 0.42          # how much each frame is redrawn: 0.25 barely, 0.42 photographic,
                         # 0.58 starts inventing
FEEDBACK = 0.7           # how much of the last output flows in: 0 = flicker, 0.7 = melt,
                         # above 0.9 runs away into abstraction
DETAIL = 0.85            # how much of the video's own texture comes back (0 to 1)
TAKE = 0                 # which video to melt: 0 = the first in the folder, 1 = the second ...
FRAMES = 0               # only the first N frames (0 = all). 48 to try a setting quickly.
SEED = 0                 # another number = another melt
# -----------------------------------------------------------------------------

HERE = Path(__file__).parent
OUT = HERE / Path(__file__).stem
OUT.mkdir(exist_ok=True)
# the model lives inside the kit, next to the Python that runs this script
MODEL = Path(sys.executable).resolve().parent.parent / "ComfyUI" / "models" / "melt" / "sd-turbo"

import torch
from diffusers import AutoPipelineForImage2Image
from diffusers.utils import logging
from PIL import Image

logging.set_verbosity_error()
print("loading sd-turbo ...")
pipe = AutoPipelineForImage2Image.from_pretrained(str(MODEL), torch_dtype=torch.float16,
                                                  safety_checker=None, local_files_only=True).to("cuda")
pipe.set_progress_bar_config(disable=True)

take = sorted(HERE.glob("*.mp4"))[TAKE]
video = cv2.VideoCapture(str(take))
fps = video.get(cv2.CAP_PROP_FPS) or 24
total = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
limit = FRAMES or total
w, h = int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
w, h = w - w % 8, h - h % 8                           # the model wants multiples of 8
steps = max(4, int(np.ceil(1 / STRENGTH)) + 1)       # sd-turbo needs STRENGTH * steps >= 1
generator = torch.Generator("cuda").manual_seed(SEED)
print(f"melting {take.name}: {limit} frames")

name = f"{take.stem} strength {STRENGTH} feedback {FEEDBACK}"
writer = cv2.VideoWriter(str(OUT / f"{name}.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
last = None
for i in range(limit):
    ok, frame = video.read()
    if not ok:
        break
    src = cv2.cvtColor(cv2.resize(frame, (w, h)), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    mixed = src if last is None else src * (1 - FEEDBACK) + last * FEEDBACK      # the loop
    img = pipe(prompt=PROMPT, image=Image.fromarray((mixed * 255).astype(np.uint8)), strength=STRENGTH,
               guidance_scale=0.0, num_inference_steps=steps, generator=generator).images[0]
    out = np.asarray(img).astype(np.float32) / 255
    if DETAIL > 0:                                    # put the video's own fine texture back
        out = cv2.GaussianBlur(out, (0, 0), 5.5) + (src - cv2.GaussianBlur(src, (0, 0), 5.5)) * DETAIL
    last = np.clip(out, 0, 1)
    writer.write(cv2.cvtColor((last * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    print(f"  {i + 1}/{limit}", end="\r", flush=True)
writer.release()

(OUT / f"{name}.txt").write_text(
    f'PROMPT "{PROMPT}"\nSTRENGTH {STRENGTH}  FEEDBACK {FEEDBACK}  DETAIL {DETAIL}  SEED {SEED}\n'
    f"melted from {take.name}, {limit} frames, sd-turbo, {steps} steps per frame", encoding="utf-8")
print(f"\n-> {OUT.name}\\{name}.mp4")
