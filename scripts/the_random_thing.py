"""THE RANDOM THING - random, syncopated palindromic video cuts.

Put beside at least two MP4 takes of the same shot. Run with your RUN.bat.
Each bar's x/. pattern AND alternate-take choices read identically backwards.
The footage keeps moving forward (this is a rhythmic palindrome, not reversed video).
Outputs silent video, like pulse_cut.py, plus a recipe beside it.
Requires opencv-python. All takes must have the same size and frame rate.
"""
from pathlib import Path
import math
import random
import secrets
import cv2

# ---- settings ---------------------------------------------------------------
METERS = (5, 7, 11, 13)  # Allowed eighth-note counts: 5/8, 7/8, 11/8, 13/8 only.
STEP = 3                 # Frames per sixteenth-note slot (24 fps: 3 = 120 BPM).
LENGTH = 1               # Frames borrowed on each hit; must be less than STEP.
DENSITY = 0.35            # Chance of a hit before enforcing symmetry/syncopation.
WINDOW = (0, 99)          # Seconds where cuts may occur; only whole bars are used.
SEED = None              # None = fresh randomness; an integer repeats the recipe.
# -----------------------------------------------------------------------------

HERE = Path(__file__).parent


def make_bar(rnd, beats, take_count):
    """Two slots per eighth note; strong group starts use 2+...+2+3 eighths."""
    groups = [2] * ((beats - 3) // 2) + [3]
    rnd.shuffle(groups)
    strong, cursor = [], 0
    for group in groups:
        strong.append(cursor * 2)
        cursor += group
    slots = beats * 2
    for _ in range(10000):
        half = [rnd.random() < DENSITY for _ in range(beats)]
        hits = half + half[::-1]
        # Anticipate a strong group beat, then leave that beat empty.
        sync = any(hits[(s - 1) % slots] and not hits[s] for s in strong)
        # Reject smaller repeating cells (including hidden regular four-slot loops).
        periodic = any(all(hits[i] == hits[i % p] for i in range(slots))
                       for p in range(1, slots) if slots % p == 0)
        if sync and not periodic and 2 <= sum(hits) <= slots - 2:
            chosen = [rnd.randrange(1, take_count) if hit else 0 for hit in half]
            return hits, chosen + chosen[::-1], groups
    raise RuntimeError("Could not build a pattern; try DENSITY nearer 0.35.")


def main():
    if not METERS or any(m not in (5, 7, 11, 13) for m in METERS):
        raise ValueError("METERS must contain only 5, 7, 11, or 13 (eighth notes).")
    if not isinstance(STEP, int) or not isinstance(LENGTH, int) or not 0 < LENGTH < STEP:
        raise ValueError("Use integer settings with 0 < LENGTH < STEP.")
    if not 0 < DENSITY < 1 or not 0 <= WINDOW[0] < WINDOW[1]:
        raise ValueError("Use 0 < DENSITY < 1 and an increasing, nonnegative WINDOW.")
    takes = sorted(Path(__file__).parent.glob("*.mp4"))
    if len(takes) < 2:
        raise ValueError("Put this script beside at least TWO .mp4 takes.")
    seed = secrets.randbits(64) if SEED is None else SEED
    rnd = random.Random(seed)
    clips, fps, size = [], None, None
    for path in takes:
        cap = cv2.VideoCapture(str(path))
        frames = []
        try:
            rate = cap.get(cv2.CAP_PROP_FPS)
            if not cap.isOpened() or not math.isfinite(rate) or rate <= 0:
                raise ValueError(f"Cannot read frame rate: {path.name}")
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if size is None:
                    size = (frame.shape[1], frame.shape[0])
                if (frame.shape[1], frame.shape[0]) != size:
                    raise ValueError(f"Different frame sizes: {path.name}")
                frames.append(frame)
        finally:
            cap.release()
        if not frames:
            raise ValueError(f"No readable frames: {path.name}")
        if fps is not None and abs(rate - fps) > 0.01:
            raise ValueError(f"Different frame rates: {path.name}")
        fps = rate if fps is None else fps
        clips.append(frames)
        print(f"Loaded {path.name}: {len(frames)} frames")
    n = min(map(len, clips))
    source = [0] * n
    start = math.ceil(WINDOW[0] * fps)
    stop = min(n, math.floor(WINDOW[1] * fps))
    bars = []
    while start < stop:
        fitting = [m for m in METERS if start + m * 2 * STEP <= stop]
        if not fitting:
            break  # Leave the tail on the base take; never truncate a palindrome.
        beats = rnd.choice(fitting)
        hits, choices, groups = make_bar(rnd, beats, len(takes))
        pattern = ''.join('x' if hit else '.' for hit in hits)
        bars.append(f"frame {start}: {beats}/8 groups={'+'.join(map(str, groups))} "
                    f"pattern={pattern} takes={choices}")
        print(bars[-1])
        for slot, take in enumerate(choices):
            if take:
                pos = start + slot * STEP
                source[pos:pos + LENGTH] = [take] * LENGTH
        start += beats * 2 * STEP
    if not bars:
        raise ValueError("No full bar fits. Use longer takes, a wider WINDOW, or smaller STEP.")
    out = HERE / Path(__file__).stem
    out.mkdir(exist_ok=True)
    # Preserve previous renders, including repeat runs with the same seed.
    stem = f"The Random Thing seed {seed}"
    target = out / f"{stem}.mp4"
    version = 2
    while target.exists() or target.with_suffix('.txt').exists():
        target = out / f"{stem} v{version}.mp4"
        version += 1
    writer = cv2.VideoWriter(str(target), cv2.VideoWriter_fourcc(*'mp4v'), fps, size)
    if not writer.isOpened():
        raise RuntimeError("Could not open MP4 writer. Check OpenCV codec support.")
    try:
        for f, take in enumerate(source):
            writer.write(clips[take][f])
    finally:
        writer.release()
    changed = sum(s != 0 for s in source)
    lines = ["THE RANDOM THING", f"SEED={seed} METERS={METERS} STEP={STEP} "
             f"LENGTH={LENGTH} DENSITY={DENSITY} WINDOW={WINDOW}",
             f"FPS={fps} FRAMES={n} SIZE={size}",
             "Sixteenth-note grid; x=cut, .=base; take indices start at 0.",
             "Each complete bar's hit pattern and take sequence are palindromes.",
             "Strong beats follow the logged eighth-note grouping.",
             "Footage moves forward; output has no audio.",
             "Frames outside complete bars remain on the base take.",
             "", "TAKES"]
    lines += [f"{i}: {p.name}" for i, p in enumerate(takes)]
    lines += ["", "BARS"] + bars + ["", "frame  take"]
    lines += [f"{f:6d}  {takes[s].name}" for f, s in enumerate(source) if s]
    target.with_suffix('.txt').write_text('\n'.join(lines), encoding='utf-8')
    print(f"{len(bars)} bars; {changed}/{n} frames borrowed -> {target}")


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        raise SystemExit(f"The Random Thing: {error}")
