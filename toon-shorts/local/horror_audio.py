"""Procedural horror score + SFX baked onto one bed track.

timeline: list of dicts {start, dur, sfx: [...], line_times: [...]} in film time (s).
SFX: buzz (phone vibrate), sting (shock hit), ring (ringback x2), steps (heavy footsteps),
heartbeat, tick (clock).
"""
import math
import wave

import numpy as np

SR = 44100


def _t(sec):
    return np.arange(int(sec * SR)) / SR


def _env(n, a=0.01, r=0.2):
    e = np.ones(n)
    ai, ri = int(a * SR), int(r * SR)
    if ai:
        e[:ai] = np.linspace(0, 1, ai)
    if ri:
        e[-ri:] *= np.linspace(1, 0, ri)
    return e


def _lp(x, k=30):
    return np.convolve(x, np.ones(k) / k, mode="same")


def drone(sec, seed=0):
    t = _t(sec)
    rng = np.random.default_rng(seed)
    x = np.zeros_like(t)
    for f, a in ((41.2, 0.5), (41.9, 0.4), (61.7, 0.25), (87.3, 0.12), (92.5, 0.1)):   # E1 cluster, tritone hint
        x += a * np.sin(2 * math.pi * f * t + rng.uniform(0, 6))
    x *= 0.75 + 0.25 * np.sin(2 * math.pi * 0.07 * t)
    air = _lp(rng.normal(0, 1, len(t)), 200) * 0.6
    return x + air


def strings_swell(sec, base=220.0):
    t = _t(sec)
    x = np.zeros_like(t)
    for k, f in enumerate((base, base * 1.06, base * 1.414, base * 1.5)):
        vib = 1 + 0.006 * np.sin(2 * math.pi * (5 + k) * t)
        ph = 2 * math.pi * f * np.cumsum(vib) / SR
        x += (2 * ((ph / (2 * math.pi)) % 1) - 1) * 0.25
    x = _lp(x, 12)
    return x * np.linspace(0, 1, len(t)) ** 2


def buzz(sec=0.9):
    t = _t(sec)
    x = np.sign(np.sin(2 * math.pi * 160 * t)) * 0.5 + np.sin(2 * math.pi * 320 * t) * 0.3
    gate = ((t % 0.45) < 0.32).astype(float)
    return _lp(x, 6) * gate * 0.6


def sting():
    t = _t(2.5)
    boom = np.sin(2 * math.pi * 38 * t * (1 - 0.3 * t / 2.5)) * np.exp(-t * 1.8)
    rng = np.random.default_rng(3)
    hit = _lp(rng.normal(0, 1, len(t)), 3) * np.exp(-t * 6) * 0.5
    screech = np.zeros_like(t)
    for f in (1180, 1250, 1320):
        screech += np.sin(2 * math.pi * f * t + 3 * np.sin(2 * math.pi * 6 * t)) * 0.12
    screech *= np.exp(-t * 1.4) * np.minimum(1, t / 0.05)
    return boom * 0.9 + hit + screech


def ring():
    t = _t(4.2)
    x = (np.sin(2 * math.pi * 440 * t) + np.sin(2 * math.pi * 480 * t)) * 0.18
    gate = (((t % 2.0) < 1.0) & (t < 3.0)).astype(float)
    return x * _lp(gate, 200)


def step():
    t = _t(0.9)
    thud = np.sin(2 * math.pi * 55 * t) * np.exp(-t * 9)
    rng = np.random.default_rng(1)
    knock = _lp(rng.normal(0, 1, len(t)), 8) * np.exp(-t * 30) * 0.6
    x = thud + knock
    tail = np.zeros_like(x)
    for d, g in ((0.12, 0.35), (0.25, 0.2), (0.4, 0.1)):
        i = int(d * SR)
        tail[i:] += x[:-i] * g
    return x + tail


def heartbeat(sec):
    out = np.zeros(int(sec * SR))
    beat = 0.82
    t = 0.0
    while t < sec:
        for off, g in ((0, 1.0), (0.22, 0.7)):
            tt = _t(0.25)
            b = np.sin(2 * math.pi * 48 * tt) * np.exp(-tt * 18) * g
            i = int((t + off) * SR)
            j = min(len(out), i + len(b))
            if i < len(out):
                out[i:j] += b[: j - i]
        t += beat
        beat = max(0.5, beat * 0.96)
    return out


def tick(sec):
    out = np.zeros(int(sec * SR))
    rng = np.random.default_rng(5)
    for k in range(int(sec)):
        tt = _t(0.04)
        c = _lp(rng.normal(0, 1, len(tt)), 2) * np.exp(-tt * 120) * (0.6 if k % 2 else 0.9)
        i = int(k * SR)
        out[i:i + len(c)] += c[: len(out) - i]
    return out


def render(path_out, total, timeline):
    n = int(SR * (total + 1))
    bed = np.zeros(n)
    fx = np.zeros(n)

    def add(buf, sig, t0, g):
        i = int(t0 * SR)
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        buf[i:j] += sig[: j - i] * g

    add(bed, drone(total + 1), 0, 0.5)
    # a slow string swell building over the whole episode, peaking at the reveal
    reveal = next((s["start"] for s in timeline if "heartbeat" in s.get("sfx", [])), total * 0.8)
    add(bed, strings_swell(reveal), 0, 0.22)
    for s in timeline:
        st, du = s["start"], s["dur"]
        for name in s.get("sfx", []):
            if name == "buzz":
                first = next((lt[0] for lt in s.get("line_times", []) if lt[3]), 0.3)
                add(fx, buzz(), st + max(0, first - 0.35), 0.5)
            elif name == "sting":
                when = st + (s["line_times"][0][1] + 0.1 if s.get("line_times") and s["id"] == 12 else 0.0)
                add(fx, sting(), when, 0.55)
            elif name == "ring":
                add(fx, ring(), st + 0.2, 0.5)
            elif name == "steps":
                k = 0.3
                while k < du:
                    add(fx, step(), st + k, 0.75 * min(1, 0.4 + k / du))
                    k += 1.15
            elif name == "heartbeat":
                add(fx, heartbeat(du + 9), st, 0.8)
            elif name == "tick":
                add(fx, tick(du), st, 0.35)
    # choice card: drone drops to near silence except the ticking
    last = timeline[-1]
    i0 = int(last["start"] * SR)
    bed[i0:] *= np.linspace(1, 0.35, n - i0)
    mix = bed / max(1e-6, np.max(np.abs(bed))) * 0.55 + fx / max(1e-6, np.max(np.abs(fx))) * 0.85
    mix = mix[: int(SR * total)]
    fade = int(SR * 0.8)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix * 1.2) * 0.9
    st = np.stack([mix, np.roll(mix, 300)], axis=1)
    with wave.open(path_out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    return path_out
