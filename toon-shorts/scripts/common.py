"""Shared helpers for the toon-shorts pipeline stages."""
import json
import os
import subprocess
import sys

DEFAULTS = {
    "aspect": "9:16",
    # text-to-image model for character sheets and character-free shots
    "image_model": "flux-dev",
    # reference/edit model used when a shot contains characters, so they stay on-model.
    # NOTE: model slug + reference parameter name are configurable because they differ
    # per MuAPI model. Check the model page on muapi.ai and adjust in story.json.
    "ref_image_model": "nano-banana-edit",
    "ref_param": "images_list",        # "images_list" (list of urls) or "image_url" (single url)
    "video_model": "veo3.1-image-to-video",
    "voice_model": "minimax-speech-2.6-turbo",
    "music_model": "suno-create-music",
}


def load(project_dir):
    path = os.path.join(project_dir, "story.json")
    with open(path) as f:
        doc = json.load(f)
    for k, v in DEFAULTS.items():
        doc.setdefault(k, v)
    return path, doc


def save(path, doc):
    with open(path, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("Updated", path)


def args():
    """Return (project_dir, dry_run). Usage: <stage>.py out/<project> [--dry-run]"""
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a:
        sys.exit(f"usage: {os.path.basename(sys.argv[0])} out/<project> [--dry-run]")
    return os.path.abspath(a[0]), "--dry-run" in sys.argv


def probe_dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    try:
        return float(out.strip())
    except ValueError:
        return 0.0
