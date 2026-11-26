"""Procedural music bed: quiet, mischievous sea-shanty loop (mandolin, accordion, bass, foghorn)."""
import math
import wave

import numpy as np

SR = 44100


def _ks(freq, dur, bright=0.5, seed=0):
    """Karplus-Strong plucked string."""
    n = int(SR * dur)
    p = max(2, int(SR / freq))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, p)
    out = np.empty(n)
    idx = 0
    damp = 0.996 - (1 - bright) * 0.01
    for i in range(n):
        out[i] = buf[idx]
        nxt = (idx + 1) % p
        buf[idx] = damp * 0.5 * (buf[idx] + buf[nxt])
        idx = nxt
    return out * np.exp(-np.linspace(0, 4, n))


def _note(name):
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    pitch, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[pitch] + (octave - 4) * 12) / 12)


CHORDS = [("D", ["D3", "F3", "A3"]), ("A", ["C#3", "E3", "A3"]), ("D", ["D3", "F3", "A3"]), ("C", ["C3", "E3", "G3"]),
          ("F", ["F3", "A3", "C4"]), ("C", ["C3", "E3", "G3"]), ("A", ["C#3", "E3", "A3"]), ("D", ["D3", "F3", "A3"])]
MELODY = ["A4", "D5", "D5", "E5", "F5", "E5", "D5", "C#5", "E5", "A4", "D5", "F5", "A5", "G5", "F5", "E5",
          "C5", "E5", "G5", "E5", "F5", "A5", "C6", "A5", "G5", "E5", "C5", "E5", "E5", "C#5", "A4", "D5"]


def render(path_out, seconds, bpm=104):
    beat = 60 / bpm
    bar = beat * 3                      # waltz-ish 3/4 shanty lilt
    n = int(SR * (seconds + 2))
    mix = np.zeros(n)

    def add(sig, t0, gain):
        i = int(t0 * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        mix[i:j] += sig[: j - i] * gain

    bar_i = 0
    t = 0.0
    cache = {}
    while t < seconds + 1:
        root, chord = CHORDS[bar_i % len(CHORDS)]
        # bass on 1, chord plucks on 2 & 3
        bf = _note(root + "2")
        k = ("b", bf)
        cache.setdefault(k, _ks(bf, bar, 0.3, 1))
        add(cache[k], t, 0.55)
        for b in (1, 2):
            for ci, nm in enumerate(chord):
                f = _note(nm) * 2
                k = ("c", f)
                cache.setdefault(k, _ks(f, beat * 1.2, 0.7, ci + 3))
                add(cache[k], t + b * beat + ci * 0.012, 0.16)
        # accordion pad (detuned saws, soft)
        dur = bar
        tt = np.arange(int(dur * SR)) / SR
        pad = np.zeros_like(tt)
        for nm in chord:
            f = _note(nm)
            vib = 1 + 0.004 * np.sin(2 * math.pi * 5.5 * tt)
            for det in (0.997, 1.003):
                ph = 2 * math.pi * f * det * np.cumsum(vib) / SR
                pad += (2 * ((ph / (2 * math.pi)) % 1) - 1)
        env = np.minimum(1, tt / 0.15) * np.minimum(1, (dur - tt) / 0.15)
        pad = np.convolve(pad, np.ones(18) / 18, mode="same") * env
        add(pad, t, 0.03 if bar_i >= 4 else 0.0)
        # mandolin melody: two notes per bar (tremolo-ish double pluck), enters bar 8
        if bar_i >= 8:
            for k_i in range(2):
                nm = MELODY[(bar_i * 2 + k_i) % len(MELODY)]
                f = _note(nm)
                k = ("m", f)
                cache.setdefault(k, _ks(f, beat * 1.6, 0.85, 9))
                add(cache[k], t + k_i * beat * 1.5, 0.22)
                add(cache[k], t + k_i * beat * 1.5 + 0.09, 0.12)
        # shaker
        rng = np.random.default_rng(bar_i)
        for b in range(6):
            sh = rng.uniform(-1, 1, int(0.05 * SR)) * np.exp(-np.linspace(0, 8, int(0.05 * SR)))
            add(sh, t + b * beat / 2, 0.035 if b % 2 else 0.05)
        # distant foghorn every 16 bars
        if bar_i % 16 == 12:
            tt = np.arange(int(2.2 * SR)) / SR
            horn = (np.sin(2 * math.pi * 73 * tt) + 0.4 * np.sin(2 * math.pi * 146 * tt))
            horn *= np.minimum(1, tt / 0.4) * np.minimum(1, (2.2 - tt) / 0.6)
            add(horn, t, 0.18)
        t += bar
        bar_i += 1

    mix = mix[: int(SR * seconds)]
    mix /= max(1e-6, np.max(np.abs(mix))) / 0.8
    fade = int(SR * 1.5)
    mix[-fade:] *= np.linspace(1, 0, fade)
    st = np.stack([mix, np.roll(mix, 220)], axis=1)
    with wave.open(path_out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    return path_out
