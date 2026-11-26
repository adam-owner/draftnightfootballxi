#!/usr/bin/env python3
"""
Stage 2 - keyframes.
One still per shot. Shots with characters go through the reference/edit model
with the character sheets attached; shots without characters (inserts,
establishing shots) use plain text-to-image.

    python3 scripts/keyframes.py out/<project> [--dry-run]
"""
import os

import common
import style


def run(project_dir, dry):
    path, doc = common.load(project_dir)
    kf_dir = os.path.join(project_dir, "keyframes")
    os.makedirs(kf_dir, exist_ok=True)
    sheets = doc.get("character_sheets", {})

    jobs = {}
    for shot in doc["shots"]:
        if shot.get("keyframe_url"):
            continue
        prompt = style.shot_prompt(shot, doc, doc["aspect"])
        shot["keyframe_prompt"] = prompt
        refs = [sheets[c]["url"] for c in shot.get("characters", []) if (sheets.get(c) or {}).get("url")]
        jobs[str(shot["id"])] = (shot, prompt, refs)

    if dry:
        for k, (_, p, refs) in jobs.items():
            print(f"--- shot {k} refs={len(refs)}\n{p}\n")
        return

    from provider import get_provider, run_jobs
    prov = get_provider(doc.get("provider"))
    specs = {}
    for k, (shot, p, refs) in jobs.items():
        if refs:
            ref_val = refs if doc["ref_param"] == "images_list" else refs[0]
            params = {doc["ref_param"]: ref_val, "aspect_ratio": doc["aspect"]}
            specs[k] = (lambda p=p, par=params: prov.submit_image(doc["ref_image_model"], p, **par))
        else:
            specs[k] = (lambda p=p: prov.submit_image(doc["image_model"], p,
                                                      aspect_ratio=doc["aspect"], resolution="1k"))
    done = run_jobs(prov, specs, poll_s=3, stall_s=90, max_retries=2, deadline_s=600)
    for k, url in done.items():
        if not url:
            continue
        shot = jobs[k][0]
        dest = os.path.join(kf_dir, f"kf_{k}.jpg")
        prov.download(url, dest)
        shot["keyframe_url"], shot["keyframe_path"] = url, dest
        print(f"[{k}] saved {dest}")
    common.save(path, doc)


if __name__ == "__main__":
    run(*common.args())
