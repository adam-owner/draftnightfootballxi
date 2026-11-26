#!/usr/bin/env python3
"""
Stage 5 - assembly (local ffmpeg, no API calls). No captions, no watermark.

Each shot lasts as long as its narration line + a small breath (min_shot), the
clip is trimmed (or slowed slightly, then frozen) to fit, narration lines are
laid end-to-end, and the music bed is ducked under the voice.

    python3 scripts/assemble.py out/<project>
"""
import os
import subprocess

import common

FPS = 30
RES = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}


def ff(a):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)


def run(project_dir, _dry=False):
    path, doc = common.load(project_dir)
    W, H = RES.get(doc["aspect"], RES["9:16"])
    mix = doc.get("mix", {})
    breath = float(mix.get("gap", 0.15))          # silence between lines
    min_shot = float(mix.get("min_shot", 1.5))
    tmp = os.path.join(project_dir, "_seg")
    os.makedirs(tmp, exist_ok=True)

    segs, t, voice_in, voice_f = [], 0.0, [], []
    for shot in doc["shots"]:
        clip = shot.get("clip_path")
        if not clip or not os.path.exists(clip):
            raise SystemExit(f"shot {shot['id']}: missing clip - run clips.py first")
        a = shot.get("audio_path")
        adur = shot.get("audio_duration") or (common.probe_dur(a) if a else 0)
        dur = round(max(float(shot.get("hold", 0)), adur + breath, min_shot), 3)
        cdur = common.probe_dur(clip)
        slow = dur / cdur if cdur and dur > cdur else 1.0
        pre = f"setpts={min(slow, 1.35):.4f}*PTS," if slow > 1.02 else ""
        out = os.path.join(tmp, f"seg_{shot['id']}.mp4")
        ff(["-i", clip, "-an", "-vf",
            f"{pre}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
            f"tpad=stop_mode=clone:stop_duration={dur}",
            "-t", f"{dur}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "18", out])
        segs.append(out)
        if a and os.path.exists(a):
            i = len(voice_in) // 2 + 1
            voice_in += ["-i", a]
            ms = int(t * 1000)
            voice_f.append(f"[{i}:a]aresample=44100,adelay={ms}|{ms}[v{i}]")
        t += dur
    total = round(t, 3)

    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    video = os.path.join(tmp, "video.mp4")
    ff(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])

    bgm = os.path.join(project_dir, "audio", "bgm.mp3")
    inputs = ["-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=r=44100:cl=stereo", *voice_in]
    n = len(voice_in) // 2
    chains = list(voice_f)
    labels = "".join(f"[v{i}]" for i in range(1, n + 1))
    chains.append(f"[0:a]{labels}amix=inputs={n + 1}:duration=first:normalize=0,"
                  f"volume={mix.get('voice', 1.0)}[vo]")
    if os.path.exists(bgm):
        b = n + 1
        inputs += ["-stream_loop", "-1", "-i", bgm]
        chains.append(f"[{b}:a]volume={mix.get('music', 0.25)},afade=t=out:st={max(total - 1.5, 0)}:d=1.5[bg]")
        chains.append("[vo]asplit[vo1][vo2]")
        chains.append("[bg][vo1]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300[duck]")
        chains.append("[vo2][duck]amix=inputs=2:duration=first:normalize=0[pre]")
    else:
        chains.append("[vo]anull[pre]")
    # reference shorts sit around -17 LUFS integrated; -16 is the usual phone/TikTok target
    chains.append(f"[pre]loudnorm=I={mix.get('lufs', -16)}:TP=-1.5:LRA=11,aresample=44100[aout]")
    audio = os.path.join(tmp, "mix.m4a")
    ff([*inputs, "-filter_complex", ";".join(chains), "-map", "[aout]", "-t", f"{total}",
        "-c:a", "aac", "-b:a", "192k", audio])

    final = os.path.join(project_dir, "final.mp4")
    ff(["-i", video, "-i", audio, "-map", "0:v", "-map", "1:a", "-c", "copy", "-shortest",
        "-movflags", "+faststart", final])
    print(f"Done -> {final} ({total:.1f}s, {len(segs)} shots)")


if __name__ == "__main__":
    run(*common.args())
