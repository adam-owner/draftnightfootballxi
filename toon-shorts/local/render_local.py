#!/usr/bin/env python3
"""
Offline (no API key) render of a story: local neural TTS (Kokoro), procedural
music, vector-animated shots, then the normal assemble.py.

    python3 local/render_local.py out/fog-keeper [--preview] [--voice am_michael]

--preview renders one still per shot into out/<p>/preview/ (fast check).
Needs: pip install skia-python kokoro-onnx soundfile numpy, plus the Kokoro model
files (kokoro-v1.0.int8.onnx, voices-v1.0.bin) in $KOKORO_DIR or local/models/.
"""
import importlib
import json
import os
import subprocess
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import skia  # noqa: E402

W, H, FPS = 720, 1280, 30
FILMS = {"fog-keeper": "film_fogkeeper"}


def film_for(doc):
    return importlib.import_module(FILMS[doc["project"]])


def tts(doc, adir, voice):
    from kokoro_onnx import Kokoro
    import soundfile as sf
    mdir = os.environ.get("KOKORO_DIR", os.path.join(HERE, "models"))
    k = Kokoro(os.path.join(mdir, "kokoro-v1.0.int8.onnx"), os.path.join(mdir, "voices-v1.0.bin"))
    speed = float(doc.get("voice", {}).get("local_speed", 0.97))
    for s in doc["shots"]:
        wav = os.path.join(adir, f"narr_{s['id']}.wav")
        mp3 = os.path.join(adir, f"narr_{s['id']}.mp3")
        if not os.path.exists(mp3):
            text = s["narration"].replace("...", ", ").strip(" ,")
            samples, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
            sf.write(wav, samples, sr)
            # trim edge silence, light warmth + compression
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-af",
                            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                            "bass=g=2:f=150,acompressor=threshold=-18dB:ratio=3",
                            "-ar", "44100", "-b:a", "192k", mp3], check=True)
            os.remove(wav)
        s["audio_path"] = mp3
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
                             capture_output=True, text=True).stdout
        s["audio_duration"] = float(out)
        print(f"[narr {s['id']}] {s['audio_duration']:.2f}s  {s['narration']}")


def shot_len(doc, s):
    mix = doc.get("mix", {})
    return round(max(float(s.get("hold", 0)), s["audio_duration"] + float(mix.get("gap", 0.15)),
                     float(mix.get("min_shot", 1.5))), 3)


def render_shot(args):
    project, sid, T, out = args
    with open(os.path.join(project, "story.json")) as f:
        doc = json.load(f)
    film = film_for(doc)
    fn = film.SHOTS[sid]
    n = int(round(T * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for i in range(n):
        cv = surf.getCanvas()
        cv.clear(skia.ColorBLACK)
        fn(cv, W, H, i / FPS, T)
        arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        ff.stdin.write(arr.tobytes())
    ff.stdin.close()
    ff.wait()
    return sid, out


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    project = os.path.abspath(a[0])
    voice = sys.argv[sys.argv.index("--voice") + 1] if "--voice" in sys.argv else "am_michael"
    path = os.path.join(project, "story.json")
    with open(path) as f:
        doc = json.load(f)
    film = film_for(doc)

    if "--preview" in sys.argv:
        pdir = os.path.join(project, "preview")
        os.makedirs(pdir, exist_ok=True)
        surf = skia.Surface(W, H)
        for s in doc["shots"]:
            cv = surf.getCanvas(); cv.clear(skia.ColorBLACK)
            film.SHOTS[s["id"]](cv, W, H, 1.6, 3.2)
            surf.makeImageSnapshot().save(os.path.join(pdir, f"p{s['id']:02d}.png"), skia.kPNG)
        print("previews ->", pdir)
        return

    adir = os.path.join(project, "audio"); os.makedirs(adir, exist_ok=True)
    cdir = os.path.join(project, "clips"); os.makedirs(cdir, exist_ok=True)
    tts(doc, adir, voice)
    total = sum(shot_len(doc, s) for s in doc["shots"])

    if doc.get("music") and not os.path.exists(os.path.join(adir, "bgm.mp3")):
        import music_local
        wav = music_local.render(os.path.join(adir, "bgm.wav"), total + 1)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-b:a", "192k", os.path.join(adir, "bgm.mp3")], check=True)
        os.remove(wav)
        print(f"[bgm] {total + 1:.1f}s")

    jobs = []
    for s in doc["shots"]:
        T = shot_len(doc, s)
        out = os.path.join(cdir, f"clip_{s['id']}.mp4")
        s["clip_path"] = out
        if not os.path.exists(out):
            jobs.append((project, s["id"], T, out))
    with open(path, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    with Pool(min(4, os.cpu_count() or 2)) as pool:
        for sid, out in pool.imap_unordered(render_shot, jobs):
            print(f"[shot {sid}] rendered")

    import assemble
    assemble.run(project)


if __name__ == "__main__":
    main()
