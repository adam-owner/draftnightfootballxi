---
name: toon-shorts
description: >
  Make a ~60s vertical narrated cartoon short in the "flat 2D characters inside a cozy 3D world"
  style (round white heads, thick outlines, iconic hats, deadpan narrator, twist ending).
  Writes the story, generates character sheets, keyframes, motion clips, voice-over and music
  on MuAPI, and assembles final.mp4 with ffmpeg. No captions. Use when asked to make one of
  these animation shorts, or to write/plan a story for one.
---

# Toon Shorts

Everything lives in `toon-shorts/`. Read `toon-shorts/STYLE_GUIDE.md` first - it is the
analysis of the reference shorts (look, characters, camera, pacing, writing, sound) and
the rules below come from it.

## Requirements
- `MUAPI_API_KEY` in the environment (or `toon-shorts/.env`), from https://muapi.ai
- `ffmpeg`/`ffprobe`, Python 3. The network must allow `api.muapi.ai` and the CDN hosts
  MuAPI returns result URLs on.

## Workflow (one project = `toon-shorts/out/<project>/story.json`)
1. **Write the story** (approval gate - show the user the script before spending credits).
   Copy `toon-shorts/story.example.json`. Follow the writing rules in STYLE_GUIDE.md sec. 5:
   hook line in the first 2 s, one-line-per-shot narration, 14-20 shots for 60 s,
   escalate, then a twist/punchline in the last 2-3 shots.
   Define every recurring character once in `characters` (hat + outfit + colours + face quirk)
   and every place once in `locations`; shots refer to them by key.
2. `python3 toon-shorts/scripts/characters.py toon-shorts/out/<p>` - character sheets.
   **Approval gate:** show the sheets; regenerate any that are off-model.
3. `python3 toon-shorts/scripts/keyframes.py toon-shorts/out/<p>` - one still per shot,
   character shots conditioned on the sheets.
4. `python3 toon-shorts/scripts/clips.py toon-shorts/out/<p>` - image-to-video per shot.
5. `python3 toon-shorts/scripts/voiceover.py toon-shorts/out/<p>` - narration + music bed.
6. `python3 toon-shorts/scripts/assemble.py toon-shorts/out/<p>` -> `final.mp4`.

Every API stage accepts `--dry-run` (prints the prompts, spends nothing) and is resumable:
finished shots are skipped, so delete a shot's `keyframe_url` / `clip_path` (or its
`audio/narr_<id>.mp3`) in story.json to redo just that shot.

## Rules
- No captions, no on-screen text, no watermark (the user asked for none).
- One narrator voice per film. Default `English_magnetic_voiced_man` at speed 1.05; see
  `vendor/muapi-director/references/voices.md` for others.
- Model slugs and the reference-image parameter are set in story.json
  (`image_model`, `ref_image_model`, `ref_param`, `video_model`). If a MuAPI call returns
  4xx, check that model's page on muapi.ai for its exact parameter names.
- Original stories and characters only - the style is the reference, not the IP.
