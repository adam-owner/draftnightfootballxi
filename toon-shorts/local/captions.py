"""Burned-in captions timed to each voiced line (reference style: bold white, dark outline, ~70% height).

Kokoro gives no word timestamps, so each line's [start, end] is split across its words in proportion to
their length, with extra weight for the pause after punctuation. Words are shown in short chunks.
"""
import re

import skia

from draw import clamp01, ease, fill, font

MAX_CHARS = 16          # a chunk is at most this many characters (~2-3 words)
CHAR_COLOUR = {"narrator": (255, 255, 255)}
SPEAKER = (255, 226, 92)  # characters' lines in yellow


def chunks(text, start, end):
    words = [w for w in re.split(r"\s+", text.replace("...", "… ").strip()) if w]
    if not words:
        return []
    weight = [len(w) + 1 + (3 if re.search(r"[,.!?…]$", w) else 0) for w in words]
    total = float(sum(weight))
    t, groups, cur, cur_s = start, [], [], start
    for w, wt in zip(words, weight):
        if cur and (len(" ".join(cur + [w])) > MAX_CHARS or re.search(r"[.!?…]$", cur[-1])):
            groups.append((" ".join(cur), cur_s, t))
            cur, cur_s = [], t
        cur.append(w)
        t += (end - start) * wt / total
    groups.append((" ".join(cur), cur_s, end))
    return groups


def draw(cv, W, H, t, shot, y_frac=0.71):
    lines = shot.get("lines", [])
    for (st, en, who, _bubble), ln in zip(shot.get("line_times", []), lines):
        if ln.get("silent") or not ln.get("text"):
            continue
        for txt, a, b in chunks(ln["text"], st, en):
            if a <= t < b + 0.05:
                pop = ease(clamp01((t - a) / 0.09))
                size = 58 if len(txt) < 12 else 50
                f = font(size, "black")
                w = f.measureText(txt)
                x, y = W / 2 - w / 2, H * y_frac
                cv.save(); cv.translate(W / 2, y); cv.scale(0.85 + 0.15 * pop, 0.85 + 0.15 * pop); cv.translate(-W / 2, -y)
                outline = skia.Paint(AntiAlias=True, Color=skia.Color(15, 10, 12, 255), Style=skia.Paint.kStroke_Style,
                                     StrokeWidth=size * 0.2, StrokeJoin=skia.Paint.kRound_Join)
                cv.drawString(txt, x + 3, y + 4, f, fill((0, 0, 0), 140))
                cv.drawString(txt, x, y, f, outline)
                cv.drawString(txt, x, y, f, fill(CHAR_COLOUR.get(who, SPEAKER)))
                cv.restore()
                return
