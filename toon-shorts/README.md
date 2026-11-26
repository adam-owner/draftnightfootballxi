# toon-shorts

A pipeline for ~60-second vertical narrated cartoon shorts in the style of the reference
clips: flat 2D characters with round white heads inside cozy, softly lit 3D worlds, a
deadpan narrator, and a twist at the end. No captions.

- **What the style is:** [`STYLE_GUIDE.md`](STYLE_GUIDE.md)
- **How Claude should drive it:** [`../.claude/skills/toon-shorts/SKILL.md`](../.claude/skills/toon-shorts/SKILL.md)
- **Voice-over/back-end skill it is built on:** [`../vendor/muapi-director`](../vendor/muapi-director)
  (MIT, from github.com/Anil-matcha/vox-ai-motion-graphics-generator; `muapi_client.py`
  and `provider.py` are copied from it unchanged)

## Setup

```bash
export MUAPI_API_KEY=...          # https://muapi.ai  (or put it in toon-shorts/.env)
# needs ffmpeg + ffprobe and python3 (standard library only)
```

## Make a short

```bash
mkdir -p toon-shorts/out/my-short
cp toon-shorts/story.example.json toon-shorts/out/my-short/story.json   # then write your story
cd toon-shorts/scripts
python3 characters.py ../out/my-short   # character reference sheets  -> check them
python3 keyframes.py  ../out/my-short   # one still per shot (on-model via the sheets)
python3 clips.py      ../out/my-short   # image-to-video per shot
python3 voiceover.py  ../out/my-short   # narration per shot + music bed
python3 assemble.py   ../out/my-short   # -> ../out/my-short/final.mp4
```

- `--dry-run` on any API stage prints the prompts and spends nothing.
- Stages resume: finished shots are skipped. To redo one shot, delete its `keyframe_url`
  / `clip_path` from story.json (and the clip file), or `audio/narr_<id>.mp3`.
- Your own voice: record `audio/narr_<id>.mp3` per shot and skip `voiceover.py`, or set
  `voice.clone_ref` to a clean 10-30 s recording to clone it.
- No music: set `"music": null`.

## story.json

| field | meaning |
| --- | --- |
| `characters` | key -> one-line look (hat, hair, face quirk, torso colour/outfit, signature prop) |
| `locations` | key -> one-line set description |
| `shots[]` | `id`, `location`, `characters[]`, `shot_size` (EST/WIDE/MEDIUM/CLOSE/INSERT/POV/TOP), `camera` (static/push_in/pull_out/track/orbit/crane_down/fly_through/whip/handheld_pov), `visual` (the still), `motion` (what moves), `narration` (one line), optional `hold` (min seconds) |
| `voice` | `voice_id`, `speed`, `delivery`, optional `clone_ref` |
| `music` | text prompt for an instrumental bed, or null |
| `mix` | `voice`, `music` (bed level), `gap` (s between lines), `min_shot`, `lufs` |
| models | `image_model`, `ref_image_model`, `ref_param`, `video_model`, `voice_model`, `music_model` |

Shot length follows its narration line, so the voice drives the edit.

## Untested parts

None of this has been run against MuAPI yet: the session that wrote it had no API key
and could not reach api.muapi.ai. `assemble.py` was tested end to end on synthetic
clips and audio. Most likely to need adjusting on a first real run: the
`ref_image_model` slug and its reference-image parameter (`ref_param`), which differ
between MuAPI models.
