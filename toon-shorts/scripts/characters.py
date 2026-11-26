#!/usr/bin/env python3
"""
Stage 1 - character sheets.
Generates one reference sheet per character so every later shot can be
conditioned on it (keeps hats, outfits and faces consistent between cuts).

    python3 scripts/characters.py out/<project> [--dry-run]
"""
import os

import common
import style


def run(project_dir, dry):
    path, doc = common.load(project_dir)
    out_dir = os.path.join(project_dir, "characters")
    os.makedirs(out_dir, exist_ok=True)
    sheets = doc.setdefault("character_sheets", {})

    todo = {n: look for n, look in doc.get("characters", {}).items()
            if not (sheets.get(n) or {}).get("url")}
    prompts = {n: style.character_sheet_prompt(n, look, doc["aspect"]) for n, look in todo.items()}
    if dry:
        for n, p in prompts.items():
            print(f"--- character {n}\n{p}\n")
        return

    from provider import get_provider, run_jobs
    prov = get_provider(doc.get("provider"))
    specs = {n: (lambda p=p: prov.submit_image(doc["image_model"], p, aspect_ratio="16:9", resolution="1k"))
             for n, p in prompts.items()}
    done = run_jobs(prov, specs, poll_s=3, stall_s=90, max_retries=2, deadline_s=400)
    for n, url in done.items():
        if not url:
            continue
        dest = os.path.join(out_dir, f"{n}.jpg")
        prov.download(url, dest)
        sheets[n] = {"url": url, "path": dest, "prompt": prompts[n]}
        print(f"[{n}] saved {dest}")
    common.save(path, doc)
    print("Review the sheets in", out_dir, "- delete an entry from character_sheets in story.json to regenerate it.")


if __name__ == "__main__":
    run(*common.args())
