#!/usr/bin/env python3
"""
The "toon-shorts" look, distilled from the reference TikTok shorts:
flat 2D cartoon characters composited into rich, softly lit 3D environments.

Every image / video prompt in the pipeline is built from these blocks so the
look stays consistent from shot to shot.
"""

# --- 1. World / render look -------------------------------------------------
WORLD = (
    "Stylized 3D-rendered environment that looks like a cozy indie-game diorama: "
    "soft global illumination, warm practical lights (lanterns, lamps, neon, moonlight), "
    "light volumetric haze, detailed handmade props, slightly chunky proportions, "
    "painterly textures, shallow cinematic depth of field."
)

# --- 2. Character look (the signature) ---------------------------------------
CHARACTER = (
    "Characters are FLAT 2D hand-drawn cartoon figures composited into the 3D scene, "
    "like a cel-animated sticker standing in a game world: "
    "a big perfectly round white head with a thick dark-brown outline, "
    "a minimal face (small dot or half-lidded line eyes, simple brow strokes, tiny mouth), "
    "an iconic hat or hairstyle that identifies the character, "
    "a rounded bean / capsule-shaped torso that IS the clothing (flat colour, simple details), "
    "stick-thin dark outlined arms and legs with small round hands, no neck. "
    "Clean flat cel shading on the characters, soft contact shadow where they touch the ground."
)

# --- 3. Framing ---------------------------------------------------------------
FRAMING = {
    "9:16": "Vertical 9:16 phone frame; keep the subject in the middle third, "
            "leave the top 15% and bottom 20% free of key action.",
    "16:9": "Widescreen 16:9 frame, subject on a rule-of-thirds line.",
    "1:1": "Square frame, subject centred.",
}

SHOT_SIZE = {
    "EST": "establishing wide shot of the whole location, characters small in frame",
    "WIDE": "wide shot, full body characters inside the environment",
    "MEDIUM": "medium shot, character from the knees up, environment behind",
    "CLOSE": "close-up, head and shoulders filling the frame, background soft-focus",
    "INSERT": "macro insert shot of a single prop or detail, no characters or only a hand",
    "POV": "first-person POV shot from the character's eyes, hands/tool visible at frame bottom",
    "TOP": "top-down overhead shot",
}

NEGATIVE = (
    "No on-screen text, no captions, no subtitles, no watermark, no logos. "
    "No realistic humans, no 3D-modelled characters, no anime style."
)

# --- 4. Motion vocabulary for image-to-video ---------------------------------
CAMERA = {
    "static": "locked-off static camera",
    "push_in": "slow smooth dolly push-in toward the subject",
    "pull_out": "slow dolly pull-out revealing the environment",
    "track": "camera tracks sideways alongside the character",
    "orbit": "slow 3D orbit around the subject (parallax on the 3D set)",
    "crane_down": "camera cranes down from above into the scene",
    "fly_through": "smooth FPV fly-through moving forward through the environment",
    "whip": "fast whip-pan that settles on the subject",
    "handheld_pov": "first-person handheld POV with subtle sway",
}


def framing(aspect):
    return FRAMING.get(aspect, FRAMING["9:16"])


def character_sheet_prompt(name, look, aspect="9:16"):
    """Prompt for a clean reference sheet of one character (used for consistency)."""
    return (
        f"Character reference sheet for '{name}'. {CHARACTER} "
        f"This character: {look}. "
        "Show the character three times side by side: front view, three-quarter view, side view, "
        "standing neutral pose, on a plain light-grey studio background, full body, even lighting. "
        f"{NEGATIVE}"
    )


def shot_prompt(shot, story, aspect="9:16"):
    """Prompt for one keyframe still."""
    locs = story.get("locations", {})
    chars = story.get("characters", {})
    loc = locs.get(shot.get("location"), shot.get("location", ""))
    cast = [f"{c} ({chars[c]})" if c in chars else c for c in shot.get("characters", [])]
    size = SHOT_SIZE.get(shot.get("shot_size", "MEDIUM"), shot.get("shot_size", ""))
    parts = [
        WORLD,
        CHARACTER if cast else "",
        f"SCENE: {loc}." if loc else "",
        f"CAST: {'; '.join(cast)}." if cast else "",
        f"ACTION / MOMENT: {shot['visual']}.",
        f"SHOT: {size}.",
        f"MOOD / LIGHT: {shot.get('mood', story.get('mood', 'warm, playful, slightly mischievous'))}.",
        framing(aspect),
        "If reference images are given, keep each character EXACTLY as drawn there "
        "(same hat, outfit colours, face style, outline weight)." if cast else "",
        NEGATIVE,
    ]
    return " ".join(p for p in parts if p)


def motion_prompt(shot):
    """Prompt for animating one keyframe into a clip."""
    cam = CAMERA.get(shot.get("camera", "push_in"), shot.get("camera", ""))
    act = shot.get("motion") or "the character breathes, blinks and shifts weight; ambient props move gently"
    return (
        "Animate this frame as a short cartoon shot. "
        f"CAMERA: {cam} - the 3D environment moves with real parallax and depth. "
        f"CHARACTER ACTION: {act}. "
        "Characters stay FLAT 2D cel-drawn cut-outs with thick outlines, snappy bouncy cartoon timing, "
        "squash-and-stretch on big moves, expressive face changes (eye squints, eyebrow raises, grins). "
        "AMBIENT: subtle life in the set - flickering light, drifting dust/snow/smoke, swaying foliage. "
        "Keep the character design identical across the clip; no morphing, no melting. "
        "No text, no captions, no subtitles appear. No talking lip-sync unless stated."
    )
