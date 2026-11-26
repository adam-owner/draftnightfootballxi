#!/usr/bin/env python3
"""
Stage 3 - motion.
Animates every keyframe into a short clip with an image-to-video model.

    python3 scripts/clips.py out/<project> [--dry-run]
"""
import os

import common
import style


def run(project_dir, dry):
    path, doc = common.load(project_dir)
    clip_dir = os.path.join(project_dir, "clips")
    os.makedirs(clip_dir, exist_ok=True)
    model = doc["video_model"]

    jobs = {}
    for shot in doc["shots"]:
        if shot.get("clip_path") and os.path.exists(shot["clip_path"]):
            continue
        prompt = style.motion_prompt(shot)
        shot["clip_prompt"] = prompt
        jobs[str(shot["id"])] = (shot, prompt)

    if dry:
        for k, (_, p) in jobs.items():
            print(f"--- clip {k}\n{p}\n")
        return

    from provider import get_provider, run_jobs
    prov = get_provider(doc.get("provider"))
    specs = {}
    for k, (shot, p) in jobs.items():
        if not shot.get("keyframe_url"):
            print(f"[{k}] no keyframe yet - run keyframes.py first")
            continue
        # veo3.1 renders fixed 8s clips; other models take a duration.
        dur = 8 if "veo3" in model else int(shot.get("clip_seconds", 5))
        params = {"image_url": shot["keyframe_url"], "duration": dur, "aspect_ratio": doc["aspect"]}
        specs[k] = (lambda p=p, par=params: prov.submit_video(model, p, **par))
    done = run_jobs(prov, specs, poll_s=5, stall_s=180, max_retries=2, deadline_s=1200)
    for k, url in done.items():
        if not url:
            continue
        shot = jobs[k][0]
        dest = os.path.join(clip_dir, f"clip_{k}.mp4")
        prov.download(url, dest)
        shot["clip_url"], shot["clip_path"] = url, dest
        print(f"[{k}] saved {dest}")
    common.save(path, doc)


if __name__ == "__main__":
    run(*common.args())
