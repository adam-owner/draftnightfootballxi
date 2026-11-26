#!/usr/bin/env python3
"""
Stage 4 - voice-over + music (adapted from muapi-director's audio.py).
One TTS line per shot (MiniMax speech on MuAPI) plus an optional instrumental bed.

    python3 scripts/voiceover.py out/<project> [--dry-run]

Using your own recorded voice instead: drop files at audio/narr_<shot id>.mp3
and they are kept (nothing is regenerated for that shot).
Voice cloning: set voice.clone_ref to a short clean recording of the voice.
"""
import base64
import os

import common

CLONE_TEMPLATE = (
    "**Speaker A** @audio1 keeps their own vocal timbre and speaks fluent natural English, "
    "{delivery}. Clean dry studio vocal only - no music, no effects, no reverb. They say: \"{script}\""
)


def run(project_dir, dry):
    path, doc = common.load(project_dir)
    adir = os.path.join(project_dir, "audio")
    os.makedirs(adir, exist_ok=True)
    voice = doc.get("voice", {})
    voice_id = voice.get("voice_id", "English_magnetic_voiced_man")
    speed = float(voice.get("speed", 1.05))
    delivery = voice.get("delivery", "calm deadpan storyteller, dry wit, unhurried pace")
    clone_ref = voice.get("clone_ref")

    todo = []
    for shot in doc["shots"]:
        dest = os.path.join(adir, f"narr_{shot['id']}.mp3")
        if os.path.exists(dest):
            shot["audio_path"], shot["audio_duration"] = dest, common.probe_dur(dest)
            continue
        if shot.get("narration"):
            todo.append(shot)

    music = doc.get("music")
    bgm_path = os.path.join(adir, "bgm.mp3")
    need_bgm = bool(music) and not os.path.exists(bgm_path)

    if dry:
        for s in todo:
            print(f"--- narr {s['id']} [{voice_id} x{speed}]: {s['narration']}")
        if need_bgm:
            print(f"--- bgm: {music}")
        return

    from provider import get_provider, run_jobs
    prov = get_provider(doc.get("provider"))
    model = doc["voice_model"]
    ref_b64 = None
    if clone_ref:
        with open(clone_ref, "rb") as f:
            ref_b64 = base64.b64encode(f.read()).decode()

    specs = {}
    for s in todo:
        t = s["narration"]
        if ref_b64:
            specs[f"narr_{s['id']}"] = (lambda t=t: prov.submit_audio(
                model, text=CLONE_TEMPLATE.format(delivery=delivery, script=t),
                format="mp3", sample_rate=44100, references=[{"audio_data": ref_b64}]))
        else:
            specs[f"narr_{s['id']}"] = (lambda t=t: prov.submit_audio(
                model, prompt=t, text=t, language="en", voice_id=voice_id,
                codec="mp3", sample_rate=44100, speed=speed))
    if need_bgm:
        specs["bgm"] = lambda: prov.submit_audio(doc["music_model"], prompt=music, style=music,
                                                 is_instrumental=True, format="mp3")

    done = run_jobs(prov, specs, poll_s=4, stall_s=150, max_retries=2, deadline_s=600)
    by_id = {f"narr_{s['id']}": s for s in todo}
    for key, url in done.items():
        if not url:
            continue
        dest = bgm_path if key == "bgm" else os.path.join(adir, f"{key}.mp3")
        prov.download(url, dest)
        if key in by_id:
            by_id[key]["audio_path"], by_id[key]["audio_duration"] = dest, common.probe_dur(dest)
        print(f"[{key}] saved {dest}")
    common.save(path, doc)


if __name__ == "__main__":
    run(*common.args())
