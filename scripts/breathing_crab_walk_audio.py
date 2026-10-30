"""BREATHING CRAB WALK - forward/backward runs shrink, then grow.

150 source frames -> maximum run 15:
+15, -13, +11, -9, +7, -5, +3, -1, 0,
-1, +3, -5, +7, -9, +11, -13, +15; repeat to the end.
Each move plays every frame along its path. Zero holds for one frame.
Output can be longer than the original. RUN rebuilds audio from the .frames file.
Put beside your MP4 takes; save and run with RUN.bat.
"""
from pathlib import Path
import math
import cv2

# ---- settings ---------------------------------------------------------------
DIVISOR = 10             # Largest run = source frame count divided by this number.
SHRINK = 2               # Frames removed per run on the way down, added on the way up.
TAKE = 0                 # Which sorted MP4 to walk: 0 = the first one.
# -----------------------------------------------------------------------------


def make_moves(maximum, shrink):
    down = list(range(maximum, 0, -shrink))
    # Start the growing sweep backward; both sweeps then make net forward progress.
    moves = [size if i % 2 == 0 else -size for i, size in enumerate(down)]
    moves += [0]
    moves += [-size if i % 2 == 0 else size
              for i, size in enumerate(reversed(down))]
    # With an odd number of levels, the two sweeps cancel. Keep the growing
    # sweep's largest move forward so the walk always reaches the end.
    if sum(moves) <= 0:
        moves[-1] = maximum
    return moves


def walk(frame_count, moves):
    position = 0
    yield position
    while position < frame_count - 1:
        for move in moves:
            if move == 0:
                yield position
                continue
            direction = 1 if move > 0 else -1
            for _ in range(abs(move)):
                next_position = position + direction
                if next_position < 0:
                    break  # At the beginning, stop the backward move.
                if next_position >= frame_count:
                    return
                position = next_position
                yield position
                if position == frame_count - 1:
                    return


def main():
    if not isinstance(DIVISOR, int) or DIVISOR < 1:
        raise ValueError('DIVISOR must be a positive integer.')
    if not isinstance(SHRINK, int) or SHRINK < 1:
        raise ValueError('SHRINK must be a positive integer.')
    here = Path(__file__).parent
    takes = sorted(Path(__file__).parent.glob('*.mp4'))
    if not takes:
        raise ValueError('Put this script beside at least one MP4 take.')
    if not isinstance(TAKE, int) or not 0 <= TAKE < len(takes):
        raise ValueError(f'TAKE must be between 0 and {len(takes) - 1}.')
    take = takes[TAKE]
    video = cv2.VideoCapture(str(take))
    frames = []
    try:
        fps = video.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps <= 0:
            fps = 24
        while True:
            ok, frame = video.read()
            if not ok:
                break
            frames.append(frame)
    finally:
        video.release()
    if not frames:
        raise ValueError(f'No readable frames in {take.name}.')
    maximum = max(1, len(frames) // DIVISOR)
    moves = make_moves(maximum, SHRINK)
    print(f'{take.name}: {len(frames)} frames; largest run = {maximum}')
    print('Moves: ' + ', '.join(f'{move:+d}' for move in moves))
    out = here / Path(__file__).stem
    out.mkdir(exist_ok=True)
    stem = f'{take.stem} max {maximum} shrink {SHRINK}'
    target = out / f'{stem}.mp4'
    version = 2
    while any(target.with_suffix(ext).exists() for ext in ('.mp4', '.txt', '.frames')):
        target = out / f'{stem} v{version}.mp4'
        version += 1
    h, w = frames[0].shape[:2]
    writer = cv2.VideoWriter(str(target), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError('Could not open the MP4 writer.')
    count = 0
    try:
        with target.with_suffix('.txt').open('w', encoding='utf-8') as recipe, \
             target.with_suffix('.frames').open('w', encoding='utf-8') as audio_map:
            recipe.write(f'BREATHING CRAB WALK\nDIVISOR {DIVISOR} SHRINK {SHRINK} TAKE {TAKE}\n'
                         f'Source: {take.name}\nSource frames: {len(frames)} FPS: {fps}\n'
                         f'Maximum: {maximum}\nMoves: {moves}\n'
                         'Zero holds one frame; backward moves stop at frame 0.\n'
                         'RUN rebuilds audio using the matching .frames file.\n\noutput_frame source_frame\n')
            for source in walk(len(frames), moves):
                writer.write(frames[source])
                audio_map.write(f'{source}\t{take.name}\n')
                recipe.write(f'{count} {source}\n')
                count += 1
            recipe.write(f'\n{len(frames)} source frames became {count} output frames.\n')
    finally:
        writer.release()
    print(f'{len(frames)} frames became {count} -> {target}')
    print(f'Audio map: {target.with_suffix(".frames").name} (RUN rebuilds the sound)')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        raise SystemExit(f'Breathing Crab Walk: {error}')
